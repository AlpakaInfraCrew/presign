from django.core import signals

# First receiver that returns a truthy value will be displayed to the user
participant_logevent_display = signals.Signal()  # Args: ['event']
