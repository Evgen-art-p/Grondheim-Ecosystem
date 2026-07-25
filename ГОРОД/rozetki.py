# -*- coding: utf-8 -*-
# GOROD_ROZETKI_V1 — розетки Маяка · десять универсальных гнёзд
"""
РОЗЕТКИ МАЯКА · универсальный космодром

Почему гнёзда, а не места. В паспорте Маяка стоит доступ 10 и
вместимость без края — он НИКОГО не отсекает. Значит наверху не
«кто сидит за партой», как в Академии, а «сколько лучей маяк держит
одновременно». Мест нет — есть каналы связи.

ГНЕЗДО УНИВЕРСАЛЬНО (слово Шефа). Ему всё равно, что воткнули:
    живой      — житель, пост города, сам Шеф. Пришёл искать.
    канал      — выход наружу: Tavily и кто придёт после.
    инструмент — своя железка города.
    сервис     — чужая машина снаружи.
Один разъём на всех. Маяк не спрашивает породу и не спрашивает роль —
только «чем ты сюда подключаешься».

ДЕРЖИТСЯ ПО-РАЗНОМУ (слово Шефа):
    каналы, инструменты, сервисы — ПОСТОЯННО, пока не выдернут руками.
    живые — НА СЕАНС. Ушёл, замолчал — гнездо само погасло.
Это честно: розетка не должна врать, что кто-то на связи, когда он
давно ушёл. Живой держит гнездо, пока подаёт признаки жизни.

ЧЕГО ЗДЕСЬ НЕТ. Модуль не ищет в интернете и не знает, как. Он только
ведёт разъёмы. Сам свет — в ГОРОД/mayak.py. Один глагол на файл.

    GRONDHEIM_CITY/посты/mayak/розетки.json

`шесть·проверено·до·корня`
"""
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

_HERE = Path(__file__).resolve().parent      # ГОРОД/
_REPO = _HERE.parent                          # корень репо

ROZETKI = _REPO / "GRONDHEIM_CITY" / "посты" / "mayak" / "розетки.json"

GNEZD = 10                    # столько лучей маяк держит разом
SEANS_MINUT = 20              # молчит дольше — живой считается ушедшим

# тип → держится ли постоянно
POSTOYANNYE = {"канал", "инструмент", "сервис"}
TIPY = ("живой", "канал", "инструмент", "сервис")


def _now():
    return datetime.now(timezone.utc)


def _iso(dt=None):
    return (dt or _now()).isoformat(timespec="seconds")


def _read() -> dict:
    try:
        return json.loads(ROZETKI.read_text(encoding="utf-8"))
    except Exception:
        return {"гнёзда": []}


def _write(data: dict) -> bool:
    try:
        ROZETKI.parent.mkdir(parents=True, exist_ok=True)
        ROZETKI.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                          encoding="utf-8")
        return True
    except Exception:
        return False


def _ostyl(z: dict) -> bool:
    """Погас ли сеанс живого. Постоянные не гаснут никогда."""
    if z.get("постоянно"):
        return False
    ts = z.get("активность") or z.get("с")
    if not ts:
        return True
    try:
        byl = datetime.fromisoformat(ts)
    except Exception:
        return True
    return (_now() - byl) > timedelta(minutes=SEANS_MINUT)


# ═══════════════════════════════════════════════════════════
# СМОТРЕТЬ
# ═══════════════════════════════════════════════════════════

def spisok() -> list:
    """Все десять гнёзд по порядку. Погасшие сеансы отдаются пустыми —
    розетка не врёт, что кто-то на связи, когда он ушёл.

    [{"гнездо", "занято", "тип", "имя", "что", "постоянно", "с", "давно"}]
    """
    data = _read()
    po_nomeru = {}
    for z in data.get("гнёзда", []) or []:
        try:
            n = int(z.get("гнездо", 0))
        except (TypeError, ValueError):
            continue
        if 1 <= n <= GNEZD and not _ostyl(z):
            po_nomeru[n] = z

    out = []
    for n in range(1, GNEZD + 1):
        z = po_nomeru.get(n)
        if not z:
            out.append({"гнездо": n, "занято": False, "тип": "", "имя": "",
                        "что": "", "постоянно": False, "с": "", "давно": ""})
            continue
        out.append({
            "гнездо": n,
            "занято": True,
            "тип": z.get("тип", ""),
            "имя": z.get("имя", ""),
            "что": z.get("что", ""),
            "постоянно": bool(z.get("постоянно")),
            "с": z.get("с", ""),
            "давно": z.get("активность") or z.get("с", ""),
        })
    return out


def svobodnyh() -> int:
    return sum(1 for g in spisok() if not g["занято"])


def nayti(imya: str) -> int:
    """В каком гнезде сидит. 0 — нигде."""
    for g in spisok():
        if g["занято"] and g["имя"] == imya:
            return g["гнездо"]
    return 0


def svodka() -> dict:
    """Короткая справка для экрана и отчётов."""
    gn = spisok()
    zanyato = [g for g in gn if g["занято"]]
    return {
        "всего": GNEZD,
        "занято": len(zanyato),
        "свободно": GNEZD - len(zanyato),
        "каналов": sum(1 for g in zanyato if g["тип"] == "канал"),
        "живых": sum(1 for g in zanyato if g["тип"] == "живой"),
    }


# ═══════════════════════════════════════════════════════════
# ВТЫКАТЬ И ВЫДЁРГИВАТЬ
# ═══════════════════════════════════════════════════════════

def votknut(tip: str, imya: str, chto: str = "",
            gnezdo: int = 0, postoyanno=None) -> tuple:
    """Воткнуть в розетку. Возвращает (номер гнезда или 0, сообщение).

    tip      — живой / канал / инструмент / сервис
    imya     — кто или что: «Нина», «Tavily», «библиотекарь»
    chto     — чем занят: «ищет про Эллиотта»
    gnezdo   — просить конкретное; 0 — любое свободное
    postoyanno — переопределить: по умолчанию живой на сеанс,
                 остальные закреплены

    Уже воткнут под этим именем — не плодим второй разъём, обновляем
    существующий. Свободных нет — честный отказ, чужое не вышибаем.
    """
    tip = (tip or "").strip().lower()
    imya = (imya or "").strip()
    if tip not in TIPY:
        return 0, f"не знаю такого разъёма: «{tip}»"
    if not imya:
        return 0, "без имени втыкать нечего"

    if postoyanno is None:
        postoyanno = tip in POSTOYANNYE

    data = _read()
    zhivye = [z for z in (data.get("гнёзда", []) or []) if not _ostyl(z)]

    # уже на связи — обновляем, не занимаем второе
    for z in zhivye:
        if z.get("имя") == imya and z.get("тип") == tip:
            z["активность"] = _iso()
            if chto:
                z["что"] = chto
            data["гнёзда"] = zhivye
            _write(data)
            return int(z.get("гнездо", 0)), "уже на связи — обновил"

    zanyato = {int(z.get("гнездо", 0)) for z in zhivye
               if str(z.get("гнездо", "")).isdigit()}

    if gnezdo:
        n = int(gnezdo)
        if not (1 <= n <= GNEZD):
            return 0, f"гнезда {n} не существует — их {GNEZD}"
        if n in zanyato:
            return 0, f"гнездо {n} занято — чужое не вышибаю"
    else:
        n = next((i for i in range(1, GNEZD + 1) if i not in zanyato), 0)
        if not n:
            return 0, f"все {GNEZD} гнёзд заняты — маяк держит предел"

    zhivye.append({
        "гнездо": n,
        "тип": tip,
        "имя": imya,
        "что": chto,
        "постоянно": bool(postoyanno),
        "с": _iso(),
        "активность": _iso(),
    })
    data["гнёзда"] = zhivye
    if not _write(data):
        return 0, "не записалось на диск"
    return n, ("закреплён" if postoyanno else "на связи")


def podderzhat(imya: str, chto: str = "") -> bool:
    """Живой подал признак жизни — сеанс продлевается. Без этого
    гнездо само погаснет через SEANS_MINUT."""
    data = _read()
    zhivye = [z for z in (data.get("гнёзда", []) or []) if not _ostyl(z)]
    tronuli = False
    for z in zhivye:
        if z.get("имя") == imya:
            z["активность"] = _iso()
            if chto:
                z["что"] = chto
            tronuli = True
    if tronuli:
        data["гнёзда"] = zhivye
        _write(data)
    return tronuli


def vynut(gnezdo: int = 0, imya: str = "") -> tuple:
    """Выдернуть из розетки — по номеру или по имени."""
    data = _read()
    bylo = [z for z in (data.get("гнёзда", []) or []) if not _ostyl(z)]
    stalo, snyali = [], ""
    for z in bylo:
        sovpal = ((gnezdo and int(z.get("гнездо", 0)) == int(gnezdo))
                  or (imya and z.get("имя") == imya))
        if sovpal and not snyali:
            snyali = z.get("имя", "?")
            continue
        stalo.append(z)
    if not snyali:
        return False, "в этом гнезде и так пусто"
    data["гнёзда"] = stalo
    _write(data)
    return True, f"{snyali} — отключён"


def pribrat() -> int:
    """Смести погасшие сеансы с диска. Возвращает, сколько убрал.
    Не обязательна — spisok() и так их не показывает; это уборка."""
    data = _read()
    bylo = data.get("гнёзда", []) or []
    stalo = [z for z in bylo if not _ostyl(z)]
    if len(stalo) != len(bylo):
        data["гнёзда"] = stalo
        _write(data)
    return len(bylo) - len(stalo)


# ═══════════════════════════════════════════════════════════
# ПЕРВЫЙ КАНАЛ — маяк не бывает без выхода наружу
# ═══════════════════════════════════════════════════════════

def zavesti_kanal_provaydera() -> tuple:
    """Ставит провайдера поиска в гнездо, если ключ есть и он ещё не
    воткнут. Зовётся при открытии кабинета — канал должен стоять сам,
    его не втыкают руками каждый раз.

    Ключа нет — не втыкаем: тёмный канал в розетке был бы враньём.
    """
    try:
        import mayak
    except ImportError:
        return 0, "модуля маяка нет"
    if not mayak.gorit():
        return 0, "провайдер без ключа — не втыкаю тёмный канал"
    return votknut("канал", "Tavily", "выход во внешний мир",
                   gnezdo=1, postoyanno=True)


# GOROD_ROZETKI_V1 — маркер идемпотентности
