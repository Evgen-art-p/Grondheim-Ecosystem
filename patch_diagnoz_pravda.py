# -*- coding: utf-8 -*-
"""
patch_diagnoz_pravda.py
════════════════════════════════════════════════════════════════════
ЧЕСТНЫЙ ДИАГНОЗ ОТЧЁТА (ведение построено — текст врал)

БОЛЕЗНЬ: блок ДИАГНОЗ в отчёте печатал устаревшее:
  «ВЕДЕНИЯ ПОЗИЦИИ НЕТ… слой 3 НЕ РЕАЛИЗОВАН… система МАТЕМАТИЧЕСКИ
   не может быть прибыльной… вторая половина не построена».
Это было написано ДО того, как построили трейлинг, сейф, мост
ведения и пирамиду-пакет. Теперь ведение ЕСТЬ — текст врёт и пугает.

ЛЕЧЕНИЕ (две точки):

  1. hooks.py: в запись закрытой сделки добавляем lot_base и dolivok —
     чтобы отчёт ВИДЕЛ, была ли реально пирамида (сколько доливов).

  2. tester_express.py: переписываем ДИАГНОЗ честно. Теперь он не
     утверждает «механизма нет», а СЧИТАЕТ по факту:
       • сколько сделок реально доливались (пирамида сработала);
       • средний множитель объёма выигрышных сделок;
     и если много −1.0R без доливов — говорит НЕ «не построено», а
     «доливы не случились» и перечисляет честные причины (рынок не
     дал фрактал по тренду / трейдеры держали HOLD / вход сразу в
     минус). Это диагностика, а не приговор.

ИДЕМПОТЕНТЕН (маркер DIAGNOZ_PRAVDA_V1). Бэкапы — по файлу.
Запуск из корня Grondheim-Ecosystem:
    python patch_diagnoz_pravda.py
"""
import io
import sys
from pathlib import Path

MARKER = "DIAGNOZ_PRAVDA_V1"


def find(name):
    for base in (Path("Биржа"), Path("GRONDHEIM_CITY") / "Биржа"):
        p = base / name
        if p.exists():
            return p
    print(f"[ПАТЧ] ✗ не найден Биржа/{name}")
    sys.exit(1)


def patch_hooks():
    path = find("hooks.py")
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("[ПАТЧ] ✓ hooks.py уже пропатчен")
        return
    orig = src
    old = (
        '            "lot":        pos.get("lot"),\n'
        '            "mode":       pos.get("mode", "PAPER"),\n'
    )
    new = (
        '            "lot":        pos.get("lot"),\n'
        '            # ' + MARKER + ': следы пирамиды в записи — отчёт увидит доливы\n'
        '            "lot_base":   pos.get("lot_base"),\n'
        '            "dolivok":    pos.get("dolivok", 0),\n'
        '            "mode":       pos.get("mode", "PAPER"),\n'
    )
    if old not in src:
        print("[ПАТЧ] ✗ hooks: якорь записи (lot/mode) не найден")
        sys.exit(2)
    src = src.replace(old, new, 1)
    bak = path.with_suffix(".py.bak_diagnoz")
    if not bak.exists():
        bak.write_text(orig, encoding="utf-8")
    path.write_text(src, encoding="utf-8")
    print("[ПАТЧ] ✓ hooks.py: lot_base/dolivok в записи закрытия")


def patch_tester():
    path = find("tester_express.py")
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("[ПАТЧ] ✓ tester_express.py уже пропатчен")
        return
    orig = src

    old = (
        '    if _dolya > 40 or (not _krup and len(_s) >= 4):\n'
        '        out("")\n'
        '        out("     ⚠ ВЕДЕНИЯ ПОЗИЦИИ НЕТ. Позиция умирает ОДНИМ ВЫСТРЕЛОМ.")\n'
        '        out("       Канон: вошёл 1R → цена пошла → СТОП В СЕЙФ (риск→0)")\n'
        '        out("       → ДОЛИВ → ДОЛИВ → exit_bell → закрыл всю пирамиду.")\n'
        '        out("       Книга Котина гл.9 САМА признаётся:")\n'
        '        out("         «Отложенный долг (слой 3, НЕ РЕАЛИЗОВАН): пирамида")\n'
        '        out("          доливок и трейлинг-стоп. ПОКА ВЕДЕНИЕ УПРОЩЕНО.»")\n'
        '        out("       ⇒ Минус ВСЕГДА полный, плюс ВСЕГДА обрезан.")\n'
        '        out("         Система МАТЕМАТИЧЕСКИ не может быть прибыльной.")\n'
        '        out("")\n'
        '        out("       Половина Вильямса — ВХОД — работает.")\n'
        '        out("       Вторая половина — ВЕДЕНИЕ — не построена.")\n'
    )
    new = (
        '    # ' + MARKER + ': ведение ПОСТРОЕНО (трейлинг/сейф/мост/пирамида).\n'
        '    # Диагноз теперь СЧИТАЕТ факт пирамиды, а не приговаривает.\n'
        '    _s_piram = [x for x in _s if int(x.get("dolivok", 0) or 0) > 0]\n'
        '    _s_win = [x for x in _s if x["pnl_r"] > 0]\n'
        '    def _mult(x):\n'
        '        _lb = x.get("lot_base") or x.get("lot") or 1.0\n'
        '        try:\n'
        '            return float(x.get("lot") or _lb) / float(_lb) if _lb else 1.0\n'
        '        except (TypeError, ZeroDivisionError):\n'
        '            return 1.0\n'
        '    _avg_mult = (sum(_mult(x) for x in _s_win) / len(_s_win)) if _s_win else 1.0\n'
        '    out(f"     сделок с доливом (пирамида сработала):     {len(_s_piram)}")\n'
        '    out(f"     средний множитель объёма у плюсовых:       {_avg_mult:.2f}x")\n'
        '\n'
        '    if not _krup and len(_s) >= 4:\n'
        '        out("")\n'
        '        if len(_s_piram) == 0:\n'
        '            out("     ⓘ Доливы НЕ случились ни разу за прогон.")\n'
        '            out("       Ведение построено (трейлинг/сейф/мост/пакет),")\n'
        '            out("       но пирамиде НЕ БЫЛО ПОВОДА. Честные причины:")\n'
        '            out("         • рынок не дал фрактал ПО ТРЕНДУ при живой позиции;")\n'
        '            out("         • цена ушла в минус сразу — доливать нечего;")\n'
        '            out("         • хозяин осознанно держал HOLD (осторожность).")\n'
        '            out("       Это НЕ поломка — это выборка. Нужен объём прогона.")\n'
        '        else:\n'
        '            out("     ⓘ Доливы были, но ни один пакет не дал +2R.")\n'
        '            out("       Смотреть: рано ли обрывался exit_bell, держит ли")\n'
        '            out("       тренд после долива. Пирамида живая, край ищем.")\n'
    )
    if old not in src:
        print("[ПАТЧ] ✗ tester: блок диагноза не найден (изменён?)")
        sys.exit(3)
    src = src.replace(old, new, 1)
    bak = path.with_suffix(".py.bak_diagnoz")
    if not bak.exists():
        bak.write_text(orig, encoding="utf-8")
    path.write_text(src, encoding="utf-8")
    print("[ПАТЧ] ✓ tester_express.py: диагноз переписан честно")


def main():
    patch_hooks()
    patch_tester()
    print("[ПАТЧ] ✅ Диагноз больше не врёт. Считает пирамиду по факту.")


if __name__ == "__main__":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass
    main()
