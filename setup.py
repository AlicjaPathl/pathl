"""
Ten plik istnieje WYŁĄCZNIE po to, by zdefiniować rozszerzenie C.
Wszystkie inne metadane (nazwa, wersja, zależności) są w pyproject.toml.
"""
from setuptools import setup, Extension

core_extension = Extension(
    name="pathl._native.core",
    sources=["pathl/_native/core.c"],
)

setup(
    ext_modules=[core_extension],
)