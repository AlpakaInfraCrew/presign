import csv
import io
from typing import Any, Dict, Optional

from django.contrib import messages
from django.db.models import QuerySet
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import View
from django.views.generic.detail import DetailView, SingleObjectTemplateResponseMixin
from django.views.generic.edit import CreateView, FormView
from django.views.generic.list import ListView

from django_scopes import scope

from presign.base.models import (
    Event,
    ParticipantStateActions,
    ParticipantStates,
    QuestionAnswer,
)

from ..constants import STATE_SETTINGS
from ..forms import (
    ChangeEventEmailTextsForm,
    ChangeEventForm,
    ChangeEventStatusTextsForm,
    CreateEventForm,
    ExportForm,
)


class MyEventsListView(ListView):
    model = Event
    template_name = "control/event/my_list.html"

    def get_queryset(self):
        with scope(user=self.request.user, organizer=None):
            return self.request.user.get_events()


class EventListView(ListView):
    model = Event
    template_name = "control/event/list.html"

    def get_queryset(self):
        with scope(organizer=self.request.organizer):
            return super().get_queryset().filter(organizer=self.request.organizer)


def event_index(request, **kwargs):
    return redirect(
        reverse(
            "control:participant-list",
            kwargs={"organizer": request.organizer.slug, "event": request.event.slug},
        )
    )


class EventCreateView(CreateView):
    model = Event
    form_class = CreateEventForm
    template_name = "control/event/create.html"

    def get_success_url(self) -> str:
        with scope(user=self.request.user):
            return reverse(
                "control:event",
                kwargs={
                    "organizer": self.object.organizer.slug,
                    "event": self.object.slug,
                },
            )

    def get_form_kwargs(self) -> Dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["organizer"] = self.request.organizer
        return kwargs


class EventDetailView(DetailView):
    model = Event
    template_name = "control/event/detail.html"

    def get_object(self, *args):
        return self.request.event

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["state_settings"] = STATE_SETTINGS
        return context


class EventUpdateView(SingleObjectTemplateResponseMixin, View):
    model = Event
    template_name = "control/event/update.html"
    form_class = ChangeEventForm

    def get_object(self, *args):
        return self.request.event

    def get_form_kwargs(self):
        kwargs = {}

        if self.request.method == "POST":
            kwargs.update(
                {
                    "data": self.request.POST,
                    "files": self.request.FILES,
                }
            )

        return kwargs

    def get_texts_form(self):
        return ChangeEventStatusTextsForm(
            initial={f"text_{k}": v for k, v in self.object.status_texts.items()},
            **self.get_form_kwargs(),
        )

    def get_email_texts_form(self):
        initial = {}
        for action in ParticipantStateActions:
            action_data = self.object.get_action_email_texts(action)
            initial[f"email_text_subject_{action}"] = action_data["subject"]
            initial[f"email_text_body_{action}"] = action_data["body"]
        return ChangeEventEmailTextsForm(
            initial=initial,
            **self.get_form_kwargs(),
        )

    def get_general_form(self):
        return ChangeEventForm(
            instance=self.object,
            organizer=self.request.organizer,
            **self.get_form_kwargs(),
        )

    def get_forms(self):
        return {
            "general_form": self.get_general_form(),
            "texts_form": self.get_texts_form(),
            "email_texts_form": self.get_email_texts_form(),
        }

    def get_context_data(self, **kwargs):
        context = kwargs
        context.update(self.get_forms())
        context["state_settings"] = STATE_SETTINGS
        return context

    def get_success_url(self) -> str:
        with scope(user=self.request.user):
            return reverse(
                "control:event",
                kwargs={
                    "organizer": self.object.organizer.slug,
                    "event": self.object.slug,
                },
            )

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        forms = self.get_forms()
        is_valid = all(x.is_valid() for x in forms.values())
        if is_valid:
            return self.forms_valid(forms)
        else:
            return self.forms_invalid(forms)

    def forms_valid(self, forms):
        self.object = forms["general_form"].save()
        self.object.status_texts = {}
        text_data = forms["texts_form"].cleaned_data
        for state in ParticipantStates:
            field_name = f"text_{state}"
            if field_name in text_data:
                self.object.status_texts[state] = text_data[field_name].data

        email_text_data = forms["email_texts_form"].cleaned_data
        for action in ParticipantStateActions:
            subject_name = f"email_text_subject_{action}"
            body_name = f"email_text_body_{action}"
            subject = email_text_data.get(subject_name)
            body = email_text_data.get(body_name)
            if subject or body:
                self.object.email_texts.set(
                    action, {"subject": subject.data, "body": body.data}
                )

        self.object.save()
        return redirect(self.get_success_url())

    def forms_invalid(self, forms):
        return self.render_to_response(self.get_context_data(**forms))


class EventConfirmActionView(DetailView):
    model = Event

    def get_object(self, queryset: Optional[QuerySet[Event]] = None) -> Event:
        return self.request.event

    @cached_property
    def event(self):
        return self.get_object()

    def get_success_url(self):
        return reverse(
            "control:event",
            kwargs={
                "organizer": self.event.organizer.slug,
                "event": self.event.slug,
            },
        )

    def get_confirmation_strings(self):
        raise ValueError("get_confirmation_strings must be implemented")

    def post(self, *args, **kwargs):
        self.run_action()
        return redirect(self.get_success_url())

    def get(self, *args, **kwargs):
        return render(
            self.request,
            "control/event/confirm_action.html",
            {
                "event": self.event,
                "confirmation_strings": self.get_confirmation_strings(),
            },
        )


class EventEnableView(EventConfirmActionView):
    def run_action(self):
        if self.event.can_be_enabled():
            self.event.enabled = True
            self.event.save(update_fields=["enabled"])
        else:
            messages.error(self.request, _("Event cannot be enabled"))

    def get_confirmation_strings(self):
        return {
            "question": _("Are you sure that you want to enable this event?"),
        }


class EventDisableView(EventConfirmActionView):
    def run_action(self):
        self.event.enabled = False
        self.event.save(update_fields=["enabled"])

    def get_confirmation_strings(self):
        return {
            "question": _("Are you sure that you want to disable this event?"),
        }


class EventExportView(FormView):
    model = Event
    template_name = "control/event/export.html"

    def get_object(self, *args):
        return self.request.event

    def get_form_kwargs(self):
        kwargs = {}

        if self.request.method == "POST":
            kwargs.update(
                {
                    "data": self.request.POST,
                    "files": self.request.FILES,
                }
            )

        return kwargs

    def get_form(self) -> ExportForm:
        return ExportForm(event=self.get_object(), **self.get_form_kwargs())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["state_settings"] = STATE_SETTINGS
        context["event"] = self.get_object()
        context["form"] = self.get_form()
        return context

    def form_valid(self, form):
        vfile = io.StringIO()
        fieldnames = [str(form.id_map[x]) for x in form.cleaned_data["fields"]]
        writer = csv.DictWriter(vfile, fieldnames=fieldnames)
        writer.writeheader()
        for participant in self.get_object().participant_set.all():
            row = {}
            for fieldname, field in zip(fieldnames, form.cleaned_data["fields"]):
                if field == "__email":
                    row[fieldname] = participant.email
                elif field == "__id":
                    row[fieldname] = participant.pk
                else:
                    try:
                        answer = QuestionAnswer.objects.get(
                            participant=participant, question=field
                        )
                        row[fieldname] = str(answer.get_value())
                    except QuestionAnswer.DoesNotExist:
                        row[fieldname] = ""
            writer.writerow(row)
        csv_text = vfile.getvalue()
        response = HttpResponse(csv_text.encode())
        response["Content-Type"] = "text/plain"
        response["Content-Disposition"] = "attachment; filename=export.csv"
        return response
