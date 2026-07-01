# 📚 Dokumentacja pathl — Tworzenie i publikacja pakietu

## Spis treści
1. [Struktura projektu](#struktura-projektu)
2. [Konfiguracja](#konfiguracja)
3. [Tworzenie wersji](#tworzenie-wersji)
4. [Budowanie](#budowanie)
5. [Publikacja na PyPI](#publikacja-na-pypi)
6. [GitHub Release](#github-release)
7. [Rozwój](#rozwoj)
8. [Najczęstsze problemy](#najczestsze-problemy)

---

## Struktura projektu

```
pathl/
├── pathl/                    # Główny kod
│   ├── __init__.py          # Wersja i eksporty
│   ├── cli.py                # Interfejs CLI
│   └── main.py                # Główne funkcje
├── tests/                    # Testy
│   └── test_main.py
├── dist/                     # Zbudowane pliki (generowane)
├── build/                    # Pliki tymczasowe (generowane)
├── pyproject.toml            # Konfiguracja pakietu i build system
├── README.md                 # Opis projektu
├── LICENSE                   # Licencja
├── CHANGELOG.md               # Historia zmian
├── .env                       # Zmienne środowiskowe (nie commitować!)
└── .gitignore                 # Pliki ignorowane przez git
```

> **Uwaga:** nowoczesne pakiety Pythona nie potrzebują już osobnego `setup.py` —
> cała konfiguracja mieści się w `pyproject.toml`. Poniższa dokumentacja
> korzysta wyłącznie z `pyproject.toml`, co jest obecnie zalecanym podejściem.

---

## Konfiguracja

### 1. Plik `pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "pathl"
version = "0.1.0b1"
description = "Pathl - biblioteka ogólnego przeznaczenia"
readme = "README.md"
requires-python = ">=3.8"
license = "MIT"
authors = [{name = "Alicja", email = "kontakt@pathl.dev"}]
dependencies = [
    "httpx",
]

[project.optional-dependencies]
dev = [
    "pytest",
    "pytest-cov",
    "black",
    "isort",
    "flake8",
    "mypy",
    "build",
    "twine",
]

[project.scripts]
pathl = "pathl.cli:main"
```

> 🔒 **Prywatność:** nie umieszczaj tu prywatnego adresu e-mail — dane
> autora w `pyproject.toml` trafiają publicznie na PyPI i są łatwym celem
> dla botów zbierających adresy do spamu. Użyj osobnego adresu
> projektowego lub aliasu (np. `kontakt@twojadomena.pl`).

### 2. Plik `.env`

```bash
# Token do PyPI (nie commitować!)
PYPI_API_TOKEN=pypi-TWÓJ_TOKEN
```

### 3. Plik `.gitignore`

```bash
__pycache__/
*.pyc
dist/
build/
*.egg-info/
.eggs/
.env
*.log
.mypy_cache/
.pytest_cache/
```

---

## Tworzenie wersji

Pakiety Pythona stosują numerację zgodną z **PEP 440**. Ważne: wersje
przedpremierowe piszemy **bez myślnika** — `0.1.0a1`, nie `0.1.0-a1`.

### Sekwencja wersji

| Wersja      | Znaczenie                | Przykład   |
|-------------|---------------------------|------------|
| `X.Y.ZaN`   | Alpha (testy wewnętrzne)  | `0.1.0a1`  |
| `X.Y.ZbN`   | Beta (testy zewnętrzne)   | `0.1.0b1`  |
| `X.Y.ZrcN`  | Release candidate         | `0.1.0rc1` |
| `X.Y.Z`     | Stabilna                  | `0.1.0`    |
| `X.Y.Z+1`   | Kolejna stabilna          | `0.1.1`    |

### Ręczne zwiększanie wersji

Wersję trzymamy w **dwóch miejscach**, które muszą być zgodne:

**1. `pathl/__init__.py`:**
```python
__version__ = "0.1.0b1"
```

**2. `pyproject.toml`:**
```toml
version = "0.1.0b1"
```

### Przykład pełnej sekwencji

```
0.1.0a1 → 0.1.0a2 → ... → 0.1.0a9
   → 0.1.0b1 → 0.1.0b2 → ... → 0.1.0b9
   → 0.1.0rc1
   → 0.1.0
   → 0.1.1 → 0.1.2 → ...
```

---

## Budowanie

Do budowania używamy narzędzia `build` (nowoczesny standard, zastępuje
przestarzałe `python setup.py sdist bdist_wheel`).

### 1. Zainstaluj narzędzia budujące (jednorazowo)

```bash
pip install --upgrade build twine
```

### 2. Wyczyść stare pliki

```bash
rm -rf build dist *.egg-info .eggs
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
```

### 3. Zbuduj paczkę

```bash
python3 -m build
```

### 4. Sprawdź poprawność

```bash
twine check dist/*
```

### 5. Zobacz co powstało

```bash
ls -lh dist/
```

Powinieneś zobaczyć:
- `pathl-0.1.0b1-py3-none-any.whl` (gotowy do instalacji)
- `pathl-0.1.0b1.tar.gz` (źródła)

---

## Publikacja na PyPI

### 1. Zdobądź token

1. Wejdź na: https://pypi.org/manage/account/token/
2. Kliknij **"Add API token"**
3. Nazwa: `pathl-upload`
4. Scope: **"Upload packages"** (najlepiej ograniczony do projektu `pathl`)
5. Skopiuj token (zaczyna się od `pypi-`) — **PyPI pokaże go tylko raz**

### 2. Zapisz token

```bash
echo "PYPI_API_TOKEN=pypi-TWÓJ_TOKEN" >> .env
```

> ⚠️ Nigdy nie wklejaj tokenu bezpośrednio w komendzie w terminalu —
> trafia wtedy do historii powłoki (`~/.bash_history`) i jest tam
> widoczny w postaci jawnego tekstu. Zawsze wczytuj go ze zmiennej.

### 3. Publikuj

```bash
export $(grep -v '^#' .env | xargs)
twine upload dist/* --username __token__ --password "$PYPI_API_TOKEN"
```

Alternatywnie, twine potrafi też sam wczytać token z pliku `~/.pypirc`:

```ini
[pypi]
username = __token__
password = pypi-TWÓJ_TOKEN
```

wtedy wystarczy:
```bash
twine upload dist/*
```

### 4. Sprawdź czy działa

```bash
pip install --upgrade pathl
python -c "import pathl; print(pathl.__version__)"
```

> 💡 Wersje `aN`/`bN`/`rcN` nie są instalowane domyślnie przez
> `pip install pathl` — trzeba dodać flagę `--pre`:
> `pip install --pre pathl`

---

## GitHub Release

### 1. Commit zmian

```bash
git add pathl/__init__.py pyproject.toml CHANGELOG.md
git commit -m "Bump version to 0.1.0b1"
git push
```

### 2. Stwórz tag

```bash
VERSION=$(python3 -c "import pathl; print(pathl.__version__)")
git tag -a "v$VERSION" -m "Release v$VERSION"
git push origin "v$VERSION"
```

### 3. Stwórz release przez CLI (`gh`)

```bash
VERSION=$(python3 -c "import pathl; print(pathl.__version__)")

gh release create "v$VERSION" \
    --title "v$VERSION" \
    --notes "📦 Wersja $VERSION

Zainstaluj:
pip install --pre pathl

🔗 PyPI: https://pypi.org/project/pathl/" \
    dist/*
```

### 4. Przez stronę GitHub (ręcznie)

1. Wejdź na: `https://github.com/<użytkownik>/pathl/releases`
2. Kliknij **"Draft a new release"**
3. Wybierz tag: `v0.1.0b1`
4. Tytuł: `v0.1.0b1`
5. Opis: `📦 Wersja 0.1.0b1`
6. Dodaj pliki z `dist/`
7. Jeśli to wersja alfa/beta/rc — zaznacz **"Set as a pre-release"**
8. Kliknij **"Publish release"**

---

## Rozwój

### Instalacja w trybie deweloperskim

```bash
pip install -e ".[dev]"
```

To pozwala na testowanie zmian w kodzie bez ponownej instalacji po
każdej edycji.

### Uruchamianie testów

```bash
pytest tests/ -v
pytest tests/ -v --cov=pathl
pytest tests/test_main.py -v
```

### Formatowanie kodu

```bash
black pathl/ tests/
isort pathl/ tests/
flake8 pathl/ tests/
```

### Typowanie (mypy)

```bash
mypy pathl/
```

---

## Najczęstsze problemy

### 1. Błąd 403 Forbidden (PyPI)

**Problem:** Nie masz uprawnień do publikacji lub token wygasł/jest zły.

**Rozwiązanie:**
```bash
# Stwórz nowy token na PyPI
# https://pypi.org/manage/account/token/

export PYPI_API_TOKEN="pypi-NOWY_TOKEN"
twine upload dist/* --username __token__ --password "$PYPI_API_TOKEN"
```

### 2. Błąd "No such file or directory: dist/*"

**Problem:** Brak plików w `dist/` — build się nie powiódł lub katalog
wyczyszczono bez ponownego budowania.

**Rozwiązanie:**
```bash
python3 -m build
```

### 3. Błąd "Module not found"

**Problem:** Brak zainstalowanych zależności deweloperskich.

**Rozwiązanie:**
```bash
pip install -e ".[dev]"
```

### 4. Błąd "Tag already exists"

**Problem:** Tag już istnieje w repozytorium (lokalnie lub zdalnie).

**Rozwiązanie:**
```bash
git tag -d v0.1.0b1
git push origin --delete v0.1.0b1

git tag -a v0.1.0b1 -m "Release v0.1.0b1"
git push origin v0.1.0b1
```

### 5. Błąd "Invalid distribution" / `twine check` nie przechodzi

**Problem:** Pliki w `dist/` są uszkodzone lub metadane są niepoprawne.

**Rozwiązanie:**
```bash
rm -rf build dist *.egg-info .eggs
python3 -m build
twine check dist/*
```

### 6. Błąd "File already exists" przy uploadzie na PyPI

**Problem:** Ta sama wersja została już opublikowana. **PyPI nie
pozwala nadpisać istniejącej wersji** — nawet jeśli ją usuniesz z
interfejsu.

**Rozwiązanie:** zwiększ numer wersji (np. `0.1.0b1` → `0.1.0b2`) i
zbuduj ponownie.

---

## Szybkie komendy

### Budowanie i publikacja

```bash
# 1. Wyczyść
rm -rf build dist *.egg-info .eggs

# 2. Zbuduj
python3 -m build

# 3. Sprawdź
twine check dist/*

# 4. Publikuj
export $(grep -v '^#' .env | xargs)
twine upload dist/* --username __token__ --password "$PYPI_API_TOKEN"
```

### GitHub release

```bash
VERSION=$(python3 -c "import pathl; print(pathl.__version__)")

git tag -a "v$VERSION" -m "Release v$VERSION"
git push origin "v$VERSION"

gh release create "v$VERSION" --title "v$VERSION" --notes "Wersja $VERSION" dist/*
```

### Zmiana wersji

```bash
# 1. Edytuj ręcznie:
#    - pathl/__init__.py   → __version__ = "X.Y.Z..."
#    - pyproject.toml      → version = "X.Y.Z..."

# 2. Sprawdź, że się zgadzają:
python3 -c "import pathl; print(pathl.__version__)"
```

---

## Lista kontrolna przed wydaniem

- [ ] Wszystkie testy przechodzą: `pytest tests/ -v`
- [ ] Kod jest sformatowany: `black pathl/ tests/`
- [ ] Wersja jest zgodna w `pathl/__init__.py` i `pyproject.toml`
- [ ] CHANGELOG.md jest zaktualizowany
- [ ] README.md jest aktualne
- [ ] Token PyPI jest w `.env` (i `.env` jest w `.gitignore`)
- [ ] Katalog `dist/` jest wyczyszczony i zbudowany od nowa: `python3 -m build`
- [ ] Paczka jest poprawna: `twine check dist/*`
- [ ] Wszystko jest zacommitowane: `git add . && git commit`
- [ ] Tag jest stworzony i wypchnięty: `git tag` / `git push --tags`
- [ ] Release jest opublikowany na GitHub (oznaczony jako pre-release, jeśli to alfa/beta/rc)
- [ ] Paczka opublikowana na PyPI: `twine upload dist/*`
- [ ] Instalacja z PyPI działa: `pip install --pre pathl`

---

## Przydatne linki

- **PyPI**: https://pypi.org/project/pathl/
- **GitHub**: https://github.com/<użytkownik>/pathl
- **Tokeny PyPI**: https://pypi.org/manage/account/token/
- **Statystyki**: https://pypistats.org/packages/pathl
- **PEP 440 (numeracja wersji)**: https://peps.python.org/pep-0440/

---

## Podsumowanie

Teraz umiesz samodzielnie:
1. Poprawnie numerować wersje zgodnie z PEP 440 (alpha, beta, rc, stabilne)
2. Budować paczkę narzędziem `build`
3. Bezpiecznie publikować na PyPI (bez wycieku tokenu do historii powłoki)
4. Tworzyć tagi i release'y na GitHubie
5. Rozwijać projekt (testy, formatowanie, typowanie)
6. Rozwiązywać typowe problemy przy publikacji

🚀 **Powodzenia z pathl!**