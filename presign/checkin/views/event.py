from django.views.generic import DetailView
from django.views.generic.edit import ModelFormMixin

from presign.base.models import Event
from presign.control.constants import STATE_SETTINGS

from presign.base.models import Participant as BaseParticipant


class EventDetailView(DetailView):
    model = Event
    template_name = "checkin/event/detail.html"

    def get_object(self, *args):
        return self.request.event

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["state_settings"] = STATE_SETTINGS

        context['participants'] = BaseParticipant.objects.all()
        return context
