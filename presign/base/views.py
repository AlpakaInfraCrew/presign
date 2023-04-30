from django.core.exceptions import PermissionDenied
from django.http import FileResponse
from django.shortcuts import render
from django.views.static import serve

from .utils import verify_url


def handler404(request, *args, template_name="errors/404.html", **kwargs):
    response = render(request, template_name)
    response.status_code = 404
    return response


def handler500(request, template_name="errors/500.html"):
    response = render(request, template_name)
    response.status_code = 500
    return response


def serve_signed(request, *args, salt: str, max_age: int, **kwargs) -> FileResponse:
    path = request.get_full_path()
    if not verify_url(path, salt=salt, max_age=max_age):
        raise PermissionDenied()
    response = serve(request, *args, **kwargs)
    return response
