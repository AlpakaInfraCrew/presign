from django.db import models

from ..signals import participant_logevent_display
from .participant import Participant


class ParticipantLogEvent(models.Model):
    event_type = models.TextField()
    data = models.JSONField(default=dict)
    datetime = models.DateTimeField(auto_now_add=True)

    participant = models.ForeignKey(
        Participant, on_delete=models.CASCADE, related_name="log_events"
    )

    def display(self) -> str:
        for _, response in participant_logevent_display.send(
            self.participant, event=self
        ):
            if response:
                return response
        return self.event_type
