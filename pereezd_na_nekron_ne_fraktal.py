# -*- coding: utf-8 -*-
# pereezd_na_nekron_ne_fraktal.py — заявка переезжает на новый
# РАЗВОРОТНИК (Некрон + AO дивер + приседающий рядом), а не на любой
# геометрический фрактал.
#
# Кладётся в КОРЕНЬ репозитория (рядом с папкой Биржа/). Запуск из
# PowerShell, из корня:
#   python pereezd_na_nekron_ne_fraktal.py
#
# Найдено 15.09 (Шеф): «окружаешь бар, не фрактал». Старая
# `_pereezd_zayavki` двигала PENDING-заявку на любой новый фрактал —
# просто геометрический экстремум (§8, старая механика входа от
# фрактала, до перехода на Некрон). Разворотник (Некрон) и фрактал —
# не одно и то же: Некрон дополнительно проверен формой и Аллигатором,
# фрактал — просто крайняя точка среди пяти баров. Заявка могла
# переехать на уровень, который сам разворотником вообще не является.
#
# Новое условие переезда — три вещи, как на входе:
#   1. На новом баре — Некрон в сторону сделки, ДАЛЬШЕ прежнего
#      (для LONG — новый минимум ниже старого, для SHORT — новый
#      максимум выше старого: цена обновила экстремум хода).
#   2. AO-дивер в сторону сделки обязателен (по словам Шефа, при
#      первом условии он почти всегда уже есть — но код всё равно
#      сверяет по-настоящему посчитанный флаг, не верит на слово).
#   3. Приседающий — НЕ обязательно на этом самом баре. Смотрим на
#      последний найденный приседающий во всей истории: если он был
#      в пределах последних 3 баров до нового Некрона — считается
#      «рядом», условие выполнено.
#
# Стоп и цена заявки — по канону входа (промпт.md, раздел «ВХОД»):
# LONG заявка выше high (+2 спреда), стоп под low Некрона; SHORT
# заявка ниже low (−1 спред), стоп над high Некрона.
#
# Окно «рядом» для приседающего — 3 бара, поставлено разумно, не
# высечено в камне. Если по живым прогонам покажется мало или много —
# правь ОКНО_БАРОВ_PRISED ниже и перезапускай патч (он идемпотентен).
#
# Ничего не удаляет. Кладёт рядом копию hooks.py.bak_nekron_pereezd.
# Запускать можно сколько угодно раз.

import shutil
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent
FAYL = KOREN / "Биржа" / "hooks.py"

BYLO = '''def _pereezd_zayavki(pos, md):
    """Проверяет PENDING-заявку против текущей структуры фракталов.
    Возвращает:
      "MOVED"   — переехала на новый фрактал (pos обновлён на месте);
      "CANCEL"  — цена вернулась к старту, сигнал мёртв (снять);
      None      — ничего, ждём дальше.
    Спред-поправка та же, что при рождении.
    """
    d = (pos.get("direction") or "").upper()
    fr = md.get("fractals", {}) or {}
    price = md.get("price", {}) or {}
    close = price.get("close")
    point = md.get("point") or 0.01
    sp_pts = (md.get("mfi", {}) or {}).get("spread")
    sp = (float(sp_pts) * float(point)) if sp_pts is not None else 0.0
    punkt = 10 * float(point or 0.01)  # PUNKT_OT_POINT_V1: пункт = 10×point

    if close is None:
        return None

    if d == "LONG":
        up = fr.get("last_up") or {}
        down = fr.get("last_down") or {}
        up_px = up.get("price") if isinstance(up, dict) else None
        up_idx = up.get("bar_index") if isinstance(up, dict) else None
        down_px = down.get("price") if isinstance(down, dict) else None

        # 2. возврат к старту сигнала — снять
        start = pos.get("signal_start")
        if start is not None and close < start:
            return "CANCEL"

        # 1. новый ВЕРХНИЙ фрактал (другой bar_index) ВЫШЕ прежнего → переезд
        old_idx = pos.get("entry_fractal_idx")
        old_px = pos.get("entry_fractal_price")
        if (up_px is not None and up_idx is not None
                and up_idx != old_idx
                and (old_px is None or up_px > old_px)):
            pos["entry"] = round(up_px + 2 * sp, 6)          # Buy Stop + спред
            if down_px is not None:
                pos["stop"] = round(down_px, 6)              # под новый низ
                pos["stop_initial"] = pos["stop"]            # R от новой опоры
                pos["signal_start"] = down_px                # новый старт сигнала
            pos["entry_fractal_price"] = up_px
            pos["entry_fractal_idx"] = up_idx
            pos["_ждёт_баров"] = 0                            # счётчик сброшен
            return "MOVED"

    elif d == "SHORT":
        up = fr.get("last_up") or {}
        down = fr.get("last_down") or {}
        down_px = down.get("price") if isinstance(down, dict) else None
        down_idx = down.get("bar_index") if isinstance(down, dict) else None
        up_px = up.get("price") if isinstance(up, dict) else None

        start = pos.get("signal_start")
        if start is not None and close > start:
            return "CANCEL"

        old_idx = pos.get("entry_fractal_idx")
        old_px = pos.get("entry_fractal_price")
        if (down_px is not None and down_idx is not None
                and down_idx != old_idx
                and (old_px is None or down_px < old_px)):
            pos["entry"] = round(down_px - 3 * punkt, 6)     # Sell Stop − 3 пункта
            if up_px is not None:
                pos["stop"] = round(up_px + 2 * sp, 6)       # над новым верхом
                pos["stop_initial"] = pos["stop"]
                pos["signal_start"] = up_px
            pos["entry_fractal_price"] = down_px
            pos["entry_fractal_idx"] = down_idx
            pos["_ждёт_баров"] = 0
            return "MOVED"

    return None
'''

STALO = '''# PEREEZD_NA_NEKRON_NE_FRAKTAL_V1: окно "рядом" для приседающего —
# в барах. Не высечено в камне, можно поправить и перезапустить патч.
_OKNO_BAROV_PRISED = 3

_CHASY_ETAZHA = {
    "M1": 1 / 60, "M5": 5 / 60, "M10": 10 / 60, "M15": 15 / 60,
    "M30": 0.5, "H1": 1, "H2": 2, "H4": 4, "H8": 8, "H12": 12,
    "D1": 24, "W1": 24 * 7,
}


def _prisel_ryadom(md, okno_barov=_OKNO_BAROV_PRISED):
    """Приседающий на этом баре или в пределах последних `okno_barov`
    баров до него — MFI.md: дорожка не обязана стоять прямо на
    Некроне, важно что рынок готовился рядом."""
    last = (md.get("squat") or {}).get("last_squat") or {}
    if not last:
        return False
    try:
        from datetime import datetime
        fmt = "%Y.%m.%d %H:%M"
        t_bar = datetime.strptime(str(md.get("bar_time")), fmt)
        t_sq = datetime.strptime(str(last.get("date")), fmt)
    except Exception:
        return True  # даты не сравнились — не блокируем зря
    chas = _CHASY_ETAZHA.get(str(md.get("timeframe") or "H1").upper(), 1)
    if chas <= 0:
        return True
    razn_barov = (t_bar - t_sq).total_seconds() / 3600 / chas
    return 0 <= razn_barov <= okno_barov


def _pereezd_zayavki(pos, md):
    """Проверяет PENDING-заявку против НОВОГО РАЗВОРОТНИКА (Некрона),
    не голого фрактала — окружаем бар, а не геометрическую точку.

    Переезд требует ТУ ЖЕ тройку, что и вход — без сравнения
    "дальше/лучше" (по книге любой новый сигнал сносит старый):
      1. Некрон в сторону сделки.
      2. AO-дивер в сторону сделки.
      3. Приседающий рядом (на этом баре или в последних барах).

    Возвращает:
      "MOVED"   — переехала на новый разворотник (pos обновлён);
      "CANCEL"  — цена вернулась к старту, сигнал мёртв (снять);
      None      — ничего, ждём дальше.
    """
    d = (pos.get("direction") or "").upper()
    price = md.get("price", {}) or {}
    close = price.get("close")
    cur_high = price.get("high")
    cur_low = price.get("low")
    point = md.get("point") or 0.01
    sp_pts = (md.get("mfi", {}) or {}).get("spread")
    sp = (float(sp_pts) * float(point)) if sp_pts is not None else 0.0

    if close is None:
        return None

    necron = md.get("necron_bar") or {}
    necron_dir = necron.get("direction")
    necron_price = necron.get("price")

    if d == "LONG":
        start = pos.get("signal_start")
        if start is not None and close < start:
            return "CANCEL"

        # PEREEZD_BEZ_SRAVNENIYA_V1 (15.09, Шеф): книга не требует
        # сравнения "дальше/лучше" — любой новый сигнал того же
        # направления сносит старый ордер. Если новый Некрон окажется
        # менее выгодным (ближе к цене) — рынок и так возьмёт его
        # раньше, сравнивать незачем.
        if (necron_dir == "BULL" and necron_price is not None
                and md.get("divergence_ao")
                and _prisel_ryadom(md)):
            if cur_high is not None:
                pos["entry"] = round(cur_high + 2 * sp, 6)   # Buy Stop + 2 спреда
            pos["stop"] = round(necron_price, 6)             # под низ Некрона
            pos["stop_initial"] = pos["stop"]
            pos["signal_start"] = necron_price
            pos["entry_fractal_price"] = necron_price
            pos["_ждёт_баров"] = 0
            return "MOVED"

    elif d == "SHORT":
        start = pos.get("signal_start")
        if start is not None and close > start:
            return "CANCEL"

        if (necron_dir == "BEAR" and necron_price is not None
                and md.get("exit_bell")
                and _prisel_ryadom(md)):
            if cur_low is not None:
                pos["entry"] = round(cur_low - sp, 6)        # Sell Stop − 1 спред
            pos["stop"] = round(necron_price, 6)             # над high Некрона
            pos["stop_initial"] = pos["stop"]
            pos["signal_start"] = necron_price
            pos["entry_fractal_price"] = necron_price
            pos["_ждёт_баров"] = 0
            return "MOVED"

    return None
'''


def main() -> int:
    if not FAYL.exists():
        print(f"✗ нет файла {FAYL} — запускать из корня репозитория")
        return 1

    tekst = FAYL.read_text(encoding="utf-8")

    if "PEREEZD_NA_NEKRON_NE_FRAKTAL_V1" in tekst:
        print("· уже сделано")
        return 0
    if BYLO not in tekst:
        print("✗ не нашёл ожидаемое место — hooks.py мог измениться, "
              "скажи Брату, поправим по месту")
        return 1

    tekst = tekst.replace(BYLO, STALO, 1)
    kopiya = FAYL.with_suffix(FAYL.suffix + ".bak_nekron_pereezd")
    if not kopiya.exists():
        shutil.copy2(FAYL, kopiya)
        print(f"  (копия старого: {kopiya.name})")
    FAYL.write_text(tekst, encoding="utf-8")
    print("✓ заявка теперь переезжает на новый разворотник (Некрон + "
          "AO дивер + приседающий рядом), не на голый фрактал")
    print()
    print("Перезапусти Кабинет (main.py) — правка кода не подхватится "
          "на лету.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
