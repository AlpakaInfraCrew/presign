import os
from urllib.parse import urlparse

from django.conf import settings
from django.urls import resolve, reverse
from django.utils import timezone
from django.utils.text import slugify

import factory
import faker
import pytest
from i18nfield.strings import LazyI18nString
from playwright.sync_api import BrowserContext
from pytest_factoryboy import register

from presign.base.models import (
    Event,
    Organizer,
    Participant,
    ParticipantStates,
    Question,
    QuestionAnswer,
    QuestionBlock,
    QuestionKind,
    Questionnaire,
)

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


fake = faker.Faker()


def random_lang_chars():
    data = {}
    for lang, name in settings.LANGUAGES:
        data[lang] = fake.text(max_nb_chars=50)
    return data


def random_i18n_chars():
    return LazyI18nString(random_lang_chars())


def event_status_texts():
    data = {}
    for state in ParticipantStates:
        data[state] = random_lang_chars()
    return data


def slugify_name(obj):
    return slugify(obj.name)


@register
class OrganizerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organizer

    name = factory.LazyFunction(random_i18n_chars)
    slug = factory.LazyAttribute(slugify_name)


@register
class EventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Event

    organizer = factory.SubFactory(OrganizerFactory)
    name = factory.Faker("text", max_nb_chars=50)
    slug = factory.LazyAttribute(slugify_name)

    enabled = True

    event_date = factory.Faker(
        "date_time_between",
        start_date="+2w",
        end_date="+2y",
        tzinfo=timezone.get_default_timezone(),
    )
    signup_start = factory.Faker(
        "date_time_between",
        start_date="-4w",
        end_date=factory.SelfAttribute("..event_date"),
        tzinfo=timezone.get_default_timezone(),
    )
    signup_end = factory.Faker(
        "date_time_between",
        start_date="+1w",
        end_date=factory.SelfAttribute("..event_date"),
        tzinfo=timezone.get_default_timezone(),
    )
    signup_end_shown = factory.Faker(
        "date_time_between",
        start_date="now",
        end_date=factory.SelfAttribute("..signup_end"),
        tzinfo=timezone.get_default_timezone(),
    )
    signup_end_shown = factory.Faker(
        "date_time_between",
        start_date=factory.SelfAttribute("..signup_end"),
        end_date=factory.SelfAttribute("..event_date"),
        tzinfo=timezone.get_default_timezone(),
    )

    status_texts = factory.LazyFunction(event_status_texts)


@register
class ParticipantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Participant

    email = factory.Faker("email")
    event = factory.SubFactory(EventFactory)


@register
class QuestionnaireFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Questionnaire

    organizer = factory.SubFactory(OrganizerFactory)


@register
class QuestionBlockFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = QuestionBlock

    order = factory.Sequence(lambda n: n)
    questionnaire = factory.SubFactory(QuestionnaireFactory)


class QuestionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Question

    required = True
    order = factory.Sequence(lambda n: n)
    block = factory.SubFactory(QuestionBlockFactory)


@register
class FileQuestionFactory(QuestionFactory):

    kind = QuestionKind.FILE


@register
class FileQuestionAnswerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = QuestionAnswer

    file = factory.django.FileField(data=os.urandom(32))
