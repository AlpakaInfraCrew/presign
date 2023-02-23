from django import forms
from django.utils.translation import gettext_lazy as _

from phonenumber_field.formfields import PhoneNumberField

from presign.base.fields import DateFormField, DateTimeLocalFormField, TimeFormField
from presign.base.models import Participant, Question, QuestionBlock, QuestionKind


class QuestionOptionDisplayMixin:
    def label_from_instance(self, obj):
        return obj.value


class QuestionOptionMultipleChoiceField(
    QuestionOptionDisplayMixin, forms.ModelMultipleChoiceField
):
    pass


class QuestionOptionChoiceField(QuestionOptionDisplayMixin, forms.ModelChoiceField):
    pass


class QuestionBlockForm(forms.Form):
    def __init__(
        self,
        *args,
        question_block: QuestionBlock,
        **kwargs,
    ):

        self.question_block = question_block
        self.form_title = question_block.name

        super().__init__(*args, **kwargs)

        question: Question
        for question in question_block.question_set.all():
            if question.kind == QuestionKind.TEXT:
                field = forms.CharField(
                    label=question.name,
                    help_text=question.help,
                    required=question.required,
                    widget=forms.Textarea,
                )
            elif question.kind == QuestionKind.STRING:
                field = forms.CharField(
                    label=question.name,
                    help_text=question.help,
                    required=question.required,
                )
            elif question.kind == QuestionKind.NUMBER:
                field = forms.IntegerField(
                    label=question.name,
                    help_text=question.help,
                    required=question.required,
                )
            elif question.kind == QuestionKind.BOOL:
                field = forms.BooleanField(
                    label=question.name,
                    help_text=question.help,
                    required=question.required,
                )
            elif question.kind == QuestionKind.FILE:
                field = forms.FileField(
                    label=question.name,
                    help_text=question.help,
                    required=question.required,
                )
            elif question.kind == QuestionKind.CHOICE:
                field = QuestionOptionChoiceField(
                    label=question.name,
                    help_text=question.help,
                    required=question.required,
                    queryset=question.options,
                )
            elif question.kind == QuestionKind.MULTIPLE_CHOICE:
                field = QuestionOptionMultipleChoiceField(
                    label=question.name,
                    help_text=question.help,
                    required=question.required,
                    queryset=question.options,
                    widget=forms.CheckboxSelectMultiple,
                )
            elif question.kind == QuestionKind.DATE:
                field = DateFormField(
                    label=question.name,
                    help_text=question.help,
                    required=question.required,
                )
            elif question.kind == QuestionKind.DATETIME:
                field = DateTimeLocalFormField(
                    label=question.name,
                    help_text=question.help,
                    required=question.required,
                )
            elif question.kind == QuestionKind.TIME:
                field = TimeFormField(
                    label=question.name,
                    help_text=question.help,
                    required=question.required,
                )
            elif question.kind == QuestionKind.PHONE:
                field = PhoneNumberField(
                    label=question.name,
                    help_text=question.help,
                    required=question.required,
                )
            elif question.kind == QuestionKind.EMAIL:
                field = forms.EmailField(
                    label=question.name,
                    help_text=question.help,
                    required=question.required,
                )
            else:
                raise ValueError(f"Unsupported question type {question}")

            field_name = f"question_{question.pk}"
            field.question = question
            self.fields[field_name] = field


class ParticipantForm(forms.ModelForm):
    form_title = _("Contact Information")

    class Meta:
        model = Participant
        fields = ["email"]
