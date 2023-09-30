import uuid

from django.db import models
from django.db.models.functions import Lower

from simple_history.models import HistoricalRecords

from ..fields import I18nCharField
from .texts import TextMixin, email_hierarkey, status_hierarkey
from .user import User


@email_hierarkey.add()
@status_hierarkey.add()
class Organizer(TextMixin, models.Model):
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
