import os
from urllib.parse import urlparse

from django.urls import resolve, reverse

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

        def get_resolved_url():
            return resolve(page.get_url_path())

        def get_url_path():
            return urlparse(page.url)[2]

        page.get_resolved_url = get_resolved_url
        page.get_url_path = get_url_path

        page.goto_url = goto_url_func
        return page

    context._hacky_original_new_page = context.new_page
    context.new_page = new_page_func

    context.set_default_timeout(5000)

    return context


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "record_video_size": {"width": 1920, "height": 1080},
    }


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
