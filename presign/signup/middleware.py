from django.http import Http404
from django.urls import resolve
from django.utils.translation import gettext_lazy as _

from django_scopes import scope

from presign.base.models import Event


class SignupMiddleware:
    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        url = resolve(request.path_info)
        request.resolved_path = url

        # Only apply this middleware to the signup urls
        if "signup" not in url.namespaces:
            return self.get_response(request)

        if "organizer" in url.kwargs and "event" in url.kwargs:
            with scope(organizer=None):
                event = Event.objects.filter(
                    slug=url.kwargs["event"], organizer__slug=url.kwargs["organizer"]
                ).first()

            if not event:
                raise Http404(_("No event found or event is not public"))

            if not event.is_public() and (
                not request.user.is_authenticated
                or request.user not in event.organizer.members.all()
            ):
                raise Http404(_("No event found or event is not public"))

            request.event = event

        if hasattr(request, "event"):
            with scope(organizer=request.event.organizer, event=request.event):
                return self.get_response(request)
        else:
            return self.get_response(request)
