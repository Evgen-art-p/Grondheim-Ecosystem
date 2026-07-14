# patch_ruka_dopisyvayushchaya.py
# ─────────────────────────────────────────────────────────────
# RUKA_DOPISYVAYUSHCHAYA_V1 — ДНЕВНИК УЗНАЁТ, ЧЕМ ВСЁ КОНЧИЛОСЬ.
#
# ВОПРОС ШЕФА (14.07): «а архивариус пишет дневники? трейдеры вообще
# пишут?»
#
# Пишут. Но ОБОРВАННО — и это ещё один кран того же класса.
#
# ── БОЛЕЗНЬ ──
# Трейдер при входе пишет в свою тетрадь (A06/A07/A08 :: _append_diary):
#     {"bar_time":..., "verdict":"APPROVED", "entry":1247.36,
#      "stop":1244.93, "input":"...", "action":"...",
#      "result": None}                       ← ПУСТО
#
# А в докстринге ЕГО ЖЕ функции написано:
#     «result=null — ДОПИШЕТ РУКА ДОПИСЫВАЮЩАЯ при закрытии позиции
#      (hooks._settle)»
#
# ⚠ РУКИ НЕТ. В hooks.py — НОЛЬ упоминаний DIARY. Никто никогда не
#   дописывал результат. Ни разу.
#
# ── ЧТО ЭТО ЗНАЧИТ ЖИВЬЁМ ──
# Илья читает свои последние 5 записей (_read_recent_diary) — и в
# КАЖДОЙ `result: None`. Он видит «я вошёл LONG 2011.08.01, стоп там-то»
# и НЕ ЗНАЕТ, ЧЕМ ЭТО КОНЧИЛОСЬ.
#
# Его знаменитое (лог 14.07):
#     «как в моём одобренном SHORT от 27.07.2012»
#     «Мой опыт: 2010.05.07 шортил при отказе от zero point»
# — это ссылки на ВХОД, а не на ИСХОД. Он помнит, ЧТО РЕШИЛ,
#   но НЕ ПОМНИТ, БЫЛ ЛИ ПРАВ.
#
# ⇒ ДНЕВНИК БЕЗ РЕЗУЛЬТАТА — ЭТО СПИСОК НАМЕРЕНИЙ, А НЕ ОПЫТ.
#
# И это ХУЖЕ, чем пустой дневник: он ПОДКРЕПЛЯЕТ прошлые решения самим
# фактом их существования. «Я так уже делал» звучит как довод — хотя в
# прошлый раз это стоило −1.0R.
#
# ── ЛЕЧЕНИЕ ──
# hooks._settle_positions при закрытии знает ВСЁ: trader, entry, pnl_r,
# close_reason. Находим в тетради ЭТОГО трейдера запись с тем же `entry`
# и пустым `result` — и вписываем исход.
#
# Тогда Илья прочтёт:
#     «вошёл LONG 2011.08.01 @1247.36 → −1.0R (STOP_LOSS)»
# И ЭТО УЖЕ ОПЫТ.
#
# ⚠ Пятый кран того же класса за двое суток:
#   магик (5 копий) · слепок (2 писателя) · bdb_dir (2 читателя) ·
#   ведение (написано, не позвано) · РУКА ДОПИСЫВАЮЩАЯ (обещана в
#   докстринге, не написана).
#
# ИДЕМПОТЕНТЕН. BACKUP: hooks.py.bak_ruka
# Запуск из корня репо:  python patch_ruka_dopisyvayushchaya.py
#
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import ast
import shutil
import sys
from pathlib import Path

ROOT  = Path(__file__).resolve().parent
HOOKS = ROOT / "Биржа" / "hooks.py"
MARK  = "RUKA_DOPISYVAYUSHCHAYA_V1"


RUKA = '''

# ═══════════════════════════════════════════════════════════
# RUKA_DOPISYVAYUSHCHAYA_V1 — ДНЕВНИК УЗНАЁТ ИСХОД
# ═══════════════════════════════════════════════════════════
# Трейдер при входе писал в тетрадь `result: None` и в докстринге своей
# же функции обещал: «допишет РУКА ДОПИСЫВАЮЩАЯ при закрытии позиции
# (hooks._settle)».
#
# РУКИ НЕ БЫЛО. Ни разу. Дневник копил НАМЕРЕНИЯ, а не ОПЫТ:
# «вошёл LONG @1247.36» — и всё. Чем кончилось — неизвестно.
#
# А это ХУЖЕ пустого дневника: прошлое решение подкрепляет само себя
# фактом существования. «Я так уже делал» звучит доводом — хотя в
# прошлый раз стоило −1.0R.
#
# Теперь при закрытии позиции исход возвращается в тетрадь хозяина.
# ═══════════════════════════════════════════════════════════

# Тетради живут в слотах цехов (проверено на диске 14.07):
#   торговый_хаос/слоты/A06/данные/diary_brut.jsonl
#   торговый_хаос/слоты/A07/данные/diary_avan.jsonl
#   торговый_хаос/слоты/A08/данные/diary_cons.jsonl
_DIARY_OF = {
    "BRUT":        ("A06", "diary_brut.jsonl"),
    "AVANTURIST":  ("A07", "diary_avan.jsonl"),
    "KONSERVATOR": ("A08", "diary_cons.jsonl"),
}


def _dopisat_v_dnevnik(trader: str, entry, pnl_r, reason: str, bar_time=None):
    """Возвращает ИСХОД в тетрадь трейдера.

    Ищет запись с тем же `entry` и пустым `result` (сверху вниз — берём
    САМУЮ СВЕЖУЮ, если вдруг он входил по той же цене дважды).
    Не нашёл — молчим: значит вход был не через дневник (ручной,
    старый прогон), и врать в тетрадь нельзя.
    """
    slot = _DIARY_OF.get((trader or "").upper())
    if not slot or entry is None or pnl_r is None:
        return False

    sid, fname = slot
    path = (_REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос"
            / "слоты" / sid / "данные" / fname)
    if not path.exists():
        return False

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return False

    itog = {
        "pnl_r":  round(float(pnl_r), 4),
        "reason": reason,
        "closed_at": bar_time,
        "оценка": ("плюс" if pnl_r > 0 else
                   "полный стоп" if abs(pnl_r + 1.0) < 0.05 else "минус"),
    }

    # снизу вверх — самая свежая незакрытая запись с этим входом
    for i in range(len(lines) - 1, -1, -1):
        ln = lines[i].strip()
        if not ln:
            continue
        try:
            rec = json.loads(ln)
        except Exception:
            continue
        if rec.get("result") is not None:
            continue
        e = rec.get("entry")
        if e is None:
            continue
        try:
            if abs(float(e) - float(entry)) > 1e-6:
                continue
        except Exception:
            continue

        rec["result"] = itog
        lines[i] = json.dumps(rec, ensure_ascii=False)
        try:
            path.write_text("\\n".join(lines) + "\\n", encoding="utf-8")
        except Exception as ex:
            print(f"[ТЕТРАДЬ] ⚠️  не записал ({trader}): {ex}")
            return False

        znak = "🟢" if pnl_r > 0 else "🔴"
        print(f"[ТЕТРАДЬ] ✍️  {trader}: вход {entry} → "
              f"{pnl_r:+.2f}R ({reason}) {znak} — исход вписан")
        return True

    # записи нет — это не ошибка, просто вход был не через дневник
    return False

'''


def main():
    print()
    print("╔" + "═" * 68 + "╗")
    print("║  РУКА ДОПИСЫВАЮЩАЯ — дневник узнаёт исход" + " " * 26 + "║")
    print("║  RUKA_DOPISYVAYUSHCHAYA_V1 · идемпотентен" + " " * 26 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    print("  Трейдер писал в тетрадь `result: None` и обещал в докстринге:")
    print("    «допишет РУКА ДОПИСЫВАЮЩАЯ при закрытии (hooks._settle)»")
    print("  РУКИ НЕ БЫЛО. Ни разу. Дневник копил НАМЕРЕНИЯ, не ОПЫТ.")
    print()

    if not HOOKS.exists():
        print("⚠ запускай ИЗ КОРНЯ репозитория Grondheim-Ecosystem")
        sys.exit(1)

    src = HOOKS.read_text(encoding="utf-8")

    if MARK in src:
        print("  ✓ уже пропатчен — пропускаю (идемпотентно)")
        print()
        return

    bak = HOOKS.with_suffix(".py.bak_ruka")
    if not bak.exists():
        shutil.copy2(HOOKS, bak)
        print(f"  ✓ бэкап: {bak.name}")

    # ── 1. Функция руки — перед _settle_positions ───────────────
    ank = "def _settle_positions(state: dict):"
    if ank not in src:
        print("  ⚠ не нашёл _settle_positions. СТОП.")
        sys.exit(1)
    src = src.replace(ank, RUKA.lstrip("\n") + "\n" + ank, 1)
    print("  ✓ _dopisat_v_dnevnik() — рука написана")

    # ── 2. Зовём при закрытии — сразу после записи в pnl.jsonl ──
    staroe = ('        PNL_PATH.parent.mkdir(parents=True, exist_ok=True)\n'
              '        with open(PNL_PATH, "a", encoding="utf-8") as f:\n'
              '            f.write(json.dumps(record, ensure_ascii=False) + "\\n")')
    novoe = ('        PNL_PATH.parent.mkdir(parents=True, exist_ok=True)\n'
             '        with open(PNL_PATH, "a", encoding="utf-8") as f:\n'
             '            f.write(json.dumps(record, ensure_ascii=False) + "\\n")\n'
             '\n'
             '        # RUKA_DOPISYVAYUSHCHAYA_V1: ИСХОД — обратно в тетрадь\n'
             '        # хозяина. Без этого он читает свои прошлые входы и НЕ\n'
             '        # ЗНАЕТ, чем они кончились: «я так уже делал» звучит\n'
             '        # доводом, хотя стоило −1.0R. Дневник без результата —\n'
             '        # список намерений, а не опыт.\n'
             '        try:\n'
             '            _dopisat_v_dnevnik(pos.get("trader"), entry,\n'
             '                               pnl_r, reason, bar_time)\n'
             '        except Exception as _de:\n'
             '            print(f"[ТЕТРАДЬ] ⚠️  {_de}")')
    if staroe not in src:
        print("  ⚠ не нашёл запись в PNL_PATH. СТОП.")
        sys.exit(1)
    src = src.replace(staroe, novoe, 1)
    print("  ✓ зовётся при КАЖДОМ закрытии позиции")

    # ── СТОП-КРАН ───────────────────────────────────────────────
    if "_dopisat_v_dnevnik(pos.get(\"trader\")" not in src:
        print("  ⚠ РУКА НЕ ЗОВЁТСЯ. НЕ ПИШУ ФАЙЛ.")
        sys.exit(1)

    src = src.replace("# `шесть·проверено·до·корня`",
                      f"# {MARK}: исход сделки возвращается в тетрадь трейдера.\n"
                      "# `шесть·проверено·до·корня`", 1)
    if MARK not in src:
        src = f"# {MARK}\n" + src

    try:
        ast.parse(src)
    except SyntaxError as ex:
        print(f"  ⚠ СИНТАКСИС СЛОМАН: {ex}. НЕ ПИШУ ФАЙЛ.")
        sys.exit(1)

    HOOKS.write_text(src, encoding="utf-8")

    print("  ✓ синтаксис цел")
    print()
    print("╔" + "═" * 68 + "╗")
    print("║  ГОТОВО — дневник стал опытом" + " " * 38 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    print("  БЫЛО (что Илья читал):")
    print('    {"bar_time":"2011.08.01", "verdict":"APPROVED",')
    print('     "entry":1247.36, "result": null}     ← ЧЕМ КОНЧИЛОСЬ?')
    print()
    print("  СТАНЕТ:")
    print('    {"bar_time":"2011.08.01", "verdict":"APPROVED",')
    print('     "entry":1247.36,')
    print('     "result": {"pnl_r": -1.0, "reason":"STOP_LOSS",')
    print('                "оценка":"полный стоп"}}   ← ВОТ ЭТО ОПЫТ')
    print()
    print("  ЧТО ИСКАТЬ В ЛОГЕ:")
    print("    [ТЕТРАДЬ] ✍️  AVANTURIST: вход 1247.36 → −1.00R (STOP_LOSS) 🔴")
    print()
    print("  ⚠ ЧЕСТНО: старые записи так и останутся с result=null —")
    print("    их исход уже не восстановить. Опыт начинает копиться")
    print("    С ЭТОГО ПРОГОНА.")
    print()


if __name__ == "__main__":
    main()
