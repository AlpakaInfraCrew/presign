from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from simple_history.admin import SimpleHistoryAdmin

from .models import (
    Event,
    EventQuestionnaire,
    Organizer,
    Participant,
    Question,
    QuestionAnswer,
    QuestionBlock,
    Questionnaire,
    QuestionOption,
    User,
)


class EventQuestionnaireAdmin(admin.TabularInline):
    model = EventQuestionnaire


class EventAdmin(SimpleHistoryAdmin):
    inlines = [EventQuestionnaireAdmin]


class QuestionnaireAdmin(SimpleHistoryAdmin):
    search_fields = ["name"]


# Register your models here.

admin.site.register(Organizer, SimpleHistoryAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Participant, SimpleHistoryAdmin)
admin.site.register(Question, SimpleHistoryAdmin)
admin.site.register(QuestionAnswer, SimpleHistoryAdmin)
admin.site.register(QuestionBlock, SimpleHistoryAdmin)
admin.site.register(Questionnaire, QuestionnaireAdmin)
admin.site.register(QuestionOption, SimpleHistoryAdmin)
admin.site.register(User, UserAdmin)
