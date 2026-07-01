# 1. Zapisujesz zmiany w repozytorium
ZATAKTUALIZUJ WERSJE PLIKÓW r__init___".py i pliku TOML

git add pyproject.toml .github/workflows/build-wheels.yml

git commit -m "Bump to 0.1.0a4, fix PyPI token publish"

git push

# 2. Tworzysz tag, który uruchamia automatyczne budowanie i publikację na PyPI
git tag v0.1.0a4

git push origin v0.1.0a4