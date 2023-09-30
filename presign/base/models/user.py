import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q

from django_scopes import scope
from simple_history.models import HistoricalRecords


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    history = HistoricalRecords()

    def has_organizer_permission(self, organizer):
        return organizer.members.contains(self)

    def has_event_permission(self, event):
        return self.has_organizer_permission(event.organizer)

    def get_organizers(self):
        from .organizer import Organizer  # Placed here to break circular imports

        with scope(user=self):
            return Organizer.objects.filter(members=self)

    def get_events(self):
        from .event import Event  # Placed here to break circular imports

        with scope(organizer=None):
            return Event.objects.filter(organizer__members=self)

    def get_visible_questionnaires(self):
        from .questions import Questionnaire  # Placed here to break circular imports

        return Questionnaire.objects.filter(
            Q(organizer__in=self.get_organizers()) | Q(is_public=True)
        )

    def get_editable_questionnaires(self):
        from .questions import Questionnaire  # Placed here to break circular imports

        return Questionnaire.objects.filter(organizer__in=self.get_organizers())
