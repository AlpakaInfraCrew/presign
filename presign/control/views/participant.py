from typing import Optional

from django.contrib import messages
from django.db.models import QuerySet
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView
from django.views.generic.list import ListView

from django_scopes import scope

from presign.base.exceptions import ParticipantStateChangeException
from presign.base.models import Participant, ParticipantStates

from ..forms import ParticipantInternalForm

STATE_CHANGE_STRINGS = {
    "approve": {
        "btn_text": _("Approve"),
        "btn_type": "success",
        "success_msg": _("Participant was approved"),
        "confirmation_question": _(
            "Are you sure that you want to approve this participant?"
        ),
    },
    "reject": {
        "btn_text": _("Reject"),
        "btn_type": "danger",
        "success_msg": _("Participant was rejected"),
        "confirmation_question": _(
            "Are you sure that you want to reject this participant?"
        ),
    },
    "request_changes": {
        "btn_text": _("Request Changes"),
        "btn_type": "warning",
        "success_msg": _("Participant was asked for changes"),
        "confirmation_question": _(
            "Are you sure that you want to ask this participant for changes?"
        ),
    },
    "unreject": {
        "btn_text": _("Un-Reject"),
        "btn_type": "warning",
        "success_msg": _("Participant was un-rejected"),
        "confirmation_question": _(
            "Are you sure that you want to un-reject this participant?"
        ),
    },
    "cancel": {
        "btn_text": _("Cancel application"),
        "btn_type": "danger",
        "success_msg": _("Participant was cancelled"),
        "confirmation_question": _(
            "Are you sure that you want to cancel this participant?"
        ),
    },
    "confirm": {
        "btn_text": _("Confirm participant"),
        "btn_type": "success",
        "success_msg": _("Participant was confirmed"),
        "confirmation_question": _(
            "Are you sure that you want to confirm this participant?"
        ),
    },
}

STATE_SETTINGS = {
    ParticipantStates.NEW: {
        "pill_color": "primary",
        "transition_buttons": ["reject", "request_changes", "approve"],
    },
    ParticipantStates.REJECTED: {
        "pill_color": "danger",
        "transition_buttons": ["unreject", "approve"],
    },
    ParticipantStates.Q1_CHANGES_REQUESTED: {
        "pill_color": "warning",
        "transition_buttons": ["cancel"],
    },
    ParticipantStates.APPROVED: {
        "pill_color": "warning",
        "transition_buttons": ["cancel"],
    },
    ParticipantStates.NEEDS_REVIEW: {
        "pill_color": "warning",
        "transition_buttons": ["cancel", "request_changes", "confirm"],
    },
    ParticipantStates.Q2_CHANGES_REQUESTED: {
        "pill_color": "warning",
        "transition_buttons": ["cancel"],
    },
    ParticipantStates.CONFIRMED: {
        "pill_color": "success",
        "transition_buttons": ["cancel"],
    },
    ParticipantStates.WITHDRAWN: {"pill_color": "danger", "transition_buttons": []},
    ParticipantStates.CANCELLED: {"pill_color": "danger", "transition_buttons": []},
}


class ParticipantListView(ListView):
    model = Participant
    template_name = "control/participant/list.html"

    def get_queryset(self):
        with scope(organizer=self.request.organizer, event=self.request.event):
            return (
                super()
                .get_queryset()
                .filter(
                    event=self.request.event, event__organizer=self.request.organizer
                )
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["state_settings"] = STATE_SETTINGS
        return context


class ParticipantView(DetailView):
    model = Participant

    def get_queryset(self):
        return Participant.objects.filter(event=self.request.event)

    def get_object(
        self, queryset: Optional[QuerySet[Participant]] = None
    ) -> Participant:
        if queryset is None:
            queryset = self.get_queryset()

        return Participant.objects.get(code=self.kwargs["code"])

    @cached_property
    def participant(self):
        return self.get_object()

    def get_participant_url(self):
        participant = self.get_object()
        return reverse(
            "control:participant-details",
            kwargs={
                "organizer": self.request.event.organizer.slug,
                "event": self.request.event.slug,
                "code": participant.code,
            },
        )


class ParticipantDetailView(ParticipantView, UpdateView):
    template_name = "control/participant/detail.html"
    form_class = ParticipantInternalForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "answers": self.participant.get_answers_to(self.request.event),
                "event": self.request.event,
                "participant": self.get_object(),
                "state_change_strings": STATE_CHANGE_STRINGS,
                "state_settings": STATE_SETTINGS,
            }
        )
        return context

    def get_success_url(self) -> str:
        return self.get_participant_url()


class ParticipantStateChangeView(ParticipantView):
    def post(self, *args, **kwargs):
        action = self.kwargs["state_change"]
        if action not in STATE_CHANGE_STRINGS:
            raise Http404()
        success_msg = STATE_CHANGE_STRINGS[action]["success_msg"]

        try:
            self.participant.change_state(action)
        except ParticipantStateChangeException as e:
            messages.error(self.request, str(e))
        else:
            messages.success(self.request, success_msg)
        return redirect(self.get_participant_url())

    def get(self, *args, **kwargs):
        action = self.kwargs["state_change"]
        if action not in STATE_CHANGE_STRINGS:
            raise Http404()
        confirmation_question = STATE_CHANGE_STRINGS[action]["confirmation_question"]

        return render(
            self.request,
            "control/participant/state_change_confirmation.html",
            {
                "participant": self.participant,
                "question": confirmation_question,
                "state_change_strings": STATE_CHANGE_STRINGS,
            },
        )
