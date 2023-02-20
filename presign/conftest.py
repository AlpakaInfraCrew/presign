import os

import pytest

# Needed for playwright
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"


@pytest.fixture
def superuser(django_user_model):
    return django_user_model.objects.create(
        username="superuser", password="superuser", is_superuser=True
    )


@pytest.fixture
def normal_user(django_user_model):
    return django_user_model.objects.create(username="eve_average", password="passw0rd")
