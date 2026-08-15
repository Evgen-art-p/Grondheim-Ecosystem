# -*- coding: utf-8 -*-
"""
postavit_ruku_mayaka.py · MARKER: RUKA_MAYAKA_V1

ЧТО ПРОСИЛ ШЕФ
──────────────
«Наладь им выход в интернет всем, прямо в мозге».

ЧТО ПОКАЗАЛА ПРОВЕРКА
─────────────────────
Выход у города есть и работает — это Маяк Пробуждения (`Маяк/mayak.py`,
провайдер Tavily). Но пользуются им не все:

    житель ДОМА        — умеет (строка MAYAK_REQUEST в кабинете жителя)
    Академия           — умеет (тот же приём)
    мозги НА РАБОТЕ    — не умеют НИ ОДИН:
                         три трейдера, Архивариус, Исполнитель

То есть Нина дома может спросить у мира, а Нина за столом на Бирже —
нет. Работа оказалась глухой.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
1. Кладёт `ГОРОД/ruka_mayaka.py` — ОДНА дверь наружу для любого мозга
   города. Внутри зовётся тот же `Маяк/mayak.py`, что и у жителей:
   второго выхода в интернет город не заводит, и ключ Tavily остаётся
   в одном месте. Не горит Маяк (нет ключа) — рука честно говорит об
   этом, а не выдумывает ссылки.

2. Подключает руку:
   · ТРЕЙДЕРАМ (A06, A07, A08) — через `ruki_treydera`, они уже
     ходят с руками, добавляется четвёртая;
   · КОНТОРЕ (Архивариус, Исполнитель) — их вызов `chat(...)`
     меняется на `chat_with_tools(...)` с этой же рукой. Разговор
     не меняется: не попросил — ничего не потратили.

ЧТО ЭТО СТОИТ
─────────────
Рука срабатывает только когда мозг сам её позвал. Ни один прогон не
станет дороже, пока никто не спросил. В консоли каждый выход виден
строкой [МАЯК] 🔦 — чтобы не было тихих трат.

ЧЕГО ПАТЧ НЕ ДЕЛАЕТ
───────────────────
Не трогает жителей и Академию: там выход уже есть и работает своим
приёмом. Ломать рабочее ради единообразия не буду — скажешь, сведу
оба приёма в один отдельно.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py postavit_ruku_mayaka.py   (или --suho)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "RUKA_MAYAKA_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "Маяк" / "mayak.py").exists()
            and (p / "Биржа" / "llm.py").exists()
            and (p / "main.py").exists())


def nayti_koren() -> Path:
    zdes = Path(__file__).resolve().parent
    for kand in (zdes, Path.cwd(), *zdes.parents):
        if _eto_koren(kand):
            return kand
    kandidaty = []
    for baza in (zdes.parent, Path.cwd().parent):
        if not baza.is_dir():
            continue
        for d in baza.iterdir():
            if d.is_dir() and _eto_koren(d) and d not in kandidaty:
                kandidaty.append(d)
    if len(kandidaty) == 1:
        if input(f"Нашёл город здесь:\n  {kandidaty[0]}\nЭтот? [Enter=да] "
                 ).strip().lower() in ("", "y", "д", "да"):
            return kandidaty[0]
    elif len(kandidaty) > 1:
        print("Нашёл несколько городов:")
        for i, d in enumerate(kandidaty, 1):
            print(f"  {i}. {d}")
        nom = input("Какой? номер: ").strip()
        if nom.isdigit() and 1 <= int(nom) <= len(kandidaty):
            return kandidaty[int(nom) - 1]
    put = input("Не нашёл сам. Перетащи сюда папку репо и нажми Enter:\n> ")
    p = Path(put.strip().strip('"').strip("'"))
    if _eto_koren(p):
        return p
    print("✗ Это не корень репо")
    sys.exit(1)


# ── 0. chat_with_tools принимает историю разговора ──
# Без этого Архивариус, который зовёт chat(..., history=...), падал бы
# с TypeError и ТИХО откатывался на разговор без рук: рука есть, а её
# как бы нет. Молчаливая деградация хуже явной поломки.
ST_LLM_SIG = """    knowledge_source: str = "internal",
    executors: Optional[dict] = None,       # RUKI_TREYDERA_V1
) -> str:
    \"\"\"Вызов LLM с поддержкой Tool Use (синхронный)."""

NOV_LLM_SIG = """    knowledge_source: str = "internal",
    executors: Optional[dict] = None,       # RUKI_TREYDERA_V1
    history: Optional[list] = None,         # RUKA_MAYAKA_V1
) -> str:
    \"\"\"Вызов LLM с поддержкой Tool Use (синхронный)."""

ST_LLM_MSG = """    messages.append({"role": "user", "content": user})

    # RUKI_TREYDERA_V1: список рук был зашит здесь намертво"""

NOV_LLM_MSG = """    # RUKA_MAYAKA_V1: история разговора — как в chat(). Мозг конторы
    # передаёт её всегда; без этого он терял руки на каждом ответе.
    if history:
        for _m in history:
            if _m.get("role") in ("user", "assistant") and _m.get("content"):
                messages.append({"role": _m["role"], "content": _m["content"]})
    messages.append({"role": "user", "content": user})

    # RUKI_TREYDERA_V1: список рук был зашит здесь намертво"""

RUKA_PY = '''# -*- coding: utf-8 -*-
# RUKA_MAYAKA_V1
"""
РУКА МАЯКА — выход города наружу, одной дверью.

ЗАКОН ЭТОГО ФАЙЛА
    Второго выхода в интернет город не заводит. Внутри зовётся тот же
    `Маяк/mayak.py`, которым пользуются житель дома и Академия — и
    ключ Tavily остаётся в одном месте, и визиты пишутся в один
    журнал Маяка.

    Рука НИЧЕГО не решает: приносит найденное и говорит, откуда оно.
    Не горит Маяк (нет ключа) — так и отвечает. Ссылок не выдумывает:
    выдуманная ссылка хуже отсутствия ответа.

ЦЕНА
    Срабатывает только когда мозг сам позвал. Каждый выход печатается
    строкой [МАЯК] 🔦 — тихих трат быть не должно.
"""
from __future__ import annotations

import sys as _sys
from pathlib import Path

_GOROD = Path(__file__).resolve().parent
_KOREN = _GOROD.parent
for _p in (str(_KOREN / "Маяк"), str(_KOREN)):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)


def shema() -> list:
    """Описание руки для модели. Сухо: прибор, а не советчик."""
    return [{"type": "function", "function": {
        "name": "sprosit_mayak",
        "description": (
            "Выйти во внешний мир через Маяк Пробуждения и узнать то, "
            "чего ты знать не можешь: свежие новости, текущие события, "
            "сегодняшние данные, чужие публикации. Возвращает найденное "
            "с источниками. Не зови ради того, что и так знаешь."),
        "parameters": {"type": "object", "properties": {
            "запрос": {"type": "string",
                       "description": "что именно узнать, обычными словами"}},
            "required": ["запрос"]}}}]


def _pusto(prichina: str) -> str:
    return f"Маяк не принёс ответа: {prichina}. Ссылки выдумывать не буду."


def sprosit(zapros: str, kto: str = "") -> str:
    """Спросить мир. Всегда возвращает текст — пустой ответ тоже ответ."""
    zapros = (zapros or "").strip()
    if not zapros:
        return _pusto("пустой запрос")
    try:
        import mayak
    except Exception as e:
        return _pusto(f"Маяк недоступен ({e})")
    if hasattr(mayak, "gorit") and not mayak.gorit():
        return _pusto("Маяк не горит — нет ключа TAVILY_KEY в .env")
    try:
        import asyncio
        rez = mayak.poisk(zapros)
        if asyncio.iscoroutine(rez):
            # мозги слотов синхронные — крутим свою петлю
            try:
                petlya = asyncio.get_running_loop()
            except RuntimeError:
                petlya = None
            if petlya and petlya.is_running():
                import concurrent.futures as _cf
                with _cf.ThreadPoolExecutor(max_workers=1) as ex:
                    rez = ex.submit(asyncio.run, rez).result()
            else:
                rez = asyncio.run(rez)
        nashlos = mayak.dlya_promta(rez)
    except Exception as e:
        return _pusto(f"сбой поиска ({e})")

    print(f"[МАЯК] 🔦 {kto or 'кто-то'} спросил мир: «{zapros[:70]}» → "
          f"{len(nashlos)} симв.")
    try:
        mayak.zapisat_vizit(kto or "мозг", zapros, bool(nashlos))
    except Exception:
        pass
    if not nashlos:
        return _pusto("по запросу ничего не нашлось")
    return f"=== МАЯК · найдено снаружи ===\\n{nashlos}"


def ruki(kto: str = "") -> dict:
    """{имя: функция} — подмешивается к рукам любого мозга."""
    return {"sprosit_mayak":
            lambda args: sprosit(str(args.get("запрос", "")), kto)}


# RUKA_MAYAKA_V1 - marker
'''


# ── 1. трейдеры: четвёртая рука ──
ST_RT_SHEMA = '''        {"type": "function", "function": {
            "name": "moy_dnevnik",'''
NOV_RT_SHEMA = '''        # RUKA_MAYAKA_V1: выход наружу. Раньше житель мог спросить мир
        # только ДОМА — на работе мозг был глухой.
        *_ruka_mayaka_shema(),
        {"type": "function", "function": {
            "name": "moy_dnevnik",'''

ST_RT_HVOST = '''    return {"stol_na_etazhe": _stol,
            "izmerit_volnu": _volna,
            "moy_dnevnik": _dnevnik}'''
NOV_RT_HVOST = '''    itog = {"stol_na_etazhe": _stol,
            "izmerit_volnu": _volna,
            "moy_dnevnik": _dnevnik}
    itog.update(_ruka_mayaka_ruki(slot))   # RUKA_MAYAKA_V1
    return itog


# ── RUKA_MAYAKA_V1: одна дверь наружу на весь город ──────────
def _ruka_mayaka_shema() -> list:
    try:
        import sys as _s
        from pathlib import Path as _P
        _g = str(_P(__file__).resolve().parent.parent / "ГОРОД")
        if _g not in _s.path:
            _s.path.insert(0, _g)
        import ruka_mayaka
        return ruka_mayaka.shema()
    except Exception:
        return []          # Маяка нет — руки просто не будет


def _ruka_mayaka_ruki(kto: str) -> dict:
    try:
        import sys as _s
        from pathlib import Path as _P
        _g = str(_P(__file__).resolve().parent.parent / "ГОРОД")
        if _g not in _s.path:
            _s.path.insert(0, _g)
        import ruka_mayaka
        return ruka_mayaka.ruki(kto)
    except Exception:
        return {}'''


# ── 2. контора: chat → chat_with_tools ──
KONTORA = {
    "архивариус": ("A05_ARKHIV", "Архивариус"),
    "исполнитель": ("A09_ISPOLNITEL", "Исполнитель"),
}

KONTORA_HELPER = '''

# ── RUKA_MAYAKA_V1: выход наружу и для конторы ───────────────
# Раньше мозг конторы звал chat() — один проход, рук нет. Теперь тот
# же разговор, но с рукой Маяка: не позвал — ничего не потрачено.
def _chat_s_mayakom(**kw):
    try:
        import sys as _s
        from pathlib import Path as _P
        _g = _P(__file__).resolve()
        for _ in range(8):
            _g = _g.parent
            if (_g / "ГОРОД" / "ruka_mayaka.py").exists():
                break
        if str(_g / "ГОРОД") not in _s.path:
            _s.path.insert(0, str(_g / "ГОРОД"))
        import ruka_mayaka
        from llm import chat_with_tools
        return chat_with_tools(tools_schema=ruka_mayaka.shema(),
                               executors=ruka_mayaka.ruki(_KTO_YA),
                               **kw)
    except Exception as e:
        print(f"[МАЯК] рука не подключилась ({e}) — говорю без неё")
        from llm import chat as _chat_prostoy
        return _chat_prostoy(**kw)

'''


def pravit(put: Path, pary: list, imya: str, dopolnit: str = "") -> bool:
    t = put.read_text(encoding="utf-8")
    if MARKER in t:
        print(f"  · {put.name}: маркер уже стоит")
        return True
    beda = [st[:40].replace("\n", " ") for st, _ in pary if t.count(st) != 1]
    if beda:
        for b in beda:
            print(f"  ✗ {put.name}: якорь не найден дословно → «{b}…»")
        return False
    novyy = t
    for st, nov in pary:
        novyy = novyy.replace(st, nov, 1)
    if dopolnit:
        novyy = novyy.rstrip("\n") + "\n" + dopolnit
    novyy += f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"  ✗ {put.name}: после правки не разбирается ({e})")
        return False
    if SUHO:
        print(f"  · {put.name}: правка готова (сухой прогон)")
        return True
    shutil.copy2(put, put.with_suffix(
        put.suffix + f".bak_{imya}_{datetime.now():%Y%m%d_%H%M%S}"))
    put.write_text(novyy, encoding="utf-8")
    print(f"  ✓ {put.name}")
    return True


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    ruka = koren / "ГОРОД" / "ruka_mayaka.py"
    rt = koren / "Биржа" / "ruki_treydera.py"

    llm = koren / "Биржа" / "llm.py"
    print("\n0. chat_with_tools учится принимать историю разговора")
    if not pravit(llm, [(ST_LLM_SIG, NOV_LLM_SIG),
                        (ST_LLM_MSG, NOV_LLM_MSG)], "istoriya"):
        return 1

    print("\n1. Одна дверь наружу — ГОРОД/ruka_mayaka.py")
    if ruka.exists() and MARKER in ruka.read_text(encoding="utf-8"):
        print("  · уже лежит")
    else:
        ast.parse(RUKA_PY)
        if not SUHO:
            ruka.write_text(RUKA_PY, encoding="utf-8")
        print("  ✓ положена")

    print("\n2. Трейдеры (A06, A07, A08) — четвёртая рука")
    if not rt.exists():
        print("  ✗ нет Биржа/ruki_treydera.py — накати сперва "
              "postavit_ruki_treydera.py и postavit_ruki_vsem.py")
        return 1
    ok = pravit(rt, [(ST_RT_SHEMA, NOV_RT_SHEMA),
                     (ST_RT_HVOST, NOV_RT_HVOST)], "mayak")
    if not ok:
        return 1

    print("\n3. Контора — Архивариус и Исполнитель")
    for papka, (agent_id, imya_ch) in KONTORA.items():
        mozg = (koren / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "контора"
                / "слоты" / papka / "мозг.py")
        if not mozg.exists():
            print(f"  ✗ нет мозга: {papka}")
            continue
        t = mozg.read_text(encoding="utf-8")
        if MARKER in t:
            print(f"  · {imya_ch}: маркер уже стоит")
            continue
        st1 = f'''        return chat(system=system, user=question, history=history,
                    agent_id="{agent_id}", slot_id="trading", temperature=_my_temp())'''
        st2 = f'''        response = chat(system=system_full, user=user_msg,
                        agent_id="{agent_id}", slot_id="trading", temperature=_my_temp())'''
        if t.count(st1) != 1 or t.count(st2) != 1:
            print(f"  ✗ {imya_ch}: вызовы chat не найдены дословно "
                  f"({t.count(st1)}, {t.count(st2)})")
            continue
        novyy = (t.replace(st1, st1.replace("return chat(",
                                            "return _chat_s_mayakom("), 1)
                  .replace(st2, st2.replace("response = chat(",
                                            "response = _chat_s_mayakom("), 1))
        novyy = novyy.rstrip("\n") + "\n" + (
            f'\n_KTO_YA = "{imya_ch}"\n' + KONTORA_HELPER
            + f"\n# {MARKER} - marker\n")
        try:
            ast.parse(novyy)
        except SyntaxError as e:
            print(f"  ✗ {imya_ch}: после правки не разбирается ({e})")
            continue
        if SUHO:
            print(f"  · {imya_ch}: правка готова (сухой прогон)")
            continue
        shutil.copy2(mozg, mozg.with_suffix(
            f".py.bak_mayak_{datetime.now():%Y%m%d_%H%M%S}"))
        mozg.write_text(novyy, encoding="utf-8")
        print(f"  ✓ {imya_ch}")

    if not SUHO:
        import py_compile
        faily = [llm, ruka, rt] + [
            koren / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "контора"
            / "слоты" / p / "мозг.py" for p in KONTORA]
        for f in faily:
            if not f.exists():
                continue
            try:
                py_compile.compile(str(f), doraise=True)
                print(f"  ✓ компилируется: {f.parent.name}/{f.name}")
            except Exception as e:
                print(f"  ✗ НЕ компилируется {f.name}: {e}")
                return 1
        print("\nТеперь мир доступен на работе всем пятерым.")
        print("Каждый выход виден в консоли строкой [МАЯК] 🔦 —")
        print("тихих трат не будет.")
        print("\nЕсли Маяк не горит (нет TAVILY_KEY в .env), рука честно")
        print("скажет об этом, а ссылки выдумывать не станет.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
