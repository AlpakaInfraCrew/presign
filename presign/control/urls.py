from django.urls import include, path

from . import views

participant_url_patterns = [
    path(
        "",
        views.participant.ParticipantDetailView.as_view(),
        name="participant-details",
    ),
    path(
        "change/<str:state_change>/",
        views.participant.ParticipantStateChangeView.as_view(),
        name="participant-change",
    ),
]
event_urlpatterns = [
    path("", views.event.EventDetailView.as_view(), name="event"),
    path("change/", views.event.EventUpdateView.as_view(), name="event-change"),
    path("enable/", views.event.EventEnableView.as_view(), name="event-enable"),
    path("disable/", views.event.EventDisableView.as_view(), name="event-disable"),
    path(
        "participant/",
        views.participant.ParticipantListView.as_view(),
        name="participant-list",
    ),
    path("participant/<str:code>/", include(participant_url_patterns)),
]
questionnaire_urlpatterns = [
    path(
        "block/<uuid:block>/change/",
        views.questionnaire.QuestionBlockUpdateView.as_view(),
        name="questionblock-change",
    ),
    path(
        "block/<uuid:block>/delete/",
        views.questionnaire.QuestionBlockDeleteView.as_view(),
        name="questionblock-delete",
    ),
    path(
        "change/new-block/",
        views.questionnaire.QuestionBlockCreateView.as_view(),
        name="questionblock-create",
    ),
    path(
        "change/",
        views.questionnaire.QuestionnaireUpdateView.as_view(),
        name="questionnaire-change",
    ),
    path(
        "block/<uuid:block>/question/<uuid:question>/change/",
        views.questionnaire.QuestionUpdateView.as_view(),
        name="question-change",
    ),
]
organizer_urlpatterns = [
    path("", views.organizer.OrganizerDetailView.as_view(), name="organizer"),
    path(
        "settings/",
        views.organizer.OrganizerSettingsView.as_view(),
        name="organizer-settings",
    ),
    path(
        "add-member/",
        views.organizer.OrganizerAddMemberView.as_view(),
        name="organizer-add_member",
    ),
    path(
        "remove-member/",
        views.organizer.OrganizerRemoveMemberView.as_view(),
        name="organizer-remove_member",
    ),
    path(
        "event/",
        views.event.EventListView.as_view(),
        name="event-list",
    ),
    path(
        "new-event/",
        views.event.EventCreateView.as_view(),
        name="event-create",
    ),
    path("event/<slug:event>/", include(event_urlpatterns)),
    path(
        "new-questionnaire/",
        views.questionnaire.QuestionnaireCreateView.as_view(),
        name="questionnaire-create",
    ),
    path(
        "questionnaire/",
        views.questionnaire.QuestionnaireListView.as_view(),
        name="questionnaire-list",
    ),
    path("questionnaire/<uuid:questionnaire>/", include(questionnaire_urlpatterns)),
]

user_urlpatterns = [
    path(
        "organizers/",
        views.organizer.OrganizerListView.as_view(),
        name="user-organizers",
    ),
    path("events/", views.event.MyEventsListView.as_view(), name="user-events"),
    path(
        "questionnaire/",
        views.questionnaire.MyQuestionnairesListView.as_view(),
        name="questionnaires",
    ),
]

urlpatterns = [
    path("", views.index, name="index"),
    path("my/", include(user_urlpatterns)),
    path(
        "new-organizer/",
        views.organizer.OrganizerCreateView.as_view(),
        name="organizer-create",
    ),
    path("organizer/<slug:organizer>/", include(organizer_urlpatterns)),
    path(
        "questionnaire/<uuid:questionnaire>/",
        views.questionnaire.QuestionnaireDetailView.as_view(),
        name="questionnaire",
    ),
    path(
        "questionnaire/<uuid:questionnaire>/clone/",
        views.questionnaire.QuestionnaireCloneView.as_view(),
        name="questionnaire-clone",
    ),
]
