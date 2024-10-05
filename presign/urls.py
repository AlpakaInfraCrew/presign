import re

from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

from presign.base.views import serve_signed

from . import views
from debug_toolbar.toolbar import debug_toolbar_urls


def get_status_patterns(prefix, view=serve, **kwargs):
    return [
        re_path(
            r"^%s(?P<path>.*)$" % re.escape(prefix.lstrip("/")), view, kwargs=kwargs
        ),
    ]


def static_pattern(prefix, view=serve, **kwargs):
    return re_path(
        r"^%s(?P<path>.*)$" % re.escape(prefix.lstrip("/")), view, kwargs=kwargs
    )


urlpatterns = [
    path("", views.HomeView.as_view()),
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
    static_pattern(
        prefix=settings.MEDIA_URL,
        view=serve_signed,
        document_root=settings.MEDIA_ROOT,
        max_age=settings.PRESIGN_MEDIA_SIGNATURE_MAX_AGE_SECONDS,
        salt=settings.PRESIGN_MEDIA_SIGNATURE_SALT,
    ),
]

if settings.SELF_SERVE_STATIC:
    urlpatterns += get_status_patterns(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )

if settings.DEBUG:
    urlpatterns += debug_toolbar_urls()

handler404 = "presign.base.views.handler404"
handler500 = "presign.base.views.handler500"
