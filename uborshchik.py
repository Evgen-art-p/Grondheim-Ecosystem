#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# UBORSHCHIK_V1
"""
УБОРЩИК — отделяет работающее от отработавшего. Ничего не удаляет.

    python uborshchik.py --suho     посмотреть, что нашёл (по умолчанию)
    python uborshchik.py --ubrat    перенести найденное в чулан

    python uborshchik.py --ubrat --kopii        только копии .bak/.snesen
    python uborshchik.py --ubrat --patchi       только отработавшие патчи
    python uborshchik.py --ubrat --odnorazovye  только разовые инструменты
    python uborshchik.py --ubrat --otsluzhivshie только заменённое

Запускать из КОРНЯ репо.

ЗАКОН ЭТОГО СКРИПТА

    Не удаляет. Переносит в `_УБОРКА/{дата}/`, сохраняя дорожки, и
    кладёт рядом манифест: что, откуда, какого размера и ПОЧЕМУ. Любой
    файл возвращается на место одной строкой из манифеста.

    По умолчанию — сухой прогон. Убирает только по прямому `--ubrat`.

    Работающее не трогает вообще: движки, кабинеты, мозги, знания,
    паспорта, документы города, данные. Список неприкасаемых — ниже, и
    он проверяется до всякого переноса.

КАК ОН РЕШАЕТ, ЧТО ОТРАБОТАЛО

    ПАТЧИ — по маркеру. Каждый патч, накатываясь, оставляет в целевом
    файле свою метку. Уборщик читает метку из самого патча и ищет её по
    репо. Нашлась — патч сделал дело, его место в чулане. НЕ нашлась —
    патч ещё не накатан, и уборщик его НЕ ТРОГАЕТ, а говорит об этом.
    Правило работает и для будущих патчей, ничего дописывать не надо.

    КОПИИ — по имени: `*.bak*` и `*.snesen`. Это следы патчей, а не
    работа. Оригиналы на месте, история в git.

    РАЗОВЫЕ ИНСТРУМЕНТЫ и ЗАМЕНЁННОЕ — поимённо, с причиной у каждого.
    Наугад тут нельзя, поэтому список короткий и проверяемый.

ЧТО ОН ПОКАЗЫВАЕТ, НО НЕ ТРОГАЕТ

    «Под вопросом» — файлы, которых никто не зовёт: ни импортом, ни по
    имени. Это ПОДОЗРЕНИЕ, а не приговор: скрипт могли запускать руками
    или он ждёт своего часа. Решает Шеф, уборщик только показывает.
"""
import argparse
import ast
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

KOREN = Path(__file__).resolve().parent
CHULAN = KOREN / "_УБОРКА"
YA = Path(__file__).name

# ── куда не заходим вовсе ─────────────────────────────────────
NE_ZAHODIT = {"_ARCHIVE", "_OLD", "_АРХИВ_ЧИСТКИ", "_УБОРКА",
              ".git", ".vscode", "__pycache__", "node_modules"}

# ── папки, которые грузятся ЦЕЛИКОМ, по имени папки ───────────
# `истоки/` — плагины крана: istoki.py обходит папку и подхватывает
# каждый файл сам. Их никто не импортирует по имени, и это НОРМАЛЬНО:
# так задумано. Без этой оговорки уборщик записал бы их в мёртвые.
PLAGINY = ("истоки",)

# ── что не трогаем ни при каких условиях ──────────────────────
# Точки входа и живые двери города. Их «никто не импортирует» — это
# нормально: их запускает Шеф руками, а не код.
NEPRIKASAEMYE = {
    "main.py", "tik.py", "uborshchik.py",
    "rabota_pult.py", "stol_pokazat.py", "sostoyanie.py",
    "istoki_pokazat.py", "pokazat_metki.py", "proverit_atlas.py",
    "proverka_kotirovok.py", "proverka_stola.py", "proverka_zreniya.py",
    "ochistit_atlas.py", "ochistit_pozicii.py", "otchet.py",
    "arkhivirovat_bak.py", "run_tester.py", "nastroit_birzhu.py",
    "perenesti_faily_birzhi.py", "pochinit_sostav.py",
    "kalibrovka_core.py", "kniga_v_rudu.py", "bibliotekar.py",
}

# ── разовые инструменты: сделали дело, лежат мёртвым весом ────
RAZOVYE = {
    "count_triggers.py": "разовый счётчик срабатываний под старую Искру",
    "konec_volny_C.py": "разовый разбор волны C, инспекция, не движок",
    "schetchik_vasya.py": "разовый счётчик по Васе",
    "schetchik_vasya2.py": "разовый счётчик по Васе, второй заход",
    "schetchik_vasya3.py": "разовый счётчик по Васе, третий заход",
    "proverka_vasya_wave.py": "разовая проверка волны Васи",
    "test_iskra_diagnostika.py": "диагностика Искры — Искра упразднена 06.08",
    "test_iskra_ekstremum.py": "диагностика Искры — Искра упразднена 06.08",
    "test_fractal_trigger.py": "разовая проверка фрактального триггера",
    "zigzag_chart.py": "разовая рисовалка зигзага, в работе не участвует",
    "razvedka_slepka.py": "разовая разведка слепка стола",
    "voronka_bdb.py": "разовая воронка БДБ",
}

# ── заменённое: работу делает кто-то другой ───────────────────
OTSLUZHIVSHIE = {
    "vakansiya_treydera.py":
        "заменён стандартом работы: места заводятся в /rabota и rabota_pult.py",
    "udalit_otslujivshie.py":
        "разовый удалятель двух файлов от 21.07 — оба уже удалены",
}


def _vnutri_arhiva(p: Path) -> bool:
    return any(part in NE_ZAHODIT for part in p.parts)


def _vse_faily():
    for p in KOREN.rglob("*"):
        if p.is_file() and not _vnutri_arhiva(p.relative_to(KOREN)):
            yield p


def _tekstovye():
    """Файлы, в которых имеет смысл искать маркеры и упоминания."""
    for p in _vse_faily():
        if p.suffix.lower() in (".py", ".md", ".json", ".txt"):
            try:
                yield p, p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue


# ══════════════════════════════════════════════════════════════
# СБОР
# ══════════════════════════════════════════════════════════════

def sobrat_kopii() -> list:
    """Следы патчей: *.bak* и *.snesen. Оригиналы на месте."""
    out = []
    for p in _vse_faily():
        n = p.name
        if ".bak" in n or n.endswith(".snesen"):
            out.append((p, "копия, оставленная патчем (оригинал на месте)"))
    return out


def sobrat_patchi(teksty: dict) -> tuple:
    """Патчи, чей маркер уже стоит в репо, — значит отработали.

    Возвращает (отработавшие, ещё_не_накатанные)."""
    gotovye, zhdut = [], []
    for p in sorted(KOREN.glob("*.py")):
        if not p.name.startswith(("patch_", "postavit_")):
            continue
        if p.name in NEPRIKASAEMYE:
            continue
        try:
            src = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        m = re.search(r'^MARKER\s*=\s*[\'"](.+?)[\'"]', src, re.M)
        if not m:
            zhdut.append((p, "не нашёл маркера внутри патча — не берусь судить"))
            continue
        marker = m.group(1)
        gde = [q.name for q, t in teksty.items() if marker in t and q != p]
        if gde:
            gotovye.append((p, f"накатан — метка {marker.strip('# ')[:28]} "
                               f"стоит в {', '.join(sorted(set(gde))[:3])}"))
        else:
            zhdut.append((p, "маркера в репо нет — патч ещё НЕ накатан"))
    return gotovye, zhdut


def sobrat_poimenno(spisok: dict) -> list:
    out = []
    for p in _vse_faily():
        if p.name in spisok and p.name not in NEPRIKASAEMYE:
            out.append((p, spisok[p.name]))
    return out


def sobrat_pod_voprosom(teksty: dict) -> list:
    """Модули, которых никто не зовёт. ПОКАЗЫВАЕМ, не трогаем."""
    py = [p for p in _vse_faily() if p.suffix == ".py"]
    importy = set()
    for p in py:
        try:
            tree = ast.parse(teksty.get(p, ""))
        except Exception:
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                for a in n.names:
                    importy.add(a.name.split(".")[0])
            elif isinstance(n, ast.ImportFrom) and n.module:
                importy.add(n.module.split(".")[0])
    vsyo = "\n".join(teksty.values())
    out = []
    for p in py:
        if p.name in NEPRIKASAEMYE or p.name == YA:
            continue
        if p.name.startswith(("patch_", "postavit_")):
            continue
        if p.name in RAZOVYE or p.name in OTSLUZHIVSHIE:
            continue
        if p.stem in importy:
            continue
        if any(part in PLAGINY for part in p.relative_to(KOREN).parts):
            continue          # плагин: грузится по папке, не по имени
        if vsyo.count(p.name) > 1:      # упоминается где-то по имени
            continue
        out.append(p)
    return out


# ══════════════════════════════════════════════════════════════
# ПЕРЕНОС
# ══════════════════════════════════════════════════════════════

def perenesti(nahodki: list, ubrat: bool) -> dict:
    if not nahodki:
        return {}
    kuda = CHULAN / datetime.now().strftime("%Y%m%d_%H%M%S")
    manifest = []
    for p, prichina in nahodki:
        otn = p.relative_to(KOREN)
        zapis = {"откуда": str(otn), "размер": p.stat().st_size,
                 "почему": prichina}
        if ubrat:
            cel = kuda / otn
            cel.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(p), str(cel))
            zapis["куда"] = str(cel.relative_to(KOREN))
        manifest.append(zapis)
    if ubrat:
        (kuda / "манифест.json").write_text(
            json.dumps({"когда": datetime.now().isoformat(timespec="seconds"),
                        "всего": len(manifest), "файлы": manifest},
                       ensure_ascii=False, indent=2), encoding="utf-8")
        (kuda / "КАК_ВЕРНУТЬ.txt").write_text(
            "Ничего не удалено — всё лежит здесь, дорожки сохранены.\n"
            "Вернуть один файл: скопировать его отсюда обратно по пути\n"
            "из поля «откуда» в манифест.json.\n"
            "Вернуть всё: скопировать содержимое этой папки в корень репо\n"
            "с сохранением дорожек (манифест и эту записку не копировать).\n",
            encoding="utf-8")
    return {"папка": kuda, "манифест": manifest}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ubrat", action="store_true",
                    help="реально перенести (без него — только показ)")
    ap.add_argument("--suho", action="store_true", help="только показать")
    ap.add_argument("--kopii", action="store_true")
    ap.add_argument("--patchi", action="store_true")
    ap.add_argument("--odnorazovye", action="store_true")
    ap.add_argument("--otsluzhivshie", action="store_true")
    a = ap.parse_args()

    if not (KOREN / "GRONDHEIM_CITY").exists():
        print("x не вижу GRONDHEIM_CITY — запускай из КОРНЯ репо")
        return 1

    vybrany = any([a.kopii, a.patchi, a.odnorazovye, a.otsluzhivshie])
    hochu = {
        "копии": a.kopii or not vybrany,
        "патчи": a.patchi or not vybrany,
        "разовые": a.odnorazovye or not vybrany,
        "заменённое": a.otsluzhivshie or not vybrany,
    }
    ubrat = a.ubrat and not a.suho

    print("=" * 66)
    print("УБОРЩИК" + ("" if ubrat else "   [СУХОЙ ПРОГОН — ничего не трогаю]"))
    print("=" * 66)

    teksty = dict(_tekstovye())
    gotovye, zhdut = sobrat_patchi(teksty)

    gruppy = []
    if hochu["копии"]:
        gruppy.append(("КОПИИ, ОСТАВЛЕННЫЕ ПАТЧАМИ", sobrat_kopii()))
    if hochu["патчи"]:
        gruppy.append(("ПАТЧИ, КОТОРЫЕ УЖЕ ОТРАБОТАЛИ", gotovye))
    if hochu["разовые"]:
        gruppy.append(("РАЗОВЫЕ ИНСТРУМЕНТЫ", sobrat_poimenno(RAZOVYE)))
    if hochu["заменённое"]:
        gruppy.append(("ЗАМЕНЁННОЕ ДРУГИМ", sobrat_poimenno(OTSLUZHIVSHIE)))

    nahodki = []
    for imya, spisok in gruppy:
        print(f"\n── {imya} — {len(spisok)} ──")
        for p, prichina in sorted(spisok, key=lambda x: str(x[0])):
            print(f"   {p.relative_to(KOREN)}")
            print(f"      · {prichina}")
        nahodki += spisok

    if zhdut:
        print(f"\n── ПАТЧИ, КОТОРЫЕ НЕ ТРОГАЮ — {len(zhdut)} ──")
        for p, prichina in zhdut:
            print(f"   {p.name}\n      · {prichina}")

    pod_voprosom = sobrat_pod_voprosom(teksty)
    if pod_voprosom:
        print(f"\n── ПОД ВОПРОСОМ (показываю, НЕ трогаю) — "
              f"{len(pod_voprosom)} ──")
        print("   Их никто не зовёт ни импортом, ни по имени. Это подозрение,")
        print("   а не приговор: реши сам, нужны они или нет.")
        print("   (плагины из папок вроде истоки/ сюда НЕ попадают — они")
        print("    грузятся по папке, и это задумано)")
        for p in sorted(pod_voprosom, key=str):
            print(f"   {p.relative_to(KOREN)}")

    print("\n" + "-" * 66)
    if not nahodki:
        print("Убирать нечего — чисто.")
        return 0

    itog = sum(p.stat().st_size for p, _ in nahodki) / 1024
    print(f"Всего к уборке: {len(nahodki)} файлов, {itog:.0f} КБ")

    if not ubrat:
        print("\nЭто был показ. Убрать по-настоящему:")
        print("    python uborshchik.py --ubrat")
        print("Ничего не удаляется — всё переедет в _УБОРКА/ с манифестом.")
        return 0

    res = perenesti(nahodki, True)
    print(f"\n+ перенесено в {res['папка'].relative_to(KOREN)}")
    print("  рядом лежат манифест.json и КАК_ВЕРНУТЬ.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
