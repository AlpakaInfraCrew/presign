from django.urls import reverse

import faker
import pytest
from django_scopes import scopes_disabled

from presign.base.models import Participant, ParticipantStateActions, ParticipantStates
from presign.conftest import ParticipantFactory

fake = faker.Faker()


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
