from django.apps import AppConfig


class ControlConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "presign.control"

    def ready(self):
        from . import logdisplay  # noqa
