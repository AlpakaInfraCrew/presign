from .base import Base


class Test(Base):
    SECRET_KEY = "test"

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
            "ATOMIC_REQUESTS": True,
        }
    }
