# patch_prizrak.py
# ─────────────────────────────────────────────────────────────
# NET_PRIZRAKOV_V1 — ПОЗИЦИЯ-ПРИЗРАК. Мёртвый агент не торгует.
#
# ⚠ НАЙДЕНО В ЖИВОМ ЛОГЕ ШЕФА (14.07). Это ХУЖЕ, чем убыток.
#
#   ⚡ A07: СБОЙ — Авантюрист не смог решить: OpenRouter вернул пустой ответ
#   ...
#   📋 ИСПОЛНИТЕЛЬ: ... Авантюрист: APPROVED SHORT
#   🟢 ОТКРЫТА: AVANTURIST SHORT @ 1202.44
#
# ИЛЬЯ УПАЛ — А ПОЗИЦИЯ ОТКРЫЛАСЬ. По вердикту, которого он НЕ ДАВАЛ.
#
# И цена выдаёт с головой: вход 1202.44, а на баре цена 1367–1387.
# Это ВЕРДИКТ С ПРОШЛОГО ПРОГОНА, застрявший в trading_state.
# Плюс в слепке компас=BULL, а вердикт SHORT — ПРОТИВ КОМПАСА.
#
# ── ПРИЧИНА (по коду, не по догадке) ──
# Трейдер пишет вердикт в стол сам: A07/мозг.py:130
#     t["avan"]["verdict"] = signal.get("avan_verdict", "REJECTED")
#     ... entry / stop / lot / direction / action ...
#     save_trading_state(t)
#
# При сбое LLM run_avan возвращает {"ok": False, "signal": {}} и
# ДО ЭТОЙ ЗАПИСИ НЕ ДОХОДИТ. Значит в столе ОСТАЁТСЯ СТАРЫЙ ВЕРДИКТ —
# живой, с ценами прошлой недели.
#
# Исполнитель приходит, читает стол, видит APPROVED SHORT @1202.44 —
# И ОТКРЫВАЕТ. Он не знает, что автор этого вердикта мёртв.
#
# ── ЧЕМ ЭТО ХУЖЕ УБЫТКА ──
# 1. Позицию НИКТО НЕ РЕШАЛ. Ни один живой агент за неё не отвечает.
# 2. Цена входа — из другой эпохи. Стоп там же. R посчитается по
#    мусору.
# 3. СУДЬЯ ПОТОМ НАКАЖЕТ ИЛЬЮ за вход, которого он не делал:
#    в его метки ляжет «МОЯ ОШИБКА» за чужое решение. Это КЛЕВЕТА,
#    и она отравит опыт — тот самый, ради которого всё строилось.
# 4. Вердикт мог быть ПРОТИВ КОМПАСА — как в логе Шефа.
#
# ── ЛЕЧЕНИЕ ──
# Правило простое и жёсткое: **МЁРТВЫЙ АГЕНТ НЕ ТОРГУЕТ.**
# Сбой (ok=False) → его вердикт на столе ОБНУЛЯЕТСЯ немедленно.
# Не «остаётся старый», не «берём по умолчанию» — ОБНУЛЯЕТСЯ.
# Молчание — это REJECTED, а не согласие.
#
# Чиним в ОДНОМ месте — в council.py (единая дверь, ENGINE_ONE_DOOR_V1),
# а не в девяти мозгах. Иначе через месяц девять копий разъедутся.
#
# ИДЕМПОТЕНТЕН. BACKUP: council.py.bak_prizrak
# Запуск из корня репо:  python patch_prizrak.py
#
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import ast
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CO   = ROOT / "Биржа" / "council.py"
MARK = "NET_PRIZRAKOV_V1"


CHISTKA = '''

# ═══════════════════════════════════════════════════════════
# NET_PRIZRAKOV_V1 — МЁРТВЫЙ АГЕНТ НЕ ТОРГУЕТ
# ═══════════════════════════════════════════════════════════
# Лог Шефа 14.07: Илья упал (OpenRouter вернул пустое тело) — а
# Исполнитель открыл SHORT @1202.44 по его СТАРОМУ вердикту, при том
# что цена на баре была 1367-1387, а компас показывал BULL.
#
# Трейдер пишет вердикт в стол САМ, в конце run_*. Упал раньше — не
# написал — в столе остался прошлый. Живой, с ценами другой эпохи.
#
# ПРАВИЛО: сбой → вердикт ОБНУЛЯЕТСЯ. Молчание — это REJECTED, а не
# согласие. Иначе судья потом впишет Илье «МОЯ ОШИБКА» за решение,
# которого он не принимал — и это отравит его опыт КЛЕВЕТОЙ.
# ═══════════════════════════════════════════════════════════

# кто где живёт в столе (проверено на диске: A06/A07/A08 :: мозг.py)
_STOL_KEY = {"A06": "brut", "A07": "avan", "A08": "cons"}


def _steret_verdikt(slot: str, prichina: str = ""):
    """Стирает вердикт упавшего трейдера со стола. Он молчал — значит
    REJECTED. Старый вердикт с прошлого бара торговать НЕ ИМЕЕТ ПРАВА."""
    key = _STOL_KEY.get(slot)
    if not key:
        return
    try:
        from hooks import load_trading_state, save_trading_state
        t = load_trading_state()
        staryi = (t.get(key, {}) or {}).get("verdict")
        t.setdefault(key, {})
        t[key] = {
            "verdict":   "REJECTED",
            "reason":    f"агент не ответил ({prichina[:60]})",
            "direction": None,
            "entry":     None,
            "stop":      None,
            "lot":       None,
            "action":    None,
            "new_stop":  None,
            "add_lot":   None,
        }
        save_trading_state(t)
        if staryi and staryi != "REJECTED":
            print(f"[ПРИЗРАК] 🚫 {slot} упал — стёр его старый вердикт "
                  f"«{staryi}». Мёртвый агент НЕ ТОРГУЕТ.")
        else:
            print(f"[ПРИЗРАК] 🚫 {slot} упал — стол очищен (REJECTED)")
    except Exception as e:
        print(f"[ПРИЗРАК] ⚠️  не смог стереть вердикт {slot}: {e}")

'''


def main():
    print()
    print("╔" + "═" * 68 + "╗")
    print("║  ПОЗИЦИЯ-ПРИЗРАК — мёртвый агент не торгует" + " " * 24 + "║")
    print("║  NET_PRIZRAKOV_V1 · идемпотентен" + " " * 35 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    print("  ИЗ ЛОГА ШЕФА (14.07):")
    print("    ⚡ A07: СБОЙ — Авантюрист не смог решить (пустой ответ)")
    print("    🟢 ОТКРЫТА: AVANTURIST SHORT @ 1202.44")
    print()
    print("  Илья УПАЛ — позиция ОТКРЫЛАСЬ. Цена входа 1202.44,")
    print("  а на баре 1367-1387. Вердикт С ПРОШЛОГО ПРОГОНА.")
    print()

    if not CO.exists():
        print("⚠ запускай ИЗ КОРНЯ репозитория Grondheim-Ecosystem")
        sys.exit(1)

    src = CO.read_text(encoding="utf-8")

    if MARK in src:
        print("  ✓ уже пропатчен — пропускаю (идемпотентно)")
        print()
        return

    bak = CO.with_suffix(".py.bak_prizrak")
    if not bak.exists():
        shutil.copy2(CO, bak)
        print(f"  ✓ бэкап: {bak.name}")

    # ── 1. Функция чистки — перед _call (единая дверь к мозгам) ──
    ank = "def _call(ceh_id: str, slot: str, fn_name: str, **kw) -> dict:"
    if ank not in src:
        print("  ⚠ не нашёл _call в council. СТОП.")
        sys.exit(1)
    src = src.replace(ank, CHISTKA.lstrip("\n") + "\n" + ank, 1)
    print("  ✓ _steret_verdikt() — чистит стол упавшего")

    # ── 2. Оборачиваем _call целиком: любой ok=False → чистка ──
    # ⚠ Матчить `return {"ok": False` НЕЛЬЗЯ: главный случай — тот, что
    # был в логе Шефа — приходит из `return fn(**kw) or {}`, где мозг
    # САМ вернул {"ok": False} (пустой ответ OpenRouter), без исключения.
    # Ловим на ВЫХОДЕ, откуда бы сбой ни пришёл.
    staroe = ('    try:\n'
              '        brain = _slot_brain(ceh_id, slot)\n'
              '        if brain is None:\n'
              '            return {"ok": False, "error": f"{ceh_id}/{slot}: мозг ещё не в слоте"}\n'
              '        fn = getattr(brain, fn_name, None)\n'
              '        if fn is None:\n'
              '            return {"ok": False, "error": f"{ceh_id}/{slot}: нет {fn_name}"}\n'
              '        return fn(**kw) or {}\n'
              '    except Exception as e:\n'
              '        return {"ok": False, "error": f"{fn_name}: {e}"}')
    novoe = ('    # NET_PRIZRAKOV_V1: ЛЮБОЙ сбой агента → его вердикт на столе\n'
             '    # ОБНУЛЯЕТСЯ. Без этого Исполнитель откроет позицию по СТАРОМУ\n'
             '    # вердикту с прошлого бара — что и случилось 14.07: Илья упал\n'
             '    # (OpenRouter вернул пустое тело), а SHORT открылся @1202.44 при\n'
             '    # цене 1367-1387 и компасе BULL. Мёртвый агент НЕ ТОРГУЕТ.\n'
             '    #\n'
             '    # Ловим на ВЫХОДЕ: главный случай — не исключение, а мозг,\n'
             '    # который САМ вернул {"ok": False} из `fn(**kw)`.\n'
             '    _res = None\n'
             '    try:\n'
             '        brain = _slot_brain(ceh_id, slot)\n'
             '        if brain is None:\n'
             '            _res = {"ok": False, "error": f"{ceh_id}/{slot}: мозг ещё не в слоте"}\n'
             '        else:\n'
             '            fn = getattr(brain, fn_name, None)\n'
             '            if fn is None:\n'
             '                _res = {"ok": False, "error": f"{ceh_id}/{slot}: нет {fn_name}"}\n'
             '            else:\n'
             '                _res = fn(**kw) or {}\n'
             '    except Exception as e:\n'
             '        _res = {"ok": False, "error": f"{fn_name}: {e}"}\n'
             '\n'
             '    if not (_res or {}).get("ok"):\n'
             '        _steret_verdikt(slot, str((_res or {}).get("error", "сбой")))\n'
             '\n'
             '    return _res')
    if staroe not in src:
        print("  ⚠ тело _call изменилось — не узнаю. СТОП.")
        print("    Смотри глазами: sed -n '93,108p' Биржа/council.py")
        sys.exit(1)
    src = src.replace(staroe, novoe, 1)
    print("  ✓ _call: ЛЮБОЙ сбой (в т.ч. пустой ответ LLM) чистит стол")

    # ── СТОП-КРАН ───────────────────────────────────────────────
    if "_steret_verdikt(slot" not in src:
        print("  ⚠ ЧИСТКА НЕ ЗОВЁТСЯ. НЕ ПИШУ ФАЙЛ.")
        sys.exit(1)

    src = src.replace("# `шесть·проверено·до·корня`",
                      f"# {MARK}: упавший агент не торгует старым вердиктом.\n"
                      "# `шесть·проверено·до·корня`", 1)
    if MARK not in src:
        src = f"# {MARK}\n" + src

    try:
        ast.parse(src)
    except SyntaxError as ex:
        print(f"  ⚠ СИНТАКСИС СЛОМАН: {ex}. НЕ ПИШУ ФАЙЛ.")
        sys.exit(1)

    CO.write_text(src, encoding="utf-8")

    print("  ✓ синтаксис цел")
    print()
    print("╔" + "═" * 68 + "╗")
    print("║  ГОТОВО — призраки не торгуют" + " " * 38 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    print("  ПРАВИЛО: сбой → вердикт ОБНУЛЯЕТСЯ. Молчание — это REJECTED,")
    print("           а не согласие.")
    print()
    print("  ЧЕМ ЭТО БЫЛО ХУЖЕ УБЫТКА:")
    print("    · позицию НИКТО не решал — ни один живой агент")
    print("    · цена входа из другой эпохи → R считался по мусору")
    print("    · СУДЬЯ ПОТОМ ВПИСАЛ БЫ ИЛЬЕ «МОЯ ОШИБКА» за чужое")
    print("      решение — КЛЕВЕТА, отравляющая тот самый опыт,")
    print("      ради которого всё и строилось")
    print()
    print("  ЧТО ИСКАТЬ В ЛОГЕ:")
    print("    [ПРИЗРАК] 🚫 A07 упал — стёр его старый вердикт «APPROVED».")
    print("              Мёртвый агент НЕ ТОРГУЕТ.")
    print()


if __name__ == "__main__":
    main()
