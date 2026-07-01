#!/usr/bin/env bash
set -euo pipefail

# --- Konfiguracja ---
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "==> Sprawdzam nagłówki Python.h (potrzebne do kompilacji rozszerzenia C)"
if ! python3 -c "import sysconfig, os; p = os.path.join(sysconfig.get_paths()['include'], 'Python.h'); exit(0 if os.path.exists(p) else 1)"; then
    echo "BŁĄD: Brak Python.h. Zainstaluj pakiet nagłówków deweloperskich, np.:"
    echo "  Fedora:  sudo dnf install python3-devel"
    echo "  Debian:  sudo apt install python3-dev"
    exit 1
fi

echo "==> Sprawdzam kompilator C (gcc)"
if ! command -v gcc >/dev/null 2>&1; then
    echo "BŁĄD: Brak gcc. Zainstaluj: sudo dnf install gcc  (lub apt install gcc)"
    exit 1
fi

echo "==> Czyszczę stare build/dist"
rm -rf build dist ./*.egg-info

echo "==> Buduję paczkę (sdist + wheel, z kompilacją rozszerzenia C)"
python3 -m build

echo "==> Sprawdzam poprawność paczki"
twine check dist/*

echo "==> Gotowe. Zawartość dist/:"
ls -lh dist/

echo ""
echo "==> Test importu skompilowanego modułu C:"
python3 - <<'PYEOF'
import sys, glob, subprocess, tempfile, os

wheel = sorted(glob.glob("dist/*.whl"))[-1]
with tempfile.TemporaryDirectory() as tmp:
    subprocess.run([sys.executable, "-m", "pip", "install", "--target", tmp, wheel], check=True)
    sys.path.insert(0, tmp)
    from pathl._native import core
    print("Moduł core załadowany poprawnie. Test path_depth('a/b/c') =", core.path_depth("a/b/c"))
PYEOF