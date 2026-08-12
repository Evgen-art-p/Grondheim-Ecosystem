# -*- coding: utf-8 -*-
# PAMYATI_GORODA_V1
"""
ПАМЯТИ ГОРОДА — реестр того, что помнится, и где оно лежит.

ЗАКОН ЭТОГО ФАЙЛА
    Архив ничего не хранит у себя и ничего не переносит. Он знает, ГДЕ
    лежит память, и умеет её показать.

    Списков здесь нет: памяти СКАНИРУЮТСЯ из папки `памяти/`, как истоки
    крана на Бирже. Появился новый файл — появилась новая память, сама.
    Ни эту страницу, ни этот файл править не надо.

    Каждая память — файл с тремя вещами:
        ИМЯ    — как называется
        est()  — есть ли она в ЭТОМ городе (на острове половины не будет)
        zapisi(predel) — записи, свежие сверху
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_HERE = Path(__file__).resolve().parent
PAPKA = _HERE / "памяти"


def _podnyat(put: Path):
    try:
        spec = importlib.util.spec_from_file_location(f"pamyat_{put.stem}", put)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m
    except Exception as e:
        print(f"[ПАМЯТЬ] ⚠️  {put.name} не поднялась: {e}")
        return None


def vse() -> list:
    """Все памяти, которые ЕСТЬ в этом городе. Пусто — честно пусто."""
    out = []
    if not PAPKA.is_dir():
        return out
    for p in sorted(PAPKA.glob("*.py")):
        if p.name.startswith("_"):
            continue
        m = _podnyat(p)
        if m is None:
            continue
        try:
            if not m.est():
                continue
        except Exception:
            continue
        out.append({"ключ": p.stem, "имя": getattr(m, "ИМЯ", p.stem),
                    "модуль": m})
    return out


def zapisi(klyuch: str, predel: int = 200) -> list:
    for p in vse():
        if p["ключ"] == klyuch:
            try:
                return p["модуль"].zapisi(predel)
            except Exception as e:
                return [{"когда": "", "что": f"память не открылась: {e}",
                         "откуда": ""}]
    return []
