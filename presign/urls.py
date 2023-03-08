import re

from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve


def get_status_patterns(prefix, view=serve, **kwargs):
    return [
        re_path(
            r"^%s(?P<path>.*)$" % re.escape(prefix.lstrip("/")), view, kwargs=kwargs
        ),
    ]


urlpatterns = [
    path(settings.ADMIN_URL_BASE, admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("accounts/", include("django.contrib.auth.urls")),
    path(
        "signup/",
        include(("presign.signup.urls", "presign.signup"), namespace="signup"),
    ),
    path(
        "control/",
        include(("presign.control.urls", "presign.control"), namespace="control"),
    ),
]

if settings.SELF_SERVE_STATIC:
    urlpatterns += get_status_patterns(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )
    urlpatterns += get_status_patterns(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )

if settings.DEBUG:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]

handler404 = "presign.base.views.handler404"
handler500 = "presign.base.views.handler500"
