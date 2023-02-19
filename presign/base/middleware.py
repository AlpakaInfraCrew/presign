from django.conf import settings
from django.http import HttpRequest
from django.urls import get_script_prefix

from django_scopes import scopes_disabled


# from https://github.com/raphaelm/django-scopes/issues/10#issuecomment-638965767
def ignore_scopes_in_admin_middleware(
    get_response, admin_path: str = settings.ADMIN_URL_BASE
):
    def middleware(request: HttpRequest):
        if request.path.startswith(get_script_prefix() + admin_path):
            with scopes_disabled():
                return get_response(request)

        return get_response(request)

    return middleware
