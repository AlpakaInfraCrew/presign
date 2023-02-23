from typing import Any, Dict

from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, FormView, UpdateView
from django.views.generic.list import ListView

from django_scopes import scope

from presign.base.models import Question, QuestionBlock, Questionnaire

from ..context import get_organizer_nav_items
from ..forms import (
    QuestionBlockForm,
    QuestionForm,
    QuestionFormSet,
    QuestionnaireCloneForm,
    QuestionnaireForm,
    QuestionOptionFormSet,
)


class MyQuestionnairesListView(ListView):
    model = Questionnaire
    template_name = "control/questionnaire/my_list.html"

    def get_queryset(self):
        return self.request.user.get_visible_questionnaires()


class QuestionnaireListView(ListView):
    model = Questionnaire
    template_name = "control/questionnaire/list.html"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                (
                    Q(organizer=self.request.organizer)
                    & Q(organizer__in=self.request.user.get_organizers())
                )
            )
        )


class QuestionnaireDetailView(DetailView):
    model = Questionnaire
    template_name = "control/questionnaire/detail.html"
    pk_url_kwarg = "questionnaire"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                Q(organizer__in=self.request.user.get_organizers()) | Q(is_public=True)
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_is_orga_member = self.request.user in self.object.organizer.members.all()
        context["can_update"] = (
            self.object in self.request.user.get_editable_questionnaires()
        )

        if user_is_orga_member:
            context["additional_nav_items"] = get_organizer_nav_items(
                request=self.request, organizer=self.object.organizer
            )

        return context


class QuestionBlockUpdateView(UpdateView):
    model = QuestionBlock
    template_name = "control/questionnaire/update_block.html"
    fields = ["name", "order"]

    def get_queryset(self):
        return self.model.objects.filter(
            (
                Q(questionnaire__organizer=self.request.organizer)
                & Q(questionnaire__organizer__in=self.request.user.get_organizers())
                & Q(questionnaire=self.kwargs["questionnaire"])
            )
        )

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        return queryset.get(id=self.kwargs["block"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["formset"] = self.get_formset()
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"instance": self.get_object()})
        return kwargs

    def get_formset(self):
        return QuestionFormSet(**self.get_formset_kwargs())

    def get_formset_kwargs(self):
        kwargs = {"block": self.get_object()}
        if self.request.method == "POST":
            kwargs.update(
                {
                    "data": self.request.POST,
                    "files": self.request.FILES,
                }
            )
        return kwargs

    def get_success_url(self) -> str:
        questionnaire = self.get_object().questionnaire
        return reverse(
            "control:questionnaire",
            kwargs={
                "questionnaire": questionnaire.pk,
            },
        )

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        formset = self.get_formset()
        form = self.get_form()
        if form.is_valid() and formset.is_valid():
            formset.save()
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class QuestionnaireCreateView(CreateView):
    model = Questionnaire
    form_class = QuestionnaireForm
    template_name = "control/questionnaire/create.html"

    def get_success_url(self) -> str:
        with scope(user=self.request.user):
            return reverse(
                "control:questionnaire",
                kwargs={
                    "questionnaire": self.object.pk,
                },
            )

    def get_form_kwargs(self) -> Dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["organizer"] = self.request.organizer
        return kwargs


class QuestionnaireUpdateView(UpdateView):
    model = Questionnaire
    form_class = QuestionnaireForm
    template_name = "control/questionnaire/update.html"
    pk_url_kwarg = "questionnaire"

    def get_queryset(self):
        return self.request.user.get_editable_questionnaires()

    def get_success_url(self) -> str:
        with scope(user=self.request.user):
            return reverse(
                "control:questionnaire",
                kwargs={
                    "questionnaire": self.object.pk,
                },
            )

    def get_form_kwargs(self) -> Dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["organizer"] = self.request.organizer
        return kwargs


class QuestionBlockCreateView(CreateView):
    model = QuestionBlock
    form_class = QuestionBlockForm
    template_name = "control/questionnaire/create_block.html"

    def get_questionnaire(self):
        return Questionnaire.objects.filter(
            (
                Q(organizer=self.request.organizer)
                & Q(organizer__in=self.request.user.get_organizers())
            )
            | Q(is_public=True)
        ).get(pk=self.kwargs["questionnaire"])

    def get_success_url(self) -> str:
        with scope(user=self.request.user):
            return reverse(
                "control:questionnaire",
                kwargs={
                    "questionnaire": self.object.questionnaire.pk,
                },
            )

    def get_form_kwargs(self) -> Dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["questionnaire"] = self.get_questionnaire()
        kwargs["initial"] = kwargs.get("initial", {})
        orders = [
            block.order for block in self.get_questionnaire().questionblock_set.all()
        ]
        if orders:
            kwargs["initial"]["order"] = max(orders) + 1
        else:
            kwargs["initial"]["order"] = 1
        return kwargs


class QuestionBlockDeleteView(DetailView):
    model = QuestionBlock
    pk_url_kwarg = "block"

    def get_questionnaire(self):
        return Questionnaire.objects.filter(
            (
                Q(organizer=self.request.organizer)
                & Q(organizer__in=self.request.user.get_organizers())
            )
            | Q(is_public=True)
        ).get(pk=self.kwargs["questionnaire"])

    def get_queryset(self):
        return self.model.objects.filter(questionnaire=self.get_questionnaire())

    def get_success_url(self):
        return reverse(
            "control:questionnaire",
            kwargs={
                "questionnaire": self.get_questionnaire().pk,
            },
        )

    def post(self, *args, **kwargs):
        self.get_object().delete()
        messages.success(self.request, _("Question block deleted."))
        return redirect(self.get_success_url())

    def get(self, *args, **kwargs):
        return render(
            self.request,
            "control/confirm_action.html",
            {
                "cancel_url": self.get_success_url(),
                "confirmation_strings": {
                    "question": _("Are you sure that you want to enable this event?"),
                },
            },
        )


class QuestionnaireCloneView(FormView):
    model = Questionnaire
    form_class = QuestionnaireCloneForm
    template_name = "control/questionnaire/clone.html"

    def get_queryset(self):
        return self.request.user.get_visible_questionnaires()

    def get_object(self):
        return self.get_queryset().get(id=self.kwargs["questionnaire"])

    def get_success_url(self) -> str:
        return reverse(
            "control:questionnaire",
            kwargs={
                "questionnaire": self.object.pk,
            },
        )

    def form_valid(self, form):
        self.object = self.get_object().make_clone(attrs=form.cleaned_data)
        return super().form_valid(form)

    def get_form_kwargs(self) -> Dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["organizers"] = self.request.user.get_organizers()
        kwargs["initial"] = kwargs.get("initial", {})
        kwargs["initial"]["name"] = self.get_object().name
        return kwargs


class QuestionUpdateView(UpdateView):
    model = Question
    form_class = QuestionForm
    template_name = "control/questionnaire/question_update.html"
    pk_url_kwarg = "question"

    def get_queryset(self):
        return Question.objects.filter(
            block__questionnaire__in=self.request.user.get_editable_questionnaires(),
            block=self.kwargs["block"],
        )

    def get_success_url(self) -> str:
        with scope(user=self.request.user):
            return reverse(
                "control:questionnaire",
                kwargs={
                    "questionnaire": self.object.block.questionnaire.pk,
                },
            )

    def get_formset(self):
        return QuestionOptionFormSet(**self.get_formset_kwargs())

    def get_formset_kwargs(self):
        kwargs = {"question": self.get_object()}
        if self.request.method == "POST":
            kwargs.update(
                {
                    "data": self.request.POST,
                    "files": self.request.FILES,
                }
            )
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["formset"] = self.get_formset()
        return context

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        formset = self.get_formset()
        form = self.get_form()
        if form.is_valid() and formset.is_valid():
            formset.save()
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
