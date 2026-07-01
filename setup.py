from setuptools import setup, find_packages

setup(
    name="pathl-utils",  # Zmieniona nazwa
    version="0.1.0-a1",
    packages=find_packages(),
    install_requires=["httpx"],
    entry_points={
        "console_scripts": [
            "pathl = pathl.cli:main",
        ],
    },
    python_requires=">=3.8",
    author="Alicja",
    author_email="alicjajett@gmail.com",
    description="Pathl - biblioteka ogólnego przeznaczenia",
    license="MIT",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
)
