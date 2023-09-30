import string
import uuid
from collections import defaultdict

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.db import models
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _

from django_scopes import ScopedManager
from simple_history.models import HistoricalRecords

from ..exceptions import ActionEmailNotConfigured, ParticipantStateChangeException
from ..fields import I18nTextField


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
    SUBMIT_APPLICATION = "submit_application"
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

    event = models.ForeignKey("base.Event", on_delete=models.CASCADE)

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
        from .questions import QuestionAnswer  # Placed here to break circular import

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
            ParticipantStateActions.WITHDRAW: ParticipantStates.WITHDRAWN,
        },
        ParticipantStates.REJECTED: {
            ParticipantStateActions.UNREJECT: ParticipantStates.NEW,
            ParticipantStateActions.APPROVE: ParticipantStates.APPROVED,
        },
        ParticipantStates.Q1_CHANGES_REQUESTED: {
            ParticipantStateActions.ANSWERS_SAVED: ParticipantStates.NEW,
            ParticipantStateActions.CANCEL: ParticipantStates.CANCELLED,
            ParticipantStateActions.WITHDRAW: ParticipantStates.WITHDRAWN,
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
        from .log import ParticipantLogEvent

        state = ParticipantStates(self.state)
        next_state = self.STATE_CHANGES.get(state, {}).get(action)
        if next_state is None:
            raise ParticipantStateChangeException(
                _("Cannot perform {action} in state {state_label}").format(
                    action=action, state_label=state.label
                )
            )

        self.state = next_state
        ParticipantLogEvent.objects.create(
            event_type="presign.base.change_state",
            participant=self,
            data={"old_state": state, "new_state": next_state, "action": action},
        )
        self.save(update_fields=["state"])

    def send_change_state_email(self, request, action):
        texts = self.event.get_action_email_texts(action)
        context_vars = defaultdict(
            str,
            {
                "participant_email": self.email,
                "event_name": self.event.name,
                "change_answer_url": request.build_absolute_uri(
                    reverse(
                        "signup:participant-update",
                        kwargs={
                            "organizer": self.event.organizer.slug,
                            "event": self.event.slug,
                            "code": self.code,
                            "secret": self.secret,
                        },
                    )
                ),
                "application_url": request.build_absolute_uri(
                    reverse(
                        "signup:participant-details",
                        kwargs={
                            "organizer": self.event.organizer.slug,
                            "event": self.event.slug,
                            "code": self.code,
                            "secret": self.secret,
                        },
                    )
                ),
            },
        )
        subject = str(texts["subject"]).format_map(context_vars)
        body = str(texts["body"]).format_map(context_vars)

        if not body:
            raise ActionEmailNotConfigured(
                _("No email was configured for this action.")
            )

        to = self.email

        html_content = render_to_string(
            "mail/participant/state_change.html",
            context={"subject": subject, "body": body},
        )
        msg = EmailMultiAlternatives(subject=subject, body=body, to=[to])
        msg.attach_alternative(html_content, "text/html")
        msg.send()
