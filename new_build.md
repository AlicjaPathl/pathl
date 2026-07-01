# 🏗️ build.md — Budowanie i wydawanie nowej wersji `pathl`

Dokumentacja procesu release'u pakietu `pathl`, który zawiera natywne
rozszerzenie C (`pathl/_native/core.c`, kompilowane przez `Python.h`) i jest
dystrybuowany jako osobne koła (`.whl`) dla **Linuksa** i **Windows** przez
cross-build w GitHub Actions (`cibuildwheel`).

## Spis treści
1. [Struktura projektu](#struktura-projektu)
2. [Jak to działa](#jak-to-dziala)
3. [Wydanie nowej wersji — krok po kroku](#wydanie-nowej-wersji)
4. [Test lokalny (Linux)](#test-lokalny)
5. [Jednorazowa konfiguracja repo](#jednorazowa-konfiguracja)
6. [Rozwiązywanie problemów](#rozwiazywanie-problemow)
7. [Szybka ściąga](#szybka-sciaga)

---

## Struktura projektu

```
pathl/
├── pathl/
│   ├── __init__.py
│   ├── cli.py
│   └── _native/
│       ├── __init__.py       # pusty plik, żeby _native było pakietem
│       └── core.c             # kod rozszerzenia C (Python.h)
├── scripts/
│   └── build.sh                # lokalny build + test (Linux)
├── .github/
│   └── workflows/
│       └── build-wheels.yml    # cross-build Linux + Windows, publikacja na PyPI
├── pyproject.toml              # metadane + konfiguracja cibuildwheel
├── setup.py                    # WYŁĄCZNIE definicja ext_modules (rozszerzenia C)
├── README.md
└── CHANGELOG.md
```

**Dlaczego jest i `pyproject.toml`, i `setup.py`?**
Cała konfiguracja pakietu (nazwa, wersja, zależności) mieszka w
`pyproject.toml` — to nowoczesny standard. Ale `pyproject.toml` nie ma
deklaratywnego pola do zdefiniowania modułów C (`ext_modules`), więc
`setup.py` jest zredukowany do jednego zadania: powiedzieć setuptools,
żeby skompilował `core.c`.

---

## Jak to działa

- **Lokalnie** (`scripts/build.sh`) — buduje wheel tylko dla Twojej
  platformy (Linux), sprawdza czy `Python.h` i `gcc` są dostępne,
  kompiluje `core.c` i testuje import. Służy do szybkiej weryfikacji
  przed wypchnięciem taga.
- **GitHub Actions** (`.github/workflows/build-wheels.yml`) — uruchamia
  się przy pushu taga `v*`. Buduje wheels **osobno** na `ubuntu-latest`
  (przez `cibuildwheel`, w środowisku manylinux) i na `windows-latest`
  (przez `cibuildwheel`, z MSVC), a następnie **automatycznie publikuje
  wszystko na PyPI**.
- Użytkownik końcowy, niezależnie czy jest na Linuksie czy Windows,
  dostaje przy `pip install pathl` gotowy, prekompilowany wheel — **nie
  potrzebuje kompilatora C**.

---

## Wydanie nowej wersji

### 1. Zmień numer wersji

Wersja żyje w **jednym miejscu** — `pyproject.toml`:

```toml
[project]
version = "0.1.0a2"
```

> ⚠️ Format zgodny z **PEP 440**: `0.1.0a2`, `0.1.0b1`, `0.1.0rc1`,
> `0.1.0` — **bez myślnika** przed literą.

| Wersja      | Znaczenie                | Przykład   |
|-------------|---------------------------|------------|
| `X.Y.ZaN`   | Alpha (testy wewnętrzne)  | `0.1.0a1`  |
| `X.Y.ZbN`   | Beta (testy zewnętrzne)   | `0.1.0b1`  |
| `X.Y.ZrcN`  | Release candidate         | `0.1.0rc1` |
| `X.Y.Z`     | Stabilna                  | `0.1.0`    |

### 2. Zaktualizuj CHANGELOG.md

Krótki wpis co się zmieniło w tej wersji.

### 3. Przetestuj build lokalnie

```bash
bash scripts/build.sh
```

Skrypt sprawdzi `Python.h`, `gcc`, zbuduje wheel, uruchomi `twine check`
i zaimportuje skompilowany moduł `pathl._native.core`, żeby upewnić się,
że kompilacja C w ogóle przeszła — **zanim** cokolwiek trafi do GitHuba.

### 4. Commit i push

```bash
git add pyproject.toml CHANGELOG.md
git commit -m "Bump version to 0.1.0a2"
git push
```

### 5. Stwórz i wypchnij tag

```bash
git tag v0.1.0a2
git push origin v0.1.0a2
```

> Tag **musi** zaczynać się od `v` i pasować do wersji w
> `pyproject.toml` — po to reaguje na niego workflow.

### 6. GitHub Actions robi resztę automatycznie

Push taga uruchamia `build-wheels.yml`, który:

1. buduje `.whl` na Linuksie (manylinux) — job `build_wheels` / `ubuntu-latest`,
2. buduje `.whl` na Windows (MSVC) — job `build_wheels` / `windows-latest`,
3. buduje `sdist` (źródła) — job `build_sdist`,
4. **automatycznie publikuje wszystko na PyPI** — job `publish`
   (uruchamia się tylko dla tagów `v*`).

Postęp śledzisz w zakładce **Actions** w repo na GitHubie.

### 7. (opcjonalnie) GitHub Release z opisem

Workflow publikuje na PyPI, ale **nie** tworzy release'a na GitHubie —
jeśli go chcesz:

```bash
gh release create "v0.1.0a2" \
    --title "v0.1.0a2" \
    --notes "Wersja 0.1.0a2" \
    --prerelease
```

Flagę `--prerelease` pomiń przy wersji stabilnej (`X.Y.Z` bez `a`/`b`/`rc`).

### 8. Zweryfikuj publikację

```bash
pip install --pre --upgrade pathl
python -c "from pathl._native import core; print(core.path_depth('a/b/c'))"
```

> 💡 Wersje `aN` / `bN` / `rcN` wymagają flagi `--pre` — bez niej `pip`
> pobierze tylko ostatnią wersję stabilną.

---

## Test lokalny

`scripts/build.sh` w skrócie robi:

```bash
rm -rf build dist ./*.egg-info      # czyszczenie
python3 -m build                     # kompilacja C + budowa sdist/wheel
twine check dist/*                   # walidacja metadanych
# + test importu skompilowanego modułu core
```

Wymagania systemowe (Fedora):
```bash
sudo dnf install python3-devel gcc
```

Wymagania systemowe (Debian/Ubuntu):
```bash
sudo apt install python3-dev gcc
```

---

## Jednorazowa konfiguracja repo

Zrób to raz, przed pierwszym releasem:

1. **Sekret PyPI** — Settings → Secrets and variables → Actions →
   New repository secret → `PYPI_API_TOKEN` (token z
   https://pypi.org/manage/account/token/, scope: Upload packages).
2. **Pliki w repo** — upewnij się, że są na miejscu:
   - `pathl/_native/__init__.py` (pusty)
   - `pathl/_native/core.c`
   - `setup.py` (definicja `ext_modules`)
   - `.github/workflows/build-wheels.yml`
3. **CLI importuje moduł natywny**, np. w `pathl/cli.py`:
   ```python
   from pathl._native import core
   ```

---

## Rozwiązywanie problemów

### Błąd: `fatal error: Python.h: No such file or directory`
Brak nagłówków deweloperskich Pythona (dotyczy tylko builda **lokalnego**
na Linuksie — na GitHub Actions `cibuildwheel` zarządza tym sam).
```bash
sudo dnf install python3-devel      # Fedora
sudo apt install python3-dev        # Debian/Ubuntu
```

### Błąd: `error: Microsoft Visual C++ 14.0 is required` (tylko lokalnie na Windows)
Nie dotyczy Cię, bo build na Windows robi GitHub Actions
(`windows-latest` z preinstalowanym MSVC przez `cibuildwheel`). Ten
błąd pojawia się tylko, gdybyś próbował budować ręcznie na własnym
Windows bez Visual Studio Build Tools.

### Błąd: `File already exists` przy publikacji na PyPI
Ta wersja już istnieje na PyPI — **nie da się jej nadpisać**. Zwiększ
numer wersji (np. `0.1.0a2` → `0.1.0a3`) i powtórz cały proces od kroku 1.

### Workflow na GitHub Actions kończy się na etapie `publish` z błędem 403
Sekret `PYPI_API_TOKEN` jest zły, wygasł, lub ma za wąski scope.
Wygeneruj nowy token na PyPI i zaktualizuj sekret w repo.

### `twine check` zgłasza błąd przy wersji `0.1.0-a2`
Myślnik jest niepoprawny wg PEP 440. Popraw na `0.1.0a2`.

---

## Szybka ściąga

```bash
# 1. Zmień wersję w pyproject.toml (np. 0.1.0a1 -> 0.1.0a2)

# 2. Test lokalny
bash scripts/build.sh

# 3. Commit
git add pyproject.toml CHANGELOG.md
git commit -m "Bump version to 0.1.0a2"
git push

# 4. Tag -> uruchamia cross-build i publikację na PyPI
git tag v0.1.0a2
git push origin v0.1.0a2

# 5. (opcjonalnie) Release na GitHub
gh release create "v0.1.0a2" --title "v0.1.0a2" --notes "Wersja 0.1.0a2" --prerelease

# 6. Weryfikacja
pip install --pre --upgrade pathl
python -c "from pathl._native import core; print(core.path_depth('a/b/c'))"
```