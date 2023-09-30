from django.dispatch import receiver

from presign.base.models import Participant, ParticipantLogEvent, ParticipantStates
from presign.base.signals import participant_logevent_display

from .constants import STATE_CHANGE_STRINGS


@receiver(
    signal=participant_logevent_display, dispatch_uid="presign.control.logevent_display"
)
def presign_control_logevent_display(
    sender: Participant, event: ParticipantLogEvent, **kwargs
):
    if event.event_type == "presign.base.change_state":
        action_text = STATE_CHANGE_STRINGS.get(event.data["action"], {}).get(
            "success_msg", event.data["action"].title()
        )
        labels = dict(ParticipantStates.choices)
        return f"{action_text}. State changes from '{labels[event.data['old_state']]}' to '{labels[event.data['new_state']]}'"
