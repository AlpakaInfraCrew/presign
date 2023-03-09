import os
from urllib.parse import urlparse

from django.urls import resolve, reverse

import pytest
from playwright.sync_api import BrowserContext

# Needed for playwright
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

PLAYWRIGHT_FIXTURES = ["browser", "live_server_context"]


class Proxy:
    def __init__(self, target) -> None:
        self.proxied_object = target

    def __getattr__(self, name):
        return getattr(self.proxied_object, name)


class LiveServerPage(Proxy):
    def __init__(self, *args, live_server, **kwargs):
        super().__init__(*args, **kwargs)
        self.__live_server = live_server

    def get_resolved_url(self):
        return resolve(self.get_url_path())

    def get_url_path(self):
        return urlparse(self.url)[2]

    def goto_url(self, url, kwargs=None):
        path = reverse(url, kwargs=kwargs)
        return self.goto(url=f"{self.__live_server.url}{path}")


class LiveServerBrowserContext(Proxy):
    def __init__(self, *args, live_server, **kwargs):
        super().__init__(*args, **kwargs)
        self.__live_server = live_server

    def new_page(self, *args, **kwargs):
        page = self.proxied_object.new_page(*args, **kwargs)
        return LiveServerPage(page, live_server=self.__live_server)


@pytest.fixture
def live_server_context(context: BrowserContext, live_server):
    live_context = LiveServerBrowserContext(context, live_server=live_server)
    live_context.set_default_timeout(10000)
    return live_context


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
