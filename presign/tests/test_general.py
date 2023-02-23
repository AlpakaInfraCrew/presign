import datetime

from django.urls import reverse

from django_scopes import scope, scopes_disabled
from playwright.sync_api import BrowserContext, expect

from presign.base.models import (
    Event,
    Organizer,
    Participant,
    ParticipantStates,
    QuestionBlock,
    QuestionKind,
    Questionnaire,
)


def test_login_works(
    logged_in_context: BrowserContext,
):
    page = logged_in_context.new_page()
    page.goto_url("control:index")
    assert page.get_resolved_url().url_name != "login"


def create_questionnaire(
    settings, page, organizer, question_blocks=[], questionnaire_num=1
):
    pre_questionnaire_count = Questionnaire.objects.count()

    page.click("text=New Questionnaire")
    assert page.get_resolved_url().url_name == "questionnaire-create"

    for lang, name in settings.LANGUAGES:
        page.fill(
            f'input[lang="{lang}"]', f"Test Questionnaire {questionnaire_num} {name}"
        )

    page.click("text=Submit")

    assert Questionnaire.objects.count() == pre_questionnaire_count + 1
    assert page.get_resolved_url().url_name == "questionnaire"
    pk = page.get_resolved_url().kwargs["questionnaire"]
    questionnaire = Questionnaire.objects.get(pk=pk)

    for block_idx, block in enumerate(question_blocks):
        assert (
            QuestionBlock.objects.filter(questionnaire=questionnaire).count()
            == block_idx
        )
        page.click("text=Add Block")

        assert page.get_url_path() == reverse(
            "control:questionblock-create",
            kwargs={"organizer": organizer.slug, "questionnaire": questionnaire.pk},
        )

        for lang, name in settings.LANGUAGES:
            page.fill(
                f'input[lang="{lang}"]',
                f"Test Questionnaire {questionnaire_num} Block 1 {name}",
            )

        page.click("text=Submit")

        page.get_by_test_id("questionblocks").locator(
            'xpath=//section//*[contains(@class, "card-header")]//a[contains(.,"Edit")]'
        ).nth(block_idx).click()

        assert page.get_resolved_url().url_name == "questionblock-change"

        for i, question in enumerate(block):
            # TODO: Create new questions if needed
            question_form = page.locator(".formset-form").nth(i)
            name_div = question_form.locator('label:has-text("Name") >> xpath=..')
            help_div = question_form.locator('label:has-text("Help") >> xpath=..')
            for lang, name in settings.LANGUAGES:
                name_div.locator(f'[lang="{lang}"]').fill(
                    f"{question['name_prefix']} {name}"
                )
                if question.get("help_prefix"):
                    help_div.locator(f'[lang="{lang}"]').fill(
                        f"{question['help_prefix']} {name}"
                    )

            question_form.get_by_label("Kind").select_option(question["kind"])
            if question["required"]:
                question_form.get_by_label("Required").check()

        page.click("text=Submit")

        # Check that no new questionnaire is created
        assert Questionnaire.objects.count() == pre_questionnaire_count + 1
        # Check that a new block is created
        assert (
            QuestionBlock.objects.filter(questionnaire=questionnaire).count()
            == block_idx + 1
        )
        # Check that we are redirected to the questionnaire page
        assert page.get_resolved_url().url_name == "questionnaire"
        pk = page.get_resolved_url().kwargs["questionnaire"]
        assert pk == questionnaire.pk

    return questionnaire


def test_full_event_lifecycle(
    logged_in_context: BrowserContext, settings, mailoutbox
) -> None:
    # Open new page
    page = logged_in_context.new_page()

    with scopes_disabled():
        assert Organizer.objects.count() == 0
        assert Questionnaire.objects.count() == 0
        assert Event.objects.count() == 0
        assert Participant.objects.count() == 0
    assert len(mailoutbox) == 0

    page.goto_url("control:user-organizers")

    page.click("text=New Organizer")
    assert page.get_resolved_url().url_name == "organizer-create"

    for lang, name in settings.LANGUAGES:
        page.fill(f'input[lang="{lang}"]', f"Test Organizer {name}")

    page.click("text=Submit")

    assert Organizer.objects.count() == 1
    organizer = Organizer.objects.get()

    assert organizer.slug.startswith("test-organizer")

    assert page.get_url_path() == reverse(
        "control:organizer", kwargs={"organizer": organizer.slug}
    )

    questionnaire_1 = create_questionnaire(
        settings,
        page,
        organizer,
        questionnaire_num=1,
        question_blocks=[
            [
                {
                    "name_prefix": "Question 1-1-1",
                    "required": True,
                    "kind": QuestionKind.STRING,
                },
                {
                    "name_prefix": "Question 1-1-2",
                    "required": False,
                    "kind": QuestionKind.BOOL,
                },
            ],
            [
                {
                    "name_prefix": "Question 1-2-1",
                    "required": False,
                    "kind": QuestionKind.STRING,
                },
                {
                    "name_prefix": "Question 1-2-2",
                    "required": True,
                    "kind": QuestionKind.BOOL,
                },
            ],
        ],
    )

    # TODO: Check that organizer appears in sidebar and click that one
    # page.locator(".sidenav").click("text=Test Organizer en")
    page.goto_url("control:organizer", kwargs={"organizer": organizer.slug})

    questionnaire_2 = create_questionnaire(
        settings,
        page,
        organizer,
        questionnaire_num=2,
        question_blocks=[
            [
                {
                    "name_prefix": "Question 2-1-1",
                    "required": True,
                    "kind": QuestionKind.STRING,
                }
            ]
        ],
    )

    # TODO: Check that organizer appears in sidebar and click that one
    # page.locator(".sidenav").click("text=Test Organizer en")
    page.goto_url("control:organizer", kwargs={"organizer": organizer.slug})

    # Click text=New Event
    page.click("text=New Event")
    # assert page.url == "http://localhost:8001/control/organizer/test-organizer-de/new-event/"

    name_div = page.locator('label:has-text("Name") >> xpath=..')
    for lang, name in settings.LANGUAGES:
        name_div.locator(f'[lang="{lang}"]').fill(f"Test Event {name}")

    event_date = datetime.datetime.now() + datetime.timedelta(days=40)

    page.fill('[placeholder="Event\\ date"]', event_date.strftime("%Y-%m-%dT%H:%M"))
    page.select_option('select[name="questionnaire_signup"]', str(questionnaire_1.pk))
    page.select_option(
        'select[name="questionnaire_after_approval"]', str(questionnaire_2.pk)
    )

    page.click("text=Submit")

    with scopes_disabled():
        assert Event.objects.count() == 1

    with scope(organizer=organizer):
        event = Event.objects.get()

    assert page.get_url_path() == reverse(
        "control:event", kwargs={"organizer": organizer.slug, "event": event.slug}
    )

    # Action: Set Email Config
    page.get_by_role("link", name="Change", exact=True).click()
    page.get_by_role("tab", name="Email Texts").click()
    for action in ["Approve", "Confirm participant"]:
        action_button = page.get_by_role("button", name=action, exact=True)
        if action_button.get_attribute("aria-expanded") == "false":
            action_button.click()
        action_item = action_button.locator("xpath=../..")
        subject_div = action_item.locator('label:has-text("Email Subject") >> xpath=..')
        body_div = action_item.locator('label:has-text("Email Body") >> xpath=..')
        for lang, name in settings.LANGUAGES:
            subject_div.locator(f'[lang="{lang}"]').fill(f"Subject {action} {name}")
            body_div.locator(f'[lang="{lang}"]').fill(f"Body {action} {name}")

    page.get_by_role("button", name="Submit").click()

    page.click("text=View on site")

    expect(page.locator('div:has-text("This event is not public yet")')).to_be_visible()

    page.goto_url(
        "control:event", kwargs={"organizer": organizer.slug, "event": event.slug}
    )

    # Enable Event
    page.click("text=Enable")
    page.click('button:has-text("Confirm")')

    assert page.get_url_path() == reverse(
        "control:event", kwargs={"organizer": organizer.slug, "event": event.slug}
    )

    # Click text=View on site
    page.click("text=View on site")

    expect(page.locator('div:has-text("This event is not public yet")')).to_have_count(
        0
    )

    # TODO: Get non-logged-in page
    user_page = logged_in_context.new_page()
    user_page.goto_url(
        "signup:participant-signup",
        kwargs={"organizer": organizer.slug, "event": event.slug},
    )

    user_page.fill("#id_email", "test@test.test")

    user_page.fill("input[placeholder^='Question 1-1-1']", "Answer 1-1-1")
    user_page.check('label:has-text("Question 1-1-2")')
    user_page.check('label:has-text("Question 1-2-2")')
    user_page.click("text=Submit")

    assert user_page.get_resolved_url().url_name == "participant-details"
    assert user_page.get_resolved_url().namespace == "signup"

    code = user_page.get_resolved_url().kwargs["code"]
    secret = user_page.get_resolved_url().kwargs["secret"]

    with scopes_disabled():
        assert Participant.objects.count() == 1
    with scope(organizer=organizer, event=event):
        participant = Participant.objects.get(event=event, code=code, secret=secret)

    assert participant.state == ParticipantStates.NEW

    page.goto_url(
        "control:event", kwargs={"organizer": organizer.slug, "event": event.slug}
    )

    page.click("text=Show participant details")

    assert page.get_url_path() == reverse(
        "control:participant-details",
        kwargs={
            "organizer": organizer.slug,
            "event": event.slug,
            "code": participant.code,
        },
    )

    page.click("text=Approve")
    page.click('button:has-text("Confirm")')

    participant.refresh_from_db()
    assert participant.state == ParticipantStates.APPROVED

    assert len(mailoutbox) == 1

    user_page.reload()
    user_page.click('a:has-text("Edit answers")')

    user_page.fill("input[placeholder^='Question 2-1-1']", "Answer 2-1-1")
    user_page.click("text=Submit")

    participant.refresh_from_db()
    assert participant.state == ParticipantStates.NEEDS_REVIEW

    page.reload()

    page.click("text=Confirm participant")
    page.click('button:has-text("Confirm")')

    participant.refresh_from_db()
    assert participant.state == ParticipantStates.CONFIRMED

    assert len(mailoutbox) == 2
