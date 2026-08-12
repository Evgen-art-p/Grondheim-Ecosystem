# -*- coding: utf-8 -*-
"""ПАМЯТЬ: Маяк — кто и когда откликался с той стороны."""
import json
from pathlib import Path

ИМЯ = "Маяк · пульсы и гнёзда"
_M = Path(__file__).resolve().parents[2] / "Маяк"


def _faily():
    if not _M.is_dir():
        return []
    return sorted(_M.rglob("пульсы.jsonl"))


def est() -> bool:
    return bool(_faily()) or (_M / "острова").is_dir()


def zapisi(predel: int = 200) -> list:
    out = []
    for f in _faily():
        kto = f.parent.name
        try:
            stroki = f.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue
        for s in stroki[-predel:]:
            try:
                d = json.loads(s)
            except Exception:
                continue
            out.append({
                "когда": str(d.get("когда") or d.get("time") or "")[:16],
                "что": json.dumps({k: v for k, v in d.items()
                                   if k not in ("когда", "time")},
                                  ensure_ascii=False)[:220],
                "откуда": kto})
    out.sort(key=lambda x: x["когда"], reverse=True)
    return out[:predel]
