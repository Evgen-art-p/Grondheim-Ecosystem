# -*- coding: utf-8 -*-
# RABOTA_DOKUMENT_V1
"""
РАБОТА — должность как документ при месте.

ЗАКОН ЭТОГО ФАЙЛА
    Работа не вкручивается в личность. Место несёт свой документ:
    `слоты/{слот}/должность.json`. В нём написано, что это за
    должность и кто на ней сейчас сидит. У жителя — только мягкая
    отметка в паспорте, чтобы он знал, кто он, где бы ни находился.
    Разошлось — правда за документом.

    Здесь нет UI и нет модели. Чистое чтение и запись диска.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

_BIRZHA = Path(__file__).resolve().parent
CITY = _BIRZHA.parent / "GRONDHEIM_CITY"
IMYA_DOKUMENTA = "должность.json"


def _teper() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _chitat_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _pisat_json(p: Path, d) -> bool:
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(d, ensure_ascii=False, indent=2),
                     encoding="utf-8")
        return True
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────
# ГДЕ ЛЕЖИТ ДОКУМЕНТ
# ─────────────────────────────────────────────────────────────

def put_slota(ceh: str, slot: str, kvartal: str = "Биржа") -> Path:
    return CITY / kvartal / "цеха" / ceh / "слоты" / slot


def put_dokumenta(ceh: str, slot: str, kvartal: str = "Биржа") -> Path:
    return put_slota(ceh, slot, kvartal) / IMYA_DOKUMENTA


def blank(ceh: str, slot: str, nazvanie: str = "",
          kvartal: str = "Биржа") -> dict:
    """Пустой бланк должности. Заполняется на Странице Работы или
    пультом; поля, которые не заполнили, честно остаются пустыми."""
    return {
        "документ": "должность",
        "версия": 1,
        "название": nazvanie or f"{ceh} · {slot}",
        "квартал": kvartal,
        "цех": ceh,
        "слот": slot,
        "чем_занят": "",
        "обязанности": [],
        "судья": "",
        "требования": "",
        "условия": "",
        "движок": "мозг.py",
        "кто_сидит": None,
        "трудовая_история": [],
        "заведён": _teper(),
    }


def chitat(ceh: str, slot: str, kvartal: str = "Биржа"):
    """Документ места или None, если его ещё не заводили."""
    return _chitat_json(put_dokumenta(ceh, slot, kvartal))


def zavesti(ceh: str, slot: str, polya: dict | None = None,
            kvartal: str = "Биржа") -> tuple:
    """Завести документ. Заведённый не перетираем — только дополняем
    пустые поля: трудовую историю терять нельзя."""
    put = put_dokumenta(ceh, slot, kvartal)
    if not put.parent.exists():
        return False, f"нет слота {ceh}/{slot}"
    d = _chitat_json(put)
    if d is None:
        d = blank(ceh, slot, (polya or {}).get("название", ""), kvartal)
        novy = True
    else:
        novy = False
    for k, v in (polya or {}).items():
        if k in ("кто_сидит", "трудовая_история"):
            continue          # это не бланк, это жизнь документа
        if v in (None, "", []):
            continue
        if novy or not d.get(k):
            d[k] = v
    if not _pisat_json(put, d):
        return False, "не записался"
    return True, ("документ заведён" if novy else "документ обновлён")


def spisok(kvartal: str = "Биржа") -> list:
    """Все места квартала: что за слот, есть ли документ, кто сидит.
    Слоты читаются из манифестов цехов — списков нигде не держим."""
    out = []
    root = CITY / kvartal / "цеха"
    if not root.exists():
        return out
    for ceh_dir in sorted(root.iterdir()):
        mf = ceh_dir / "manifest.json"
        if not ceh_dir.is_dir() or not mf.exists():
            continue
        m = _chitat_json(mf) or {}
        for s in m.get("слоты", []) or []:
            slot = s.get("слот")
            if not slot:
                continue
            d = chitat(ceh_dir.name, slot, kvartal)
            out.append({
                "цех": ceh_dir.name,
                "слот": slot,
                "роль": s.get("роль", ""),
                "документ": bool(d),
                "название": (d or {}).get("название", ""),
                "кто_сидит": ((d or {}).get("кто_сидит") or {}).get("имя", ""),
                "мозг": (put_slota(ceh_dir.name, slot, kvartal)
                         / "мозг.py").exists(),
            })
    return out


def kto_sidit(ceh: str, slot: str, kvartal: str = "Биржа") -> str:
    """Имя того, кто на месте. Документа нет — пустая строка, и это
    значит «спрашивай по-старому», а не «место пусто»."""
    d = chitat(ceh, slot, kvartal)
    if not d:
        return ""
    return ((d.get("кто_сидит") or {}).get("имя") or "").strip()


def est_dokument(ceh: str, slot: str, kvartal: str = "Биржа") -> bool:
    return put_dokumenta(ceh, slot, kvartal).exists()


# ─────────────────────────────────────────────────────────────
# ЖИТЕЛЬ: дом, отметка в паспорте
# ─────────────────────────────────────────────────────────────

def dom_zhitelya(imya: str):
    """Папка жителя по имени. Ищем по паспорту, не по имени папки —
    папка может называться иначе."""
    imya = (imya or "").strip()
    if not imya:
        return None
    root = CITY / "жители"
    if not root.exists():
        return None
    for p in sorted(root.glob("*/*/passport.json")):
        d = _chitat_json(p) or {}
        if (d.get("Official_Name") or p.parent.name).strip() == imya:
            return p.parent
    return None


def _zapisat_otmetku(imya: str, d: dict) -> bool:
    """Мягкая отметка в паспорт: «работаю там-то, с такого-то числа».
    Читается везде, где читают паспорт. Правды не несёт — правда в
    документе места."""
    dom = dom_zhitelya(imya)
    if dom is None:
        return False
    pp = dom / "passport.json"
    p = _chitat_json(pp)
    if p is None:
        return False
    p["Работа"] = {
        "должность": d.get("название", ""),
        "где": f"{d.get('квартал','')} · {d.get('цех','')} · {d.get('слот','')}",
        "с": _teper(),
        "_note": ("отметка о работе. Правда о найме живёт в документе "
                  "места (должность.json); эта строка — чтобы житель "
                  "знал, кто он, и вне своего квартала."),
    }
    return _pisat_json(pp, p)


def _pogasit_otmetku(imya: str) -> bool:
    dom = dom_zhitelya(imya)
    if dom is None:
        return False
    pp = dom / "passport.json"
    p = _chitat_json(pp)
    if p is None:
        return False
    if "Работа" in p:
        p.pop("Работа", None)
        return _pisat_json(pp, p)
    return True


def _dnevnik_uezzhaet(ceh: str, slot: str, imya: str,
                      kvartal: str = "Биржа") -> int:
    """Личное уезжает с жителем (слово Шефа): дневники из данных места
    переезжают к нему домой, в `опыт/`. Статистика места остаётся.
    Следующий садится за чистый стол и чужой памяти не читает."""
    dom = dom_zhitelya(imya)
    dannye = put_slota(ceh, slot, kvartal) / "данные"
    if dom is None or not dannye.exists():
        return 0
    kuda = dom / "опыт"
    kuda.mkdir(parents=True, exist_ok=True)
    n = 0
    for f in sorted(dannye.glob("diary_*.jsonl")):
        cel = kuda / f"{kvartal}_{ceh}_{slot}_{f.name}"
        i = 1
        while cel.exists():
            cel = kuda / f"{kvartal}_{ceh}_{slot}_{i}_{f.name}"
            i += 1
        try:
            f.replace(cel)
            n += 1
        except Exception:
            pass
    return n


# ─────────────────────────────────────────────────────────────
# ПРИЁМ И УВОЛЬНЕНИЕ
# ─────────────────────────────────────────────────────────────

def prinyat(ceh: str, slot: str, imya: str, kem: str = "Шеф",
            pochemu: str = "", kvartal: str = "Биржа") -> tuple:
    """Принять жителя на место. Занято другим — не вышибаем молча."""
    imya = (imya or "").strip()
    if not imya:
        return False, "не сказано, кого принимаем"
    put = put_dokumenta(ceh, slot, kvartal)
    d = _chitat_json(put)
    if d is None:
        return False, "у места нет документа — сперва заведи должность"
    if dom_zhitelya(imya) is None:
        return False, f"жителя «{imya}» в городе не нашёл"
    zanyal = ((d.get("кто_сидит") or {}).get("имя") or "").strip()
    if zanyal and zanyal != imya:
        return False, f"место занято: {zanyal} — сперва уволь"
    if zanyal == imya:
        return True, f"{imya} и так на этом месте"
    d["кто_сидит"] = {"имя": imya, "с": _teper()}
    d.setdefault("трудовая_история", []).append({
        "когда": _teper(), "что": "принят", "кто": imya,
        "кем": kem, "почему": pochemu,
    })
    if not _pisat_json(put, d):
        return False, "документ не записался"
    _zapisat_otmetku(imya, d)
    return True, f"{imya} принят на «{d.get('название','место')}»"


def uvolit(ceh: str, slot: str, kem: str = "Шеф", pochemu: str = "",
           kvartal: str = "Биржа") -> tuple:
    """Уволить того, кто на месте. Личное уезжает с ним."""
    put = put_dokumenta(ceh, slot, kvartal)
    d = _chitat_json(put)
    if d is None:
        return False, "у места нет документа"
    imya = ((d.get("кто_сидит") or {}).get("имя") or "").strip()
    if not imya:
        return True, "место и так свободно"
    d["кто_сидит"] = None
    d.setdefault("трудовая_история", []).append({
        "когда": _teper(), "что": "уволен", "кто": imya,
        "кем": kem, "почему": pochemu,
    })
    if not _pisat_json(put, d):
        return False, "документ не записался"
    _pogasit_otmetku(imya)
    n = _dnevnik_uezzhaet(ceh, slot, imya, kvartal)
    hvost = f", дневников уехало с ним: {n}" if n else ""
    return True, f"{imya} уволен, место свободно{hvost}"
