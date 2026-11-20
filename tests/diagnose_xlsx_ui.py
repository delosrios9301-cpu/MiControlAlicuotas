#!/usr/bin/env python3
from pathlib import Path
s=Path("site/app.js").read_text()
terms=["function modal(", "const modal=", "function toast(", "const toast=", "function renderSync()", "function renderHome()", "function renderCloudPanel()", "function renderExcelHub()", "async function refresh()", "case'review-capture'", "case'import-capture'", "function capture", "case'close-modal'", "function button("]
for t in terms:
 p=s.find(t)
 if p>=0:print("UI_DIAG",t,repr(s[p:p+ (3000 if t in ("function renderSync()","function renderCloudPanel()") else 950)]))
print("UI_DIAG_COUNT", s.count("manualExcelInput"),s.count("Capturas Excel para revisar"),s.count("data-page=\\\"sincronizacion\\\""))
