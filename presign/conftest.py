import os

from django.urls import reverse

import pytest
from playwright.sync_api import BrowserContext

# Needed for playwright
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

PLAYWRIGHT_FIXTURES = ["browser", "live_server_context"]


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


def pytest_collection_modifyitems(items):
    for item in items:
        for fixture_name in PLAYWRIGHT_FIXTURES:
            if fixture_name in getattr(item, "fixturenames", ()):
                item.add_marker("playwright")


@pytest.fixture
def superuser(django_user_model):
    return django_user_model.objects.create(
        username="superuser", password="superuser", is_superuser=True
    )


@pytest.fixture
def normal_user(django_user_model):
    return django_user_model.objects.create(username="eve_average", password="passw0rd")
