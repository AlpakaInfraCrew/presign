from configurations import values

from .base import Base


class Production(Base):
    SECRET_KEY = values.SecretValue()
