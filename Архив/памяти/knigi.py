# -*- coding: utf-8 -*-
"""ПАМЯТЬ: книги города — летопись, чертёж, законы кварталов."""
from pathlib import Path

ИМЯ = "Книги города"
_K = Path(__file__).resolve().parents[2]


def _faily():
    return sorted(p for p in _K.glob("*.md") if p.stat().st_size > 800)


def est() -> bool:
    return bool(_faily())


def zapisi(predel: int = 200) -> list:
    from datetime import datetime
    out = []
    for f in _faily():
        try:
            razmer = f.stat().st_size // 1024
            kogda = datetime.fromtimestamp(f.stat().st_mtime)
        except Exception:
            continue
        pervaya = ""
        try:
            for s in f.read_text(encoding="utf-8", errors="replace").splitlines():
                if s.strip() and not s.startswith("#"):
                    pervaya = s.strip()[:160]
                    break
        except Exception:
            pass
        out.append({"когда": kogda.strftime("%Y-%m-%d %H:%M"),
                    "что": f"{f.name} · {razmer} КБ — {pervaya}",
                    "откуда": "корень города"})
    out.sort(key=lambda x: x["когда"], reverse=True)
    return out[:predel]
