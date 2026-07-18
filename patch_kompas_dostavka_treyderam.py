# -*- coding: utf-8 -*-
"""
ПАТЧ: KOMPAS_DOSTAVKA_TREYDERAM_V1

НАЙДЕНО при проверке предыдущего патча (KOMPAS_NE_VOROTA_V1), вопросом
Шефа "в мозге у искры не нужно ничего править?" — спасибо, что спросил.

ЧТО БЫЛО СЛОМАНО (тихо, без ошибки в логе):
  До KOMPAS_NE_VOROTA_V1 старые ворота ПРИНУДИТЕЛЬНО уравнивали
  bdb_dir == compass — поэтому trend_direction (направление точки)
  и компас (тренд старшего этажа) всегда совпадали. Не важно было,
  какое из двух класть в общую память — они были одним числом.

  KOMPAS_NE_VOROTA_V1 снял это принудительное равенство — сигнал
  trend_direction теперь честно означает направление ТОЧКИ, а не
  компаса (так и написано в промпте Искры). Но у трейдеров (A06/A07/
  A08) поле anchor.global_trend по-прежнему читало trend_direction —
  и было подписано в коде как "компас старшего ТФ". После первого
  патча оно стало ТИХО ВРАТЬ: трейдер видит под именем "global_trend"
  эхо своего же сигнала, не независимый факт старшей воды. Компас как
  проверка перестал что-либо проверять — молча, без сбоя.

  Сам компас (v2_descent.compass) при этом вообще НЕ сохранялся в
  trading_state — жил только внутри одного вызова run_iskra. Трейдеры
  физически не могли его увидеть, даже если бы знали, что искать не то.

ЧТО ПРАВИТ:
  1. мозг A01 (_save_iskra_memory) — сохраняет compass и soglasie
     ОТДЕЛЬНЫМИ полями в trading_state, не путает их с trend_direction.
  2. мозг A06/A07/A08 (Брут/Аван/Консерватор) — anchor.global_trend
     читает compass (настоящий факт старшей воды), не trend_direction
     (направление точки — оно уже есть отдельно в sensors.iskra).
     Добавлено anchor.soglasie — ранг точки относительно компаса,
     готовый факт на стол, трейдеру не пересчитывать самому.

ЗАПУСК: из корня репо, ПОСЛЕ patch_kompas_ne_vorota.py
    python patch_kompas_dostavka_treyderam.py

Идемпотентно. Бэкапы рядом (.bak, перезаписываются).
"""
import ast
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
CEHA = REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "слоты"
MARKER = "KOMPAS_DOSTAVKA_TREYDERAM_V1"


# ═══════════════════════════════════════════════════════════
# A01 — сохранить compass/soglasie отдельно от trend_direction
# ═══════════════════════════════════════════════════════════
A01_TARGET = CEHA / "A01" / "мозг.py"

A01_OLD = '''    # ── ISKRA_MEM_V2: два поля спуска v2 — Морж наследует масштаб ──
    # found_timeframe берём из signal (его кладёт user_msg при found),
    # с фоллбэком на старое имя timeframe. trend_direction = компас спуска.
    # КОМПАС: приоритет — дивер-компас Искры (trend_direction/compass).  # GLOBAL_BIAS_COMPASS_V1
    # Фоллбэк — global_bias из синей линии (всегда на столе), если дивер молчит.
    _td = signal.get("trend_direction") or signal.get("compass")
    if not _td and md:
        _gb = md.get("global_bias")
        if _gb in ("BULL", "BEAR"):
            _td = _gb
    tstate["iskra"]["trend_direction"] = _td
    tstate["iskra"]["found_timeframe"] = (
        signal.get("found_timeframe") or signal.get("timeframe")
    )
    save_trading_state(tstate)'''

A01_NEW = '''    # ── ISKRA_MEM_V2: два поля спуска v2 — Морж наследует масштаб ──
    # found_timeframe берём из signal (его кладёт user_msg при found).
    # KOMPAS_DOSTAVKA_TREYDERAM_V1: trend_direction = НАПРАВЛЕНИЕ ТОЧКИ
    # (что нашла Искра), НЕ компас. Раньше эти два понятия были
    # принудительно равны (старые ворота требовали bdb_dir==compass),
    # поэтому их можно было путать безнаказанно. Теперь они могут
    # разойтись (точка против компаса — законный факт, не отказ), и
    # путать их — тихо портить данные трейдерам. Компас — ОТДЕЛЬНОЕ
    # поле, из md (живёт только внутри run_iskra, здесь фиксируется
    # на запись). Фоллбэк на global_bias — если дивера-с-якорем не было.
    _td = signal.get("trend_direction")
    if not _td and md:
        _gb = md.get("global_bias")
        if _gb in ("BULL", "BEAR"):
            _td = _gb
    tstate["iskra"]["trend_direction"] = _td
    _descent = (md or {}).get("v2_descent", {})
    tstate["iskra"]["compass"]  = _descent.get("compass")
    tstate["iskra"]["soglasie"] = _descent.get("soglasie")
    tstate["iskra"]["found_timeframe"] = (
        signal.get("found_timeframe") or signal.get("timeframe")
    )
    save_trading_state(tstate)'''


# ═══════════════════════════════════════════════════════════
# A06 (Брут) — свой вариант, с фоллбэком на global_bias
# ═══════════════════════════════════════════════════════════
A06_TARGET = CEHA / "A06" / "мозг.py"

A06_OLD = '''        "anchor": {
            # компас старшего ТФ — направление глобального тренда (этаж Искры)
            # КОМПАС: память Искры приоритетна; если пуста —  # GLOBAL_BIAS_COMPASS_V1
            # страховка прямо из market_data (синяя линия всегда на столе).
            "global_trend": (table.get("iskra", {}).get("trend_direction")
                             or (md.get("global_bias")
                                 if md.get("global_bias") in ("BULL", "BEAR")
                                 else None)),
            "found_timeframe": iskra_tf,
        },'''

A06_NEW = '''        "anchor": {
            # KOMPAS_DOSTAVKA_TREYDERAM_V1: global_trend — НАСТОЯЩИЙ компас
            # (v2_descent.compass через trading_state), не направление
            # точки. Раньше здесь читался trend_direction — до снятия
            # ворот (KOMPAS_NE_VOROTA_V1) это было то же число случайно,
            # теперь это два разных факта, и подмена тихо портила стол.
            # Фоллбэк — global_bias из market_data, если дивера-с-якорем
            # не было вовсе.
            "global_trend": (table.get("iskra", {}).get("compass")
                             or (md.get("global_bias")
                                 if md.get("global_bias") in ("BULL", "BEAR")
                                 else None)),
            "soglasie": table.get("iskra", {}).get("soglasie"),
            "found_timeframe": iskra_tf,
        },'''


# ═══════════════════════════════════════════════════════════
# A07 (Аван) / A08 (Консерватор) — общий простой шаблон
# ═══════════════════════════════════════════════════════════
def simple_old_new():
    old = '''        "anchor": {
            "global_trend": table.get("iskra", {}).get("trend_direction"),
            "found_timeframe": iskra_tf,
        },'''
    new = '''        "anchor": {
            # KOMPAS_DOSTAVKA_TREYDERAM_V1: НАСТОЯЩИЙ компас, не
            # направление точки — см. мозг A01/A06 за объяснением.
            "global_trend": table.get("iskra", {}).get("compass"),
            "soglasie": table.get("iskra", {}).get("soglasie"),
            "found_timeframe": iskra_tf,
        },'''
    return old, new


def patch_one(target: Path, old: str, new: str, label: str) -> bool:
    if not target.exists():
        print(f"[ПАТЧ] ✗ {label}: не найден {target}")
        return False
    src = target.read_text(encoding="utf-8")
    if MARKER in src:
        print(f"[ПАТЧ] ✓ {label}: {MARKER} уже применён — пропускаю")
        return True
    if old not in src:
        print(f"[ПАТЧ] ✗ {label}: якорь не найден — файл уже другой")
        return False
    src = src.replace(old, new, 1)
    src += f"\n# {MARKER} - marker\n"
    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"[ПАТЧ] ✗ {label}: результат не парсится: {e}")
        return False
    shutil.copy2(target, target.with_suffix(".py.bak"))
    target.write_text(src, encoding="utf-8")
    print(f"[ПАТЧ] ✓ {label}: {MARKER} применён")
    return True


def main():
    ok = True
    ok &= patch_one(A01_TARGET, A01_OLD, A01_NEW, "A01 (Искра, память)")
    ok &= patch_one(A06_TARGET, A06_OLD, A06_NEW, "A06 (Брут)")
    a7_old, a7_new = simple_old_new()
    ok &= patch_one(CEHA / "A07" / "мозг.py", a7_old, a7_new, "A07 (Аван)")
    ok &= patch_one(CEHA / "A08" / "мозг.py", a7_old, a7_new, "A08 (Консерватор)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
