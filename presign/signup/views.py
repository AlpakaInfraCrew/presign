from collections import defaultdict
from typing import List, Optional

from django.contrib import messages
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic.detail import DetailView

from django_scopes import scope

from presign.base.constants import CAN_CHANGE_Q1_AND_Q2_STATES, CAN_CHANGE_Q1_STATES
from presign.base.exceptions import (
    ActionEmailNotConfigured,
    ParticipantStateChangeException,
)
from presign.base.models import (
    Participant,
    ParticipantStateActions,
    ParticipantStates,
    QuestionAnswer,
    QuestionBlock,
    QuestionnaireRole,
)

from .forms import ParticipantForm, QuestionBlockForm


def can_update(participant, event):
    if participant.state not in CAN_CHANGE_Q1_STATES + CAN_CHANGE_Q1_AND_Q2_STATES:
        return False

    if timezone.now() >= event.calculated_lock_date:
        return False

    return True


def get_success_redirect(participant: Participant):
    return redirect(
        reverse(
            "signup:participant-details",
            kwargs={
                "organizer": participant.event.organizer.slug,
                "event": participant.event.slug,
                "code": participant.code,
                "secret": participant.secret,
            },
        )
    )


class ExistingParticipantMixin:
    @property
    def participant(self):
        raise NotImplementedError("Must implement `participant`")

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
        else:
            return (
                QuestionAnswer.objects.filter(participant=self.participant)
                .values_list("question__block__questionnaire", flat=True)
                .distinct()
            )

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


class ParticipantChangeView(View):
    @property
    def participant(self):
        raise NotImplementedError("Must implement `participant`")

    @property
    def questionnaires(self):
        raise NotImplementedError("`questionnaires` must be implemented")

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

    def get_forms(self, data=None, files=None):
        forms = []

        object_data = {}
        if self.participant:
            for answer in QuestionAnswer.objects.filter(
                participant=self.participant, question__block__in=self.blocks
            ):
                key = f"question_{answer.question_id}"
                object_data[key] = answer.get_value()

        for block in self.blocks:
            form = QuestionBlockForm(
                initial=object_data,
                data=data,
                question_block=block,
                files=files,
            )
            forms.append(form)
        return forms

    def get_context_data(self, forms=None):
        context = {}
        if forms is None:
            forms = self.get_forms()
        context.update({"forms": forms})
        return context

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())

    def post(self, request, *args, **kwargs):
        forms = self.get_forms(data=request.POST, files=request.FILES)
        is_valid = True
        for form in forms:
            is_valid = is_valid and form.is_valid()

        if is_valid:
            participant = self.save(forms)
            return get_success_redirect(participant)
        else:
            return render(
                request,
                self.template_name,
                self.get_context_data(forms=forms),
            )

    @transaction.atomic
    def save(self, forms_to_save):
        participant: Participant = self.participant
        answers: List[QuestionAnswer] = []

        for form in forms_to_save:
            if not form.is_valid():
                raise ValueError("You shall not save an invalid form")

            if not isinstance(form, ParticipantForm):
                for k, v in form.cleaned_data.items():
                    field = form.fields[k]
                    if v != "" and v is not None:
                        answer, _ = QuestionAnswer.objects.get_or_create(
                            question=field.question, participant=participant
                        )
                        answer.set_value(v)
                        answer.save()
                        answers.append(answer)

        return participant


class ParticipantSignupView(ParticipantChangeView):
    form_class = QuestionBlockForm
    template_name = "signup/signup.html"

    participant = None

    @cached_property
    def questionnaires(self):
        return [
            self.request.event.questionnaires.get(
                eventquestionnaire__role=QuestionnaireRole.DURING_SIGNUP
            )
        ]

    def get_forms(self, data=None, files=None):
        forms = [ParticipantForm(data=data, files=files)]
        forms += super().get_forms(data, files)
        return forms

    @transaction.atomic
    def save(self, forms_to_save):
        participant: Optional[Participant] = None
        for form in forms_to_save:
            if not form.is_valid():
                raise ValueError("You shall not save an invalid form")

            if isinstance(form, ParticipantForm):
                participant = form.instance
                participant.event = self.request.event

        if participant is None:
            raise ValueError("No participant form submitted")
        participant.save()
        self.participant = participant

        try:
            self.participant.send_change_state_email(
                self.request, ParticipantStateActions.SUBMIT_APPLICATION
            )
        except ActionEmailNotConfigured:
            pass

        return super().save(forms_to_save)

    def get(self, *args, **kwargs):
        if not self.request.event.can_signup():
            return render(self.request, "signup/signup_not_possible.html")
        return super().get(*args, **kwargs)

    def post(self, *args, **kwargs):
        if not self.request.event.can_signup():
            return render(self.request, "signup/signup_not_possible.html")
        return super().post(*args, **kwargs)


class ParticipantUpdateView(ParticipantChangeView):
    form_class = QuestionBlockForm
    template_name = "signup/update.html"

    @property
    def participant(self):
        if "code" not in self.kwargs or "secret" not in self.kwargs:
            raise ValueError("`code` or `secret` not found in kwargs")

        with scope(event=self.request.event):
            participant = Participant.objects.get(
                event=self.request.event,
                code=self.kwargs["code"],
                secret=self.kwargs["secret"],
            )

        if not can_update(participant, self.request.event):
            raise Http404("Participant not found or not updateable")

        return participant

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
        else:
            raise ValueError("Participant not in a state that can change answers")

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({"participant": self.participant})
        return context

    @transaction.atomic
    def save(self, forms_to_save):
        participant = super().save(forms_to_save=forms_to_save)
        self.update_state_machine(participant)
        return participant

    def update_state_machine(self, participant: Participant):
        if participant.state in [
            ParticipantStates.APPROVED,
            ParticipantStates.Q1_CHANGES_REQUESTED,
            ParticipantStates.Q2_CHANGES_REQUESTED,
        ]:
            participant.change_state(ParticipantStateActions.ANSWERS_SAVED)


class ParticipantDetailView(ExistingParticipantMixin, DetailView):
    model = Participant
    template_name = "signup/participant_details.html"

    NEUTRAL_STATES = [
        ParticipantStates.NEW,
        ParticipantStates.NEEDS_REVIEW,
    ]
    SUCCESS_STATES = [
        ParticipantStates.APPROVED,
        ParticipantStates.CONFIRMED,
    ]
    WARNING_STATES = [
        ParticipantStates.Q1_CHANGES_REQUESTED,
        ParticipantStates.Q2_CHANGES_REQUESTED,
    ]
    DANGER_STATES = [
        ParticipantStates.REJECTED,
        ParticipantStates.WITHDRAWN,
        ParticipantStates.CANCELLED,
    ]

    def get_object(self, queryset=None):
        return get_object_or_404(
            Participant,
            code=self.kwargs["code"],
            secret=self.kwargs["secret"],
            event=self.request.event,
        )

    @property
    def participant(self):
        return self.get_object()

    def get_status_text(self, participant: Participant):
        return str(participant.event.get_status_text(participant.state))

    def get_status_color(self, participant: Participant):
        if participant.state in self.NEUTRAL_STATES:
            return "info"
        if participant.state in self.SUCCESS_STATES:
            return "success"
        elif participant.state in self.WARNING_STATES:
            return "warning"
        elif participant.state in self.DANGER_STATES:
            return "danger"
        else:
            raise ValueError("Unknown State")

    def get_status_banner(self):
        banner_kwargs = {
            "event_name": self.participant.event.name,
            "change_answer_url": reverse(
                "signup:participant-update",
                kwargs={
                    "organizer": self.request.event.organizer.slug,
                    "event": self.request.event.slug,
                    "code": self.participant.code,
                    "secret": self.participant.secret,
                },
            ),
            "application_url": reverse(
                "signup:participant-details",
                kwargs={
                    "organizer": self.request.event.organizer.slug,
                    "event": self.request.event.slug,
                    "code": self.participant.code,
                    "secret": self.participant.secret,
                },
            ),
        }

        return {
            "type": self.get_status_color(self.participant),
            "text": self.get_status_text(self.participant).format_map(
                defaultdict(str, banner_kwargs),
            ),
        }

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        answer_by_question = {}
        answers = self.participant.get_answers()
        for answer in answers:
            answer_by_question[answer.question] = answer
        context.update(
            {
                "event": self.request.event,
                "participant": self.participant,
                "can_update": can_update(self.participant, self.request.event),
                "status_banner": self.get_status_banner(),
                "messages": self.participant.messages.filter(is_current=True),
                "blocks": self.blocks,
                "answer_by_question": answer_by_question,
            }
        )
        return context


class ParticipantWithdrawApplicationView(ParticipantDetailView):
    def post(self, *args, **kwargs):
        success_msg = _("Application was withdrawn")

        try:
            self.participant.change_state(ParticipantStateActions.WITHDRAW)
            self.participant.send_change_state_email(
                self.request, ParticipantStateActions.WITHDRAW
            )
        except ParticipantStateChangeException as e:
            messages.error(self.request, str(e))
        except ActionEmailNotConfigured as e:
            messages.warning(self.request, str(e))
            messages.success(self.request, success_msg)
        else:
            messages.success(self.request, success_msg)
        return get_success_redirect(participant=self.participant)

    def get(self, *args, **kwargs):
        return render(
            self.request,
            "signup/withdraw_confirmation.html",
            {"participant": self.participant},
        )
