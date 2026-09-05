# -*- coding: utf-8 -*-
# KONTORA_NE_KARTRIDZH_V1
"""
ПАТЧ · Контора — не картридж.

ЗАЧЕМ
    Контора одна на всю студию и не вынимается никогда. Цеха сменные:
    вставил, вынул, размножил. Лежать в одной папке они не должны —
    иначе различие стирается, и однажды контору выдернут вместе с
    картриджем (в ui_ceha.py кнопка «вынуть» двигает папку целиком).

ЧТО ДЕЛАЕТ
    1. GRONDHEIM_CITY/Студия/цеха/контора/  →  GRONDHEIM_CITY/Студия/контора/
       Переносом, со всем содержимым. Полка Студия/цеха/ остаётся пустой
       и ждёт первый картридж.

    2. ГОРОД/rabota.py :: kartridzhi() — учим смотреть в двух местах:
           квартал/контора/            постоянная служба
           квартал/цеха/*/             сменные картриджи
       и ставить в каждой записи "вид": "контора" | "цех".

       Вид определяем ПО ИМЕНИ ПАПКИ, не по месту. Поэтому контора Биржи,
       пока лежит в цеха/, всё равно помечается конторой — и когда её
       потом перенесут, ничего не шелохнётся.

ЧЕГО НЕ ДЕЛАЕТ
    Биржу не трогает вообще: ни папок, ни ui_ceha.py. Её контора остаётся
    где лежала, поведение не меняется — только появляется метка «вид».

ИДЕМПОТЕНТНОСТЬ
    Второй запуск: перенос уже сделан — молчим. В rabota.py стоит маркер
    KONTORA_NE_KARTRIDZH_V1 — не патчим повторно. Перед правкой .bak.

    Корень ищем по стабильным ориентирам, что были до всех патчей:
    GRONDHEIM_CITY/локации и ГОРОД/rabota.py.

    шесть·проверено·до·корня
"""
from __future__ import annotations

import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "KONTORA_NE_KARTRIDZH_V1"

# ─────────────────────────────────────────────────────────────
# Точный блок, который меняем в rabota.py
# ─────────────────────────────────────────────────────────────

STARYY = '''    out = []
    if not CITY.exists():
        return out
    for kv in sorted(CITY.iterdir()):
        ceha = kv / "цеха"
        if not ceha.is_dir():
            continue
        for cd in sorted(ceha.iterdir()):
            mf = cd / "manifest.json"
            if not mf.exists():
                continue
            m = _chitat(mf) or {}
            out.append({"цех": cd.name, "папка_квартала": kv.name,
                        "здание": m.get("здание", ""),
                        "квартал": m.get("квартал", ""),
                        "слоты": m.get("слоты", []) or []})
    return out'''

NOVYY = '''    # KONTORA_NE_KARTRIDZH_V1: два рода, не один. Контора квартала —
    # постоянная служба, лежит отдельной папкой и не вынимается. Цеха —
    # сменные картриджи на полке «цеха». Вид ставим ПО ИМЕНИ ПАПКИ, а не
    # по месту: контора, лежащая по старому адресу, тоже зовётся конторой,
    # и перенос её однажды ничего не сломает.
    out = []
    if not CITY.exists():
        return out
    for kv in sorted(CITY.iterdir()):
        if not kv.is_dir():
            continue
        papki = []
        kontora = kv / "контора"
        if (kontora / "manifest.json").exists():
            papki.append(kontora)
        ceha = kv / "цеха"
        if ceha.is_dir():
            papki += [c for c in sorted(ceha.iterdir())
                      if (c / "manifest.json").exists()]
        for cd in papki:
            m = _chitat(cd / "manifest.json") or {}
            out.append({"цех": cd.name, "папка_квартала": kv.name,
                        "вид": "контора" if cd.name == "контора" else "цех",
                        "здание": m.get("здание", ""),
                        "квартал": m.get("квартал", ""),
                        "слоты": m.get("слоты", []) or []})
    return out'''


def _teper() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def naiti_koren() -> Path:
    starty = [Path(__file__).resolve().parent, Path.cwd().resolve()]
    for start in starty:
        for kand in [start, *start.parents]:
            if (kand / "GRONDHEIM_CITY" / "локации").is_dir() \
                    and (kand / "ГОРОД" / "rabota.py").is_file():
                return kand
    raise SystemExit(
        "Не нашёл корень репо.\n"
        "Ищу папку, где рядом GRONDHEIM_CITY/локации и ГОРОД/rabota.py.\n"
        "Запусти патч из корня Grondheim-Ecosystem."
    )


def perenesti_kontoru(koren: Path) -> str:
    studiya = koren / "GRONDHEIM_CITY" / "Студия"
    bylo = studiya / "цеха" / "контора"
    stalo = studiya / "контора"

    if stalo.exists() and not bylo.exists():
        return "уже на месте, не трогал"
    if stalo.exists() and bylo.exists():
        return (f"ОБЕ есть — не трогаю. Разберись руками: {bylo} и {stalo}")
    if not bylo.exists():
        (studiya / "цеха").mkdir(parents=True, exist_ok=True)
        return "нечего переносить (конторы Студии нет)"

    stalo.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(bylo), str(stalo))
    (studiya / "цеха").mkdir(parents=True, exist_ok=True)
    return "перенесена: Студия/цеха/контора → Студия/контора"


def patchit_skaner(koren: Path) -> str:
    put = koren / "ГОРОД" / "rabota.py"
    tekst = put.read_text(encoding="utf-8")

    if MARKER in tekst:
        return "уже пропатчен, не трогал"
    if STARYY not in tekst:
        return ("НЕ НАШЁЛ блок kartridzhi() в ожидаемом виде — "
                "файл уже кто-то правил. Ничего не менял, разбираемся.")

    bak = put.with_suffix(f".py.bak_{_teper()}")
    shutil.copyfile(put, bak)
    put.write_text(tekst.replace(STARYY, NOVYY, 1), encoding="utf-8")
    return f"пропатчен, старый в {bak.name}"


def proverit(koren: Path) -> None:
    import importlib.util

    try:
        spec = importlib.util.spec_from_file_location(
            "_rabota_probe", koren / "ГОРОД" / "rabota.py")
        if spec is None or spec.loader is None:
            print("  · сканер не завёлся"); return
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        vse = mod.kartridzhi()
    except Exception as e:
        print(f"  · сканер споткнулся: {e}")
        print("    ОТКАТ: верни rabota.py из .bak рядом")
        return

    for k in sorted(vse, key=lambda x: (x["папка_квартала"], x["цех"])):
        vid = k.get("вид", "?")
        sloty = ", ".join(s.get("слот", "?") for s in k.get("слоты", []))
        print(f"  · {k['папка_квартала']:<10} {vid:<8} {k['цех']:<16} "
              f"места: {sloty or '—'}")

    try:
        mesta = mod.mesta()
        nashi = [m for m in mesta if m.get("цех") == "контора"]
        print(f"  · вакансий по конторам: {len(nashi)}")
        for m in nashi:
            print(f"      {m['id']} · {m['название']} · "
                  f"{m.get('кто_сидит') or 'вакантно'}")
    except Exception as e:
        print(f"  · mesta() споткнулась: {e}")


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except Exception:
        pass

    koren = naiti_koren()
    print(f"Корень: {koren}\n")
    print(f"Контора Студии: {perenesti_kontoru(koren)}")
    print(f"Сканер города:  {patchit_skaner(koren)}")
    print("\nСпрашиваю город:")
    proverit(koren)
    print("\nГотово. Биржа не тронута — её контора где лежала, там и лежит,\n"
          "просто теперь город знает, что она контора.\n"
          "шесть·проверено·до·корня")


if __name__ == "__main__":
    main()
