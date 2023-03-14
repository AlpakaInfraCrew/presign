from pathlib import Path

from django.utils.translation import gettext_lazy as _

from configurations import Configuration, values

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Base(Configuration):
    DEBUG = values.BooleanValue(default=False)
    ALLOWED_HOSTS = values.ListValue(default=["*"])
    CSRF_TRUSTED_ORIGINS = values.ListValue(default=[])

    # Application definition
    INSTALLED_APPS = [
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "livereload",
        "django.contrib.staticfiles",
        "django_bootstrap5",
        "compressor",
        "simple_history",
        "presign.base",
        "presign.control",
        "presign.signup",
    ]

    MIDDLEWARE = [
        "django.middleware.security.SecurityMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.locale.LocaleMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
        "simple_history.middleware.HistoryRequestMiddleware",
        "presign.base.middleware.ignore_scopes_in_admin_middleware",
        "presign.control.middleware.ControlMiddleware",
        "presign.signup.middleware.SignupMiddleware",
    ]

    ROOT_URLCONF = "presign.urls"

    TEMPLATES = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [],
            "APP_DIRS": True,
            "OPTIONS": {
                "context_processors": [
                    "django.template.context_processors.debug",
                    "django.template.context_processors.request",
                    "django.contrib.auth.context_processors.auth",
                    "django.contrib.messages.context_processors.messages",
                    "presign.control.context.contextprocessor",
                ],
            },
        },
    ]

    WSGI_APPLICATION = "presign.wsgi.application"

    # Password validation
    # https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

    AUTH_PASSWORD_VALIDATORS = [
        {
            "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
        },
    ]

    # Internationalization
    # https://docs.djangoproject.com/en/3.2/topics/i18n/

    LANGUAGE_CODE = "en"

    TIME_ZONE = "UTC"

    USE_I18N = True

    USE_TZ = True

    # Static files (CSS, JavaScript, Images)
    # https://docs.djangoproject.com/en/3.2/howto/static-files/

    STATIC_URL = "/static/"

    STATICFILES_DIRS = [
        BASE_DIR / "presign/static",
    ]

    STATICFILES_FINDERS = (
        "django.contrib.staticfiles.finders.FileSystemFinder",
        "django.contrib.staticfiles.finders.AppDirectoriesFinder",
        "compressor.finders.CompressorFinder",
    )

    STATIC_ROOT = BASE_DIR / "static"

    COMPRESS_PRECOMPILERS = (
        ("text/x-scss", "django_libsass.SassCompiler"),
        ("text/typescript", "tsc --target ES2016 --out {outfile} {infile}"),
    )
    # Default primary key field type
    # https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

    DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

    AUTH_USER_MODEL = "base.User"

    # If you change the langs here, also update $langs in main.scss
    LANGUAGES = [
        ("de", _("German")),
        ("en", _("English")),
    ]
    DATE_INPUT_FORMATS = ("Y-m-d", "d.m.Y")
    FORMAT_MODULE_PATH = ["presign.formats"]

    ADMIN_URL_BASE = "admin/"

    BOOTSTRAP5 = {
        "formset_renderers": {
            "default": "django_bootstrap5.renderers.FormsetRenderer",
            "cards": "presign.base.renderers.CardFormsetRenderer",
        },
    }

    PHONENUMBER_DEFAULT_REGION = "DE"

    PRESIGN_SECRET_RETRIES = 10

    LOGOUT_REDIRECT_URL = "control:index"

    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {
                "format": "{name} {levelname} {asctime} {module} {process:d} {thread:d} {message}",
                "style": "{",
            },
        },
        "handlers": {
            "console": {"class": "logging.StreamHandler", "level": "DEBUG"},
        },
        "loggers": {
            "": {
                "handlers": ["console"],
                "level": "DEBUG",
                "formatter": "verbose",
            },
        },
        "root": {"handlers": ["console"], "level": "DEBUG"},
    }

    SELF_SERVE_STATIC = True
    STATIC_URL = "/static/"

    DATABASES = values.DatabaseURLValue()
