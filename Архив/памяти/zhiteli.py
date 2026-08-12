# -*- coding: utf-8 -*-
"""ПАМЯТЬ: метки жителей — то, что человек нажил и оплатил."""
import json
from pathlib import Path

ИМЯ = "Жители · метки"
_K = Path(__file__).resolve().parents[2] / "GRONDHEIM_CITY" / "жители" / "ковчег"


def _faily():
    if not _K.is_dir():
        return []
    return sorted(_K.glob("*/2_метки/metki.json"))


def est() -> bool:
    return bool(_faily())


def zapisi(predel: int = 200) -> list:
    out = []
    for f in _faily():
        kto = f.parents[1].name
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        spisok = d if isinstance(d, list) else d.get("метки", [])
        for m in spisok or []:
            if not isinstance(m, dict):
                continue
            out.append({
                "когда": str(m.get("когда", ""))[:16],
                "что": str(m.get("текст", ""))[:220],
                "откуда": f"{kto} · {m.get('откуда', '')}"})
    out.sort(key=lambda x: x["когда"], reverse=True)
    return out[:predel]
