# -*- coding: utf-8 -*-
"""
pochinit_mayak.py · MARKER: MAYAK_403_V1

ЧТО СЛУЧИЛОСЬ
─────────────
Проверялка показала: ключ на месте, имя правильное, Маяк «горит», а
Tavily отвечает 403 Forbidden. Полез в код — причин две, и обе
настоящие.

ПРИЧИНА ПЕРВАЯ (главная): МАЯК ХОДИТ БЕЗ ПРОКСИ
    Весь город ходит наружу через PROXY_URL — и llm.py, и Ректор, и
    Библиотекарь, и кабинет жителя: везде `httpx.AsyncClient(...,
    proxy=PROXY_URL)`. А в Маяке — `httpx.AsyncClient(timeout=30)`,
    без прокси. Слова PROXY в файле нет вообще.

    То есть OpenRouter город зовёт из-за прокси, а Tavily — напрямую,
    со своего адреса. Отсюда и 403: провайдер просто не пускает.

ПРИЧИНА ВТОРАЯ (задел на будущее): КЛЮЧ В ТЕЛЕ ЗАПРОСА
    Ключ шлётся полем "api_key" внутри JSON — так делали раньше.
    Сейчас Tavily принимает его заголовком Authorization: Bearer.
    Старый способ местами ещё работает, но именно он и отвечает 403,
    когда перестаёт. Патч шлёт заголовком, а поле оставляет — так
    примут оба варианта, и старый, и новый.

ЧТО ПРАВИТ
──────────
`Маяк/mayak.py` — обе двери наружу (поиск и «достать страницу»):
прокси как у всего города плюс ключ заголовком. Логика поиска, поля
ответа и всё остальное не тронуты.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py pochinit_mayak.py   (или --suho)
Потом:  py proverka_mayaka.py  — она скажет, ожил ли выход.
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "MAYAK_403_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return (p / "Маяк" / "mayak.py").exists() and (p / "main.py").exists()


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


# ── 1. прокси и заголовок объявляем рядом с ключом ──
ST_KEY = '''TAVILY_KEY = os.getenv("TAVILY_KEY", "")
TAVILY_SEARCH = "https://api.tavily.com/search"
TAVILY_EXTRACT = "https://api.tavily.com/extract"'''

NOV_KEY = '''TAVILY_KEY = os.getenv("TAVILY_KEY", "")
TAVILY_SEARCH = "https://api.tavily.com/search"
TAVILY_EXTRACT = "https://api.tavily.com/extract"

# MAYAK_403_V1: маяк ходил наружу БЕЗ ПРОКСИ — один во всём городе.
# llm.py, Ректор, Библиотекарь, кабинет жителя — все зовут внешний мир
# через PROXY_URL, а маяк шёл напрямую со своего адреса. Отсюда и
# 403 Forbidden: провайдер не пускал. Читаем при каждом запросе, а не
# один раз при импорте: маяк часто поднимают до загрузки .env.
def _proxy():
    return os.getenv("PROXY_URL", "") or None


# Ключ шлём ЗАГОЛОВКОМ (нынешний способ Tavily) и оставляем в теле
# (прежний). Так примут и старый эндпоинт, и новый — а 403 из-за
# способа передачи ключа больше не случится.
def _zagolovki() -> dict:
    return {"Authorization": f"Bearer {TAVILY_KEY}",
            "Content-Type": "application/json"}'''

# ── 2. поиск ──
ST_POISK = '''        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(TAVILY_SEARCH, json={
                "api_key": TAVILY_KEY,'''
NOV_POISK = '''        async with httpx.AsyncClient(timeout=30, proxy=_proxy()) as client:
            r = await client.post(TAVILY_SEARCH, headers=_zagolovki(), json={
                "api_key": TAVILY_KEY,'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    mayak = koren / "Маяк" / "mayak.py"
    t = mayak.read_text(encoding="utf-8")

    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0

    pary = [(ST_KEY, NOV_KEY), (ST_POISK, NOV_POISK)]
    beda = [st[:40].replace("\n", " ") for st, _ in pary if t.count(st) != 1]
    if beda:
        for b in beda:
            print(f"✗ якорь не найден дословно → «{b}…»")
        return 1

    novyy = t
    for st, nov in pary:
        novyy = novyy.replace(st, nov, 1)

    # ── 3. «достать страницу» — те же два лечения, сколько бы там ни
    #     было клиентов: правим ВСЕ оставшиеся выходы наружу ──
    ostalos = novyy.count("httpx.AsyncClient(timeout=30)")
    if ostalos:
        novyy = novyy.replace(
            "httpx.AsyncClient(timeout=30)",
            "httpx.AsyncClient(timeout=30, proxy=_proxy())")
        print(f"  · и ещё {ostalos} выход(а) наружу переведены на прокси")
    if novyy.count("client.post(TAVILY_EXTRACT, json={") == 1:
        novyy = novyy.replace(
            "client.post(TAVILY_EXTRACT, json={",
            "client.post(TAVILY_EXTRACT, headers=_zagolovki(), json={", 1)
        print("  · ключ заголовком и для «достать страницу»")

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ после правки не разбирается: {e}")
        return 1

    if SUHO:
        print("· правка готова (сухой прогон)")
        return 0

    bak = mayak.with_suffix(f".py.bak_403_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(mayak, bak)
    mayak.write_text(novyy + f"\n# {MARKER} - marker\n", encoding="utf-8")
    print(f"✓ Маяк поправлен (копия: {bak.name})")

    import py_compile
    try:
        py_compile.compile(str(mayak), doraise=True)
        print("✓ компилируется")
    except Exception as e:
        print(f"✗ НЕ компилируется: {e}")
        return 1

    print("\nТеперь прогони проверялку — она скажет, ожил ли выход:")
    print("   py proverka_mayaka.py")
    print("\nЕсли 403 останется — значит дело не в дороге, а в самом")
    print("ключе: посмотри на tavily.com, жив ли он и не исчерпан ли лимит.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
