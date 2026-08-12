# -*- coding: utf-8 -*-
"""ПАМЯТЬ: дневники работников — что делал и почему, своими словами."""
import json
from pathlib import Path

ИМЯ = "Дневники работников"
_CITY = Path(__file__).resolve().parents[2] / "GRONDHEIM_CITY"


def _faily():
    if not _CITY.is_dir():
        return []
    return sorted(_CITY.rglob("данные/diary_*.jsonl"))


def est() -> bool:
    return bool(_faily())


def zapisi(predel: int = 200) -> list:
    out = []
    for f in _faily():
        chasti = f.parts
        slot = chasti[-3] if len(chasti) > 3 else ""
        try:
            stroki = f.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue
        for s in stroki[-predel:]:
            try:
                d = json.loads(s)
            except Exception:
                continue
            zapis = d.get("diary_entry") or d
            kogda = d.get("ts") or d.get("когда") or d.get("время") or ""
            # время бывает числом секунд — переводим в человеческое
            try:
                if isinstance(kogda, (int, float)) or (
                        isinstance(kogda, str) and kogda.replace(".", "", 1).isdigit()):
                    from datetime import datetime
                    kogda = datetime.fromtimestamp(float(kogda)).strftime(
                        "%Y-%m-%d %H:%M")
            except Exception:
                pass
            out.append({
                "когда": str(kogda)[:16],
                "что": (str(zapis.get("action") or zapis.get("что") or "")
                        [:220] or json.dumps(zapis, ensure_ascii=False)[:220]),
                "откуда": f"{slot} · {f.name}"})
    out.sort(key=lambda x: x["когда"], reverse=True)
    return out[:predel]
