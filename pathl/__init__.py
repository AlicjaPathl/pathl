"""Pathl - biblioteka ogólnego przeznaczenia."""

__version__ = "0.1.0-a1"

from .hello.world import hello
from .crypto.rsa import rsa
__all__ = ["hello", "__version__","rsa"]
