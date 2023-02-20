from urllib.parse import urlparse

from django.urls import resolve, reverse

import pytest
from playwright.sync_api import BrowserContext


@pytest.fixture
def live_server_context(context: BrowserContext, live_server):
    """
    VERY HACKY! If you have a better idea how to solve this, please tell me :pleading-face:

    This replaces the `new_page` function on the context with one that returns a patched page.

    The patched page has a new `goto_url` function, which uses djangos `reverse` function to access
    views by name instead of url. This also captures the live_server into the context

    This allows you to do something like

    ```
    def test_something(live_server_context):
        page = live_server_context.new_page()
        page.goto_url("control:index")
    ```
    """

    def new_page_func(*args, **kwargs):
        page = context._hacky_original_new_page(*args, **kwargs)

        def goto_url_func(url, kwargs=None):
            path = reverse(url, kwargs=kwargs)
            page.goto(url=f"{live_server.url}{path}")

        page.goto_url = goto_url_func
        return page

    context._hacky_original_new_page = context.new_page
    context.new_page = new_page_func

    return context


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


@pytest.mark.db
def test_login_works(
    logged_in_context: BrowserContext,
):
    page = logged_in_context.new_page()
    page.goto_url("control:index")
    resolved_url = resolve(urlparse(page.url)[2])
    assert resolved_url.url_name != "login"
