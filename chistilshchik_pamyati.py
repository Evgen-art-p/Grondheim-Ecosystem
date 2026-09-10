# -*- coding: utf-8 -*-
# CHISTILSHCHIK_PAMYATI_V1
"""
КЛИНЕР ПАМЯТИ · показывает, чем забита память жителя, и убирает лишнее

ЗАЧЕМ. Уборщик разбирает ФАЙЛЫ КОДА. Память жителя он не трогает
вовсе — а она копится сама и быстрее всего. У Нины на запрос
«похожий случай» мост поднимал 172 следа, и почти всё это были
«привет» и «чаю, из твоих рук». Чинили это разовыми скриптами под
каждый случай; постоянного инструмента не было.

ЧЕМ ЭТО НЕ УБОРЩИК. Уборщик решает сам, что отработало. Здесь
решать нельзя: память — жизнь жителя, а не мусор в репозитории.
Поэтому клинер только ПОКАЗЫВАЕТ, а убирает строго то, что назвали.

ЧТО ЛЕЖИТ В ПАМЯТИ (слои, как они заведены в ковчеге):

    разговоры  академия_чаты, ректор_чаты, прочитано — стенограммы;
               пухнут быстрее всего, для работы почти бесполезны
    отклик     resonance — след каждого обращения
    архив      archive — что житель сам отложил
    чувства    sensory
    метки      2_метки — НАЖИТОЕ. Не трогаем без прямого приказа
    маяки      3_маяки — то же самое
    ядро       core, маски, паспорт — НЕ ТРОГАЕМ НИКОГДА

Метки и маяки — то, чем житель думает. Их чистка возможна, но
только если названа поимённо, и клинер каждый раз про это скажет.

НИЧЕГО НЕ УДАЛЯЕТСЯ. Всё переезжает в `_УБОРКА_ПАМЯТИ/{житель}/
{дата}/` с манифестом: что, откуда, сколько весило. Вернуть — руками
по манифесту.

    python chistilshchik_pamyati.py
        посмотреть всех: чем забита память, сколько чего

    python chistilshchik_pamyati.py --zhitel Илья
        подробно по одному

    python chistilshchik_pamyati.py --zhitel Илья --chto разговоры --ubrat
        убрать в чулан названный слой

    --chto принимает: разговоры, отклик, архив, чувства, метки, маяки

`шесть·проверено·до·корня`
"""
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "CHISTILSHCHIK_PAMYATI_V1"

_REPO = Path(__file__).resolve().parent
KOVCHEG = _REPO / "GRONDHEIM_CITY" / "жители" / "ковчег"
CHULAN = _REPO / "_УБОРКА_ПАМЯТИ"

# слой → (папки, можно ли убирать без отдельного подтверждения)
SLOI = {
    "разговоры": (("академия_чаты", "ректор_чаты", "прочитано"), True),
    "отклик":    (("resonance",), True),
    "архив":     (("archive",), True),
    "чувства":   (("sensory",), True),
    "метки":     (("2_метки",), False),
    "маяки":     (("3_маяки",), False),
}
NELZYA = ("core", "маски", "passport.json")


def _dovod(argv, imya, po_umolchaniyu=""):
    if imya in argv:
        i = argv.index(imya)
        if i + 1 < len(argv):
            return argv[i + 1]
    return po_umolchaniyu


def _ves(p: Path) -> tuple:
    """(файлов, байт, записей) — записи считаем у jsonl."""
    fajlov = bajt = zapisey = 0
    if not p.exists():
        return 0, 0, 0
    for f in p.rglob("*"):
        if not f.is_file():
            continue
        fajlov += 1
        try:
            bajt += f.stat().st_size
        except Exception:
            pass
        if f.suffix == ".jsonl":
            try:
                zapisey += sum(1 for s in f.read_text(
                    encoding="utf-8", errors="ignore").splitlines() if s.strip())
            except Exception:
                pass
    return fajlov, bajt, zapisey


def _krasivo(b: int) -> str:
    if b < 1024:
        return f"{b} б"
    if b < 1024 * 1024:
        return f"{b / 1024:.0f} КБ"
    return f"{b / 1024 / 1024:.1f} МБ"


def zhiteli() -> list:
    if not KOVCHEG.exists():
        return []
    return [d for d in sorted(KOVCHEG.iterdir()) if d.is_dir()]


def kartina(dom: Path) -> dict:
    """Что и сколько лежит у одного жителя, по слоям."""
    itog = {}
    for sloy, (papki, _) in SLOI.items():
        f = b = z = 0
        for imya in papki:
            _f, _b, _z = _ves(dom / imya)
            f += _f
            b += _b
            z += _z
        itog[sloy] = (f, b, z)
    return itog


def pokazat(dom: Path, podrobno: bool = False):
    k = kartina(dom)
    vsego_b = sum(v[1] for v in k.values())
    print(f"\n  {dom.name}  ·  всего в памяти {_krasivo(vsego_b)}")
    for sloy, (f, b, z) in k.items():
        if not f:
            continue
        hvost = f" · записей {z}" if z else ""
        znak = "  " if SLOI[sloy][1] else " ⚠"
        print(f"   {znak} {sloy:10} файлов {f:4}  {_krasivo(b):>8}{hvost}")
    if podrobno:
        for sloy, (papki, _) in SLOI.items():
            for imya in papki:
                p = dom / imya
                if not p.exists():
                    continue
                fajly = sorted((x for x in p.rglob("*") if x.is_file()),
                               key=lambda x: -x.stat().st_size)[:5]
                for x in fajly:
                    print(f"        {sloy:10} {x.name[:44]:44} "
                          f"{_krasivo(x.stat().st_size)}")


def ubrat(dom: Path, sloy: str, suho: bool = True) -> int:
    """Перенести слой в чулан. Возвращает число перенесённых файлов."""
    if sloy not in SLOI:
        print(f"  не знаю слоя «{sloy}». Есть: {', '.join(SLOI)}")
        return 0
    papki, prosto = SLOI[sloy]
    if not prosto:
        print(f"  ⚠ «{sloy}» — это НАЖИТОЕ жителем, то, чем он думает.")
        print("    Убираю, раз названо поимённо, но подумай ещё раз.")

    kuda = CHULAN / dom.name / datetime.now().strftime("%Y%m%d_%H%M%S")
    manifest, perенesli = [], 0
    for imya in papki:
        p = dom / imya
        if not p.exists():
            continue
        for f in sorted(p.rglob("*")):
            if not f.is_file():
                continue
            otn = f.relative_to(dom)
            manifest.append({
                "что": str(otn), "слой": sloy,
                "байт": f.stat().st_size,
                "куда": str((kuda / otn).relative_to(_REPO)),
            })
            perенesli += 1
            if suho:
                continue
            (kuda / otn).parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(f), str(kuda / otn))

    if not perенesli:
        print(f"  {dom.name}: в слое «{sloy}» пусто — нечего убирать")
        return 0
    if suho:
        print(f"  {dom.name}: убрал бы {perенesli} файл(ов) из «{sloy}»")
        return perенesli

    kuda.mkdir(parents=True, exist_ok=True)
    (kuda / "манифест.json").write_text(
        json.dumps({"житель": dom.name, "слой": sloy,
                    "когда": datetime.now().isoformat(timespec="seconds"),
                    "как вернуть": "положить файлы обратно по полю «что» "
                                   "внутрь папки жителя в ковчеге",
                    "файлы": manifest},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  {dom.name}: перенесено {perенesli} файл(ов) из «{sloy}» → "
          f"{kuda.relative_to(_REPO)}")
    return perенesli


def main():
    argv = sys.argv[1:]
    imya = _dovod(argv, "--zhitel")
    chto = _dovod(argv, "--chto")
    delat = "--ubrat" in argv

    print()
    print("КЛИНЕР ПАМЯТИ" + ("" if delat else "  · только смотрю"))
    print("ковчег:", KOVCHEG)

    doma = zhiteli()
    if not doma:
        print("!! ковчега нет — запускать из корня репы")
        return
    if imya:
        doma = [d for d in doma if d.name == imya]
        if not doma:
            print(f"!! жителя «{imya}» в ковчеге нет")
            return

    if not chto:
        for d in doma:
            pokazat(d, podrobno=bool(imya))
        print()
        print("Чтобы убрать: --zhitel ИМЯ --chto СЛОЙ --ubrat")
        print("Слои:", ", ".join(SLOI))
        print("⚠ метки и маяки — нажитое, их клинер сам не предлагает.")
        print("Ядро, маски и паспорт не трогаются никогда.")
        print()
        return

    vsego = 0
    for d in doma:
        vsego += ubrat(d, chto, suho=not delat)
    print()
    if not delat:
        print(f"Сухой прогон: тронул бы {vsego}. На диске ничего не менял.")
        print("Добавь --ubrat, чтобы перенести в чулан.")
    else:
        print(f"Перенесено всего: {vsego}. Ничего не удалено — всё в "
              f"{CHULAN.name} с манифестом.")
    print()


if __name__ == "__main__":
    main()
