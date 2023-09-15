from .models import ParticipantStates

CAN_CHANGE_Q1_STATES = [
    ParticipantStates.NEW,
    ParticipantStates.Q1_CHANGES_REQUESTED,
]
CAN_CHANGE_Q1_AND_Q2_STATES = [
    ParticipantStates.APPROVED,
    ParticipantStates.NEEDS_REVIEW,
    ParticipantStates.Q2_CHANGES_REQUESTED,
    ParticipantStates.CONFIRMED,
]
