# Generated by Django 4.2.5 on 2023-09-15 14:31

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("base", "0004_organizer_email_textsstore"),
    ]

    operations = [
        migrations.CreateModel(
            name="GlobalSettings_Email_TextsStore",
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
    ]
