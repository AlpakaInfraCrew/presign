# Generated by Django 4.2.5 on 2023-09-30 12:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0007_participantcustommessage"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="historicalparticipant",
            name="public_comment",
        ),
        migrations.RemoveField(
            model_name="participant",
            name="public_comment",
        ),
    ]
