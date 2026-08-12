# -*- coding: utf-8 -*-
"""ПАМЯТЬ: трудовые истории мест — кого принимали и за что снимали."""
import json
from pathlib import Path

ИМЯ = "Трудовые истории мест"
_P = Path(__file__).resolve().parents[2] / "GRONDHEIM_CITY" / "посты"


def est() -> bool:
    return _P.is_dir() and any(_P.glob("*/пост.json"))


def zapisi(predel: int = 200) -> list:
    out = []
    for f in sorted(_P.glob("*/пост.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        nazv = d.get("название", f.parent.name)
        for z in d.get("трудовая_история", []) or []:
            pochemu = f" — {z.get('почему')}" if z.get("почему") else ""
            out.append({
                "когда": str(z.get("когда", ""))[:16],
                "что": f"{z.get('что','')}: {z.get('кто','')}{pochemu}",
                "откуда": nazv})
    out.sort(key=lambda x: x["когда"], reverse=True)
    return out[:predel]
