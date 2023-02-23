import datetime

from django import forms
from django.db import models

from i18nfield import fields as i18n_fields


class DateTimeLocalInput(forms.DateTimeInput):
    input_type = "datetime-local"

    def format_value(self, value: datetime.datetime):
        if isinstance(value, datetime.datetime):
            return value.isoformat()
        return value


class DateTimeLocalFormField(forms.DateTimeField):
    widget = DateTimeLocalInput()

    def to_python(self, value):
        if value in self.empty_values:
            return None
        value = datetime.datetime.fromisoformat(value)
        return value


class DateTimeLocalModelField(models.DateTimeField):
    def formfield(self, **kwargs):
        return super().formfield(
            **{
                "form_class": DateTimeLocalFormField,
                **kwargs,
            }
        )


class DateInput(forms.DateInput):
    input_type = "date"

    def format_value(self, value: datetime.date):
        if isinstance(value, datetime.date):
            return value.isoformat()
        return value


class DateFormField(forms.DateField):
    widget = DateInput()

    def to_python(self, value):
        if value in self.empty_values:
            return None
        value = datetime.date.fromisoformat(value)
        return value


class DateModelField(models.DateField):
    def formfield(self, **kwargs):
        return super().formfield(
            **{
                "form_class": DateFormField,
                **kwargs,
            }
        )


class TimeInput(forms.TimeInput):
    input_type = "time"

    def format_value(self, value: datetime.time):
        if isinstance(value, datetime.time):
            return value.isoformat()
        return value


class TimeFormField(forms.TimeField):
    widget = TimeInput()

    def to_python(self, value):
        if value in self.empty_values:
            return None
        value = datetime.time.fromisoformat(value)
        return value


class TimeModelField(models.TimeField):
    def formfield(self, **kwargs):
        return super().formfield(
            **{
                "form_class": TimeFormField,
                **kwargs,
            }
        )


class SmallerTextArea(forms.Textarea):
    def __init__(self, attrs=None):
        # Django uses 40x4 by default, which is way too large IMHO
        default_attrs = {"cols": None, "rows": None}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)


class InputGroupI18nTextarea(forms.Textarea):
    template_name = "base/forms/widgets/textarea.html"


class I18nSmallerTextArea(i18n_fields.I18nTextarea):
    widget = InputGroupI18nTextarea

    def __init__(self, attrs=None, **kwargs):
        # Django uses 40x4 by default, which is way too large IMHO
        default_attrs = {"cols": None, "rows": None}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs, **kwargs)


class I18nLargeTextArea(i18n_fields.I18nTextarea):
    widget = InputGroupI18nTextarea


class InputGroupLangAwareTextInput(forms.TextInput):
    template_name = "base/forms/widgets/textfield.html"


class InputGroupI18nTextInput(i18n_fields.I18nTextInput):
    widget = InputGroupLangAwareTextInput


class I18nTextField(i18n_fields.I18nTextField):
    widget = I18nSmallerTextArea

    def formfield(self, **kwargs):
        return super().formfield(
            **{
                **({} if self.choices is not None else {"widget": self.widget}),
                **kwargs,
            }
        )


class I18nCharField(i18n_fields.I18nCharField):
    widget = InputGroupI18nTextInput
