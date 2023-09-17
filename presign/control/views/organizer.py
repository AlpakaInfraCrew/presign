from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic.detail import DetailView, SingleObjectTemplateResponseMixin
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView

from django_scopes import scope

from presign.base.models import Organizer, ParticipantStateActions, ParticipantStates

from ..forms import (
    ChangeEventEmailTextsForm,
    ChangeEventStatusTextsForm,
    CreateOrganizerForm,
    OrganizerSettingsForm,
)

User = get_user_model()


class OrganizerListView(ListView):
    model = Organizer
    template_name = "control/organizer/list.html"

    def get_queryset(self):
        with scope(user=self.request.user):
            return super().get_queryset().filter(members=self.request.user)


class OrganizerDetailView(DetailView):
    model = Organizer
    template_name = "control/organizer/detail.html"

    def get_object(self, *args):
        return self.request.organizer


class OrganizerCreateView(CreateView):
    model = Organizer
    form_class = CreateOrganizerForm
    template_name = "control/organizer/create.html"

    def get_success_url(self) -> str:
        with scope(user=self.request.user):
            return reverse(
                "control:organizer",
                kwargs={"organizer": self.object.slug},
            )

    @transaction.atomic
    def form_valid(self, form):
        ret = super().form_valid(form)
        self.object.members.add(self.request.user)
        return ret


class OrganizerSettingsView(SingleObjectTemplateResponseMixin, View):
    template_name = "control/organizer/settings.html"

    def get_object(self, *args):
        return self.request.organizer

    def get_success_url(self) -> str:
        with scope(user=self.request.user):
            return reverse(
                "control:organizer",
                kwargs={"organizer": self.object.slug},
            )

    def form_valid(self, form):
        self.object = form.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = kwargs
        context.update({"object": self.get_object()})
        context.update(self.get_forms())
        return context

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

    def get_general_form(self):
        return OrganizerSettingsForm(
            instance=self.object,
            **self.get_form_kwargs(),
        )

    def get_texts_form(self):
        initial = {}
        for state in ParticipantStates:
            initial[f"text_{state}"] = self.object.get_status_text(state)

        return ChangeEventStatusTextsForm(
            initial=initial,
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
        text_data = forms["texts_form"].cleaned_data
        for state in ParticipantStates:
            field_name = f"text_{state}"
            if (
                field_name in text_data
                and self.object.get_status_text(state) != text_data[field_name].data
            ):
                self.object.status_texts.set(state, text_data[field_name].data)

        email_text_data = forms["email_texts_form"].cleaned_data
        for action in ParticipantStateActions:
            subject_name = f"email_text_subject_{action}"
            body_name = f"email_text_body_{action}"
            subject = email_text_data.get(subject_name)
            body = email_text_data.get(body_name)
            if subject or body:
                data = {"subject": subject.data, "body": body.data}
                if self.object.get_action_email_texts(action) != data:
                    self.object.email_texts.set(action, data)

        self.object.save()
        return redirect(self.get_success_url())

    def forms_invalid(self, forms):
        return self.render_to_response(self.get_context_data(**forms))

    def get_forms(self):
        return {
            "general_form": self.get_general_form(),
            "texts_form": self.get_texts_form(),
            "email_texts_form": self.get_email_texts_form(),
        }


class ChangeMembershipView(View):
    def post(self, request, *args, **kwargs):
        try:
            username = request.POST.get("username", None)
            if not username:
                raise User.DoesNotExist()
            user = User.objects.get(username=username)
            self.run_action(request, user)
        except User.DoesNotExist:
            messages.warning(request, _("User not found"))
        return redirect(
            reverse(
                "control:organizer-settings",
                kwargs={"organizer": request.organizer.slug},
            )
        )


class OrganizerAddMemberView(ChangeMembershipView):
    def run_action(self, request, user):
        if user in request.organizer.members.all():
            messages.warning(request, _("User was already a member"))
        else:
            request.organizer.members.add(user)


class OrganizerRemoveMemberView(ChangeMembershipView):
    def run_action(self, request, user):
        if request.user == user and request.organizer.members.count() < 2:
            messages.warning(
                request,
                _(
                    "You cannot remove yourself from an organizer if you're the only member"
                ),
            )
        else:
            request.organizer.members.remove(user)
