from django.contrib.auth import get_user_model

import pytest

User = get_user_model()


@pytest.fixture
def superuser():
    return User.objects.create(
        username="superuser", password="superuser", is_superuser=True
    )
