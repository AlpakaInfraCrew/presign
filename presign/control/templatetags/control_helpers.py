from django.template.defaulttags import register


@register.filter
def get_value(value, arg):
    return value.get(arg, None)


@register.simple_tag(takes_context=True)
def can_update_questionnaire(context, questionnaire):
    return questionnaire.can_user_update(context["request"].user)
