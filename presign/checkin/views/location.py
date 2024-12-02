from typing import Dict, Any
from django import forms

from django.urls import reverse
from django.views.generic import CreateView, DetailView
from django_scopes import scope

from presign.base.models import Event
from presign.checkin.models import Location
from presign.control.constants import STATE_SETTINGS

from presign.checkin.models import Location, Participant as CheckinParticipant
from presign.base.models import Participant as BaseParticipant


class LocationDetailView(DetailView):
    model = Location
    template_name = "checkin/location/detail.html"

    def get_object(self, *args):
        return self.request.location

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["state_settings"] = STATE_SETTINGS

        context['participants'] = BaseParticipant.objects.all()

        return context


class CreateLocationForm(forms.ModelForm):

    def __init__(self, *args, event, **kwargs):
        super().__init__(*args, **kwargs)
        self.event = event

    class Meta:
        model = Location
        fields = [
            "name",
        ]

    def save(self, *args, **kwargs):
        self.instance.event = Event.objects.filter(
            id=self.event
        ).first()
        self.instance = super().save(*args, **kwargs)

        return self.instance


class LocationCreateView(CreateView):
    model = Location
    form_class = CreateLocationForm
    template_name = "checkin/location/create.html"

    def get_success_url(self) -> str:
        with scope(user=self.request.user):
            return reverse(
                "checkin:event-overview",
                kwargs={
                    "organizer": self.request.organizer.slug,
                    "event": self.request.event.slug,
                },
            )

    def get_form_kwargs(self) -> Dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["event"] = self.request.event.id
        return kwargs

