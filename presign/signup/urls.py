from django.urls import path

from . import views

urlpatterns = [
    path(
        "<slug:organizer>/<slug:event>/",
        views.ParticipantSignupView.as_view(),
        name="participant-signup",
    ),
    path(
        "<slug:organizer>/<slug:event>/<str:code>/<str:secret>/",
        views.ParticipantDetailView.as_view(),
        name="participant-details",
    ),
    path(
        "<slug:organizer>/<slug:event>/<str:code>/<str:secret>/update/",
        views.ParticipantUpdateView.as_view(),
        name="participant-update",
    ),
    path(
        "<slug:organizer>/<slug:event>/<str:code>/<str:secret>/withdraw/",
        views.ParticipantWithdrawApplicationView.as_view(),
        name="participant-withdraw",
    ),
]
