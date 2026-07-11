# -*- coding: utf-8 -*-
"""
proverka_mostika.py
────────────────────────────────────────────────────────────────────
ПРОВЕРКА ФУНДАМЕНТА ЗАПИСИ (после patch_magic_v_masku_v1 +
patch_dvizhok_stol_chisto_vyvod_v1).

Почему этот файл вообще есть: PowerShell на машине Шефа СЪЕДАЕТ букву «Б»
при вставке («Биржа» → «иржа»), поэтому обычная проверка
`python Биржа/cartridge_registry.py` не запускается. Здесь имя файла —
чистый ASCII, а папку с реестром скрипт ищет САМ, обходя диск. Ни одной
кириллической буквы набирать не нужно.

Запуск из КОРНЯ репы (одно слово, всё ASCII):
    python proverka_mostika.py

Что проверяет:
  1. magic лёг в маски трёх трейдеров (Брут/Илья/Василий);
  2. resolve_by_magic(100002) → Илья  (обратный мостик жив);
  3. Dvizhok.nakryt_stol_chisto() читает личность Ильи БЕЗ записи;
  4. Dvizhok.dopisat_vyvod существует (саму запись НЕ делает — паспорт
     Ильи не мутируем, только смотрим, что рука на месте).

Ничего не меняет на диске. Чистое чтение.
"""
from __future__ import annotations
import io
import json
import sys
from pathlib import Path

if isinstance(sys.stdout, io.TextIOWrapper):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent
OK, BAD = "OK ", "!! "


def find_dir_with(filename: str):
    """Ищет папку с нужным файлом, не набирая кириллицу руками."""
    hits = [p.parent for p in ROOT.glob(f"*/{filename}")]
    return hits[0] if hits else None


def main() -> int:
    print("=" * 62)
    print("PROVERKA MOSTIKA — фундамент записи (magic -> носитель)")
    print("=" * 62)
    fails = 0

    # ── 1. реестр ────────────────────────────────────────────────
    birzha = find_dir_with("cartridge_registry.py")
    if birzha is None:
        print(BAD + "не нашёл cartridge_registry.py — ты в корне репы?")
        return 1
    print(OK + f"реестр найден: {birzha.name}/cartridge_registry.py")
    sys.path.insert(0, str(birzha))

    try:
        import cartridge_registry as cr
    except Exception as e:
        print(BAD + f"реестр не импортируется: {e}")
        return 1

    if not hasattr(cr, "resolve_by_magic"):
        print(BAD + "resolve_by_magic НЕТ — патч A не лёг в реестр!")
        return 1
    print(OK + "resolve_by_magic на месте")

    # ── 2. маски трёх трейдеров ──────────────────────────────────
    print("-" * 62)
    print("МАСКИ (magic рядом с Turbo_Role):")
    scan = cr._scan_zhiteli_maski()
    for z in scan:
        m = z.get("magic")
        if m is not None:
            print(f"    {z['имя']:<10} слот {z['слот']:<12} magic {m}")
    with_magic = [z for z in scan if z.get("magic") is not None]
    if len(with_magic) < 3:
        print(BAD + f"магик стоит только у {len(with_magic)} — ждал 3 "
                    "(Брут/Илья/Василий). Патч A прошёл частично?")
        fails += 1
    else:
        print(OK + f"магик у {len(with_magic)} носителей")

    # ── 3. ГЛАВНОЕ: обратный мостик ──────────────────────────────
    print("-" * 62)
    ilya = cr.resolve_by_magic(100002)
    if not ilya:
        print(BAD + "magic 100002 -> НИКТО. Мостик мёртв!")
        fails += 1
        return 1
    print(f">>> magic 100002 -> {ilya['имя']}   ({ilya.get('id','')})")
    print(OK + f"цех={ilya['цех']}  слот={ilya['слот']}")
    if ilya["имя"] != "Илья":
        print(BAD + "но это НЕ Илья — разбираемся!")
        fails += 1

    # честные None
    if cr.resolve_by_magic(999999) is None and cr.resolve_by_magic(None) is None:
        print(OK + "мусор и чужой магик -> честный None")
    else:
        print(BAD + "мостик отдаёт что-то на мусорный магик")
        fails += 1

    # ── 4. Дижок: чистое чтение личности Ильи ────────────────────
    print("-" * 62)
    zhiteli_code = find_dir_with("dvizhok.py")
    if zhiteli_code is None:
        print(BAD + "не нашёл dvizhok.py")
        return 1
    sys.path.insert(0, str(zhiteli_code))
    try:
        from dvizhok import Dvizhok
    except Exception as e:
        print(BAD + f"dvizhok не импортируется: {e}")
        return 1

    dom = Path(ilya["папка"])
    for m in ("nakryt_stol_chisto", "dopisat_vyvod"):
        if not hasattr(Dvizhok, m):
            print(BAD + f"Dvizhok.{m} НЕТ — патч B не лёг!")
            fails += 1
    if fails:
        return 1
    print(OK + "Dvizhok: nakryt_stol_chisto + dopisat_vyvod на месте")

    d = Dvizhok(dom)
    stol = d.nakryt_stol_chisto()
    print("-" * 62)
    print(f"СТОЛ ИЛЬИ (чистое чтение, без записи в память):")
    print(f"    кто_я : {stol['кто_я']}")
    print(f"    ядро  : {stol['ядро']}")
    print(f"    натура: Автономия {stol['натура'].get('Autonomy_Level')}, "
          f"Упрямство {stol['натура'].get('Stubbornness')}")
    yak = stol["якоря"] or ""
    # разделитель бывает литеральный (форма рождения) и настоящий
    parts = [x.strip() for x in yak.replace("\\n", "\n").split("\n") if x.strip()]
    print(f"    ЯКОРЯ ({len(parts)} шт — нога Опыта, сюда ляжет вывод из сделки):")
    for ln in parts:
        print(f"       - {ln}")
    if not stol["ядро"]:
        print(BAD + "ЯДРО ПУСТО — нужен patch_dvizhok_yakorya_yadro_v1")
        fails += 1
    if len(parts) < 2 and "\\n" in yak:
        print(BAD + "ЯКОРЯ СЛИПЛИСЬ — нужен patch_dvizhok_yakorya_yadro_v1")
        fails += 1

    print("=" * 62)
    if fails:
        print(f"ИТОГ: {fails} проблем(ы). Фундамент НЕ готов.")
        return 1
    print("ИТОГ: ФУНДАМЕНТ ЗАПИСИ СТОИТ.")
    print("magic -> носитель работает, рука опыта на месте.")
    print("Можно строить эталон Авана (оба конца).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
