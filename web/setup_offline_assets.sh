#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WEB_DIR="$ROOT_DIR/web"
PY_BIN="${PYTHON:-python}"
export WEB_DIR

mkdir -p "$WEB_DIR/vendor/pyscript" "$WEB_DIR/vendor/pyodide" "$WEB_DIR/vendor/wheels"

"$PY_BIN" - <<'PY'
import os
import re
from pathlib import Path
from urllib.request import Request, urlopen

BASE = "https://pyscript.net/releases/2025.3.1/"
OUT = Path(os.environ["WEB_DIR"]) / "vendor" / "pyscript"
OUT.mkdir(parents=True, exist_ok=True)


def download(name: str) -> None:
  req = Request(BASE + name, headers={"User-Agent": "Mozilla/5.0"})
  data = urlopen(req).read()
  (OUT / name).write_bytes(data)


for core_asset in ("core.js", "core.css"):
  download(core_asset)

pattern = re.compile(r'"\./([A-Za-z0-9._-]+)"')
seen: set[str] = set()
queue = ["core.js", "core.css"]

while queue:
  name = queue.pop(0)
  if name in seen:
    continue
  seen.add(name)
  path = OUT / name
  if not path.exists() or path.suffix not in {".js", ".css"}:
    continue

  text = path.read_text(encoding="utf-8", errors="ignore")
  for dep in sorted(set(pattern.findall(text))):
    dep_path = OUT / dep
    if not dep_path.exists():
      try:
        download(dep)
        print(f"downloaded {dep}")
      except Exception:
        # Alguns caminhos são runtime-only e não são arquivos estáticos publicados.
        continue
    if dep.endswith((".js", ".css")) and dep not in seen:
      queue.append(dep)

print(f"PyScript local: {len(list(OUT.glob('*')))} arquivo(s).")
PY

curl -fsSL "https://github.com/pyodide/pyodide/releases/download/0.27.7/pyodide-0.27.7.tar.bz2" -o /tmp/pyodide-0.27.7.tar.bz2
rm -rf "$WEB_DIR/vendor/pyodide"/*
tar -xjf /tmp/pyodide-0.27.7.tar.bz2 -C "$WEB_DIR/vendor/pyodide" --strip-components=1

"$PY_BIN" -m pip download --no-deps -d "$WEB_DIR/vendor/wheels" \
  "pypdf==5.9.0" \
  "openpyxl==3.1.5" \
  "et_xmlfile==2.0.0"

echo "Offline assets preparados em $WEB_DIR/vendor"
