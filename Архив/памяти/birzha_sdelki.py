# -*- coding: utf-8 -*-
"""ПАМЯТЬ: сделки Биржи — атлас случаев и результат по деньгам."""
import json
from pathlib import Path

ИМЯ = "Биржа · сделки"
_D = Path(__file__).resolve().parents[2] / "GRONDHEIM_CITY" / "Биржа" / "данные"


def _faily():
    if not _D.is_dir():
        return []
    return [p for p in _D.glob("*.jsonl")
            if p.name.startswith(("atlas_trading", "trading_pnl"))
            and "archive" not in p.name]


def est() -> bool:
    return bool(_faily())


def zapisi(predel: int = 200) -> list:
    out = []
    for f in _faily():
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
                "когда": str(d.get("ts") or d.get("время") or d.get("когда")
                             or d.get("timestamp") or "")[:16],
                "что": (d.get("итог") or d.get("вердикт") or d.get("сигнал")
                        or json.dumps(d, ensure_ascii=False))[:220],
                "откуда": f.name})
    out.sort(key=lambda x: x["когда"], reverse=True)
    return out[:predel]
