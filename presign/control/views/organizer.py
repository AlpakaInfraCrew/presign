from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, FormView
from django.views.generic.list import ListView

from django_scopes import scope

from presign.base.models import Organizer

from ..forms import CreateOrganizerForm, OrganizerSettingsForm

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


class OrganizerSettingsView(FormView):
    template_name = "control/organizer/settings.html"
    form_class = OrganizerSettingsForm

    def get_object(self, *args):
        return self.request.organizer

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"instance": self.get_object()})
        return kwargs

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
        context = super().get_context_data(**kwargs)
        context.update({"object": self.get_object()})
        return context


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
