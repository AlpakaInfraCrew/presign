from .base import BASE_DIR, Base


def show_toolbar_to_superusers(request):
    return request.user.is_superuser


class Dev(Base):
    # SECURITY WARNING: keep the secret key used in production secret!
    SECRET_KEY = "django-insecure-*@rchc%vvw5#!((4s1x1=rzh0_myd0_=^=dnzpw^(!3cy#y#3l"
    # SECURITY WARNING: don't run with debug turned on in production!
    DEBUG = False

    # Database
    # https://docs.djangoproject.com/en/3.2/ref/settings/#databases

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
            "ATOMIC_REQUESTS": True,
        }
    }

    EMAIL_BACKEND = "eml_email_backend.EmailBackend"
    EMAIL_FILE_PATH = BASE_DIR / "sent_email/"

    if DEBUG:
        # Add debug toolbar
        INSTALLED_APPS = Base.INSTALLED_APPS + [
            "debug_toolbar",
        ]
        MIDDLEWARE = Base.MIDDLEWARE.copy()

        MIDDLEWARE.insert(
            MIDDLEWARE.index("django.contrib.auth.middleware.AuthenticationMiddleware")
            + 1,
            "debug_toolbar.middleware.DebugToolbarMiddleware",
        )

        DEBUG_TOOLBAR_CONFIG = {
            "SHOW_TOOLBAR_CALLBACK": "presign.settings.dev.show_toolbar_to_superusers",
        }

        # Add livereload
        MIDDLEWARE += ("livereload.middleware.LiveReloadScript",)
