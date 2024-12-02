import uuid

from django.db import models

from presign.base.fields import I18nCharField
from presign.base.models import User, TextMixin, Event

from django.utils.translation import gettext_lazy as _


class ParticipantStates(models.TextChoices):
    # Step 1: Signup, orga reviews questionnaire 1 and approved / rejects the user
    UNKNOWN = "NEW", _("Unknown")
    CHECKED_IN = "CIN", _("Checked In")
    CHECKED_OUT = "COU", _("Checked Out")
    LEFT = "LFT", _("Left")


# Create your models here.
class Participant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    base_participant = models.ForeignKey(User, models.CASCADE)
    last_change = models.DateTimeField

    state = models.CharField(
        choices=ParticipantStates.choices, default=ParticipantStates.UNKNOWN, max_length=3
    )

    def __str__(self) -> str:
        return str(self.base_participant.get_full_name())


class Location(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = I18nCharField(max_length=50)
    event = models.ForeignKey(Event, models.CASCADE)
