from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

import factory
import faker
import pytest
from django_scopes import scopes_disabled
from i18nfield.strings import LazyI18nString
from pytest_factoryboy import register

from presign.base.models import (
    Event,
    Organizer,
    Participant,
    ParticipantStateActions,
    ParticipantStates,
)

fake = faker.Faker()


def random_lang_chars():
    data = {}
    for lang, name in settings.LANGUAGES:
        data[lang] = fake.text(max_nb_chars=50)
    return data


def random_i18n_chars():
    return LazyI18nString(random_lang_chars())


def event_status_texts():
    data = {}
    for state in ParticipantStates:
        data[state] = random_lang_chars()
    return data


def slugify_name(obj):
    return slugify(obj.name)


@register
class OrganizerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organizer

    name = factory.LazyFunction(random_i18n_chars)
    slug = factory.LazyAttribute(slugify_name)


@register
class EventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Event

    organizer = factory.SubFactory(OrganizerFactory)
    name = factory.Faker("text", max_nb_chars=50)
    slug = factory.LazyAttribute(slugify_name)

    enabled = True

    event_date = factory.Faker(
        "date_time_between",
        start_date="+2w",
        end_date="+2y",
        tzinfo=timezone.get_default_timezone(),
    )
    signup_start = factory.Faker(
        "date_time_between",
        start_date="-4w",
        end_date=factory.SelfAttribute("..event_date"),
        tzinfo=timezone.get_default_timezone(),
    )
    signup_end = factory.Faker(
        "date_time_between",
        start_date="+1w",
        end_date=factory.SelfAttribute("..event_date"),
        tzinfo=timezone.get_default_timezone(),
    )
    signup_end_shown = factory.Faker(
        "date_time_between",
        start_date="now",
        end_date=factory.SelfAttribute("..signup_end"),
        tzinfo=timezone.get_default_timezone(),
    )
    signup_end_shown = factory.Faker(
        "date_time_between",
        start_date=factory.SelfAttribute("..signup_end"),
        end_date=factory.SelfAttribute("..event_date"),
        tzinfo=timezone.get_default_timezone(),
    )

    status_texts = factory.LazyFunction(event_status_texts)


@register
class ParticipantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Participant

    email = factory.Faker("email")
    event = factory.SubFactory(EventFactory)


@pytest.mark.django_db
@scopes_disabled()
def test_change_state_sends_email(
    participant_factory: ParticipantFactory, mailoutbox, superuser, client
):
    client.force_login(superuser)

    with scopes_disabled():
        participant: Participant = participant_factory.create()
    participant.event.organizer.members.add(superuser)

    participant.event.email_texts.set(
        ParticipantStateActions.APPROVE,
        {
            "subject": {"en": "Approved Subject"},
            "body": {"en": "**Approved** Text"},
        },
    )
    participant.event.save()

    assert len(mailoutbox) == 0

    client.post(
        reverse(
            "control:participant-change",
            kwargs={
                "organizer": participant.event.organizer.slug,
                "event": participant.event.slug,
                "code": participant.code,
                "state_change": ParticipantStateActions.APPROVE,
            },
        )
    )

    participant.refresh_from_db()
    assert participant.state == ParticipantStates.APPROVED

    assert len(mailoutbox) == 1
    state_change_mail = mailoutbox[0]

    assert state_change_mail.to == [participant.email]

    assert state_change_mail.subject == "Approved Subject"
    assert state_change_mail.body == "**Approved** Text"
    assert len(state_change_mail.alternatives) == 1
    alt_text, alt_type = state_change_mail.alternatives[0]

    assert alt_type == "text/html"
    assert "<p><strong>Approved</strong> Text</p>" in alt_text
