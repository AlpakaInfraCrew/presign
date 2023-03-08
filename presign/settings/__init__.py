from .base import Base
from .dev import Dev
from .prod import Production
from .test import Test

try:
    from .local_settings import *  # noqa
except ImportError:
    pass

__all__ = [Base, Dev, Production, Test]
