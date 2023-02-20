import pytest


@pytest.mark.django_db
def test_superuser_is_superuser(superuser):
    assert superuser.is_superuser
