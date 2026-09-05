# -*- coding: utf-8 -*-
# MARKER: SLOT_NE_DVAZHDY_V1
"""
МЕСТО БОЛЬШЕ НЕ ЗАВОДИТСЯ ДВАЖДЫ ПОД РАЗНЫМИ ИМЕНАМИ.

ЧТО БЫЛО СЛОМАНО
────────────────
На экране Работы у A06/A07/A08 по два места каждое: одно занято
(Илья, Нина), рядом — «свободно». Дублей быть не должно, в самом коде
об этом прямо написано.

Причина в `zavesti_mesta_kartridzhey()`. Она заводит должность на
каждый слот манифеста, и проверяет, не заведена ли уже, — ТАК:

    pid = id_dlya_slota(k["цех"], slot)      # "торговый_хаос__A06"
    if _chitat(put_posta(pid)) is not None:  # ищет ИМЕННО такую папку
        continue

Она смотрит на конкретное имя файла. А у трёх старых должностей имена
другие — они заведены ещё в августе, до того как появилось правило
именования «цех__слот»:

    torговый_хаос__A06  vs  treyder_proboy    (Илья, живая история)
    торговый_хаос__A07  vs  treyder_ranniy    (Нина, живая история)
    торговый_хаос__A08  vs  treyder_otkat

Проверка их не видит — думает, слот свободен, и заводит рядом новую
пустую должность. Ровно это случилось 28.08: все три слота получили
фантомного близнеца.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
1. Проверка теперь честная: смотрит не на имя файла, а на то, у кого
   из ВСЕХ уже заведённых должностей поля цех+слот совпадают с этим
   слотом манифеста — под каким бы именем эта должность ни лежала.
   Дальше новых дублей не появится.

2. Убирает уже возникшие: показывает, что нашёл, и спрашивает
   подтверждения. Удаляет ТОЛЬКО пустой близнец (кто_сидит: null,
   пустая трудовая история) — старую живую должность с человеком и
   историей не трогает никогда. Перед удалением кладёт копию в
   посты/_убрано_дубли/.

Идемпотентен. .bak рядом с кодом. Путь ищет сам.
"""
import json
import shutil
import sys
from pathlib import Path

MARKER = "SLOT_NE_DVAZHDY_V1"


def _nayti_koren() -> Path:
    def eto_koren(p: Path) -> bool:
        try:
            return (p / "ГОРОД" / "rabota.py").exists() \
                and (p / "GRONDHEIM_CITY" / "посты").is_dir()
        except OSError:
            return False
    zdes = Path(__file__).resolve().parent
    for kand in (zdes, Path.cwd().resolve(), *zdes.parents):
        if eto_koren(kand):
            return kand
    print("Не нашёл корень репо (нужны ГОРОД/rabota.py и "
          "GRONDHEIM_CITY/посты).")
    s = input("Перетащи сюда корень репозитория и нажми Enter:\n> ")
    p = Path(s.strip().strip('"').strip("'"))
    if eto_koren(p):
        return p
    raise SystemExit("Это не корень — нужных папок там нет.")


# ── 1. ПРАВКА ПРОВЕРКИ ────────────────────────────────────────
YAKOR = '''    zavedeno, bylo = 0, 0
    for k in kartridzhi():
        m = _chitat(Path(k["папка"]) / "manifest.json") or {} \\
            if k.get("папка") else {}
        for s in (k.get("слоты") or []):
            slot = s.get("слот")
            if not slot:
                continue
            pid = id_dlya_slota(k["цех"], slot)
            if _chitat(put_posta(pid)) is not None:
                bylo += 1
                continue
'''

NOVOE = '''    zavedeno, bylo = 0, 0

    # SLOT_NE_DVAZHDY_V1: проверка «место уже заведено?» смотрела на
    # ИМЯ ФАЙЛА (id_dlya_slota), а не на то, что реально записано в
    # должностях. Три места (треугольник Биржи) были заведены давно
    # под старыми именами — их эта проверка не видела и заводила рядом
    # пустого близнеца. Теперь смотрим по факту: цех+слот среди ВСЕХ
    # заведённых должностей, каким бы файлом они ни лежали.
    _zanyatye_slota = set()
    if POSTY.exists():
        for _d in POSTY.iterdir():
            _p = _chitat(_d / "пост.json")
            if _p and _p.get("цех") and _p.get("слот"):
                _zanyatye_slota.add((_p["цех"], _p["слот"]))

    for k in kartridzhi():
        m = _chitat(Path(k["папка"]) / "manifest.json") or {} \\
            if k.get("папка") else {}
        for s in (k.get("слоты") or []):
            slot = s.get("слот")
            if not slot:
                continue
            if (k["цех"], slot) in _zanyatye_slota:
                bylo += 1
                continue
            pid = id_dlya_slota(k["цех"], slot)
'''


def pravka_koda(koren: Path) -> None:
    p = koren / "ГОРОД" / "rabota.py"
    text = p.read_text(encoding="utf-8")
    if MARKER in text:
        print("  . rabota.py: уже накачен, пропускаю")
        return
    if text.count(YAKOR) != 1:
        raise SystemExit(
            f"  X rabota.py: якорь не найден или не один "
            f"({text.count(YAKOR)}). Код НЕ ТРОНУТ.")
    novyy = text.replace(YAKOR, NOVOE)
    novyy = novyy.rstrip() + "\n\n# " + MARKER + " - marker\n"
    import ast
    ast.parse(novyy)
    shutil.copy2(p, p.with_suffix(".py.bak_dubli"))
    p.write_text(novyy, encoding="utf-8")
    print("  + rabota.py: проверка теперь по цех+слот (.bak_dubli рядом)")


# ── 2. УБОРКА ВОЗНИКШИХ ДУБЛЕЙ ────────────────────────────────
def uborka_dubley(koren: Path) -> None:
    posty = koren / "GRONDHEIM_CITY" / "посты"
    if not posty.is_dir():
        print("  . папки посты/ нет — убирать нечего")
        return

    zapisi = []   # (papka, json)
    for d in sorted(posty.iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        f = d / "пост.json"
        if not f.exists():
            continue
        try:
            j = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        zapisi.append((d, j))

    gruppy: dict = {}
    for d, j in zapisi:
        cex, slot = j.get("цех"), j.get("слот")
        if not cex or not slot:
            continue
        gruppy.setdefault((cex, slot), []).append((d, j))

    dubli = {k: v for k, v in gruppy.items() if len(v) > 1}
    if not dubli:
        print("  . дублей по цех+слот не нашёл — чисто")
        return

    k_udaleniyu = []
    print("\n  Нашёл дубли:")
    for (cex, slot), zapisi_gr in dubli.items():
        zapisi_gr.sort(key=lambda x: x[1].get("заведён", ""))
        stariy = zapisi_gr[0]
        print(f"\n  {cex} · {slot}")
        for d, j in zapisi_gr:
            kto = (j.get("кто_сидит") or {}).get("имя")
            metka = "ОСТАВЛЯЮ (старейшая)" if (d, j) == stariy else ""
            print(f"      {d.name:<24} заведён {j.get('заведён','?'):<20} "
                  f"{'занято: ' + kto if kto else 'пусто'}  {metka}")
        for d, j in zapisi_gr[1:]:
            pusto = not j.get("кто_сидит") and not j.get("трудовая_история")
            if pusto:
                k_udaleniyu.append(d)
            else:
                print(f"      ⚠ {d.name} не пустая (есть история или "
                      f"занята) — НЕ трогаю, разбирайся сам")

    if not k_udaleniyu:
        print("\n  Удалять нечего — все дубли либо заняты, либо с "
              "историей. Смотри руками.")
        return

    print(f"\n  Удалю {len(k_udaleniyu)} пустых папок (список выше).")
    print("  Перед удалением — копия в посты/_убрано_дубли/.")
    if input("  Продолжить? [Enter=да, любое другое — отмена] ").strip():
        print("  Отменено, ничего не тронул.")
        return

    kuda = posty / "_убрано_дубли"
    kuda.mkdir(exist_ok=True)
    for d in k_udaleniyu:
        shutil.copytree(d, kuda / d.name, dirs_exist_ok=True)
        shutil.rmtree(d)
        print(f"  + убрал {d.name} (копия в _убрано_дубли/)")


def main():
    koren = _nayti_koren()
    print(f"\nРепо: {koren}\n")
    pravka_koda(koren)
    uborka_dubley(koren)
    print("\nГотово. Перезапусти город и глянь страницу Работа —")
    print("на трейдерских местах дублей быть не должно.")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        print(e)
    except Exception:
        import traceback
        traceback.print_exc()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно ")
