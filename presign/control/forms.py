from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Max, Q
from django.forms import BaseModelFormSet, modelformset_factory
from django.utils.translation import gettext_lazy as _

from django_scopes import scope
from i18nfield import forms as i18n_forms

from presign.base.fields import I18nSmallerTextArea
from presign.base.models import (
    Event,
    EventQuestionnaire,
    Organizer,
    Participant,
    ParticipantStates,
    Question,
    QuestionBlock,
    Questionnaire,
    QuestionnaireRole,
    QuestionOption,
)


class ParticipantInternalForm(forms.ModelForm):
    class Meta:
        model = Participant
        fields = ["internal_comment", "public_comment", "state"]


class CreateOrganizerForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].widget.attrs["data-auto-slugify-from"] = "name"

    class Meta:
        model = Organizer
        fields = ["name", "slug"]

    def clean_slug(self):
        slug = self.cleaned_data["slug"]
        with scope(user=None):
            if Organizer.objects.filter(slug__iexact=slug).exists():
                raise forms.ValidationError(
                    _("There is already an organizer with this slug."),
                    code="slug_not_unique",
                )
            return slug


class CreateEventForm(forms.ModelForm):
    questionnaire_signup = forms.ModelChoiceField(queryset=None, required=False)
    questionnaire_after_approval = forms.ModelChoiceField(queryset=None, required=False)

    def __init__(self, *args, organizer, **kwargs):
        super().__init__(*args, **kwargs)
        self.organizer = organizer
        self.fields["slug"].widget.attrs["data-auto-slugify-from"] = "name"
        questionnaire_queryset = Questionnaire.objects.filter(
            Q(organizer=organizer) | Q(is_public=True)
        )
        self.fields["questionnaire_signup"].queryset = questionnaire_queryset
        self.fields[
            "questionnaire_signup"
        ].initial = self.instance.questionnaire_signup()
        self.fields["questionnaire_after_approval"].queryset = questionnaire_queryset
        self.fields[
            "questionnaire_after_approval"
        ].initial = self.instance.questionnaire_after_approval()

    class Meta:
        model = Event
        fields = [
            "name",
            "slug",
            "event_date",
            "signup_start",
            "signup_end",
            "signup_end_shown",
            "lock_date",
        ]

    def clean_slug(self):
        slug = self.cleaned_data["slug"]
        with scope(user=None):
            if Event.objects.filter(slug__iexact=slug).exists():
                raise forms.ValidationError(
                    _("There is already an event with this slug."),
                    code="slug_not_unique",
                )
            return slug

    def save(self, *args, **kwargs):
        self.instance.organizer = self.organizer
        self.instance = super().save(*args, **kwargs)
        if self.cleaned_data["questionnaire_signup"]:
            EventQuestionnaire.objects.update_or_create(
                {"questionnaire": self.cleaned_data["questionnaire_signup"]},
                event=self.instance,
                role=QuestionnaireRole.DURING_SIGNUP,
            )
        if self.cleaned_data["questionnaire_after_approval"]:
            EventQuestionnaire.objects.update_or_create(
                {"questionnaire": self.cleaned_data["questionnaire_after_approval"]},
                event=self.instance,
                role=QuestionnaireRole.AFTER_APPROVAL,
            )

        return self.instance


class ChangeEventForm(forms.ModelForm):
    questionnaire_signup = forms.ModelChoiceField(queryset=None)
    questionnaire_after_approval = forms.ModelChoiceField(queryset=None)

    def __init__(self, *args, organizer, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].disabled = True
        questionnaire_queryset = Questionnaire.objects.filter(
            Q(organizer=organizer) | Q(is_public=True)
        )
        self.fields["questionnaire_signup"].queryset = questionnaire_queryset
        self.fields[
            "questionnaire_signup"
        ].initial = self.instance.questionnaire_signup()
        self.fields["questionnaire_after_approval"].queryset = questionnaire_queryset
        self.fields[
            "questionnaire_after_approval"
        ].initial = self.instance.questionnaire_after_approval()

    class Meta:
        model = Event
        fields = [
            "name",
            "slug",
            "description",
            "event_date",
            "signup_start",
            "signup_end",
            "signup_end_shown",
            "lock_date",
        ]

    def save(self, *args) -> Event:
        EventQuestionnaire.objects.update_or_create(
            {"questionnaire": self.cleaned_data["questionnaire_signup"]},
            event=self.instance,
            role=QuestionnaireRole.DURING_SIGNUP,
        )
        EventQuestionnaire.objects.update_or_create(
            {"questionnaire": self.cleaned_data["questionnaire_after_approval"]},
            event=self.instance,
            role=QuestionnaireRole.AFTER_APPROVAL,
        )
        return super().save(*args)

    def clean_questionnaire_after_approval(self):
        value = self.cleaned_data["questionnaire_after_approval"]
        if (
            self.cleaned_data["questionnaire_signup"]
            == self.cleaned_data["questionnaire_after_approval"]
        ):
            raise ValidationError(_("The two questionnaires must be different"))

        return value


class BaseQuestionFormSet(BaseModelFormSet):
    def __init__(self, *args, block, **kwargs):
        super().__init__(*args, **kwargs)
        self.block = block
        self.queryset = Question.objects.filter(block=block)
        self.max_order = self.queryset.aggregate(Max("order"))["order__max"]
        if self.max_order is None:
            self.max_order = 0

    def save_existing(self, form, *args, **kwargs):
        form.instance.block = self.block
        return super().save_existing(form, *args, **kwargs)

    def save_new(self, form, *args, **kwargs):
        form.instance.block = self.block
        return super().save_new(form, *args, **kwargs)

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        if index >= self.initial_form_count():
            kwargs["initial"] = kwargs.get("initial", {})
            kwargs["initial"]["order"] = self.max_order + 1
            self.max_order += 1
        return kwargs


QuestionFormSet = modelformset_factory(
    Question,
    formset=BaseQuestionFormSet,
    fields=("name", "kind", "required", "help", "order"),
    extra=2,
    can_delete=True,
)


class QuestionnaireForm(forms.ModelForm):
    def __init__(self, *args, organizer=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organizer = organizer

    class Meta:
        model = Questionnaire
        fields = ("name", "is_public")

    def save(self, *args, **kwargs):
        if self.organizer:
            self.instance.organizer = self.organizer
        return super().save(*args, **kwargs)


class QuestionBlockForm(forms.ModelForm):
    def __init__(self, *args, questionnaire=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.questionnaire = questionnaire

    class Meta:
        model = QuestionBlock
        fields = ("name", "order")

    def save(self, *args, **kwargs):
        if self.questionnaire:
            self.instance.questionnaire = self.questionnaire
        return super().save(*args, **kwargs)


class OrganizerSettingsForm(forms.ModelForm):
    class Meta:
        model = Organizer
        fields = ("name",)


class QuestionnaireCloneForm(forms.ModelForm):
    def __init__(self, *args, organizers, **kwargs):
        super().__init__(*args, **kwargs)
        self.organizers = organizers
        self.fields["organizer"].queryset = organizers

    class Meta:
        model = Questionnaire
        fields = ("organizer", "name", "is_public")

    def save(self, *args, **kwargs):
        if self.organizer:
            self.instance.organizer = self.organizer
        return super().save(*args, **kwargs)


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ("name", "kind", "required", "help", "order")


class BaseQuestionOptionFormSet(BaseModelFormSet):
    def __init__(self, *args, question, **kwargs):
        super().__init__(*args, **kwargs)
        self.question = question
        self.queryset = QuestionOption.objects.filter(question=question)
        self.max_order = self.queryset.aggregate(Max("order"))["order__max"]
        if self.max_order is None:
            self.max_order = 0

    def save_existing(self, form, *args, **kwargs):
        form.instance.question = self.question
        return super().save_existing(form, *args, **kwargs)

    def save_new(self, form, *args, **kwargs):
        form.instance.question = self.question
        return super().save_new(form, *args, **kwargs)

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        if index >= self.initial_form_count():
            kwargs["initial"] = kwargs.get("initial", {})
            kwargs["initial"]["order"] = self.max_order + 1
            self.max_order += 1
        return kwargs


QuestionOptionFormSet = modelformset_factory(
    QuestionOption,
    formset=BaseQuestionOptionFormSet,
    fields=("value", "order"),
    extra=1,
    can_delete=True,
)


class ChangeEventStatusTextsForm(forms.Form):
    def __init__(self, *args, organizer, **kwargs):
        super().__init__(*args, **kwargs)

        for state, label in zip(ParticipantStates, ParticipantStates.labels):
            self.fields[f"text_{state}"] = i18n_forms.I18nFormField(
                label=label,
                help_text=_(
                    'Text shown to the user in the "%(state)s" state. You can use markdown and the following variables: %(variables)s'
                )
                % {
                    "state": label,
                    "variables": "{event_name}, {application_url}, {change_answer_url}",
                },
                required=False,
                widget=I18nSmallerTextArea,
            )
