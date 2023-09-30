import datetime
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from django_scopes import ScopedManager
from model_clone.models import CloneModel
from simple_history.models import HistoricalRecords

from ..fields import I18nCharField, I18nTextField
from ..utils import sign_url
from .organizer import Organizer
from .participant import Participant


class QuestionKind(models.TextChoices):
    NUMBER = "N", _("Number")
    STRING = "S", _("Text (one line)")
    TEXT = "TX", _("Multiline text")
    BOOL = "B", _("Yes/No")
    CHOICE = "C", _("Choose one from a list")
    MULTIPLE_CHOICE = "M", _("Choose multiple from a list")
    FILE = "F", _("File upload")
    DATE = "D", _("Date")
    TIME = "TI", _("Time")
    DATETIME = "DT", _("Date and time")
    PHONE = "PN", _("Phone number")
    EMAIL = "EM", _("Email address")


class Questionnaire(CloneModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    history = HistoricalRecords()

    name = I18nCharField(max_length=100)

    organizer = models.ForeignKey(Organizer, on_delete=models.CASCADE)
    is_public = models.BooleanField(default=False)

    _clone_fields = ("name",)
    _clone_m2o_or_o2m_fields = ("questionblock_set",)

    def can_user_update(self, user):
        return self.organizer in user.get_organizers()

    def __str__(self) -> str:
        return str(self.name)


class QuestionBlock(CloneModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    history = HistoricalRecords()

    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE)

    name = I18nCharField(max_length=100)
    order = models.IntegerField()

    _clone_fields = ("name", "order")
    _clone_m2o_or_o2m_fields = ("question_set",)

    class Meta:
        ordering = ("questionnaire", "order", "name")

    def __str__(self) -> str:
        return str(self.name)


class Question(CloneModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    history = HistoricalRecords()

    block = models.ForeignKey(QuestionBlock, on_delete=models.CASCADE)
    kind = models.CharField(choices=QuestionKind.choices, max_length=2)
    required = models.BooleanField()
    name = I18nCharField(max_length=255)
    help = I18nTextField(blank=True)
    order = models.PositiveBigIntegerField()

    class Meta:
        ordering = ("order", "name")

    def __str__(self) -> str:
        return str(self.name)

    _clone_fields = ("kind", "required", "name", "help", "order")
    _clone_m2o_or_o2m_fields = ("options",)


class QuestionOption(CloneModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    history = HistoricalRecords()

    question = models.ForeignKey(
        "Question",
        related_name="options",
        on_delete=models.CASCADE,
        limit_choices_to={
            "kind__in": [QuestionKind.MULTIPLE_CHOICE, QuestionKind.CHOICE]
        },
    )
    value = I18nCharField(verbose_name=_("Value"), max_length=255)
    order = models.IntegerField(default=0)

    _clone_fields = ("value", "order")

    class Meta:
        ordering = ("order",)

    def __str__(self):
        return f"{self.question.name}: {self.value}"


class QuestionAnswer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    history = HistoricalRecords()

    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    answer = models.TextField(blank=True, null=True)
    options = models.ManyToManyField(QuestionOption, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    changed_at = models.DateTimeField(auto_now=True)

    file = models.FileField(null=True)

    objects = ScopedManager(organizer="participant__event__organizer")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                "participant", "question", name="unique_participant_question"
            )
        ]

    def get_value(self):
        if self.question.kind == QuestionKind.NUMBER:
            if self.answer is None:
                return None
            return int(self.answer)
        elif self.question.kind in [QuestionKind.STRING, QuestionKind.TEXT]:
            return self.answer
        elif self.question.kind == QuestionKind.BOOL:
            return bool(self.answer)
        elif self.question.kind == QuestionKind.CHOICE:
            return self.options.get()
        elif self.question.kind == QuestionKind.MULTIPLE_CHOICE:
            return self.options.all()
        elif self.question.kind == QuestionKind.FILE:
            return self.file
        elif self.question.kind == QuestionKind.DATE:
            return datetime.date.fromisoformat(self.answer)
        elif self.question.kind == QuestionKind.TIME:
            return datetime.time.fromisoformat(self.answer)
        elif self.question.kind == QuestionKind.DATETIME:
            return datetime.datetime.fromisoformat(self.answer)
        elif self.question.kind in [QuestionKind.PHONE, QuestionKind.EMAIL]:
            return self.answer
        else:
            raise ValueError("Unknown QuestionKind")

    def set_value(self, value):
        if self.question.kind == QuestionKind.NUMBER:
            self.answer = str(value)
        elif self.question.kind in [QuestionKind.STRING, QuestionKind.TEXT]:
            self.answer = value
        elif self.question.kind == QuestionKind.BOOL:
            self.answer = str(value)
        elif self.question.kind == QuestionKind.CHOICE:
            self.options.clear()
            self.options.add(value)
        elif self.question.kind == QuestionKind.MULTIPLE_CHOICE:
            self.options.clear()
            self.options.add(*value)
        elif self.question.kind == QuestionKind.FILE:
            self.file = value
        elif self.question.kind in [
            QuestionKind.DATE,
            QuestionKind.TIME,
            QuestionKind.DATETIME,
        ]:
            self.answer = value.isoformat()
        elif self.question.kind in [QuestionKind.PHONE, QuestionKind.EMAIL]:
            self.answer = value
        else:
            raise ValueError("Unknown QuestionKind")

    def clean(self, *args, **kwargs):
        if not self.get_value() and self.question.required:
            raise ValidationError(
                _("Answers to required questions may not be false-y.")
            )

    def __str__(self) -> str:
        return str(self.get_value())

    def render_answer(self):
        if self.question.kind == QuestionKind.FILE:
            return render_to_string("questions/answers/file.html", {"answer": self})
        elif self.question.kind == QuestionKind.MULTIPLE_CHOICE:
            selected = self.get_value()
            return render_to_string(
                "questions/answers/multiple_choice.html",
                {"answer": self, "selected": selected},
            )
        elif self.question.kind == QuestionKind.CHOICE:
            selected = self.get_value()
            return render_to_string(
                "questions/answers/choice.html",
                {"answer": self, "selected": selected},
            )
        else:
            return self.get_value()

    def file_media_url(self, request=None):
        url = sign_url(self.file.url, salt=settings.PRESIGN_MEDIA_SIGNATURE_SALT)
        if request is not None:
            return request.build_absolute_uri(url)
        else:
            return url
