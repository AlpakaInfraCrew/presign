from django.template.defaulttags import register

from presign.base.models import Event


@register.simple_tag(takes_context=True)
def can_change_event(context, event: Event):
    if not context["request"].user.is_authenticated:
        return False
    return context["request"].user.has_event_permission(event)


@register.filter
def to_string(value):
    return str(value)
