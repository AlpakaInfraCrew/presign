from django.shortcuts import redirect
from django.urls import reverse

from . import event, location


def index(*args, **kwargs):
    return redirect(reverse("control:user-events"))


__all__ = ["index", "event", "location"]
