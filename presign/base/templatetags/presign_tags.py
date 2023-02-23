from django.template.defaulttags import register
from django.utils.html import mark_safe

import markdown
import nh3

from presign.base.models import Event


@register.simple_tag(takes_context=True)
def can_change_event(context, event: Event):
    if not context["request"].user.is_authenticated:
        return False
    return context["request"].user.has_event_permission(event)


@register.filter
def to_string(value):
    return str(value)


@register.filter
def markdownify(value):
    if not isinstance(value, str):
        value = str(value)
    html = markdown.markdown(value)
    cleaned_html = nh3.clean(html)
    return mark_safe(cleaned_html)
