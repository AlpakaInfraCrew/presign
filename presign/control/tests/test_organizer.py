from urllib.parse import urlparse

from django.urls import reverse

import pytest
from playwright.sync_api import BrowserContext, expect

from presign.base.models import Organizer


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


@pytest.mark.django_db
def test_organizer_slug_autofill(logged_in_context: BrowserContext):
    page = logged_in_context.new_page()
    page.goto_url("control:organizer-create")

    page.fill('input[name^="name_"][lang="de"]', "Test Organizer")

    expect(page.locator("input[name=slug]")).to_have_value("test-organizer")
