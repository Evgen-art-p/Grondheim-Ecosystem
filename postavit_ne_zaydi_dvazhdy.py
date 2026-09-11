# -*- coding: utf-8 -*-
# NE_ZAYDI_DVAZHDY_V1
"""
ПОКА ЗАЯВКА ВИСИТ — ВТОРОЙ РАЗ НЕ ВХОДЯТ

ПРОГОН 12.09. Трейдер вошёл в 06:00 — LONG по 1.04205. В 07:00 его
разбудили поводом «своя PENDING — заявка ещё висит», и он... вошёл
снова. Тем же ENTER, теми же ценой и стопом. В 08:00 опять. В 09:00
опять. Позиций стало четыре вместо одной.

ВИНОВАТ НЕ ОН. Ему сообщают, что заявка висит, — и больше ничего: ни
стороны, ни цены, ни стопа. Он смотрит на график заново, видит три
части, и честно входит по нашему же правилу «сошлись — окружай».
Откуда ему знать, что окружено уже четырежды.

ЧТО ДЕЛАЕТ ПАТЧ, две вещи.

 1. ОН ВИДИТ, ЧТО У НЕГО ЕСТЬ. В первом сообщении, сразу за поводом,
    появляется строка про своё: сторона, цена входа, стоп, состояние
    (висит заявка или позиция открыта). Раньше этого не было вовсе.

 2. РУКА НЕ ПРИНИМАЕТ ВТОРОЙ ВХОД. Есть своя заявка или позиция —
    ENTER отбивается, как отбивается вход без стопа. С объяснением:
    у тебя уже есть вот это, теперь можно держать, двигать стоп,
    доливать или закрывать.

Уговоры мы уже пробовали — не работают. Здесь то же решение, что с
приказом: не запрет на словах, а устройство.

ДОЛИВ ОСТАЁТСЯ. Добавить к позиции по-прежнему можно — но приказом
ADD, который для этого и есть. Это разные вещи, и теперь они
различаются.

КУДА КЛАСТЬ ЭТОТ ФАЙЛ: в корень репы, рядом с main.py.

БЕЗОПАСНОСТЬ: .bak_dvazhdy, идемпотентен, синтаксис до записи,
`--suho` не трогает диск.

    python postavit_ne_zaydi_dvazhdy.py --suho
    python postavit_ne_zaydi_dvazhdy.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "NE_ZAYDI_DVAZHDY_V1"
SUHO = "--suho" in sys.argv

_REPO = Path(__file__).resolve().parent
RUKI = _REPO / "Биржа" / "ruki_treydera.py"
SLOTY = _REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "слоты"

# ── 1. рука не принимает второй вход ─────────────────────────
STAROE_RUKI = '''        if chto == "ENTER":
            net = []'''

NOVOE_RUKI = '''        if chto == "ENTER":
            # NE_ZAYDI_DVAZHDY_V1: своё уже есть — второй ENTER не
            # принимаем. 12.09 трейдер вошёл четыре раза подряд в одно
            # место: его будили «заявка висит», а он разбирал график
            # заново и честно входил по правилу «сошлись — окружай».
            _moyo = _chto_u_menya_est()
            if _moyo:
                return ("Приказ НЕ отдан: у тебя УЖЕ есть " + _moyo +
                        ". Второй раз в то же место не входят. Сейчас "
                        "можно: HOLD — держать, MOVE_STOP — подвинуть "
                        "стоп, ADD — долить к этой же позиции, "
                        "CLOSE — закрыть.")
            net = []'''

TELO_RUKI = '''

    def _chto_u_menya_est() -> str:
        """NE_ZAYDI_DVAZHDY_V1: своя заявка или позиция — словами.

        Пусто — значит руки свободны и входить можно.
        """
        try:
            from hooks import load_trading_state as _lts
            _t = _lts() or {}
            for _p in (_t.get("positions") or []):
                if str(_p.get("symbol", "")).strip().upper() != \\
                        str(symbol).strip().upper():
                    continue
                _st = str(_p.get("status") or "").upper()
                if _st not in ("OPEN", "PENDING"):
                    continue
                _kto = str(_p.get("slot") or _p.get("agent") or "")
                if _kto and _kto.upper() != str(slot).upper():
                    continue
                _n = str(_p.get("direction") or "?").upper()
                _c = _p.get("entry")
                _s = _p.get("stop")
                _chto = ("позиция" if _st == "OPEN" else "висящая заявка")
                return (f"{_chto}: {_n} {symbol}"
                        + (f" по {_c}" if _c else "")
                        + (f", стоп {_s}" if _s else ""))
        except Exception as _e:
            print(f"[РУКА] своё не спросилось ({_e}) — пропускаю приказ")
        return ""
'''

# ── 2. мозг показывает своё в первом сообщении ───────────────
STAROE_MOZG = '''def _povod_blok(povod: str) -> str:'''

NOVOE_MOZG = '''def _svoyo_blok() -> str:
    """NE_ZAYDI_DVAZHDY_V1: что у меня уже есть.

    Раньше трейдеру говорили только «заявка ещё висит» — без стороны,
    цены и стопа. Он разбирал график заново и входил снова: за один
    час четыре одинаковых входа. Теперь видит своё первым делом.
    """
    try:
        from hooks import load_trading_state as _lts
        _t = _lts() or {}
        _moi = []
        for _p in (_t.get("positions") or []):
            _st = str(_p.get("status") or "").upper()
            if _st not in ("OPEN", "PENDING"):
                continue
            _n = str(_p.get("direction") or "?").upper()
            _c = _p.get("entry")
            _s = _p.get("stop")
            _moi.append(("ПОЗИЦИЯ ОТКРЫТА" if _st == "OPEN"
                         else "ЗАЯВКА ВИСИТ")
                        + f": {_n} {_p.get('symbol', '')}"
                        + (f" по {_c}" if _c else "")
                        + (f", стоп {_s}" if _s else ""))
        if not _moi:
            return ""
        return ("=== ЧТО У ТЕБЯ УЖЕ ЕСТЬ ===\\n"
                + "\\n".join(_moi)
                + "\\nВходить второй раз в то же место НЕ НАДО — рука "
                  "такой приказ и не примет. Твоя работа сейчас: "
                  "держать (HOLD), двигать стоп (MOVE_STOP), доливать "
                  "(ADD) или закрывать (CLOSE).\\n\\n")
    except Exception as _e:
        print(f"[СВОЁ] не спросилось ({_e})")
        return ""


def _povod_blok(povod: str) -> str:'''

STAROE_VYZOV = '''        + _povod_blok(povod)      # POVOD_VIDEN_V1'''
NOVOE_VYZOV = '''        + _povod_blok(povod)      # POVOD_VIDEN_V1
        + _svoyo_blok()           # NE_ZAYDI_DVAZHDY_V1'''


def _pravka_mozga(slot: str) -> int:
    p = SLOTY / slot / "мозг.py"
    if not p.exists():
        print(f"  {slot}: файла нет")
        return 0
    txt = p.read_text(encoding="utf-8")
    if MARKER in txt:
        print(f"  {slot}: уже стоит")
        return 0
    if "POVOD_VIDEN_V1" not in txt:
        print(f"  {slot}: ОТКАЗ — сперва postavit_povod_vzglyada.py")
        return -1
    novy = txt
    for imya, st, nv in (("блок «своё»", STAROE_MOZG, NOVOE_MOZG),
                         ("вызов в сообщении", STAROE_VYZOV, NOVOE_VYZOV)):
        if novy.count(st) != 1:
            print(f"  {slot}: ОТКАЗ на «{imya}» — {novy.count(st)} совпадений")
            return 0
        novy = novy.replace(st, nv, 1)
    novy = novy.rstrip("\n") + f"\n\n# {MARKER} - marker\n"
    try:
        ast.parse(novy)
    except SyntaxError as e:
        print(f"  {slot}: ОТКАЗ — синтаксис сломан ({e})")
        return 0
    if not SUHO:
        shutil.copy2(p, p.with_suffix(".py.bak_dvazhdy"))
        p.write_text(novy, encoding="utf-8")
    print(f"  {slot}: {'готов' if SUHO else 'поправлен'}")
    return 1


def main():
    print()
    print("НЕ ЗАЙДИ ДВАЖДЫ" + ("  · СУХОЙ ПРОГОН" if SUHO else ""))
    print("корень:", _REPO)
    print()

    vsego = 0
    print("1. РУКА — не принимает второй вход:")
    if not RUKI.exists():
        print("  ruki_treydera.py: файла нет")
    else:
        txt = RUKI.read_text(encoding="utf-8")
        if MARKER in txt:
            print("  ruki_treydera.py: уже стоит")
        elif txt.count(STAROE_RUKI) != 1:
            print(f"  ruki_treydera.py: ОТКАЗ — якорь встречается "
                  f"{txt.count(STAROE_RUKI)} раз(а)")
        else:
            novy = txt.replace(STAROE_RUKI, NOVOE_RUKI, 1)
            # тело кладём РЯДОМ с _otdat, внутрь _ruka_prikaza_ruki:
            # в соседней области видимости его не видно — проверено
            # на живом файле, NameError на первом же приказе.
            yakor = "    def _otdat(args: dict) -> str:"
            if novy.count(yakor) != 1:
                print(f"  ruki_treydera.py: ОТКАЗ — не нашёл _otdat "
                      f"({novy.count(yakor)} совпадений)")
                return
            novy = novy.replace(yakor, TELO_RUKI.strip("\n") +
                                "\n\n" + yakor, 1)
            try:
                ast.parse(novy)
                if not SUHO:
                    shutil.copy2(RUKI, RUKI.with_suffix(".py.bak_dvazhdy"))
                    RUKI.write_text(novy, encoding="utf-8")
                print(f"  ruki_treydera.py: {'готов' if SUHO else 'поправлен'}")
                vsego += 1
            except SyntaxError as e:
                print(f"  ruki_treydera.py: ОТКАЗ — синтаксис ({e})")

    print()
    print("2. МОЗГИ — он видит, что у него есть:")
    if not SLOTY.exists():
        print("  слотов нет")
    else:
        for s in ("A06", "A07", "A08"):
            r = _pravka_mozga(s)
            if r < 0:
                return
            vsego += r

    print()
    if SUHO:
        print("Сухой прогон: на диске ничего не изменилось.")
    else:
        print(f"Тронуто файлов: {vsego}. Бэкапы — .bak_dvazhdy")
    print("Своё видно, второй вход не проходит. Долив — приказом ADD.")
    print()


if __name__ == "__main__":
    main()
