from urllib.parse import urlparse

from django.urls import resolve

import pytest
from playwright.sync_api import BrowserContext


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
