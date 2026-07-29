# -*- coding: utf-8 -*-
"""
PATCH_PRICHAL_V1 — причал Маяка: приём пульса от других городов

ЗАМЫСЕЛ. Первый рейс через границу — ПУЛЬС (решение Шефа 29.07):
остров говорит «я жив» и пару чисел. Самый дешёвый груз, который
проверяет самое дорогое — что провод вообще есть.

ПОЧЕМУ СНАЧАЛА ПРИЧАЛ, А НЕ ОСТРОВ. Причал можно довести до зелёного
БЕЗ острова — послать себе фальшивый пульс и увидеть, что он лёг на
полку. Если строить остров первым, стучаться некуда и проверять
нечем. Сначала розетка, потом вилка.

ОДИН ФАЙЛ НА ОБЕ СТОРОНЫ (Закон Двух Стандартов: на границе общий
язык). `Маяк/prichal.py` умеет и принимать, и отправлять, и не тянет
за собой город — только stdlib и httpx. Остров копирует этот же файл
к себе и зовёт `otpravit()`. Формат один, потому что код один — двух
правд о формате быть не может физически. Тот же приём, что
`story_package.json` + `STANDARD.md v3.0` в Живой Книге, где один
контракт заменил собой два разошедшихся документа.

КУДА ЛОЖИТСЯ. На полки, заведённые 26.07 «на будущее» и до сих пор
пустые: `Маяк/города/{id}/` или `Маяк/острова/{id}/` — отправитель
сам говорит в пульсе, кто он. Формат карточки — ровно тот, что уже
читает `khranitel_mayaka._skan_polki()` (имя, адрес, последний_пульс).
Ничего нового под это не заводим: Хранитель Маяка увидит новый мир
сам, без правки его кода.

БЕЗОПАСНОСТЬ, ЧЕСТНО. Ручка `POST /api/pulse` открыта всем, кто
достучится. Пока город крутится на localhost — это никого не
касается. Прежде чем выставлять наружу, положи в .env:
    GRONDHEIM_PULSE_KEY=<любая длинная строка>
Задан ключ — причал требует его в заголовке `X-Grondheim-Key` и
молча отвергает чужих. Не задан — пускает всех (удобно для
локальной проверки, ОПАСНО в интернете). Причал не притворяется,
что защищён, когда не защищён.

ЧТО ДЕЛАЕТ ПАТЧ:
  1. Создаёт `Маяк/prichal.py` — контракт, приём, отправка, проверка.
  2. Регистрирует ручку `POST /api/pulse` в `main.py` (NiceGUI стоит
     на FastAPI, `app` — то же приложение, отдельный сервер не нужен).

ПОСЛЕ ПАТЧА — ПРОВЕРКА БЕЗ ОСТРОВА (песочница до зелёного):
    терминал 1:  python main.py
    терминал 2:  python Маяк/prichal.py --проверить
  Должно: «✓ пульс принят», и на полке `Маяк/острова/` появится
  карточка тестового острова. Потом её можно просто удалить.
  Заодно спроси Хранителя Маяка в кабинете — он должен увидеть новый
  мир на связи, хотя его код не менялся.

Запуск из корня репозитория:
    python patch_prichal.py

Идемпотентно, бэкап .bak.
`шесть·проверено·до·корня`
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
MAYAK_DIR = REPO / "Маяк"
PRICHAL_PATH = MAYAK_DIR / "prichal.py"
MAIN_PATH = REPO / "main.py"

MARKER_MAIN = "PRICHAL_V1"


def _stop(msg: str) -> None:
    print(f"⛔ ОСТАНОВКА: {msg}")
    print("Ничего не записано на диск.")
    sys.exit(1)


def _apply_one(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n == 0:
        _stop(f"[{label}] якорь не найден — код изменился, нужна ручная сверка.")
    if n > 1:
        _stop(f"[{label}] якорь встретился {n} раз — должен быть один.")
    return text.replace(old, new, 1)


# ═══════════════════════════════════════════════════════════
# ФАЙЛ — Маяк/prichal.py
# ═══════════════════════════════════════════════════════════

PRICHAL_CODE = '''# -*- coding: utf-8 -*-
# PRICHAL_V1 — причал Маяка: граница между городами
"""
ПРИЧАЛ · один контракт на обе стороны границы

Этот файл знает ФОРМАТ ПУЛЬСА — и умеет его принять, и умеет его
отправить. Обе стороны берут ОДИН И ТОТ ЖЕ файл, поэтому двух правд
о формате быть не может физически: разойтись нечему.

    материк:  prinyat(dannye)   — кладёт карточку на полку Маяка
    остров:   otpravit(...)     — шлёт пульс на материк
    оба:      SHEMA, proverit_pulse() — что считается правильным пульсом

САМОДОСТАТОЧЕН НАРОЧНО. Не импортирует ни город, ни rezidenty, ни
mayak — только stdlib и httpx. Остров живёт в другом репозитории, у
него нет ни ковчега, ни гнёзд; он копирует этот файл к себе и зовёт
otpravit(). Всё, что нужно для границы, лежит здесь.

ЧТО ТАКОЕ ПУЛЬС (решение Шефа 29.07 — первый рейс). Не сделка, не
вывод, не личность. Только: я жив, вот кто я, вот пара чисел. Самый
дешёвый груз, каким проверяют, что провод есть.

ЧЕСТНО ПРО ГРАНИЦУ:
  • пульс НЕ несёт личность. Житель границу не пересекает — это
    прямое решение (Живая Книга возит biography_snapshot, снимок, а
    не самих агентов).
  • пульс НЕ доказывает, что остров говорит правду о своих числах.
    Он доказывает только, что остров жив и на связи.
  • нет ключа в .env — причал пускает всех. Это удобно локально и
    опасно в интернете, и причал об этом честно говорит, а не
    притворяется защищённым.

`шесть·проверено·до·корня`
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent      # Маяк/ (на материке)

GORODA_DIR = _HERE / "города"
OSTROVA_DIR = _HERE / "острова"

# Общий секрет. Пусто — причал открыт всем (локально это нормально).
PULSE_KEY = os.getenv("GRONDHEIM_PULSE_KEY", "")
KEY_HEADER = "X-Grondheim-Key"

RODY = ("город", "остров")


# ═══════════════════════════════════════════════════════════
# СХЕМА — что считается правильным пульсом
# ═══════════════════════════════════════════════════════════

SHEMA = {
    "id":     "строка, обязательно — короткое имя папки (латиница/цифры/-_)",
    "имя":    "строка, обязательно — как звать этот мир по-человечески",
    "род":    f"строка, обязательно — одно из {RODY}",
    "адрес":  "строка, необязательно — где его искать (URL)",
    "числа":  "объект, необязательно — что мир хочет сказать о себе",
    "версия": "строка, необязательно — версия шасси, чтобы видеть расхождение",
}


def _chistyy_id(raw: str) -> str:
    """ID станет именем ПАПКИ — пускаем только безопасное. Это не
    придирка: без чистки чужой мир мог бы попросить записать себя
    куда угодно на диске («../../»), и причал послушно записал бы."""
    razresheno = set("abcdefghijklmnopqrstuvwxyz"
                     "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
    s = "".join(c for c in str(raw or "") if c in razresheno)
    return s[:48]


def proverit_pulse(d: dict) -> tuple:
    """Проверка пульса. Возвращает (ок: bool, причина: str, чистый: dict).
    Кривой пульс не записываем — молча испорченная полка хуже отказа."""
    if not isinstance(d, dict):
        return False, "пульс не объект", {}
    pid = _chistyy_id(d.get("id", ""))
    if not pid:
        return False, "пустой или недопустимый id", {}
    imya = str(d.get("имя", "") or pid).strip()[:80]
    rod = str(d.get("род", "") or "").strip().lower()
    if rod not in RODY:
        return False, f"род должен быть одним из {RODY}, пришло «{rod}»", {}
    chisla = d.get("числа") or {}
    if not isinstance(chisla, dict):
        chisla = {}
    return True, "", {
        "id": pid,
        "имя": imya,
        "род": rod,
        "адрес": str(d.get("адрес", "") or "")[:200],
        "числа": chisla,
        "версия": str(d.get("версия", "") or "")[:40],
    }


def _polka(rod: str) -> Path:
    return OSTROVA_DIR if rod == "остров" else GORODA_DIR


# ═══════════════════════════════════════════════════════════
# СТОРОНА МАТЕРИКА — принять
# ═══════════════════════════════════════════════════════════

def prinyat(dannye: dict, klyuch: str = "") -> dict:
    """Принимает пульс и кладёт карточку на полку Маяка.

    Возвращает {"ok": bool, "причина": str, "id": str}.
    Карточка — ровно тот формат, что уже читает Хранитель Маяка
    (khranitel_mayaka._skan_polki): имя, адрес, последний_пульс.
    Плюс рядом журнал `пульсы.jsonl` — история, append-only, чтобы
    видеть не только последний удар, но и ритм.
    """
    if PULSE_KEY and klyuch != PULSE_KEY:
        return {"ok": False, "причина": "ключ не подошёл", "id": ""}

    ok, prichina, p = proverit_pulse(dannye)
    if not ok:
        return {"ok": False, "причина": prichina, "id": ""}

    teper = datetime.now(timezone.utc).isoformat(timespec="seconds")
    dom = _polka(p["род"]) / p["id"]
    try:
        dom.mkdir(parents=True, exist_ok=True)
        kartochka_path = dom / "город.json"
        # первое знакомство помним отдельно — когда этот мир появился
        staroe = {}
        if kartochka_path.exists():
            try:
                staroe = json.loads(kartochka_path.read_text(encoding="utf-8"))
            except Exception:
                staroe = {}
        kartochka = {
            "id": p["id"],
            "имя": p["имя"],
            "род": p["род"],
            "адрес": p["адрес"],
            "версия": p["версия"],
            "числа": p["числа"],
            "первый_пульс": staroe.get("первый_пульс") or teper,
            "последний_пульс": teper,
            "пульсов": int(staroe.get("пульсов", 0)) + 1,
        }
        kartochka_path.write_text(
            json.dumps(kartochka, ensure_ascii=False, indent=2),
            encoding="utf-8")
        with (dom / "пульсы.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"когда": teper, "числа": p["числа"],
                                "версия": p["версия"]},
                               ensure_ascii=False) + "\\n")
    except Exception as e:
        return {"ok": False, "причина": f"не записалось: {e}", "id": p["id"]}

    return {"ok": True, "причина": "", "id": p["id"]}


def kto_na_svyazi(molchit_chasov: float = 24.0) -> list:
    """Все миры с полок + давно ли молчат. Для отчётов и Хранителя.
    Возвращает [{"id","имя","род","часов_молчит","живой"}]."""
    out = []
    teper = datetime.now(timezone.utc)
    for polka, rod in ((GORODA_DIR, "город"), (OSTROVA_DIR, "остров")):
        if not polka.exists():
            continue
        for d in sorted(polka.iterdir()):
            if not d.is_dir():
                continue
            try:
                k = json.loads((d / "город.json").read_text(encoding="utf-8"))
            except Exception:
                continue
            chasov = None
            try:
                t = datetime.fromisoformat(str(k.get("последний_пульс", "")))
                if t.tzinfo is None:
                    t = t.replace(tzinfo=timezone.utc)
                chasov = round((teper - t).total_seconds() / 3600.0, 1)
            except Exception:
                pass
            out.append({
                "id": k.get("id", d.name),
                "имя": k.get("имя", d.name),
                "род": k.get("род", rod),
                "часов_молчит": chasov,
                "живой": (chasov is not None and chasov <= molchit_chasov),
                "пульсов": k.get("пульсов", 0),
            })
    return out


# ═══════════════════════════════════════════════════════════
# СТОРОНА ОСТРОВА — отправить
# ═══════════════════════════════════════════════════════════

async def otpravit(kuda: str, id: str, imya: str, rod: str = "остров",
                   chisla: dict = None, versia: str = "",
                   adres: str = "", klyuch: str = "",
                   timeout: float = 15.0) -> dict:
    """Шлёт пульс на материк. Зовётся С ОСТРОВА, из его собственного
    тика — материк никого не опрашивает (иначе он молчаливо становится
    начальником, и сеть равных не вырастет; решение 29.07).

    kuda — базовый адрес материка, напр. "http://localhost:8080"
    Возвращает {"ok": bool, "причина": str}.

    Обрыв связи — НЕ ошибка острова. Остров живёт дальше (Автономный
    Форт из Живой Книги: связь для обмена, не для жизни). Вызывающий
    просто пишет неудачу себе в журнал и работает как работал.
    """
    import httpx
    telo = {"id": id, "имя": imya, "род": rod,
            "числа": chisla or {}, "версия": versia, "адрес": adres}
    zagolovki = {"Content-Type": "application/json"}
    kl = klyuch or PULSE_KEY
    if kl:
        zagolovki[KEY_HEADER] = kl
    url = kuda.rstrip("/") + "/api/pulse"
    try:
        async with httpx.AsyncClient(timeout=timeout) as c:
            r = await c.post(url, json=telo, headers=zagolovki)
            if r.status_code != 200:
                return {"ok": False,
                        "причина": f"материк ответил {r.status_code}: {r.text[:200]}"}
            return r.json()
    except Exception as e:
        return {"ok": False, "причина": f"материк не отозвался: {e}"}


# ═══════════════════════════════════════════════════════════
# ПРОВЕРКА — песочница до зелёного, без острова
# ═══════════════════════════════════════════════════════════

async def _samoproverka(kuda: str = "http://localhost:8080"):
    """Шлёт фальшивый пульс самому себе. Нужен, чтобы довести причал
    до зелёного ДО того, как остров вообще появится."""
    print(f"── проверка причала · стучусь в {kuda}")
    rez = await otpravit(
        kuda=kuda,
        id="test-ostrov",
        imya="Тестовый остров (проверка причала)",
        rod="остров",
        chisla={"сделок": 0, "это": "проверка, не настоящий мир"},
        versia="проверка",
    )
    if rez.get("ok"):
        print(f"✓ пульс принят, id={rez.get('id','')}")
        print(f"  смотри полку: Маяк/острова/test-ostrov/")
        print(f"  спроси Хранителя Маяка — он должен увидеть новый мир")
        print(f"  карточку потом просто удали, она тестовая")
    else:
        print(f"✗ не принят: {rez.get('причина','')}")
        print("  город запущен? (python main.py) причал встроен в main.py?")
    return rez


if __name__ == "__main__":
    import sys as _s
    if "--проверить" in _s.argv or "--check" in _s.argv:
        import asyncio
        _kuda = "http://localhost:8080"
        for _i, _a in enumerate(_s.argv):
            if _a in ("--куда", "--to") and _i + 1 < len(_s.argv):
                _kuda = _s.argv[_i + 1]
        asyncio.run(_samoproverka(_kuda))
    else:
        print(__doc__)
        print("\\nЧто на связи прямо сейчас:")
        for m in kto_na_svyazi():
            _s_ = "жив" if m["живой"] else "молчит"
            print(f"  · {m['имя']} ({m['род']}) — {_s_}, "
                  f"пульсов {m['пульсов']}")
        print("\\nПроверить причал:  python Маяк/prichal.py --проверить")


# PRICHAL_V1 — маркер идемпотентности
'''


# ═══════════════════════════════════════════════════════════
# ПРАВКА — main.py
# ═══════════════════════════════════════════════════════════

OLD_MAIN = '''# ── МАЯК ПРОБУЖДЕНИЯ — выход города наружу ── MAYAK_KABINET_V2
# Общегородской. Гнёзда всеядны: житель, пост, канал, инструмент.
from ui_mayak import page_mayak

@ui.page("/mayak")
def _mayak():
    page_mayak()'''

NEW_MAIN = '''# ── МАЯК ПРОБУЖДЕНИЯ — выход города наружу ── MAYAK_KABINET_V2
# Общегородской. Гнёзда всеядны: житель, пост, канал, инструмент.
from ui_mayak import page_mayak

@ui.page("/mayak")
def _mayak():
    page_mayak()


# ── ПРИЧАЛ — граница между городами ── PRICHAL_V1
# Первый рейс через границу: ПУЛЬС (я жив + пара чисел). Ручка, не
# страница — стучится сюда машина, не человек. Отдельный сервер не
# нужен: NiceGUI стоит на FastAPI, `app` — то же приложение.
# Стучится ОСТРОВ САМ, по своему тику; материк никого не опрашивает —
# иначе он молча становится начальником, и сеть равных не вырастет.
from fastapi import Request as _PrichalRequest
import prichal as _prichal

@app.post("/api/pulse")
async def _priyom_pulsa(request: _PrichalRequest):
    """Приём пульса от другого города или острова.

    Ключ проверяется, только если GRONDHEIM_PULSE_KEY задан в .env.
    Не задан — причал открыт всем: локально это нормально, в
    интернете опасно, и он об этом честно говорит, а не притворяется
    защищённым.
    """
    try:
        telo = await request.json()
    except Exception:
        return {"ok": False, "причина": "тело не разобралось как JSON", "id": ""}
    return _prichal.prinyat(telo, request.headers.get(_prichal.KEY_HEADER, ""))'''


def main() -> None:
    print("── PATCH_PRICHAL_V1 ──")

    if not MAYAK_DIR.exists():
        _stop(f"{MAYAK_DIR} не найдена.")
    if not MAIN_PATH.exists():
        _stop(f"{MAIN_PATH} не найден.")

    main_text = MAIN_PATH.read_text(encoding="utf-8")
    est_prichal = PRICHAL_PATH.exists()
    est_ruchka = MARKER_MAIN in main_text

    if est_prichal and est_ruchka:
        print("✓ причал и ручка уже на месте — патч уже применён.")
        _podskazka()
        return
    if est_prichal != est_ruchka:
        print(f"⚠ половинчато: причал={'есть' if est_prichal else 'нет'}, "
              f"ручка={'есть' if est_ruchka else 'нет'} — доложу недостающее.")

    new_main = main_text
    if not est_ruchka:
        new_main = _apply_one(new_main, OLD_MAIN, NEW_MAIN,
                              "main.py: ручка причала")
        print("✓ якорь main.py найден и применён в памяти")

    if not est_prichal:
        PRICHAL_PATH.write_text(PRICHAL_CODE, encoding="utf-8")
        print(f"✓ создан причал: {PRICHAL_PATH}")

    if not est_ruchka:
        bak = MAIN_PATH.with_suffix(".py.bak_prichal")
        if not bak.exists():
            bak.write_text(main_text, encoding="utf-8")
        MAIN_PATH.write_text(new_main, encoding="utf-8")
        print(f"✓ бэкап: {bak.name}")
        print(f"✓ ручка встроена: {MAIN_PATH}")

    # полки должны быть на месте — они заведены 26.07, но не будем надеяться
    for d in (MAYAK_DIR / "города", MAYAK_DIR / "острова"):
        d.mkdir(parents=True, exist_ok=True)

    _podskazka()


def _podskazka() -> None:
    print()
    print("ПРОВЕРКА БЕЗ ОСТРОВА — песочница до зелёного:")
    print("  терминал 1:  python main.py")
    print("  терминал 2:  python Маяк/prichal.py --проверить")
    print("Должно: «✓ пульс принят» и карточка в Маяк/острова/test-ostrov/")
    print("Потом спроси Хранителя Маяка в кабинете — он увидит новый мир,")
    print("хотя его код не менялся. Тестовую карточку удали руками.")
    print()
    print("ПЕРЕД ВЫХОДОМ В ИНТЕРНЕТ: положи в .env")
    print("  GRONDHEIM_PULSE_KEY=<длинная строка>")
    print("Без ключа причал пускает всех — локально нормально, снаружи нет.")
    print("шесть·проверено·до·корня")


if __name__ == "__main__":
    main()
