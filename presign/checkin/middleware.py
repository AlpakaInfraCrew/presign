from django.contrib.auth.views import redirect_to_login
from django.http import Http404
from django.urls import resolve
from django.utils.translation import gettext_lazy as _

from django_scopes import scope

from presign.base.models import Event, Organizer
from presign.checkin.models import Location


class CheckinMiddleware:
    def __init__(self, get_response=None):
        self.get_response = get_response

    def _login_redirect(self, request):
        return redirect_to_login(request.get_full_path())

    def __call__(self, request):

        url = resolve(request.path_info)
        request.resolved_path = url

        # Only apply this middleware to the checkin urls
        if "checkin" not in url.namespaces:
            return self.get_response(request)

        # Checkin is only available for authenticated users
        if not request.user.is_authenticated:
            return self._login_redirect(request)

        if "organizer" in url.kwargs:
            with scope(user=request.user):
                organizer = Organizer.objects.filter(
                    members=request.user, slug=url.kwargs["organizer"]
                ).first()

            if not organizer or not request.user.has_organizer_permission(organizer):
                raise Http404(
                    _("No organizer found or you don't have permissions for it")
                )

            request.organizer = organizer

        if hasattr(request, "organizer") and "event" in url.kwargs:
            with scope(organizer=request.organizer):
                event = Event.objects.filter(
                    organizer=request.organizer, slug=url.kwargs["event"]
                ).first()

                if not event or not request.user.has_event_permission(event):
                    raise Http404(
                        _("No event found or you don't have permissions for it ")
                    )

                request.event = event

                locations = Location.objects.filter(
                    event=event.id
                )

                request.locations = locations

                if "location" in url.kwargs:
                    location = Location.objects.filter(
                        id=url.kwargs["location"]
                    ).first()

                    if not location:
                        raise Http404(
                            _("Location not found")
                        )

                    request.location = location


        if hasattr(request, "event"):
            with scope(organizer=request.organizer, event=request.event):
                return self.get_response(request)
        elif hasattr(request, "organizer"):
            with scope(organizer=request.organizer):
                return self.get_response(request)
        else:
            return self.get_response(request)
