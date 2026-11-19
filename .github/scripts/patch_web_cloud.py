#!/usr/bin/env python3
"""Corrige la web antes de publicar; falla si el paquete web no coincide con lo esperado.
No contiene secretos, datos clinicos ni cambios en el Excel original.
"""
from pathlib import Path
import json

PATCHES = json.loads(r'''[{"path":"cloud.js","label":"formato REST de Firestore","old":"return `${base()}/owners/${safe(session.uid)}/entries/${hex}`;","next":"return `projects/${safe(config.projectId)}/databases/(default)/documents/owners/${safe(session.uid)}/entries/${hex}`;"},{"path":"cloud.js","label":"consulta documento remoto","old":"async function fetchOne(name){try{return await request(name);}","next":"async function fetchOne(name){try{return await request('https://firestore.googleapis.com/v1/'+name);}"},{"path":"app.js","label":"estado real OneDrive","old":"${renderCloudPanel()}<section class=\"card sync-box\">","next":"${renderCloudPanel()}<section class=\"card\"><div class=\"card-head\"><h3>OneDrive personal de Outlook</h3><span class=\"badge warn\">Pendiente de autorización Microsoft</span></div><p class=\"small muted\">La lectura automática de tu copia del Excel se está preparando de forma independiente del capturador Windows. Todavía no hay acceso autorizado a OneDrive ni importación automática; no es necesario instalar Azure. Cuando esté activada, las filas llegarán como capturas pendientes de revisión, nunca como congelaciones confirmadas.</p></section><section class=\"card sync-box\">"}]''')
root = Path("site")
changes = {}
for item in PATCHES:
    path = root / item["path"]
    if not path.is_file():
        raise RuntimeError("No existe el archivo web: " + str(path))
    source = changes.get(item["path"], path.read_text(encoding="utf-8"))
    matches = source.count(item["old"])
    if matches != 1:
        raise RuntimeError(f"Parche {item['label']}: esperado 1 coincidencia, encontrado {matches}")
    changes[item["path"]] = source.replace(item["old"], item["next"], 1)
for name, updated in changes.items():
    (root / name).write_text(updated, encoding="utf-8")
print("Correcciones web listas: Firestore y recepcion remota OneDrive pendientes de activar.")
