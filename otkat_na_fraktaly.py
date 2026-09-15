# -*- coding: utf-8 -*-
# otkat_na_fraktaly.py — ведение стопа возвращается на фракталы
# («2 фрактала назад»), система «2-3 бара» снимается.
#
# Кладётся в КОРЕНЬ репозитория (рядом с папкой Биржа/). Запуск из
# PowerShell, из корня:
#   python otkat_na_fraktaly.py
#
# Причина (15.09, проверено на истории): на 1500 барах EURUSD H4,
# 17 сравнимых сделок из живых сигналов (Некрон+AO+приседающий),
# фракталы дали +26.5R, «2-3 бара» −3.2R на тех же входах. Разница
# в основном на нескольких длинных ходах — «2-3 бара» подтягивает
# стоп слишком резко и режет прибыль на обычном откате внутри
# хорошего движения (одна сделка: +16.07R фракталами против ровно
# 0 у «2-3 бара», выбитой на 16-м баре). Без пары («пять баров
# одного цвета» на явном рывке) книжная система голой не годится.
#
# Ничего не удаляет. Кладёт рядом копию hooks.py.bak_otkat_fraktaly.
# Запускать можно сколько угодно раз.

import shutil
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent
FAYL = KOREN / "Биржа" / "hooks.py"

BYLO_FUNKTSIYA = '''# ═══════════════════════════════════════════════════════════
# VEDENIE_2_3_BARA_V1 — система «2-3 бара» (Вильямс, уровень новичка)
# ═══════════════════════════════════════════════════════════
# Книга: «Стоп-лосс подтягивается за экстремум (хай/лоу)
# предпоследнего бара (система 2-3 баров) по направлению тренда».
# Без ожидания подтверждения — фракталы для стопа больше не
# используются, они узнаются с задержкой в 2 бара, книга не про это.
#
# Правило «пять баров одного цвета» (стоп вплотную при явном рывке)
# сюда сознательно не входит — отдельный разговор, не сейчас.
#
# Стоп ходит ТОЛЬКО в сторону прибыли — назад никогда.

def _vesti_stopy(md: dict, bars: list) -> int:
    """Подтянуть стопы открытых позиций. Возвращает, сколько сдвинуто.

    Это не решение о сделке, а исполнение правила, которое трейдер
    принял, когда входил. Потому и делается кодом, без вопросов.
    """
    try:
        if not bars or len(bars) < 2:
            return 0
        predposledniy = bars[-2]
        _bar_sym = str((md or {}).get("symbol", "") or "").strip().upper()

        t = load_trading_state()
        sdvinuto = 0
        for pos in (t.get("positions") or []):
            if pos.get("status") not in ("OPEN", "WATCHING"):
                continue
            _psym = (pos.get("symbol") or "").strip().upper()
            if _psym and _bar_sym and _psym != _bar_sym:
                continue          # чужой рынок — не наше дело
            napr = (pos.get("direction") or "").upper()
            stop = pos.get("stop")
            if stop is None:
                continue
            if napr == "LONG":
                novyy = predposledniy.get("low")
                dvigat = novyy is not None and novyy > stop
            elif napr == "SHORT":
                novyy = predposledniy.get("high")
                dvigat = novyy is not None and novyy < stop
            else:
                continue
            if not dvigat:
                continue          # назад стоп не ходит
            pos["stop"] = novyy
            pos["stop_vedyot"] = "2-3 бара (предпоследний)"
            sdvinuto += 1
            print(f"[ВЕДЕНИЕ] ⇢ {napr} {pos.get('entry')} · "
                  f"стоп {stop} → {novyy} (2-3 бара)")
        if sdvinuto:
            save_trading_state(t)
        return sdvinuto
    except Exception as e:
        print(f"[ВЕДЕНИЕ] стопы не подтянулись ({e}) — позиции целы")
        return 0'''

STALO_FUNKTSIYA = '''# ═══════════════════════════════════════════════════════════
# VEDENIE_FRAKTALY_V1 — стоп на два фрактала назад
# ═══════════════════════════════════════════════════════════
# «РЫНОЧНЫЙ ФРАКТАЛ», §4.2: «Стоп-лосс перемещается на уровень,
# расположенный на два фрактала назад в противоположном направлении.
# Это позволяет плыть по течению и защищает прибыль при развороте.»
#
# Ни порогов, ни процентов. Только фракталы, которые и так считаются.
# Стоп ходит ТОЛЬКО в сторону прибыли — назад никогда.

def _vesti_stopy(md: dict) -> int:
    """Подтянуть стопы открытых позиций. Возвращает, сколько сдвинуто.

    Это не решение о сделке, а исполнение правила, которое трейдер
    принял, когда входил. Потому и делается кодом, без вопросов.
    """
    try:
        fr = (md or {}).get("fractals") or {}
        verh = list(fr.get("all_up") or [])
        niz = list(fr.get("all_down") or [])
        _bar_sym = str((md or {}).get("symbol", "") or "").strip().upper()

        t = load_trading_state()
        sdvinuto = 0
        for pos in (t.get("positions") or []):
            if pos.get("status") not in ("OPEN", "WATCHING"):
                continue
            _psym = (pos.get("symbol") or "").strip().upper()
            if _psym and _bar_sym and _psym != _bar_sym:
                continue          # чужой рынок — не наше дело
            napr = (pos.get("direction") or "").upper()
            stop = pos.get("stop")
            if stop is None:
                continue
            # два фрактала назад в ПРОТИВОПОЛОЖНОМ направлении
            if napr == "LONG":
                if len(niz) < 2:
                    continue
                novyy = niz[-2].get("price")
                dvigat = novyy is not None and novyy > stop
            elif napr == "SHORT":
                if len(verh) < 2:
                    continue
                novyy = verh[-2].get("price")
                dvigat = novyy is not None and novyy < stop
            else:
                continue
            if not dvigat:
                continue          # назад стоп не ходит
            pos["stop"] = novyy
            pos["stop_vedyot"] = "два фрактала назад"
            sdvinuto += 1
            print(f"[ВЕДЕНИЕ] ⇢ {napr} {pos.get('entry')} · "
                  f"стоп {stop} → {novyy} (2 фрактала назад)")
        if sdvinuto:
            save_trading_state(t)
        return sdvinuto
    except Exception as e:
        print(f"[ВЕДЕНИЕ] стопы не подтянулись ({e}) — позиции целы")
        return 0'''

BYLO_VYZOV = "    _vesti_stopy(md, bars)\n"
STALO_VYZOV = "    _vesti_stopy(md)\n"


def main() -> int:
    if not FAYL.exists():
        print(f"✗ нет файла {FAYL} — запускать из корня репозитория")
        return 1

    tekst = FAYL.read_text(encoding="utf-8")

    if "def _vesti_stopy(md: dict) -> int:" in tekst:
        print("· уже сделано")
        return 0

    if BYLO_FUNKTSIYA not in tekst:
        print("✗ не нашёл функцию _vesti_stopy (систему «2-3 бара») — "
              "hooks.py мог измениться, скажи Брату, поправим по месту")
        return 1
    if BYLO_VYZOV not in tekst:
        print("✗ не нашёл вызов _vesti_stopy(md, bars) — скажи Брату, "
              "поправим по месту")
        return 1

    tekst = tekst.replace(BYLO_FUNKTSIYA, STALO_FUNKTSIYA, 1)
    tekst = tekst.replace(BYLO_VYZOV, STALO_VYZOV, 1)

    kopiya = FAYL.with_suffix(FAYL.suffix + ".bak_otkat_fraktaly")
    if not kopiya.exists():
        shutil.copy2(FAYL, kopiya)
        print(f"  (копия старого: {kopiya.name})")
    FAYL.write_text(tekst, encoding="utf-8")
    print("✓ ведение стопа вернулось на фракталы («2 фрактала назад»)")
    print()
    print("Перезапусти Кабинет (main.py) — правка кода не подхватится "
          "на лету.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
