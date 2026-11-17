#!/usr/bin/env python3
"""Configura el frontend usando SOLAMENTE la apiKey pública de Firebase.

NO administra Firebase, NO sube datos clínicos y NO requiere cuenta de servicio.
Si no hay configuración, el sitio se publica en modo local; la interfaz ofrece
conexión manual desde Sincronización.
"""
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

PROJECT = "mi-control-de-alicuotas-cde8d"
PATTERN = re.compile(r"^AIza[0-9A-Za-z_-]{20,}$")
OUTPUT = Path("site/firebase-config.js")
SUMMARY = os.environ.get("GITHUB_STEP_SUMMARY")

def report(message):
    print(message)
    if SUMMARY:
        with open(SUMMARY, "a", encoding="utf-8") as target:
            target.write(message + "\n")

def public_config():
    hosts = (
        f"https://{PROJECT}.web.app/__/firebase/init.json",
        f"https://{PROJECT}.firebaseapp.com/__/firebase/init.json",
    )
    for url in hosts:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "MCA-public-config/1.0"})
            with urllib.request.urlopen(req, timeout=6) as response:
                data = json.load(response)
            if data.get("projectId") == PROJECT and PATTERN.fullmatch(str(data.get("apiKey", ""))):
                return data["apiKey"], "configuración pública de Firebase Hosting"
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return None, None

def main():
    if not OUTPUT.is_file():
        sys.exit("El paquete web no contiene firebase-config.js.")
    api_key = os.environ.get("FIREBASE_WEB_API_KEY", "").strip()
    source = "variable de repositorio de GitHub"
    if not api_key:
        api_key, source = public_config()
    if not api_key:
        report("⚠️ Firebase pendiente: Hosting público no ofrece init.json y FIREBASE_WEB_API_KEY no está configurada. La web sigue disponible en modo local; se puede conectar desde Sincronización.")
        return
    if not PATTERN.fullmatch(api_key):
        sys.exit("FIREBASE_WEB_API_KEY no tiene formato de clave web pública Firebase. Se rechaza el cambio.")
    config = {"apiKey": api_key, "projectId": PROJECT}
    OUTPUT.write_text(
        "// Configuración WEB PÚBLICA de Firebase. No contiene credenciales administrativas.\n"
        + "window.MCA_FIREBASE_CONFIG = "
        + json.dumps(config, ensure_ascii=False, separators=(",", ":"))
        + ";\n",
        encoding="utf-8",
    )
    report(f"✅ Configuración web pública de Firebase preparada desde {source}. Aún se debe verificar Authentication y las reglas reales de Firestore.")

if __name__ == "__main__":
    main()
