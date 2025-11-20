# tools/filesystem.py
import os
from pathlib import Path

PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", ".")).resolve()

def _safe_path(rel_path: str) -> Path:
    p = (PROJECT_ROOT / rel_path).resolve()
    if PROJECT_ROOT not in p.parents and p != PROJECT_ROOT:
        raise ValueError("Access outside PROJECT_ROOT is not allowed")
    return p

def read_file(path: str) -> dict:
    p = _safe_path(path)
    if not p.exists():
        return {"exists": False, "content": None}
    with p.open("r", encoding="utf-8") as f:
        return {"exists": True, "content": f.read()}

def write_file(path: str, content: str, overwrite: bool = True) -> dict:
    p = _safe_path(path)
    if p.exists() and not overwrite:
        return {"ok": False, "reason": "File exists and overwrite=False"}
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        f.write(content)
    return {"ok": True, "path": str(p)}

def list_files(path: str = ".", max_files: int = 200) -> dict:
    base = _safe_path(path)
    if not base.exists():
        return {"exists": False, "files": []}
    files = []
    for root, dirs, filenames in os.walk(base):
        for name in filenames:
            rel = Path(root).joinpath(name).relative_to(PROJECT_ROOT)
            files.append(str(rel))
            if len(files) >= max_files:
                return {"exists": True, "files": files, "truncated": True}
    return {"exists": True, "files": files, "truncated": False}
