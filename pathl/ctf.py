#!/usr/bin/env python3
"""
CTF Manager – uniwersalne narzędzie do uruchamiania, tworzenia i zarządzania
zadaniami CTF w różnych technologiach (Python, Flask, skrypty, Docker).
"""

import os
import json
import argparse
import importlib.util
import subprocess
import sys
import time
import webbrowser
import threading
import socket
import platform
import shutil


# ============================================================================
# FUNKCJE POMOCNICZE
# ============================================================================

def load_ctf(ctf_number):
    """Wczytuje konfigurację CTF z pliku ctf.json."""
    path = os.path.join("ctfs", str(ctf_number), "ctf.json")
    if not os.path.isfile(path):
        print(f"❌ Błąd: nie znaleziono {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_free_port():
    """Znajduje wolny port w systemie."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def is_docker_installed():
    """Sprawdza, czy Docker jest dostępny w systemie."""
    try:
        subprocess.run(['docker', '--version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


# ============================================================================
# URACHAMIANIE RÓŻNYCH TYPÓW ENTRY
# ============================================================================

def run_entry(ctf_number, entry, data=None):
    """
    Uruchamia wpis (entry) z ctf.json w zależności od typu.
    Zwraca True jeśli uruchomiono pomyślnie, False w przypadku błędu.
    """
    if not isinstance(entry, dict):
        # Prosty zapis "modul:funkcja"
        module_name, function_name = entry.split(":")
        module_path = os.path.join("ctfs", str(ctf_number), f"{module_name}.py")
        if not os.path.isfile(module_path):
            print(f"❌ Brak pliku {module_path}")
            return False
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if hasattr(module, function_name):
            func = getattr(module, function_name)
            func(data) if data else func()
            return True
        else:
            print(f"❌ Brak funkcji {function_name} w {module_name}.py")
            return False

    entry_type = entry.get('type', 'python')
    ctf_dir = os.path.join("ctfs", str(ctf_number))

    # ---------- DOCKER ----------
    if entry_type == 'docker':
        if not is_docker_installed():
            print("❌ Docker nie jest zainstalowany!")
            print("   Zainstaluj Docker Desktop: https://www.docker.com/products/docker-desktop")
            print("   Lub na Fedorze: sudo dnf install docker-ce docker-ce-cli containerd.io")
            print("   Następnie: sudo systemctl start docker")
            print("   I dodaj użytkownika: sudo usermod -aG docker $USER")
            return False

        dockerfile = entry.get('dockerfile', 'Dockerfile')
        image_name = entry.get('image_name', f'ctf-{ctf_number}')
        container_name = entry.get('container_name', f'ctf-{ctf_number}')
        port = entry.get('port')
        host_port = entry.get('host_port')
        timeout = entry.get('timeout', 300)

        print(f"\n🐳 Budowanie obrazu Docker dla CTF {ctf_number}")
        print("=" * 50)

        build_cmd = [
            'docker', 'build',
            '-t', image_name,
            '-f', os.path.join(ctf_dir, dockerfile),
            ctf_dir
        ]
        try:
            subprocess.run(build_cmd, check=True)
            print(f"✅ Obraz {image_name} zbudowany")
        except subprocess.CalledProcessError as e:
            print(f"❌ Błąd budowania: {e}")
            return False
        except FileNotFoundError:
            print("❌ Nie znaleziono Dockera.")
            return False

        # Zatrzymaj i usuń stary kontener
        subprocess.run(['docker', 'stop', container_name], capture_output=True)
        subprocess.run(['docker', 'rm', container_name], capture_output=True)

        run_cmd = [
            'docker', 'run', '-d',
            '--name', container_name,
            '--restart', 'unless-stopped'
        ]
        if port and host_port:
            run_cmd.extend(['-p', f'{host_port}:{port}'])
        if timeout:
            run_cmd.extend(['--stop-timeout', str(timeout)])
        run_cmd.append(image_name)

        print(f"\n🚀 Uruchamianie kontenera {container_name}")
        if port and host_port:
            print(f"🔗 Port: {host_port} -> {port}")
        print("=" * 50)

        try:
            result = subprocess.run(run_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Błąd: {result.stderr}")
                return False

            container_id = result.stdout.strip()
            print(f"✅ Kontener uruchomiony: {container_id[:12]}")

            # Pobierz IP kontenera
            ip_cmd = ['docker', 'inspect', '-f', '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}',
                      container_name]
            ip_result = subprocess.run(ip_cmd, capture_output=True, text=True)
            container_ip = ip_result.stdout.strip()

            print("\n" + "=" * 50)
            print("📡 INFORMACJE O POŁĄCZENIU")
            print("=" * 50)
            if port and host_port:
                print(f"🌐 Połączenie z hosta:   telnet localhost {host_port}")
                if port == 23:
                    print("   👤 Login: root")
                    print("   🔑 Hasło: (puste – naciśnij ENTER)")
            if container_ip:
                print(f"🐳 Połączenie wewnętrzne: telnet {container_ip} {port}")
            print("=" * 50)

            # Status
            time.sleep(2)
            status_cmd = ['docker', 'ps', '--filter', f'name={container_name}', '--format', '{{.Status}}']
            status = subprocess.run(status_cmd, capture_output=True, text=True).stdout.strip()
            if status:
                print(f"📊 Status: {status}")
            else:
                print("⚠️  Kontener może mieć problem – sprawdź logi:")
                subprocess.run(['docker', 'logs', '--tail', '20', container_name])

            print("\n💡 Komendy pomocnicze:")
            print(f"   # Zobacz logi:  docker logs {container_name}")
            print(f"   # Zatrzymaj:    docker stop {container_name}")
            print(f"   # Status:       python3 ctf.py status {ctf_number}")

            return True

        except Exception as e:
            print(f"❌ Wyjątek: {e}")
            return False

    # ---------- PYTHON ----------
    elif entry_type == 'python':
        module_name = entry.get('module', 'main')
        function_name = entry.get('function', 'main')
        module_path = os.path.join(ctf_dir, f"{module_name}.py")
        if not os.path.isfile(module_path):
            print(f"❌ Brak pliku {module_path}")
            return False
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if hasattr(module, function_name):
            func = getattr(module, function_name)
            func(data) if data else func()
            return True
        else:
            print(f"❌ Brak funkcji {function_name}")
            return False

    # ---------- SERVER (Flask/Django) ----------
    elif entry_type == 'server':
        module_name = entry.get('module', 'app')
        app_name = entry.get('app', 'app')
        port = entry.get('port') or find_free_port()
        host = entry.get('host', '127.0.0.1')
        module_path = os.path.join(ctf_dir, f"{module_name}.py")
        if not os.path.isfile(module_path):
            print(f"❌ Brak pliku {module_path}")
            return False
        sys.path.insert(0, ctf_dir)
        try:
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            app = getattr(module, app_name)

            if 'flask' in str(type(app)).lower():
                print(f"\n🌐 Serwer Flask: http://{host}:{port}")
                print("📱 Ctrl+C aby zatrzymać")
                threading.Thread(target=lambda: time.sleep(1) or webbrowser.open(f"http://{host}:{port}"),
                                 daemon=True).start()
                app.run(host=host, port=port, debug=False)
                return True
            elif 'django' in str(type(app)).lower():
                print(f"\n🌐 Serwer Django: http://{host}:{port}")
                cmd = [sys.executable, os.path.join(ctf_dir, "manage.py"), "runserver", f"{host}:{port}"]
                subprocess.run(cmd)
                return True
            else:
                print(f"❌ Nieznany typ aplikacji: {type(app)}")
                return False
        except Exception as e:
            print(f"❌ Błąd serwera: {e}")
            return False

    # ---------- SKRYPT ----------
    elif entry_type == 'script':
        script_path = entry.get('path', '')
        args = entry.get('args', [])
        full_path = os.path.join(ctf_dir, script_path)
        if not os.path.isfile(full_path):
            print(f"❌ Brak skryptu {full_path}")
            return False
        if script_path.endswith('.py'):
            cmd = [sys.executable, full_path] + args
        elif script_path.endswith('.sh'):
            cmd = ['bash', full_path] + args
        elif script_path.endswith('.js'):
            cmd = ['node', full_path] + args
        else:
            cmd = [full_path] + args
        print(f"\n🔄 Uruchamianie: {script_path}")
        subprocess.run(cmd)
        return True

    # ---------- KOMENDA ----------
    elif entry_type == 'command':
        command = entry.get('command', '')
        print(f"\n🔄 Uruchamianie: {command}")
        subprocess.run(command, shell=True, cwd=ctf_dir)
        return True

    else:
        print(f"❌ Nieznany typ entry: {entry_type}")
        return False


# ============================================================================
# TEST WIEDZY (PYTANIA)
# ============================================================================

def ask_questions(questions_data):
    """Zadaje pytania i sprawdza odpowiedzi. Zwraca True jeśli zaliczono."""
    if not questions_data:
        return True

    print("\n" + "=" * 50)
    print("📝 TEST WIEDZY – odpowiedz na pytania:")
    print("=" * 50 + "\n")

    correct = 0
    total = len(questions_data)
    wrong = []

    for i, q in enumerate(questions_data, 1):
        print(f"Pytanie {i}/{total}")
        print(q['question'])

        if q.get('type') == 'choice':
            print("Opcje:")
            for idx, opt in enumerate(q['options'], 1):
                print(f"  {idx}. {opt}")
            while True:
                try:
                    ans_idx = int(input("\nTwój wybór (numer): ")) - 1
                    if 0 <= ans_idx < len(q['options']):
                        user_ans = q['options'][ans_idx]
                        break
                    else:
                        print("❌ Nieprawidłowy numer.")
                except ValueError:
                    print("❌ Podaj numer.")
        else:
            user_ans = input("\nTwoja odpowiedź: ").strip()

        expected = q['answer']
        ok = user_ans.lower() == expected.lower()
        if ok:
            print("✅ Poprawna!")
            correct += 1
        else:
            print(f"❌ Niepoprawna. Prawidłowa: {expected}")
            wrong.append({'q': q['question'], 'your': user_ans, 'correct': expected})

        if 'hint' in q and not ok:
            print(f"💡 Podpowiedź: {q['hint']}")
        print("-" * 40)

    print("\n" + "=" * 50)
    print("PODSUMOWANIE")
    print("=" * 50)
    print(f"Poprawne: {correct}/{total} ({correct / total * 100:.1f}%)")
    for w in wrong:
        print(f"\nPytanie: {w['q']}\nTwoja: {w['your']}\nPrawidłowa: {w['correct']}")

    passed = correct / total >= 0.6
    if passed:
        print("\n✅ Gratulacje! Zdałeś test!")
    else:
        print("\n❌ Nie zdałeś testu (wymagane 60%).")
    return passed


# ============================================================================
# GŁÓWNE FUNKCJE CTF
# ============================================================================

def run_ctf(ctf_number, skip_questions=False):
    """Ładuje i uruchamia CTF o podanym numerze."""
    data = load_ctf(ctf_number)

    entry = data.get("entry")
    if not entry:
        print("❌ Brak pola 'entry' w ctf.json")
        return

    print("\n" + "=" * 50)
    print(f"🚀 Uruchamianie: {data.get('name', 'CTF')}")
    print("=" * 50 + "\n")

    # 🔥 NAJPIERW URUCHAMIAMY CTF (kontener/serwer)
    success = run_entry(ctf_number, entry, data)

    # 🔥 TEST WIEDZY TYLKO JEŚLI KONTENER WYSTARTOWAŁ POMYŚLNIE
    if success and not skip_questions and data.get("questions"):
        print("\n" + "=" * 50)
        print("📝 TEST WIEDZY – odpowiedz na pytania:")
        print("=" * 50)
        if not ask_questions(data["questions"]):
            print("\n❌ Nie zaliczyłeś testu wiedzy.")
            print("💡 Możesz spróbować ponownie z flagą -s (pomiń test)")
            print("   python3 ctf.py run 4 -s")
        else:
            print("\n✅ Gratulacje! Zdałeś test wiedzy!")
    elif success and skip_questions:
        print("\n⏭️  Pomijanie testu wiedzy (--skip-questions)")
    elif not success:
        print("\n❌ Nie udało się uruchomić CTF. Test wiedzy pominięty.")


def list_ctfs():
    """Wyświetla listę dostępnych CTF-ów."""
    ctfs_dir = "ctfs"
    if not os.path.exists(ctfs_dir):
        print(f"📁 Folder {ctfs_dir} nie istnieje.")
        return

    available = []
    for item in os.listdir(ctfs_dir):
        path = os.path.join(ctfs_dir, item)
        if os.path.isdir(path):
            json_path = os.path.join(path, "ctf.json")
            if os.path.isfile(json_path):
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        name = data.get("name", item)
                        diff = data.get("difficulty", "?")
                        pts = data.get("points", "?")
                        has_q = "✓" if data.get("questions") else "✗"
                        entry = data.get("entry")
                        etype = entry.get("type", "python") if isinstance(entry, dict) else "python"
                        available.append((item, name, diff, pts, has_q, etype))
                except:
                    available.append((item, "⚠️ Błąd odczytu", "?", "?", "?", "?"))

    if available:
        print("\n📋 Dostępne CTF-y:")
        print("-" * 80)
        print(f"{'Nr':<6} {'Nazwa':<30} {'Trudność':<12} {'Punkty':<8} {'Pytania':<8} {'Typ'}")
        print("-" * 80)
        for nr, name, diff, pts, q, typ in sorted(available):
            print(f"{nr:<6} {name[:30]:<30} {diff:<12} {pts:<8} {q:<8} {typ}")
        print("-" * 80)
    else:
        print("❌ Nie znaleziono żadnych CTF-ów.")


def create_ctf(ctf_number):
    """Tworzy nowy szablon CTF w folderze ctfs/<numer>/."""
    ctf_dir = os.path.join("ctfs", str(ctf_number))
    if os.path.exists(ctf_dir):
        print(f"❌ CTF o numerze {ctf_number} już istnieje.")
        return
    os.makedirs(ctf_dir)

    print("\n" + "=" * 50)
    print("🏗️  CREATOR CTF")
    print("=" * 50)
    print("Wybierz typ:")
    print("  1. Python function (main:main)")
    print("  2. Flask web server")
    print("  3. Skrypt Python")
    print("  4. Komenda systemowa")
    print("  5. Docker – Telnet (root bez hasła)")
    print("  6. Docker – niestandardowy (własny Dockerfile)")

    choice = input("\nTwój wybór (1-6): ").strip()

    entry = None
    files_to_create = {}

    # ---------- Opcja 5: Telnet Docker ----------
    if choice == '5':
        entry = {
            "type": "docker",
            "dockerfile": "Dockerfile",
            "port": 23,
            "host_port": 2323,
            "image_name": f"telnet-ctf-{ctf_number}",
            "container_name": f"telnet-ctf-{ctf_number}",
            "timeout": 300
        }
        files_to_create["Dockerfile"] = '''FROM debian:bullseye-slim

RUN apt-get update && apt-get install -y telnetd xinetd procps && rm -rf /var/lib/apt/lists/*

COPY flag.txt /root/flag.txt
COPY start.sh /start.sh
RUN chmod +x /start.sh

RUN echo "service telnet" > /etc/xinetd.d/telnet && \\
    echo "{" >> /etc/xinetd.d/telnet && \\
    echo "  disable         = no" >> /etc/xinetd.d/telnet && \\
    echo "  socket_type     = stream" >> /etc/xinetd.d/telnet && \\
    echo "  protocol        = tcp" >> /etc/xinetd.d/telnet && \\
    echo "  wait            = no" >> /etc/xinetd.d/telnet && \\
    echo "  user            = root" >> /etc/xinetd.d/telnet && \\
    echo "  server          = /usr/sbin/in.telnetd" >> /etc/xinetd.d/telnet && \\
    echo "  server_args     = -L /bin/login" >> /etc/xinetd.d/telnet && \\
    echo "}" >> /etc/xinetd.d/telnet

RUN passwd -d root
RUN useradd -m -s /bin/bash adam && echo "adam:adam123" | chpasswd
RUN useradd -m -s /bin/bash kasia && echo "kasia:kasia456" | chpasswd
RUN useradd -m -s /bin/bash guest && echo "guest:guest" | chpasswd
RUN echo "FLAG{this_is_a_fake_flag}" > /home/guest/fake_flag.txt

EXPOSE 23
CMD ["/start.sh"]
'''
        files_to_create["start.sh"] = '''#!/bin/bash
echo "========================================"
echo "🚩 TELNET CTF - Debian"
echo "========================================"
echo "👤 Login:  root"
echo "🔑 Hasło:  (puste – naciśnij ENTER)"
echo "📁 Flaga:  /root/flag.txt"
echo "========================================"
/usr/sbin/xinetd -dontfork
'''
        files_to_create["flag.txt"] = "CTF{root_has_no_password_how_dangerous}"

        name = input("Nazwa CTF [Telnet - Root without password]: ").strip() or "Telnet - Root without password"
        difficulty = input("Trudność (łatwy/średni/trudny) [łatwy]: ").strip() or "łatwy"
        points = input("Punkty [100]: ").strip()
        points = int(points) if points else 100
        questions = [
            {
                "question": "Jaka jest flaga w katalogu roota?",
                "answer": "CTF{root_has_no_password_how_dangerous}",
                "type": "text",
                "hint": "Zaloguj się jako root bez hasła i użyj cat /root/flag.txt"
            }
        ]
        author = input("Autor [Anonymous]: ").strip() or "Anonymous"

        ctf_data = {
            "name": name,
            "description": "Połącz się przez Telnet i znajdź flagę. Hasło roota jest puste!",
            "entry": entry,
            "author": author,
            "difficulty": difficulty,
            "points": points,
            "questions": questions
        }
        print("\n✅ Utworzono CTF Telnet w Dockerze.")
        print(f"📁 Folder: {ctf_dir}")
        print(f"🔗 Port: 2323 -> 23")

    # ---------- Opcja 6: Docker niestandardowy ----------
    elif choice == '6':
        entry = {
            "type": "docker",
            "dockerfile": "Dockerfile",
            "image_name": f"docker-ctf-{ctf_number}",
            "container_name": f"docker-ctf-{ctf_number}",
            "timeout": 300
        }
        port = input("Port w kontenerze (np. 80) [pomiń]: ").strip()
        if port:
            entry["port"] = int(port)
            host_port = input(f"Port na hoście dla {port} [pomiń]: ").strip()
            if host_port:
                entry["host_port"] = int(host_port)

        files_to_create["Dockerfile"] = '''FROM debian:bullseye-slim
RUN apt-get update && apt-get install -y curl wget && rm -rf /var/lib/apt/lists/*
RUN useradd -m -s /bin/bash ctfuser
COPY flag.txt /flag.txt
RUN chmod 644 /flag.txt
RUN echo "root:password" | chpasswd
CMD ["/bin/bash"]
'''
        files_to_create["flag.txt"] = "FLAG{your_docker_flag_here}"

        name = input("Nazwa CTF [Docker CTF]: ").strip() or "Docker CTF"
        difficulty = input("Trudność (łatwy/średni/trudny) [łatwy]: ").strip() or "łatwy"
        points = input("Punkty [100]: ").strip()
        points = int(points) if points else 100
        author = input("Autor [Anonymous]: ").strip() or "Anonymous"

        ctf_data = {
            "name": name,
            "description": input("Opis zadania: ").strip() or "Opis zadania Docker",
            "entry": entry,
            "author": author,
            "difficulty": difficulty,
            "points": points,
            "questions": []
        }
        print("\n✅ Utworzono niestandardowy CTF Docker.")
        print("📝 Edytuj Dockerfile i flag.txt według potrzeb.")

    # ---------- Opcje 1-4 oraz domyślna ----------
    else:
        if choice == '1':
            entry = "main:main"
            filename = "main.py"
            content = '''#!/usr/bin/env python3
def main():
    print("Rozwiązanie CTF")
    print("Flaga: FLAG{test}")
if __name__ == "__main__":
    main()
'''
        elif choice == '2':
            entry = {"type": "server", "module": "app", "app": "app", "host": "127.0.0.1"}
            filename = "app.py"
            content = '''#!/usr/bin/env python3
from flask import Flask, request, jsonify
app = Flask(__name__)
@app.route('/')
def home():
    return "<h1>CTF</h1><!-- FLAG{test} -->"
@app.route('/flag', methods=['POST'])
def flag():
    data = request.json
    if data and data.get('password') == 'admin123':
        return jsonify({'flag': 'FLAG{test}'})
    return jsonify({'error': 'Wrong password'}), 403
if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=5000)
'''
        elif choice == '3':
            entry = {"type": "script", "path": "solve.py", "args": ["--flag", "FLAG{test}"]}
            filename = "solve.py"
            content = '''#!/usr/bin/env python3
import argparse
def solve(flag):
    print(f"Rozwiązanie: {flag}")
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--flag")
    args = parser.parse_args()
    if args.flag:
        solve(args.flag)
    else:
        print("Podaj flagę: --flag FLAG{...}")
'''
        elif choice == '4':
            entry = {"type": "command", "command": "python3 solve.py"}
            filename = "solve.py"
            content = '''#!/usr/bin/env python3
print("Rozwiązanie CTF – uruchomione przez komendę")
print("Flaga: FLAG{test}")
'''
        else:
            entry = "main:main"
            filename = "main.py"
            content = '''#!/usr/bin/env python3
def main():
    print("Rozwiązanie CTF")
if __name__ == "__main__":
    main()
'''

        files_to_create[filename] = content

        name = input("Nazwa CTF [CTF {ctf_number}]: ").strip() or f"CTF {ctf_number}"
        difficulty = input("Trudność (łatwy/średni/trudny) [łatwy]: ").strip() or "łatwy"
        points = input("Punkty [100]: ").strip()
        points = int(points) if points else 100
        author = input("Autor [Anonymous]: ").strip() or "Anonymous"
        add_q = input("Czy dodać pytania weryfikacyjne? (tak/NIE): ").strip().lower()
        questions = [
            {
                "question": "Jaka jest flaga?",
                "answer": "FLAG{test}",
                "type": "text",
                "hint": "Sprawdź kod źródłowy"
            }
        ] if add_q == "tak" else []

        ctf_data = {
            "name": name,
            "description": input("Opis zadania: ").strip() or "Opis zadania CTF",
            "entry": entry,
            "author": author,
            "difficulty": difficulty,
            "points": points,
            "questions": questions
        }
        print(
            f"\n✅ Utworzono CTF numer {ctf_number} (typ: {entry if isinstance(entry, str) else entry.get('type', 'python')})")

    # Zapis plików
    for fname, content in files_to_create.items():
        with open(os.path.join(ctf_dir, fname), "w", encoding="utf-8") as f:
            f.write(content)

    with open(os.path.join(ctf_dir, "ctf.json"), "w", encoding="utf-8") as f:
        json.dump(ctf_data, f, indent=4, ensure_ascii=False)

    print(f"📁 Folder: {ctf_dir}")
    print("📝 Możesz edytować pliki, aby dostosować zadanie.")


def remove_ctf(ctf_number):
    """Usuwa CTF – zatrzymuje kontener (jeśli istnieje) i kasuje folder."""
    ctf_dir = os.path.join("ctfs", str(ctf_number))
    if not os.path.exists(ctf_dir):
        print(f"❌ CTF o numerze {ctf_number} nie istnieje.")
        return

    # Spróbuj zatrzymać kontener Docker, jeśli istnieje
    try:
        with open(os.path.join(ctf_dir, "ctf.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
            entry = data.get("entry", {})
            if isinstance(entry, dict) and entry.get("type") == "docker":
                container_name = entry.get("container_name", f"ctf-{ctf_number}")
                subprocess.run(['docker', 'stop', container_name], capture_output=True)
                subprocess.run(['docker', 'rm', container_name], capture_output=True)
    except:
        pass

    if os.listdir(ctf_dir):
        print(f"Zawartość folderu {ctf_dir}:")
        for f in os.listdir(ctf_dir):
            print(f"  - {f}")
        confirm = input("Czy na pewno usunąć? (tak/NIE): ")
        if confirm.lower() != "tak":
            print("Anulowano.")
            return

    shutil.rmtree(ctf_dir)
    print(f"✅ Usunięto CTF o numerze {ctf_number}.")


def stop_ctf(ctf_number):
    """Zatrzymuje kontener Docker dla CTF."""
    try:
        data = load_ctf(ctf_number)
        entry = data.get("entry", {})
        if isinstance(entry, dict) and entry.get("type") == "docker":
            container_name = entry.get("container_name", f"ctf-{ctf_number}")
            print(f"🛑 Zatrzymywanie kontenera {container_name}...")
            result = subprocess.run(['docker', 'stop', container_name], capture_output=True)
            if result.returncode == 0:
                print("✅ Kontener zatrzymany.")
            else:
                print(f"❌ Błąd: {result.stderr}")
        else:
            print("❌ To nie jest CTF typu docker.")
    except Exception as e:
        print(f"❌ Błąd: {e}")


def clean_ctf(ctf_number):
    """Usuwa kontener i obraz Docker dla CTF."""
    try:
        data = load_ctf(ctf_number)
        entry = data.get("entry", {})
        if isinstance(entry, dict) and entry.get("type") == "docker":
            container_name = entry.get("container_name", f"ctf-{ctf_number}")
            image_name = entry.get("image_name", f"ctf-{ctf_number}")
            print(f"🧹 Czyszczenie kontenera {container_name}...")
            subprocess.run(['docker', 'stop', container_name], capture_output=True)
            subprocess.run(['docker', 'rm', container_name], capture_output=True)
            print(f"🧹 Usuwanie obrazu {image_name}...")
            subprocess.run(['docker', 'rmi', image_name], capture_output=True)
            print("✅ Posprzątano.")
        else:
            print("❌ To nie jest CTF typu docker.")
    except Exception as e:
        print(f"❌ Błąd: {e}")


def status_ctf(ctf_number):
    """Wyświetla status kontenera Docker dla CTF."""
    try:
        data = load_ctf(ctf_number)
        entry = data.get("entry", {})
        if not (isinstance(entry, dict) and entry.get("type") == "docker"):
            print("❌ To nie jest CTF typu docker.")
            return

        container_name = entry.get("container_name", f"ctf-{ctf_number}")
        image_name = entry.get("image_name", f"ctf-{ctf_number}")
        port = entry.get("port")
        host_port = entry.get("host_port")

        print("\n" + "=" * 50)
        print(f"📊 STATUS CTF {ctf_number}")
        print("=" * 50)

        # Czy kontener istnieje?
        ps_cmd = ['docker', 'ps', '-a', '--filter', f'name={container_name}', '--format', '{{.Status}}']
        status = subprocess.run(ps_cmd, capture_output=True, text=True).stdout.strip()
        if status:
            print(f"✅ Kontener: {container_name}")
            print(f"📊 Status:   {status}")
            ip_cmd = ['docker', 'inspect', '-f', '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}',
                      container_name]
            ip = subprocess.run(ip_cmd, capture_output=True, text=True).stdout.strip()
            if ip:
                print(f"🌐 IP:       {ip}")
            if port and host_port:
                print(f"🔗 Port:     {host_port} -> {port}")
                print(f"🌐 Połącz:   telnet localhost {host_port}")
                if port == 23:
                    print("👤 Login:    root")
                    print("🔑 Hasło:    (puste)")
        else:
            print(f"❌ Kontener {container_name} nie istnieje lub nie działa.")
            img_cmd = ['docker', 'images', '--filter', f'reference={image_name}', '--format', '{{.Repository}}']
            img = subprocess.run(img_cmd, capture_output=True, text=True).stdout.strip()
            if img:
                print(f"📦 Obraz:   {image_name} (istnieje)")
                print(f"💡 Uruchom: python3 ctf.py run {ctf_number}")
            else:
                print(f"📦 Obraz:   {image_name} (nie istnieje)")

        print("=" * 50)

    except Exception as e:
        print(f"❌ Błąd: {e}")


# ============================================================================
# CLI – PARSER ARGUMENTÓW
# ============================================================================

def main():
    parser = argparse.ArgumentParser(prog="ctf",
                                     description="CTF Manager – uruchamiaj, twórz i zarządzaj zadaniami CTF.")
    subparsers = parser.add_subparsers(dest="command", help="Komendy")

    subparsers.add_parser("list", help="Wyświetla listę dostępnych CTF-ów")

    run_p = subparsers.add_parser("run", help="Uruchamia CTF")
    run_p.add_argument("number", type=int, help="Numer CTF")
    run_p.add_argument("-s", "--skip-questions", action="store_true", help="Pomiń test wiedzy")

    create_p = subparsers.add_parser("create", help="Tworzy nowy CTF")
    create_p.add_argument("number", type=int, help="Numer nowego CTF")

    remove_p = subparsers.add_parser("remove", help="Usuwa CTF")
    remove_p.add_argument("number", type=int, help="Numer CTF do usunięcia")

    stop_p = subparsers.add_parser("stop", help="Zatrzymuje kontener Docker CTF")
    stop_p.add_argument("number", type=int, help="Numer CTF")

    clean_p = subparsers.add_parser("clean", help="Usuwa kontener i obraz Docker CTF")
    clean_p.add_argument("number", type=int, help="Numer CTF")

    status_p = subparsers.add_parser("status", help="Sprawdza status kontenera Docker CTF")
    status_p.add_argument("number", type=int, help="Numer CTF")

    args = parser.parse_args()

    if args.command == "list":
        list_ctfs()
    elif args.command == "run":
        run_ctf(args.number, args.skip_questions)
    elif args.command == "create":
        create_ctf(args.number)
    elif args.command == "remove":
        remove_ctf(args.number)
    elif args.command == "stop":
        stop_ctf(args.number)
    elif args.command == "clean":
        clean_ctf(args.number)
    elif args.command == "status":
        status_ctf(args.number)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()