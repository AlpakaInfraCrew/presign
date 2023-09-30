from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("organizer/<slug:organizer>/event/<slug:event>/", views.event.EventDetailView.as_view(), name="event-overview"),
    path("organizer/<slug:organizer>/event/<slug:event>/location/create/", views.location.LocationCreateView.as_view(), name="location-create"),
]
