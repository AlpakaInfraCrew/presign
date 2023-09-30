import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django_scopes import ScopedManager
from simple_history.models import HistoricalRecords

from ..fields import DateTimeLocalModelField, I18nCharField, I18nTextField
from .texts import TextMixin, email_hierarkey, status_hierarkey


@email_hierarkey.add(parent_field="organizer")
@status_hierarkey.add(parent_field="organizer")
class Event(TextMixin, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    history = HistoricalRecords()

    organizer = models.ForeignKey("Organizer", on_delete=models.CASCADE)
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
