# Generated by Django 4.2.5 on 2023-09-15 15:04

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("base", "0005_globalsettings_email_textsstore"),
    ]

    operations = [
        migrations.CreateModel(
            name="GlobalSettings_Status_TextsStore",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("key", models.CharField(max_length=255)),
                ("value", models.TextField()),
            ],
        ),
        migrations.RemoveField(
            model_name="event",
            name="status_texts",
        ),
        migrations.RemoveField(
            model_name="historicalevent",
            name="status_texts",
        ),
        migrations.CreateModel(
            name="Organizer_Status_TextsStore",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("key", models.CharField(max_length=255)),
                ("value", models.TextField()),
                (
                    "object",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="_status_texts_objects",
                        to="base.organizer",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Event_Status_TextsStore",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("key", models.CharField(max_length=255)),
                ("value", models.TextField()),
                (
                    "object",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="_status_texts_objects",
                        to="base.event",
                    ),
                ),
            ],
        ),
    ]
