from typing import Optional

from django.contrib import messages
from django.db.models import QuerySet
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.functional import cached_property
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView
from django.views.generic.list import ListView

from django_scopes import scope

from presign.base.constants import CAN_CHANGE_Q1_AND_Q2_STATES, CAN_CHANGE_Q1_STATES
from presign.base.exceptions import (
    ActionEmailNotConfigured,
    ParticipantStateChangeException,
)
from presign.base.models import (
    Participant,
    ParticipantStates,
    QuestionBlock,
    QuestionnaireRole,
)

from ..constants import STATE_CHANGE_STRINGS, STATE_SETTINGS
from ..forms import ParticipantInternalForm


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

    @cached_property
    def questionnaires(self):
        if self.participant.state in CAN_CHANGE_Q1_STATES:
            return self.request.event.questionnaires.filter(
                eventquestionnaire__role=QuestionnaireRole.DURING_SIGNUP
            )
        elif self.participant.state in CAN_CHANGE_Q1_AND_Q2_STATES:
            return self.request.event.questionnaires.filter(
                eventquestionnaire__role__in=[
                    QuestionnaireRole.DURING_SIGNUP,
                    QuestionnaireRole.AFTER_APPROVAL,
                ]
            ).order_by("eventquestionnaire__role")
        elif self.participant.state == ParticipantStates.WITHDRAWN:
            return []
        else:
            raise ValueError("Participant not in a state that can change answers")

    @cached_property
    def blocks(self):
        blocks = []
        for questionnaire in self.questionnaires:
            blocks += list(
                QuestionBlock.objects.filter(questionnaire=questionnaire).exclude(
                    question=None
                )
            )
        return blocks


class ParticipantDetailView(ParticipantView, UpdateView):
    template_name = "control/participant/detail.html"
    form_class = ParticipantInternalForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["is_superuser"] = (
            self.request.user.is_authenticated and self.request.user.is_superuser
        )
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        answer_by_question = {}
        answers = self.participant.get_answers()
        for answer in answers:
            answer_by_question[answer.question] = answer

        context.update(
            {
                "answer_by_question": answer_by_question,
                "event": self.request.event,
                "participant": self.get_object(),
                "state_change_strings": STATE_CHANGE_STRINGS,
                "state_settings": STATE_SETTINGS,
                "blocks": self.blocks,
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
            self.participant.send_change_state_email(self.request, action)
        except ParticipantStateChangeException as e:
            messages.error(self.request, str(e))
        except ActionEmailNotConfigured as e:
            messages.warning(self.request, str(e))
            messages.success(self.request, success_msg)
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
