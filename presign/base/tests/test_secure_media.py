import pytest
from django_scopes import scope, scopes_disabled

from presign.conftest import (
    FileQuestionAnswerFactory,
    FileQuestionFactory,
    ParticipantFactory,
)

from ..models import Participant, Question, QuestionAnswer, QuestionKind


@pytest.fixture
def participant_with_file(
    participant_factory: ParticipantFactory,
    file_question_factory: FileQuestionFactory,
    file_question_answer_factory: FileQuestionAnswerFactory,
):
    with scopes_disabled():
        participant: Participant = participant_factory.create()
        question: Question = file_question_factory.create(kind=QuestionKind.FILE)
        file_question_answer_factory.create(question=question, participant=participant)
    return participant


@pytest.mark.django_db
def test_participant_media_signed(participant_with_file: Participant, client):
    with scope(
        organizer=participant_with_file.event.organizer,
    ):
        file_answer = QuestionAnswer.objects.get(
            participant=participant_with_file, question__kind=QuestionKind.FILE
        )
    req = client.get(file_answer.file.url)
    assert req.status_code == 403

    req = client.get(file_answer.file_media_url())
    assert req.status_code == 200
    response_bytes = req.getvalue()
    assert response_bytes == file_answer.file.read()
