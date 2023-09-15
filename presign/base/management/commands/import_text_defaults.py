from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from presign.base.models import GlobalSettings
from argparse import FileType
import json


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("EMAIL_TEXTS", type=FileType("r"))
        parser.add_argument("STATUS_TEXTS", type=FileType("r"))

    def handle(self, *args, **options):
        data = json.load(options.get("EMAIL_TEXTS"))
        settings = GlobalSettings()
        for k, v in data.items():
            settings.email_texts.set(k, v)

        data = json.load(options.get("STATUS_TEXTS"))
        settings = GlobalSettings()
        for k, v in data.items():
            settings.status_texts.set(k, v)
