from urllib.parse import urlparse

from django.urls import resolve, reverse

import pytest
from playwright.sync_api import BrowserContext

from presign.base.models import Organizer


@pytest.fixture
def logged_in_context(django_user_model, live_server_context):
    user = django_user_model.objects.create(username="eve_example")
    user.set_password("example_pw")
    user.save()

    page = live_server_context.new_page()

    page.goto_url("login")

    page.fill('[placeholder="Username"]', "eve_example")
    page.fill('[placeholder="Password"]', "example_pw")
    page.click('button[type="submit"]')

    page.close()

    return live_server_context


@pytest.mark.django_db
def test_login_works(
    logged_in_context: BrowserContext,
):
    page = logged_in_context.new_page()
    page.goto_url("control:index")
    resolved_url = resolve(urlparse(page.url)[2])
    assert resolved_url.url_name != "login"


@pytest.mark.django_db
def test_create_organizer(
    logged_in_context: BrowserContext,
):
    page = logged_in_context.new_page()
    page.goto_url("control:index")

    page.click("text=New Organizer")

    page.fill('input[name^="name_"][lang="de"]', "Test Organizer German")
    page.fill('input[name^="name_"][lang="en"]', "Test Organizer English")
    page.fill('[placeholder="Slug"]', "test-organizer")

    page.click("text=Submit")

    assert urlparse(page.url)[2] == reverse(
        "control:organizer", kwargs={"organizer": "test-organizer"}
    )

    assert Organizer.objects.filter(slug="test-organizer").count() == 1

    organizer = Organizer.objects.get(slug="test-organizer")

    assert organizer.name.data == {
        "de": "Test Organizer German",
        "en": "Test Organizer English",
    }
