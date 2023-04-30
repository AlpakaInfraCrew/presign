from django.shortcuts import redirect
from django.urls import reverse

from . import event, organizer, participant, questionnaire, user


def index(*args, **kwargs):
    return redirect(reverse("control:user-organizers"))


__all__ = ["index", "event", "organizer", "participant", "questionnaire", "user"]
