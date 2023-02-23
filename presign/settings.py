from pathlib import Path

from django.utils.translation import gettext_lazy as _

from configurations import Configuration


def show_toolbar_to_superusers(request):
    return request.user.is_superuser


class Base(Configuration):
    # Build paths inside the project like this: BASE_DIR / 'subdir'.
    BASE_DIR = Path(__file__).resolve().parent.parent

    # Quick-start development settings - unsuitable for production
    # See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

    DEBUG = False

    ALLOWED_HOSTS = ["*"]

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

    # Database
    # https://docs.djangoproject.com/en/3.2/ref/settings/#databases

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
            "ATOMIC_REQUESTS": True,
        }
    }

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
        # other finders..
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


class Dev(Base):
    # SECURITY WARNING: keep the secret key used in production secret!
    SECRET_KEY = "django-insecure-*@rchc%vvw5#!((4s1x1=rzh0_myd0_=^=dnzpw^(!3cy#y#3l"

    EMAIL_BACKEND = "eml_email_backend.EmailBackend"
    EMAIL_FILE_PATH = Base.BASE_DIR / "sent_email/"

    MEDIA_ROOT = Base.BASE_DIR / "storage"
    MEDIA_URL = "/media/"

    # Add debug toolbar
    INSTALLED_APPS = Base.INSTALLED_APPS + [
        "debug_toolbar",
    ]
    MIDDLEWARE = Base.MIDDLEWARE.copy()

    MIDDLEWARE.insert(
        MIDDLEWARE.index("django.contrib.auth.middleware.AuthenticationMiddleware") + 1,
        "debug_toolbar.middleware.DebugToolbarMiddleware",
    )

    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": "presign.settings.show_toolbar_to_superusers",
    }

    # Add livereload
    MIDDLEWARE += ("livereload.middleware.LiveReloadScript",)

    # SECURITY WARNING: don't run with debug turned on in production!
    DEBUG = True


class Test(Base):
    SECRET_KEY = "test"

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
            "ATOMIC_REQUESTS": True,
        }
    }
