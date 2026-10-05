"""Arranque local Linux/Windows: backend y frontend compilado en un solo puerto."""

import argparse
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser(description="Iniciar Inspector MSG local")
    parser.add_argument("--sin-navegador", action="store_true")
    options = parser.parse_args()
    python = (
        ROOT
        / "backend"
        / ".venv"
        / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    )
    if not python.is_file():
        print(
            "Falta preparar el entorno. Consulte los pasos de instalación en README.md."
        )
        return 1
    if not (ROOT / "frontend/dist/index.html").is_file():
        print(
            "Falta compilar la interfaz: entre en frontend y ejecute npm ci y npm run build."
        )
        return 1
    url = "http://127.0.0.1:8000"
    try:
        urllib.request.urlopen(f"{url}/api/health", timeout=1).close()
    except (urllib.error.URLError, OSError):
        pass
    else:
        print(f"La aplicación ya está en ejecución: {url}")
        if not options.sin_navegador:
            webbrowser.open(url)
        return 0
    process = subprocess.Popen(
        [
            str(python),
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
            "--no-access-log",
        ],
        cwd=ROOT / "backend",
    )

    def open_when_ready() -> None:
        for _ in range(50):
            if process.poll() is not None:
                return
            try:
                urllib.request.urlopen(f"{url}/api/health", timeout=1).close()
                webbrowser.open(url)
                return
            except (urllib.error.URLError, OSError):
                time.sleep(0.2)

    if not options.sin_navegador:
        threading.Thread(target=open_when_ready, daemon=True).start()
    print(f"Inspector MSG: {url} | Ctrl+C para cerrar", flush=True)
    try:
        return process.wait()
    except KeyboardInterrupt:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        return 0


if __name__ == "__main__":
    sys.exit(main())
