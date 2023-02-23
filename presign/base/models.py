import datetime
import string
import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _

from django_scopes import ScopedManager, scope
from hierarkey.models import Hierarkey
from i18nfield.strings import LazyI18nString
from model_clone.models import CloneModel
from simple_history.models import HistoricalRecords

from .exceptions import ParticipantStateChangeException
from .fields import DateTimeLocalModelField, I18nCharField, I18nTextField

email_hierarkey = Hierarkey(attribute_name="email_texts")


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    history = HistoricalRecords()

    def has_organizer_permission(self, organizer):
        return organizer.members.contains(self)

    def has_event_permission(self, event):
        return self.has_organizer_permission(event.organizer)

    def get_organizers(self):
        with scope(user=self):
            return Organizer.objects.filter(members=self)

    def get_events(self):
        with scope(organizer=None):
            return Event.objects.filter(organizer__members=self)

    def get_visible_questionnaires(self):
        return Questionnaire.objects.filter(
            Q(organizer__in=self.get_organizers()) | Q(is_public=True)
        )

    def get_editable_questionnaires(self):
        return Questionnaire.objects.filter(organizer__in=self.get_organizers())


class Organizer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    history = HistoricalRecords()

    slug = models.SlugField(unique=True)

    name = I18nCharField(max_length=50)

    members = models.ManyToManyField(User)

    class Meta:
        constraints = [
            models.UniqueConstraint(Lower("slug"), name="unique_organizer_lower_slug")
        ]

    def __str__(self) -> str:
        return str(self.name)


@email_hierarkey.add()
class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    history = HistoricalRecords()

    organizer = models.ForeignKey(Organizer, on_delete=models.CASCADE)
    objects = ScopedManager(organizer="organizer")

    name = I18nCharField(max_length=50)
    slug = models.SlugField()
    description = I18nTextField(default="", blank=True)

    enabled = models.BooleanField(default=False)

    event_date = DateTimeLocalModelField()
    signup_start = DateTimeLocalModelField(null=True, blank=True)
    signup_end_shown = DateTimeLocalModelField(
        verbose_name=_("Shown Signup End"), null=True, blank=True
    )
    signup_end = DateTimeLocalModelField(null=True, blank=True)
    lock_date = DateTimeLocalModelField(null=True, blank=True)

    status_texts = models.JSONField(default=dict)

    questionnaires = models.ManyToManyField(
        "Questionnaire", related_name="events", through="EventQuestionnaire"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("slug"), "organizer", name="unique_event_slug_per_organizer"
            ),
        ]

    def get_absolute_url(self):
        return reverse(
            "signup:participant-signup",
            kwargs={"organizer": self.organizer.slug, "event": self.slug},
        )

    def has_signup_started(self):
        if not self.signup_start:
            return True
        return self.signup_start < timezone.now()

    def is_public(self):
        if not self.enabled:
            return False

        if not self.has_signup_started():
            return False

        return True

    @property
    def calculated_signup_end(self):
        if self.signup_end:
            return self.signup_end
        return self.event_date

    @property
    def calculated_lock_date(self):
        if self.lock_date:
            return self.lock_date
        return self.event_date

    @property
    def calculated_signup_end_show(self):
        if self.signup_end_shown:
            return self.signup_end_shown
        return self.calculated_signup_end

    def can_signup(self):
        if not self.is_public():
            return False

        if self.calculated_signup_end < timezone.now():
            return False

        return True

    def __str__(self) -> str:
        return str(self.name)

    def questionnaire_signup(self):
        return self.questionnaires.filter(
            eventquestionnaire__role=QuestionnaireRole.DURING_SIGNUP
        ).first()

    def questionnaire_after_approval(self):
        return self.questionnaires.filter(
            eventquestionnaire__role=QuestionnaireRole.AFTER_APPROVAL
        ).first()

    def can_be_enabled(self):
        return (
            self.questionnaire_signup() is not None
            and self.questionnaire_after_approval() is not None
        )

    def clean(self):
        if self.signup_start and self.signup_start >= self.calculated_signup_end:
            raise ValidationError(_("Signup Start must be before Signup End"))

        if (
            self.signup_end_shown
            and self.signup_end_shown >= self.calculated_signup_end
        ):
            raise ValidationError(_("Shown Signup End must be before Signup End"))

    def get_action_email_texts(self, action: "ParticipantStateActions"):
        action_texts = self.email_texts.get(action, as_type=dict, default="{}")
        return {
            "subject": LazyI18nString(action_texts.get("subject", {})),
            "body": LazyI18nString(action_texts.get("body", {})),
        }


class QuestionnaireRole(models.IntegerChoices):
    # Step 1: Signup, pre-review
    DURING_SIGNUP = 1, _("During Signup")
    # Step 2: After approval
    AFTER_APPROVAL = 2, _("After Approval")


class EventQuestionnaire(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    history = HistoricalRecords()

    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    questionnaire = models.ForeignKey("Questionnaire", on_delete=models.CASCADE)

    role = models.IntegerField(choices=QuestionnaireRole.choices)

    objects = ScopedManager(organizer="event__organizer")

    class Meta:
        ordering = ("role",)

        constraints = [
            models.UniqueConstraint(
                "event", "role", name="one_questionnaire_per_event_and_role"
            ),
        ]


class ParticipantStates(models.TextChoices):
    # Step 1: Signup, orga reviews questionnaire 1 and approved / rejects the user
    NEW = "NEW", _("New signup")
    REJECTED = "REJ", _("Rejected")
    Q1_CHANGES_REQUESTED = "Q1C", _("Changes requested in questionnaire 1")
    # Step 2: Participant receives documents, fills out second questionnaire, orga reviews questionnaire
    APPROVED = "APP", _("Approved")
    NEEDS_REVIEW = "NER", _("Needs review")
    Q2_CHANGES_REQUESTED = "Q2C", _("Changes requested in questionnaire 2")
    # Step 3a: Participant did all their duties, let's welcome them to the event
    CONFIRMED = "CON", _("Confirmed")
    # Step 3b: :'(
    WITHDRAWN = "WIT", _("Withdrawn")  # Participant withdrew their signup
    CANCELLED = "CAN", _("Cancelled")  # Orga cancelled the participation


class ParticipantStateActions(models.TextChoices):
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"
    UNREJECT = "unreject"
    ANSWERS_SAVED = "answers_saved"
    CANCEL = "cancel"
    WITHDRAW = "withdraw"
    CONFIRM = "confirm"


def generate_participant_secret():
    for _i in range(settings.PRESIGN_SECRET_RETRIES):
        secret = get_random_string(
            length=32, allowed_chars=string.ascii_lowercase + string.digits
        )
        if not Participant.objects.filter(secret=secret).exists():
            return secret
    raise ValidationError("Could not generate participant secret")


def generate_participant_code():
    for _i in range(settings.PRESIGN_SECRET_RETRIES):
        code = get_random_string(
            length=10, allowed_chars=string.ascii_lowercase + string.digits
        )
        if not Participant.objects.filter(code=code).exists():
            return code
    raise ValidationError("Could not generate participant code")


class Participant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    history = HistoricalRecords()

    event = models.ForeignKey(Event, on_delete=models.CASCADE)

    email = models.EmailField()

    code = models.CharField(
        max_length=10, default=generate_participant_code, unique=True
    )
    secret = models.CharField(
        max_length=32, default=generate_participant_secret, unique=True
    )

    state = models.CharField(
        choices=ParticipantStates.choices, default=ParticipantStates.NEW, max_length=3
    )
    public_comment = I18nTextField(
        blank=True,
        null=True,
        help_text=_(
            "This text <strong>will be shown to the participant</strong> on their overview page. "
            "You can for example use it for requesting more information."
        ),
    )

    internal_comment = I18nTextField(
        blank=True,
        help_text=_(
            "The text entered in this field will <em>not</em> be shown to the participant."
        ),
    )

    objects = ScopedManager(organizer="event__organizer", event="event")

    def __str__(self) -> str:
        return self.email

    def get_answers(self):
        return QuestionAnswer.objects.filter(participant=self).order_by(
            "question__block__questionnaire",
            "question__block__order",
            "question__order",
        )

    # ### Participant State Machine ###
    #                                                       +------------+
    #                                                       |  REJECTED  |
    #                                                       +------------+------>***
    #                        ** unreject                       | **  ^
    #                                          answers_saved   v     | reject
    #               +------------------------+---------------->++----+
    # +-------------+  Q1_CHANGES_REQUESTED  |                 | NEW +-------------------------------------+
    # |             +------------------------+<----------------+--+--+                                     |
    # |                                         request_changes   |                                        |
    # |                                                           v                                        |
    # |                                        ***--------->+-----+----+      withdraw                     v
    # |<----------------------------------------------------+ APPROVED +-----------------------------------+
    # |                     *                               +-----+----+                                   |
    # |                     ^                                     | answers_saved             *            |
    # |                     |             answers_saved           v                           |            |
    # |          +----------+-----------+---------------->+--------------+                    |            |
    # |<---------+ Q2_CHANGES_REQUESTED |                 | NEEDS_REVIEW +--------------------+            |
    # |          +----------------------+<----------------+--+----+------+                    |            |
    # |                                    request_changes   |    |                           |withdraw    |
    # |                                                      |    |                           |            |
    # |                  +-----------------------------------+    |confirm                    |            |
    # |                  v         cancel                         v                           v            |
    # |            +------------+                           +-----------+               +-----------+      |
    # +----------->| CANCELLED  |<--------------------------+ CONFIRMED +-------------->| WITHDRAWN +<-----+
    #   cancel     +------------+              cancel       +-----------+  withdraw     +-----------+

    STATE_CHANGES = {
        ParticipantStates.NEW: {
            ParticipantStateActions.APPROVE: ParticipantStates.APPROVED,
            ParticipantStateActions.REJECT: ParticipantStates.REJECTED,
            ParticipantStateActions.REQUEST_CHANGES: ParticipantStates.Q1_CHANGES_REQUESTED,
        },
        ParticipantStates.REJECTED: {
            ParticipantStateActions.UNREJECT: ParticipantStates.NEW,
            ParticipantStateActions.APPROVE: ParticipantStates.APPROVED,
        },
        ParticipantStates.Q1_CHANGES_REQUESTED: {
            ParticipantStateActions.ANSWERS_SAVED: ParticipantStates.NEW,
            ParticipantStateActions.CANCEL: ParticipantStates.CANCELLED,
        },
        ParticipantStates.APPROVED: {
            ParticipantStateActions.ANSWERS_SAVED: ParticipantStates.NEEDS_REVIEW,
            ParticipantStateActions.WITHDRAW: ParticipantStates.WITHDRAWN,
            ParticipantStateActions.CANCEL: ParticipantStates.CANCELLED,
        },
        ParticipantStates.NEEDS_REVIEW: {
            ParticipantStateActions.REQUEST_CHANGES: ParticipantStates.Q2_CHANGES_REQUESTED,
            ParticipantStateActions.CONFIRM: ParticipantStates.CONFIRMED,
            ParticipantStateActions.WITHDRAW: ParticipantStates.WITHDRAWN,
            ParticipantStateActions.CANCEL: ParticipantStates.CANCELLED,
        },
        ParticipantStates.Q2_CHANGES_REQUESTED: {
            ParticipantStateActions.ANSWERS_SAVED: ParticipantStates.NEEDS_REVIEW,
            ParticipantStateActions.WITHDRAW: ParticipantStates.WITHDRAWN,
            ParticipantStateActions.CANCEL: ParticipantStates.CANCELLED,
        },
        ParticipantStates.CONFIRMED: {
            ParticipantStateActions.WITHDRAW: ParticipantStates.WITHDRAWN,
            ParticipantStateActions.CANCEL: ParticipantStates.CANCELLED,
        },
    }

    def change_state(self, action):
        state = ParticipantStates(self.state)
        next_state = self.STATE_CHANGES.get(state, {}).get(action)
        if next_state is None:
            raise ParticipantStateChangeException(
                _("Cannot perform {action} in state {state_label}").format(
                    action=action, state_label=state.label
                )
            )

        self.state = next_state
        self.save(update_fields=["state"])


class QuestionKind(models.TextChoices):
    NUMBER = "N", _("Number")
    STRING = "S", _("Text (one line)")
    TEXT = "TX", _("Multiline text")
    BOOL = "B", _("Yes/No")
    CHOICE = "C", _("Choose one from a list")
    MULTIPLE_CHOICE = "M", _("Choose multiple from a list")
    FILE = "F", _("File upload")
    DATE = "D", _("Date")
    TIME = "TI", _("Time")
    DATETIME = "DT", _("Date and time")
    PHONE = "PN", _("Phone number")
    EMAIL = "EM", _("Email address")


class Questionnaire(CloneModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    history = HistoricalRecords()

    name = I18nCharField(max_length=100)

    organizer = models.ForeignKey(Organizer, on_delete=models.CASCADE)
    is_public = models.BooleanField(default=False)

    _clone_fields = ("name",)
    _clone_m2o_or_o2m_fields = ("questionblock_set",)

    def can_user_update(self, user):
        return self.organizer in user.get_organizers()

    def __str__(self) -> str:
        return str(self.name)


class QuestionBlock(CloneModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    history = HistoricalRecords()

    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE)

    name = I18nCharField(max_length=100)
    order = models.IntegerField()

    _clone_fields = ("name", "order")
    _clone_m2o_or_o2m_fields = ("question_set",)

    class Meta:
        ordering = ("questionnaire", "order", "name")

    def __str__(self) -> str:
        return str(self.name)


class Question(CloneModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    history = HistoricalRecords()

    block = models.ForeignKey(QuestionBlock, on_delete=models.CASCADE)
    kind = models.CharField(choices=QuestionKind.choices, max_length=2)
    required = models.BooleanField()
    name = I18nCharField(max_length=255)
    help = I18nTextField(blank=True)
    order = models.PositiveBigIntegerField()

    class Meta:
        ordering = ("order", "name")

    def __str__(self) -> str:
        return str(self.name)

    _clone_fields = ("kind", "required", "name", "help", "order")
    _clone_m2o_or_o2m_fields = ("options",)


class QuestionOption(CloneModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    history = HistoricalRecords()

    question = models.ForeignKey(
        "Question",
        related_name="options",
        on_delete=models.CASCADE,
        limit_choices_to={
            "kind__in": [QuestionKind.MULTIPLE_CHOICE, QuestionKind.CHOICE]
        },
    )
    value = I18nCharField(verbose_name=_("Value"), max_length=255)
    order = models.IntegerField(default=0)

    _clone_fields = ("value", "order")

    class Meta:
        ordering = ("order",)

    def __str__(self):
        return f"{self.question.name}: {self.value}"


class QuestionAnswer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    history = HistoricalRecords()

    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    answer = models.TextField(blank=True, null=True)
    options = models.ManyToManyField(QuestionOption, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    changed_at = models.DateTimeField(auto_now=True)

    file = models.FileField(null=True)

    objects = ScopedManager(organizer="participant__event__organizer")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                "participant", "question", name="unique_participant_question"
            )
        ]

    def get_value(self):
        if self.question.kind == QuestionKind.NUMBER:
            if self.answer is None:
                return None
            return int(self.answer)
        elif self.question.kind in [QuestionKind.STRING, QuestionKind.TEXT]:
            return self.answer
        elif self.question.kind == QuestionKind.BOOL:
            return bool(self.answer)
        elif self.question.kind == QuestionKind.CHOICE:
            return self.options.get()
        elif self.question.kind == QuestionKind.MULTIPLE_CHOICE:
            return self.options.all()
        elif self.question.kind == QuestionKind.FILE:
            return self.file
        elif self.question.kind == QuestionKind.DATE:
            return datetime.date.fromisoformat(self.answer)
        elif self.question.kind == QuestionKind.TIME:
            return datetime.time.fromisoformat(self.answer)
        elif self.question.kind == QuestionKind.DATETIME:
            return datetime.datetime.fromisoformat(self.answer)
        elif self.question.kind in [QuestionKind.PHONE, QuestionKind.EMAIL]:
            return self.answer
        else:
            raise ValueError("Unknown QuestionKind")

    def set_value(self, value):
        if self.question.kind == QuestionKind.NUMBER:
            self.answer = str(value)
        elif self.question.kind in [QuestionKind.STRING, QuestionKind.TEXT]:
            self.answer = value
        elif self.question.kind == QuestionKind.BOOL:
            self.answer = str(value)
        elif self.question.kind == QuestionKind.CHOICE:
            self.options.clear()
            self.options.add(value)
        elif self.question.kind == QuestionKind.MULTIPLE_CHOICE:
            self.options.clear()
            self.options.add(*value)
        elif self.question.kind == QuestionKind.FILE:
            self.file = value
        elif self.question.kind in [
            QuestionKind.DATE,
            QuestionKind.TIME,
            QuestionKind.DATETIME,
        ]:
            self.answer = value.isoformat()
        elif self.question.kind in [QuestionKind.PHONE, QuestionKind.EMAIL]:
            self.answer = value
        else:
            raise ValueError("Unknown QuestionKind")

    def clean(self, *args, **kwargs):
        if not self.get_value() and self.question.required:
            raise ValidationError(
                _("Answers to required questions may not be false-y.")
            )

    def __str__(self) -> str:
        return str(self.get_value())

    def render_answer(self):
        if self.question.kind == QuestionKind.FILE:
            return render_to_string("questions/answers/file.html", {"answer": self})
        elif self.question.kind == QuestionKind.MULTIPLE_CHOICE:
            selected = self.get_value()
            return render_to_string(
                "questions/answers/multiple_choice.html",
                {"answer": self, "selected": selected},
            )
        elif self.question.kind == QuestionKind.CHOICE:
            selected = self.get_value()
            return render_to_string(
                "questions/answers/choice.html",
                {"answer": self, "selected": selected},
            )
        else:
            return self.get_value()
