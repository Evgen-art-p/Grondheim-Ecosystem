# -*- coding: utf-8 -*-
# GOROD_REZIDENTY_V1 — городской менеджер резидентов
"""
ГОРОДСКИЕ РЕЗИДЕНТЫ · реестр постов

Что это. В городе есть ПОСТЫ — рабочие места, которые существуют
независимо от того, кто их занимает. Библиотекарь Академии. Хронист.
Архиватор. Пост стоит, даже когда он пуст.

ГЛАВНЫЙ ЗАКОН ЭТОГО ФАЙЛА (слово Шефа):
    ЛИЧНОСТЬ НЕ ПРИКРУЧЕНА К РОЛИ.
Пост не знает, кто в нём сидит. Житель не знает, что он «библиотекарь
навсегда». Связь живёт ОТДЕЛЬНО — в файле поста, и меняется в один
приём. Посади другого — движок тот же, голос другой.

    ПОСТ (роль)      — что делают на этом месте. Файл движка.
    ЖИТЕЛЬ (личность) — кто именно там сидит. Паспорт в ковчеге.
    СВЯЗЬ            — {пост}.json, одна строка. Меняется свободно.

И РОД (порода) здесь НЕ проверяется нигде. Рабочее место не
привязано к роду — это прямой закон Шефа. Кто угодно может занять
любой пост, если Брат его туда посадил.

Что НЕ делает: не запускает движки, не думает за них, не держит
списка постов в коде. Посты сканируются с диска (Закон Картриджа) —
завёл папку, пост появился сам.

    GRONDHEIM_CITY/посты/{id}/
        пост.json       ← что за пост: название, где, какой движок
        хранитель.json  ← кто сейчас сидит (нет файла = вакансия)

`шесть·проверено·до·корня`
"""
import json
from pathlib import Path
from datetime import datetime, timezone

_HERE = Path(__file__).resolve().parent      # ГОРОД/
_REPO = _HERE.parent                          # корень репо

POSTY_DIR = _REPO / "GRONDHEIM_CITY" / "посты"
KOVCHEG = _REPO / "GRONDHEIM_CITY" / "жители" / "ковчег"


# ═══════════════════════════════════════════════════════════
# ДИСК — читаем честно, пустое отдаём пустым
# ═══════════════════════════════════════════════════════════

def _read_json(p: Path, default=None):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(p: Path, data) -> bool:
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                    encoding="utf-8")
        return True
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════
# ПОСТЫ — сканируем, не держим списком
# ═══════════════════════════════════════════════════════════

def list_posty() -> list:
    """Все посты города. Сканируем папку — новый пост появляется сам,
    без правки этого файла (Закон Картриджа).

    Возвращает [{"id", "название", "где", "движок", "житель", "занят"}].
    Постов нет — пустой список, это честное состояние молодого города.
    """
    out = []
    if not POSTY_DIR.exists():
        return out
    for d in sorted(POSTY_DIR.iterdir()):
        if not d.is_dir():
            continue
        m = _read_json(d / "пост.json", {}) or {}
        hr = _read_json(d / "хранитель.json", {}) or {}
        zhitel = hr.get("житель", "") or ""
        out.append({
            "id": d.name,
            "название": m.get("название", d.name),
            "где": m.get("где", ""),
            "движок": m.get("движок", ""),
            "житель": zhitel,
            "занят": bool(zhitel),
        })
    return out


def get_post(post_id: str) -> dict:
    """Один пост по id. Нет такого — пустой словарь, не выдумываем."""
    for p in list_posty():
        if p["id"] == post_id:
            return p
    return {}


def zavesti_post(post_id: str, nazvanie: str, gde: str = "",
                 dvizhok: str = "") -> tuple:
    """Заводит пост на диске. Уже есть — не трогаем (идемпотентно).

    dvizhok — имя модуля, который умеет работать на этом посту
    (например "bibliotekar"). Пусто — пост есть, работы пока нет.
    Возвращает (успех: bool, сообщение: str).
    """
    d = POSTY_DIR / post_id
    mf = d / "пост.json"
    if mf.exists():
        return True, "пост уже заведён"
    ok = _write_json(mf, {
        "id": post_id,
        "название": nazvanie,
        "где": gde,
        "движок": dvizhok,
        "заведён": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })
    return (True, "пост заведён") if ok else (False, "не записался на диск")


# ═══════════════════════════════════════════════════════════
# СВЯЗЬ ПОСТ ↔ ЖИТЕЛЬ — отдельно от обоих
# ═══════════════════════════════════════════════════════════

def posadit(post_id: str, imya_zhitelya: str, zid: str = "") -> tuple:
    """Сажает жителя на пост. Род НЕ проверяется — закон Шефа.
    Пост занят другим — честно сменяем, но возвращаем, кто был,
    чтобы вызывающий мог сказать это вслух (не тайком).

    Возвращает (успех: bool, сообщение: str).
    """
    d = POSTY_DIR / post_id
    if not (d / "пост.json").exists():
        return False, f"поста «{post_id}» нет — сначала заведи"
    byl = (_read_json(d / "хранитель.json", {}) or {}).get("житель", "")
    ok = _write_json(d / "хранитель.json", {
        "житель": imya_zhitelya,
        "id": zid,
        "с": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })
    if not ok:
        return False, "не записался на диск"
    if byl and byl != imya_zhitelya:
        return True, f"сменил(а) на посту: {byl}"
    return True, "на посту"


def snyat(post_id: str) -> tuple:
    """Освобождает пост. Пост остаётся, вакансия открыта."""
    f = POSTY_DIR / post_id / "хранитель.json"
    if not f.exists():
        return True, "пост и так свободен"
    try:
        f.unlink()
        return True, "пост освобождён"
    except Exception as e:
        return False, str(e)


def kto_na_postu(post_id: str) -> str:
    """Имя того, кто сейчас на посту. Пусто — вакансия."""
    return (_read_json(POSTY_DIR / post_id / "хранитель.json", {})
            or {}).get("житель", "") or ""


def dom_zhitelya(imya: str) -> Path | None:
    """Дом жителя по имени. Нет — None. Нужен, чтобы движок поста
    поднял ЛИЧНОСТЬ того, кто сидит: паспорт, натуру, память."""
    if not imya:
        return None
    d = KOVCHEG / imya
    return d if (d / "passport.json").exists() else None


def lichnost_na_postu(post_id: str) -> tuple:
    """Личность того, кто на посту: (паспорт: dict, дом: Path) или
    (None, None), если пост пуст или дом не найден.

    ЭТО И ЕСТЬ РАЗВЯЗКА личности и роли: движок поста зовёт эту
    функцию и получает ЧЕЛОВЕКА. Кто это — движку всё равно, он
    одинаково работает с любым.
    """
    imya = kto_na_postu(post_id)
    dom = dom_zhitelya(imya)
    if dom is None:
        return None, None
    return _read_json(dom / "passport.json", {}), dom


# ═══════════════════════════════════════════════════════════
# ДУША — общий сбор личности, один способ на весь город
# ═══════════════════════════════════════════════════════════

def sobrat_dushu(p: dict) -> str:
    """Личность жителя словами — для системного промпта.
    Тот же набор полей, что кабинет жителя показывает Шефу
    (один способ на город). Пустые поля пропускаем.

    ВАЖНО: здесь НЕТ ни слова о работе, посте или роли. Это чистая
    личность. Роль приклеивает движок поста — своим текстом, сверху.
    """
    if not p:
        return ""
    imya = p.get("Official_Name", "житель")
    s = (f"Ты — {imya}, житель Грондхейма. Говоришь от первого лица, "
         f"живым голосом, не как ассистент.\n")
    for polе, podpis in (
        ("Core_Phrase",      "Твоё ядро (коронная фраза)"),
        ("Hidden_History",   "Твоя скрытая история"),
        ("Sensory_Response", "Как ты чувствуешь мир"),
        ("Anchor_Points",    "Твои незыблемые якоря"),
        ("Hidden_Taste",     "Твой скрытый вкус"),
        ("Pull_Vector",      "Тебя тянет к"),
        ("домашний_промпт",  "Твой дом, который ты носишь в себе всегда"),
    ):
        v = p.get(polе)
        if v:
            s += f"{podpis}: {v}\n"
    dna = p.get("DNA_Static", {}) or {}
    if isinstance(dna, dict) and dna:
        s += ("Твоя натура (черты характера): "
              + " · ".join(f"{k.split('_')[0]} {v}" for k, v in dna.items())
              + "\n")
    try:
        z = float(p.get("_charge", 0.0) or 0.0)
        s += (f"Сейчас твоё внутреннее состояние: {z:+.2f} "
              f"(от -1 до 1). Не называй это числом — просто веди себя в тон.\n")
    except (TypeError, ValueError):
        pass
    return s


# GOROD_REZIDENTY_V1 — маркер идемпотентности
