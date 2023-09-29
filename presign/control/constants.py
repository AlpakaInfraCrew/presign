from django.utils.translation import gettext_lazy as _

from presign.base.models import ParticipantStateActions, ParticipantStates

STATE_CHANGE_STRINGS = {
    ParticipantStateActions.APPROVE: {
        "btn_text": _("Approve"),
        "btn_type": "success",
        "success_msg": _("Participant was approved"),
        "confirmation_question": _(
            "Are you sure that you want to approve this participant?"
        ),
    },
    ParticipantStateActions.REJECT: {
        "btn_text": _("Reject"),
        "btn_type": "danger",
        "success_msg": _("Participant was rejected"),
        "confirmation_question": _(
            "Are you sure that you want to reject this participant?"
        ),
    },
    ParticipantStateActions.REQUEST_CHANGES: {
        "btn_text": _("Request Changes"),
        "btn_type": "warning",
        "success_msg": _("Participant was asked for changes"),
        "confirmation_question": _(
            "Are you sure that you want to ask this participant for changes?"
        ),
    },
    ParticipantStateActions.UNREJECT: {
        "btn_text": _("Un-Reject"),
        "btn_type": "warning",
        "success_msg": _("Participant was un-rejected"),
        "confirmation_question": _(
            "Are you sure that you want to un-reject this participant?"
        ),
    },
    ParticipantStateActions.CANCEL: {
        "btn_text": _("Cancel application"),
        "btn_type": "danger",
        "success_msg": _("Participant was cancelled"),
        "confirmation_question": _(
            "Are you sure that you want to cancel this participant?"
        ),
    },
    ParticipantStateActions.CONFIRM: {
        "btn_text": _("Confirm participant"),
        "btn_type": "success",
        "success_msg": _("Participant was confirmed"),
        "confirmation_question": _(
            "Are you sure that you want to confirm this participant?"
        ),
    },
    ParticipantStateActions.WITHDRAW: {
        "btn_text": _("Withdraw Application"),
    },
}

STATE_SETTINGS = {
    ParticipantStates.NEW: {
        "pill_color": "primary",
        "transition_buttons": [
            ParticipantStateActions.REJECT,
            ParticipantStateActions.REQUEST_CHANGES,
            ParticipantStateActions.APPROVE,
        ],
    },
    ParticipantStates.REJECTED: {
        "pill_color": "danger",
        "transition_buttons": [
            ParticipantStateActions.UNREJECT,
            ParticipantStateActions.APPROVE,
        ],
    },
    ParticipantStates.Q1_CHANGES_REQUESTED: {
        "pill_color": "warning",
        "transition_buttons": [ParticipantStateActions.CANCEL],
    },
    ParticipantStates.APPROVED: {
        "pill_color": "warning",
        "transition_buttons": [ParticipantStateActions.CANCEL],
    },
    ParticipantStates.NEEDS_REVIEW: {
        "pill_color": "warning",
        "transition_buttons": [
            ParticipantStateActions.CANCEL,
            ParticipantStateActions.REQUEST_CHANGES,
            ParticipantStateActions.CONFIRM,
        ],
    },
    ParticipantStates.Q2_CHANGES_REQUESTED: {
        "pill_color": "warning",
        "transition_buttons": [ParticipantStateActions.CANCEL],
    },
    ParticipantStates.CONFIRMED: {
        "pill_color": "success",
        "transition_buttons": [ParticipantStateActions.CANCEL],
    },
    ParticipantStates.WITHDRAWN: {"pill_color": "danger", "transition_buttons": []},
    ParticipantStates.CANCELLED: {"pill_color": "danger", "transition_buttons": []},
}
