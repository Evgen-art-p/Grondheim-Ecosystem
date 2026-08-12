# -*- coding: utf-8 -*-
"""ПАМЯТЬ: собственный склад Архива — то, что принесли рудой.

Раньше он был единственным. Теперь — одна память среди прочих.
"""
import json
from pathlib import Path

ИМЯ = "Склад Архива"
_K = Path(__file__).resolve().parents[1] / "данные" / "архив" / "каталог.json"


def est() -> bool:
    return _K.is_file()


def zapisi(predel: int = 200) -> list:
    try:
        d = json.loads(_K.read_text(encoding="utf-8"))
    except Exception:
        return []
    out = []
    for z in (d.get("записи") or []):
        if not isinstance(z, dict):
            continue
        out.append({"когда": str(z.get("когда") or z.get("дата", ""))[:16],
                    "что": str(z.get("название") or z.get("что", ""))[:220],
                    "откуда": str(z.get("раздел", ""))})
    out.sort(key=lambda x: x["когда"], reverse=True)
    return out[:predel]
