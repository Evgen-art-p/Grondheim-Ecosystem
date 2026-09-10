# -*- coding: utf-8 -*-
# VZGLYAD_DOHODIT_V1 — что Шеф показал, то трейдер и видит
"""
КАДР ВЗГЛЯДА ДОХОДИТ ДО ТРЕЙДЕРА

КАК БЫЛО. Кадры ходили в одну сторону. Трейдер сходил рукой — Шеф
это видит (живой кадр, таймер в кабинете). А Шеф нажал «Взгляд»,
выбрал инструмент и этаж — трейдер про это не знает вовсе: в глаза
ему всегда рисуется ЕГО собственная пара.

Отсюда старая беда: Шеф спрашивает про то, что видит сам, трейдер
честно отвечает про своё, и разговор идёт про разные картинки.

ЧТО ДЕЛАЕТ ПАТЧ:

 1. `Биржа/ui_torg.py` — «Взгляд» кладёт свой кадр на общую площадь
    (`vzglyad_shefa`: путь, подпись, время). Экран Шефа при этом
    работает как работал.

 2. Мозги A06/A07/A08 — если Шеф что-то показал, кадр уходит модели
    ВТОРОЙ картинкой, с подписью, чей он. Свой кадр остаётся первым:
    мы не подменяем ему рабочий взгляд, а добавляем показанное.
    Иначе он потеряет свой этаж и начнёт отвечать про чужой.

Показанное живёт 15 минут — дальше считается несвежим и не
досылается: чтобы вчерашняя картинка не всплыла посреди новой
работы.

ТРЕБУЕТ: POVOD_VIDEN_V1 в мозгах (патч встаёт рядом).

БЕЗОПАСНОСТЬ: .bak_vzglyad, идемпотентен, синтаксис до записи,
`--suho` не трогает диск.

    python postavit_vzglyad_dohodit.py --suho
    python postavit_vzglyad_dohodit.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "VZGLYAD_DOHODIT_V1"
SUHO = "--suho" in sys.argv

_REPO = Path(__file__).resolve().parent
TORG = _REPO / "Биржа" / "ui_torg.py"
SLOTY = _REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "слоты"

# ── кабинет: «Взгляд» оставляет след на общей площади ────────
YAKOR_TORG = '''            _t_zk = load_trading_state()
            if _t_zk.get("zhivoy_kadr"):
                _t_zk["zhivoy_kadr"] = {}
                save_trading_state(_t_zk)'''

NOVOE_TORG = '''            _t_zk = load_trading_state()
            if _t_zk.get("zhivoy_kadr"):
                _t_zk["zhivoy_kadr"] = {}
            # VZGLYAD_DOHODIT_V1: то, что Шеф показал, должно дойти и
            # до трейдера — иначе он отвечает про свою картинку, а
            # спрашивают его про эту, и оба правы.
            try:
                from datetime import datetime as _dtv
                _t_zk["vzglyad_shefa"] = {
                    "путь": str(put),
                    "подпись": f"{symbol} {tf}",
                    "когда": _dtv.now().isoformat(timespec="seconds"),
                }
            except Exception:
                pass
            save_trading_state(_t_zk)'''

# ── мозг: досылаем показанное вторым ─────────────────────────
MESTA_MOZGA = [
    ('                    images=[{"base64": base64.b64encode(\n                                 _P(put).read_bytes()).decode("ascii"),\n                              "mime_type": "image/png",\n                              "name": _P(put).name}],\n',
     '                    images=([{"base64": base64.b64encode(\n                                 _P(put).read_bytes()).decode("ascii"),\n                              "mime_type": "image/png",\n                              "name": _P(put).name}]\n                            + _kadr_shefa()),\n'),
    ('                    images=[{"base64": base64.b64encode(\n                                 _P(put).read_bytes()).decode("ascii"),\n                             "mime_type": "image/png",\n                             "name": _P(put).name}],\n',
     '                    images=([{"base64": base64.b64encode(\n                                 _P(put).read_bytes()).decode("ascii"),\n                             "mime_type": "image/png",\n                             "name": _P(put).name}]\n                            + _kadr_shefa()),\n'),
]

TELO = '''

# ── VZGLYAD_DOHODIT_V1: кадр, который показал Шеф ─────────────
# Свой кадр у трейдера остаётся ПЕРВЫМ — рабочий взгляд не
# подменяем. Показанное идёт вторым, с подписью, чьё оно. Иначе он
# потеряет свой этаж и станет отвечать про чужую картинку.

def _kadr_shefa() -> list:
    """Картинка со «Взгляда» Шефа, если она свежая. Иначе пусто."""
    try:
        import base64
        from datetime import datetime, timedelta
        from pathlib import Path as _P
        from hooks import load_trading_state
        v = (load_trading_state() or {}).get("vzglyad_shefa") or {}
        put = v.get("путь")
        if not put:
            return []
        try:
            kogda = datetime.fromisoformat(str(v.get("когда")))
            if datetime.now() - kogda > timedelta(minutes=15):
                return []      # старое — не всплывает посреди работы
        except Exception:
            pass
        p = _P(put)
        if not p.exists():
            return []
        print(f"[ВЗГЛЯД] Шеф показывает: {v.get('подпись', '')}")
        return [{"base64": base64.b64encode(
                     p.read_bytes()).decode("ascii"),
                 "mime_type": "image/png",
                 "name": f"показал Шеф · {v.get('подпись', '')}"}]
    except Exception as _e:
        print(f"[ВЗГЛЯД] кадр Шефа не подложился ({_e}) — не беда")
        return []


# VZGLYAD_DOHODIT_V1 - marker
'''


def _pravka_torg() -> int:
    if not TORG.exists():
        print("  ui_torg.py: файла нет")
        return 0
    txt = TORG.read_text(encoding="utf-8")
    if MARKER in txt:
        print("  ui_torg.py: уже стоит")
        return 0
    if txt.count(YAKOR_TORG) != 1:
        print(f"  ui_torg.py: ОТКАЗ — якорь встречается "
              f"{txt.count(YAKOR_TORG)} раз(а)")
        return 0
    novy = txt.replace(YAKOR_TORG, NOVOE_TORG, 1)
    try:
        ast.parse(novy)
    except SyntaxError as e:
        print(f"  ui_torg.py: ОТКАЗ — синтаксис сломан ({e})")
        return 0
    if not SUHO:
        shutil.copy2(TORG, TORG.with_suffix(".py.bak_vzglyad"))
        TORG.write_text(novy, encoding="utf-8")
    print(f"  ui_torg.py: {'готов' if SUHO else 'поправлен'}")
    return 1


def _pravka_mozga(slot: str) -> int:
    p = SLOTY / slot / "мозг.py"
    if not p.exists():
        print(f"  {slot}/мозг.py: файла нет")
        return 0
    txt = p.read_text(encoding="utf-8")
    if MARKER in txt:
        print(f"  {slot}/мозг.py: уже стоит")
        return 0
    novy, n = txt, 0
    for staroe, novoe in MESTA_MOZGA:
        if staroe in novy:
            novy = novy.replace(staroe, novoe)
            n += 1
    if not n:
        print(f"  {slot}/мозг.py: ОТКАЗ — места отправки картинки не нашёл")
        return 0
    novy = novy.rstrip("\n") + "\n" + TELO
    try:
        ast.parse(novy)
    except SyntaxError as e:
        print(f"  {slot}/мозг.py: ОТКАЗ — синтаксис сломан ({e})")
        return 0
    if not SUHO:
        shutil.copy2(p, p.with_suffix(".py.bak_vzglyad"))
        p.write_text(novy, encoding="utf-8")
    print(f"  {slot}/мозг.py: {'готов' if SUHO else 'поправлен'} "
          f"({n} мест(а) отправки)")
    return 1


def main():
    print()
    print("ВЗГЛЯД ДОХОДИТ" + ("  · СУХОЙ ПРОГОН" if SUHO else ""))
    print("корень:", _REPO)
    print()
    print("1. КАБИНЕТ — «Взгляд» оставляет след:")
    vsego = _pravka_torg()
    print()
    print("2. МОЗГИ — показанное доходит вторым кадром:")
    if not SLOTY.exists():
        print("  слотов нет — запускать из корня репы")
    else:
        for s in ("A06", "A07", "A08"):
            vsego += _pravka_mozga(s)
    print()
    if SUHO:
        print("Сухой прогон: на диске ничего не изменилось.")
    else:
        print(f"Тронуто файлов: {vsego}. Бэкапы — .bak_vzglyad")
    print("Теперь кадры ходят в обе стороны.")
    print()


if __name__ == "__main__":
    main()
