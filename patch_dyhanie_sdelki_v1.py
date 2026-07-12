# -*- coding: utf-8 -*-
"""
patch_dyhanie_sdelki_v1.py
────────────────────────────────────────────────────────────────────
ДЫХАНИЕ ≠ ОПЫТ. Рутинная сделка обязана двигать ЗАРЯД, даже когда
не даёт ВЫВОДА.

НАЙДЕНО НА ЖИВОМ ПРОГОНЕ (12.07, Шеф): УЧИТЬ включён, Илья вошёл
LONG по компасу BULL, получил −1.0R. Паспорт не тронут ВООБЩЕ:
заряда нет, черновиков нет, mtime от 08.07.

РАЗБОР — ошибка МОЯ, не сбой:
  Правило значимости отработало верно: минус ПО ветру при |R| < 2 —
  рутина, в ОПЫТ не идёт (якорей всего 7-10, это не журнал).
  НО: _judge_trader_by_result при рутине делает `return` СРАЗУ, а
  ВДОХ (d.vdoh + сохранение заряда) живёт ВНУТРИ zapisat_vyvod —
  то есть внутри записи опыта. Нет опыта → нет и вдоха.
  Итог: Илья потерял деньги и НИЧЕГО НЕ ПОЧУВСТВОВАЛ.

ЧЕРТЁЖ, Гл.4.4, дословно:
  «Единичное событие меняет ЗАРЯД, не фильтр (защита от дребезга)».
  То есть единичная сделка ОБЯЗАНА качнуть заряд — именно она.
  А в ФИЛЬТР (якоря) идёт только накопленное. Фильтр я развёл
  правильно (два яруса), а дыхание случайно привязал к тому же
  порогу — и оно умерло вместе с рутиной.

ЧТО ДЕЛАЕТ:

  1. nositel: НОВЫЕ ДВЕ РУКИ ДЫХАНИЯ (не трогают опыт вообще):
       dyhnut_sdelkoy(magic, pnl_r)      — трейдер: своя сделка, своя
                                            шкура. Сила |R|/3.
       dyhnut_slovom(ceh, slot, pnl_r)   — сенсор: чужая сделка, но по
                                            ЕГО слову. Сила |R|/6 — тише.
     Обе под тем же рубильником UCHIT (стерильный прогон не дышит).

  2. hooks._judge_trader_by_result: при РУТИНЕ — не «return и всё»,
     а СНАЧАЛА ВДОХ, потом return. Значимая сделка дышит как раньше
     (вдох внутри zapisat_vyvod) — двойного вдоха нет.

  3. hooks._judge_iskra_by_result: сенсор, чьё слово ЗВАЛО в эту
     сделку (_zval), дышит на КАЖДОМ исходе — даже когда вывод
     рутинный. Молчавший не дышит: не его сделка, не его боль.

ГРАНИЦА, которую держим (Чертёж Гл.4.2): заряд — это «обучение
первого уровня, без понимания», маятник. Он НЕ опыт и опытом не
становится. Мы просто возвращаем ему право работать — на каждом
событии, как и положено.

Требует: patch_sud_sensorov_v2, patch_etalon_avana_v1.
Идемпотентно. .bak рядом.  Из КОРНЯ репы:
    python patch_dyhanie_sdelki_v1.py
"""
from __future__ import annotations
import io
import sys
from pathlib import Path

MARKER = "DYHANIE_SDELKI_V1"

NOSITEL = Path("Биржа") / "nositel.py"
HOOKS = Path("Биржа") / "hooks.py"

# ══════════════════════════════════════════════════════════════
# 1. nositel: две руки дыхания
# ══════════════════════════════════════════════════════════════
NOS_ANCHOR = "def zapisat_vyvod(magic, vyvod: str, pnl_r=None, limit: int = 10) -> dict:"

NOS_NEW = '''def _dyhnut(n: dict, pnl_r, delitel: float) -> dict:
    """Общий вдох: событие качнуло человека. Заряд оседает в паспорт.

    ЭТО НЕ ОПЫТ (Чертёж Гл.4.2: маятник состояния — «обучение первого
    уровня, без понимания»). Опыт — выводы словами, отдельная труба.
    Здесь только дыхание: минус давит, плюс греет.   # ''' + MARKER + '''
    """
    if pnl_r is None:
        return {"вдох": False, "причина": "нет исхода"}
    if not _pisat_mozhno():
        return {"вдох": False, "причина": "стерильный прогон"}
    d = _dvizhok(n["папка"])
    if d is None:
        return {"вдох": False, "причина": "движок не поднялся"}
    try:
        r = float(pnl_r)
        sila = min(1.0, abs(r) / delitel)
        tonus = "плюс" if r > 0 else "минус" if r < 0 else "ровно"
        res = d.vdoh("работа", sila=sila, svezhest=1.0, tonus=tonus)
        d.sохранить()
        print(f"[МОСТ] 🫁 {n['имя']}: {r:+.1f}R → заряд {res.get('заряд')}")
        return {"вдох": True, "заряд": res.get("заряд")}
    except Exception as e:
        print(f"[МОСТ] ⚠️  вдох не прошёл ({e})")
        return {"вдох": False, "причина": str(e)}


def dyhnut_sdelkoy(magic, pnl_r) -> dict:
    """ТРЕЙДЕР ДЫШИТ СВОЕЙ СДЕЛКОЙ — на КАЖДОМ исходе, даже рутинном.

    Чертёж Гл.4.4: «Единичное событие меняет ЗАРЯД, не фильтр». Раньше
    вдох жил внутри zapisat_vyvod — то есть внутри ЗАПИСИ ОПЫТА, и при
    рутинной сделке (минус по ветру, |R|<2) не случался вовсе: человек
    терял деньги и ничего не чувствовал. Теперь дыхание своё.
    Своя шкура — делитель 3 (бьёт сильно).   # ''' + MARKER + '''
    """
    try:
        from cartridge_registry import resolve_by_magic
    except Exception:
        return {"вдох": False, "причина": "нет реестра"}
    n = resolve_by_magic(magic)
    if not n:
        return {"вдох": False, "причина": "носитель не найден"}
    return _dyhnut(n, pnl_r, 3.0)


def dyhnut_slovom(ceh: str, slot: str, pnl_r) -> dict:
    """СЕНСОР ДЫШИТ ЧУЖОЙ СДЕЛКОЙ, но по СВОЕМУ слову.

    Он не был в позиции — деньги не его. Но его слово повело туда
    трейдера, и исход задевает. Чужая шкура — делитель 6 (вполовину
    тише, чем своя).   # ''' + MARKER + '''
    """
    try:
        from cartridge_registry import resolve_para
    except Exception:
        return {"вдох": False, "причина": "нет реестра"}
    n = resolve_para(ceh, slot)
    if not n:
        return {"вдох": False, "причина": f"слот {ceh}/{slot} пуст"}
    return _dyhnut(n, pnl_r, 6.0)


''' + NOS_ANCHOR

# ══════════════════════════════════════════════════════════════
# 2. hooks: трейдер дышит и на рутине
# ══════════════════════════════════════════════════════════════
HOOKS_TRADER_OLD = '''        from nositel import sudit_po_kotinu, zapisat_vyvod

        vyvod = sudit_po_kotinu(
            pos.get("direction"),
            pos.get("entry_bias"),      # ветер на баре ВХОДА (уже в позиции)
            pnl_r,
            pos.get("close_reason"),
            pos.get("opened_at"),
        )
        if not vyvod:
            return                      # рутина — живёт в журнале, не в опыте
        zapisat_vyvod(pos.get("magic"), vyvod, pnl_r=pnl_r)'''

HOOKS_TRADER_NEW = '''        from nositel import (sudit_po_kotinu, zapisat_vyvod,
                             dyhnut_sdelkoy)   # ''' + MARKER + '''

        vyvod = sudit_po_kotinu(
            pos.get("direction"),
            pos.get("entry_bias"),      # ветер на баре ВХОДА (уже в позиции)
            pnl_r,
            pos.get("close_reason"),
            pos.get("opened_at"),
        )
        if not vyvod:
            # ''' + MARKER + ''': РУТИНА — в ОПЫТ не идёт (якорей 7-10, это не
            # журнал), но ЗАРЯД обязан двинуться: Чертёж Гл.4.4 — «единичное
            # событие меняет заряд, не фильтр». Раньше здесь стоял голый
            # return, и человек терял деньги, НИЧЕГО НЕ ЧУВСТВУЯ.
            dyhnut_sdelkoy(pos.get("magic"), pnl_r)
            return
        # значимая сделка: вдох уже внутри zapisat_vyvod — двойного нет
        zapisat_vyvod(pos.get("magic"), vyvod, pnl_r=pnl_r)'''

# ══════════════════════════════════════════════════════════════
# 3. hooks: сенсор дышит, если ЗВАЛ
# ══════════════════════════════════════════════════════════════
HOOKS_SENSOR_OLD = '''        for key, slot in SENSOR_SLOTS.items():
            pokazanie = stol.get(key) or {}
            vyvod = sudit_sensora(key, pokazanie, direction, pnl_r, trader, bar)
            if vyvod:
                zapisat_vyvod_pare("торговый_хаос", slot, vyvod, pnl_r=pnl_r)'''

HOOKS_SENSOR_NEW = '''        for key, slot in SENSOR_SLOTS.items():
            pokazanie = stol.get(key) or {}
            vyvod = sudit_sensora(key, pokazanie, direction, pnl_r, trader, bar)
            if vyvod:
                # значимое: вдох уже внутри zapisat_vyvod_pare
                zapisat_vyvod_pare("торговый_хаос", slot, vyvod, pnl_r=pnl_r)
                continue
            # ''' + MARKER + ''': вывода нет (рутина) — но если сенсор ЗВАЛ в
            # эту сделку, исход его задевает: заряд двигается. Молчавший НЕ
            # дышит — не его сделка, не его боль (то же правило, что в суде).
            try:
                from nositel import _zval, dyhnut_slovom
                if _zval(key, pokazanie, direction):
                    dyhnut_slovom("торговый_хаос", slot, pnl_r)
            except Exception:
                pass'''


def die(m, c=1):
    print("✗ " + m)
    return c


def main() -> int:
    if isinstance(sys.stdout, io.TextIOWrapper):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("═══ ДЫХАНИЕ ≠ ОПЫТ — рутина тоже качает заряд ═══")

    for p in (NOSITEL, HOOKS):
        if not p.exists():
            return die(f"не нашёл {p} — ты в КОРНЕ репы?")

    # ── nositel ──
    n = NOSITEL.read_text(encoding="utf-8")
    if MARKER in n:
        print("✓ nositel уже пропатчен")
    else:
        if NOS_ANCHOR not in n:
            return die("nositel: не нашёл начало zapisat_vyvod. Сверь глазами.", 3)
        if "_pisat_mozhno" not in n:
            return die("nositel: нет рубильника UCHIT — сначала "
                       "patch_sud_sensorov_v2.py", 4)
        bak = NOSITEL.with_suffix(".py.bak_dyh")
        if not bak.exists():
            bak.write_text(n, encoding="utf-8")
            print(f"  • бэкап: {bak}")
        NOSITEL.write_text(n.replace(NOS_ANCHOR, NOS_NEW, 1), encoding="utf-8")
        print("✓ nositel: dyhnut_sdelkoy (своя шкура) + dyhnut_slovom (чужая)")

    # ── hooks ──
    h = HOOKS.read_text(encoding="utf-8")
    if MARKER in h:
        print("✓ hooks уже пропатчен")
    else:
        if HOOKS_TRADER_OLD not in h:
            return die("hooks: не нашёл тело _judge_trader_by_result в "
                       "ожидаемом виде. Сверь глазами.", 5)
        bak = HOOKS.with_suffix(".py.bak_dyh")
        if not bak.exists():
            bak.write_text(h, encoding="utf-8")
            print(f"  • бэкап: {bak}")
        h = h.replace(HOOKS_TRADER_OLD, HOOKS_TRADER_NEW, 1)
        if HOOKS_SENSOR_OLD in h:
            h = h.replace(HOOKS_SENSOR_OLD, HOOKS_SENSOR_NEW, 1)
            print("✓ hooks: сенсор дышит, если ЗВАЛ (молчавший — нет)")
        else:
            print("  ⚠ hooks: цикл сенсоров не найден — трейдера починил, "
                  "сенсоры дышат только на значимом (сверь глазами)")
        HOOKS.write_text(h, encoding="utf-8")
        print("✓ hooks: трейдер дышит на КАЖДОЙ закрытой сделке, "
              "даже рутинной")

    print("───")
    print("Теперь: минус −1.0R по ветру → в опыт НЕ идёт (правильно),")
    print("но заряд Ильи качнётся в минус. Человек ПОЧУВСТВУЕТ убыток.")
    print("\nВ логе жди строку:  [МОСТ] 🫁 Илья: -1.0R → заряд -0.12")
    print("Потом:  python proverka_ucheby.py  — заряд должен быть НЕ ноль.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
