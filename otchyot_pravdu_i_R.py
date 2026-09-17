# -*- coding: utf-8 -*-
# otchyot_pravdu_i_R.py — отчёт перестаёт врать и показывает R.
#
# Кладётся в КОРЕНЬ репозитория, рядом с main.py.
# Запуск из PowerShell, из корня:
#     python otchyot_pravdu_i_R.py
#
# ═══ ПОЛОМКА ПЕРВАЯ: «ВОШЁЛ» ТАМ, ГДЕ НЕ ВХОДИЛА ═══
#
# В подписи места проверка ВЕРДИКТА стояла ПЕРЕД проверкой ДЕЙСТВИЯ.
# А вердикт APPROVED город ставит на любой принятый приказ — и на
# HOLD, и на MOVE_STOP. Значит ведение подписывалось как вход.
#
# Живой пример из прогона 17.09:
#   №23 08:00 «выставил отложенный SHORT»        → настоящий вход
#   №24 12:00 «сделку не трогаю»                 → HOLD, а подписан «ВОШЁЛ»
#   №25 30.01 «подтягиваю стоп за этот фрактал»  → MOVE_STOP, тоже «ВОШЁЛ»
#
# Одна сделка — три строки «ВОШЁЛ @ 1.08926». Шеф читал отчёт и не
# понимал, почему открыт новый вход при незакрытом старом. Нового
# входа не было: отчёт соврал.
#
# Отсюда же расхождение в счёте: 19 «входов» при 15 сделках.
#
# Чинится перестановкой: сперва действие, потом вердикт.
#
# ═══ ПОЛОМКА ВТОРАЯ: НЕТ ПОКАЗАТЕЛЕЙ ═══
#
# В отчёте только текст. Ни результата сделки, ни R. Проверить её
# слова числом нельзя — только поверить или не поверить.
#
# А числа есть: город считает pnl_r при каждом закрытии и кладёт в
# журнал trading_pnl.jsonl. Отчёт туда не заглядывал.
#
# ═══ ЧТО СТАВИМ ═══
#
# 1. Подпись чинится: ведение больше не входит.
# 2. У каждого входа рядом с ценой и стопом встаёт ЕГО R и чем
#    кончилось — стоп, колокол или вручную.
# 3. В шапке — ИТОГ: сделок, в плюс, в минус, общий R и средний R.
#
# R берётся из журнала по цене входа. Сделка ещё открыта или журнала
# нет — пишем «в работе», ничего не выдумывая.
#
# ЧЕГО НЕ ДЕЛАЕТ. Торговли не касается вовсе. Это страница отчёта:
# ни одного правила, ни одной цены, ни одного решения не меняется.
#
# БЕЗОПАСНО. Проверяет ast.parse. Рядом кладёт ui_otchyot.py.bak_pravda.
# Запускать можно сколько угодно раз.

import ast
import shutil
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent
MARKER = "OTCHYOT_PRAVDU_I_R_V1"

# ── 1. подпись: действие раньше вердикта ──
STAROE_1 = (
    'def _chto_sdelal(m: dict) -> tuple:\n'
    '    """(метка, цвет) — вошёл, ведёт, отказался или промолчал."""\n'
    '    d = str(m.get("действие") or "").upper()\n'
    '    v = str(m.get("вердикт") or "").upper()\n'
    '    if d == "ENTER" or v in ("APPROVED", "ENTER", "OK"):\n'
)
NOVOE_1 = (
    'def _chto_sdelal(m: dict) -> tuple:\n'
    '    """(метка, цвет) — вошёл, ведёт, отказался или промолчал."""\n'
    '    d = str(m.get("действие") or "").upper()\n'
    '    v = str(m.get("вердикт") or "").upper()\n'
    '    # OTCHYOT_PRAVDU_I_R_V1: ДЕЙСТВИЕ СМОТРИМ ПЕРВЫМ. Раньше\n'
    '    # вердикт стоял раньше — а APPROVED город ставит на ЛЮБОЙ\n'
    '    # принятый приказ, и HOLD с MOVE_STOP подписывались как\n'
    '    # «ВОШЁЛ». Одна сделка давала три строки «ВОШЁЛ @ …», и\n'
    '    # выходило, будто открыт новый вход при незакрытом старом.\n'
    '    if d in ("HOLD", "MOVE_STOP", "ADD", "CLOSE"):\n'
    '        return {"HOLD": "ДЕРЖУ", "MOVE_STOP": "СТОП ПЕРЕНЁС",\n'
    '                "ADD": "ДОЛИЛ", "CLOSE": "ЗАКРЫЛ"}[d], "#4d9bff"\n'
    '    if d == "WAIT":\n'
    '        return "ОТКАЗ", "#ffb454"\n'
    '    if d == "ENTER" or v in ("APPROVED", "ENTER", "OK"):\n'
)

# ── 2. журнал закрытий и R места ──
STAROE_2 = (
    'def _chto_sdelal(m: dict) -> tuple:\n'
)
NOVOE_2 = (
    '# ── OTCHYOT_PRAVDU_I_R_V1: результат сделки числом ──\n'
    '# Город считает pnl_r при каждом закрытии и кладёт в журнал\n'
    '# trading_pnl.jsonl. Отчёт туда не заглядывал — оттого в нём был\n'
    '# один текст и ни одного показателя.\n'
    '\n'
    '_ZHURNAL: dict = {}\n'
    '\n'
    '\n'
    'def _zhurnal_zakrytiy() -> dict:\n'
    '    """Закрытия по цене входа: {цена: запись}. Читается один раз."""\n'
    '    if _ZHURNAL:\n'
    '        return _ZHURNAL\n'
    '    try:\n'
    '        import json as _js\n'
    '        from hooks import PNL_PATH\n'
    '        p = Path(PNL_PATH)\n'
    '        if not p.exists():\n'
    '            _ZHURNAL["_"] = None\n'
    '            return _ZHURNAL\n'
    '        with open(p, encoding="utf-8") as f:\n'
    '            for stroka in f:\n'
    '                stroka = stroka.strip()\n'
    '                if not stroka:\n'
    '                    continue\n'
    '                try:\n'
    '                    z = _js.loads(stroka)\n'
    '                except Exception:\n'
    '                    continue\n'
    '                vh = z.get("entry")\n'
    '                if isinstance(vh, (int, float)):\n'
    '                    _ZHURNAL[round(float(vh), 5)] = z\n'
    '    except Exception as e:\n'
    '        print(f"[ОТЧЁТ] журнал закрытий не прочитался: {e}")\n'
    '        _ZHURNAL["_"] = None\n'
    '    return _ZHURNAL\n'
    '\n'
    '\n'
    'ПО_РУССКИ_ЗАКРЫТИЕ = {"STOP_LOSS": "стоп", "EXIT_BELL": "колокол",\n'
    '                      "MANUAL_CLOSE": "закрыла сама"}\n'
    '\n'
    '\n'
    'def _itog_mesta(m: dict):\n'
    '    """(R числом или None, словами) для места-входа."""\n'
    '    c = m.get("цена_входа")\n'
    '    if not isinstance(c, (int, float)):\n'
    '        return None, ""\n'
    '    z = _zhurnal_zakrytiy().get(round(float(c), 5))\n'
    '    if not z:\n'
    '        return None, "в работе"\n'
    '    r = z.get("pnl_r")\n'
    '    chem = ПО_РУССКИ_ЗАКРЫТИЕ.get(str(z.get("close_reason")), "?")\n'
    '    if isinstance(r, (int, float)):\n'
    '        return float(r), f"{float(r):+.2f}R · {chem}"\n'
    '    return None, f"R не посчитан · {chem}"\n'
    '\n'
    '\n'
    'def _chto_sdelal(m: dict) -> tuple:\n'
)

# ── 3. R у карточки места ──
STAROE_3 = (
    '                    f\'<span style="color:{cvet}; font-weight:700; \'\n'
    "                    f'font-size:0.82rem;\">{metka}</span></div>')\n"
)
NOVOE_3 = (
    '                    f\'<span style="color:{cvet}; font-weight:700; \'\n'
    "                    f'font-size:0.82rem;\">{metka}</span>'\n"
    '                    # OTCHYOT_PRAVDU_I_R_V1: чем кончилась ЭТА сделка.\n'
    '                    + _itog_kuskom(m) + \'</div>\')\n'
)

STAROE_4 = (
    'def _kartochka(ceh: str, papka: Path, nomer: int, m: dict):\n'
)
NOVOE_4 = (
    'def _itog_kuskom(m: dict) -> str:\n'
    '    """OTCHYOT_PRAVDU_I_R_V1: кусок разметки с результатом сделки."""\n'
    '    d = str(m.get("действие") or "").upper()\n'
    '    v = str(m.get("вердикт") or "").upper()\n'
    '    if not (d == "ENTER" or (d not in ("HOLD", "MOVE_STOP", "ADD",\n'
    '                                       "CLOSE", "WAIT")\n'
    '                             and v in ("APPROVED", "ENTER", "OK"))):\n'
    '        return ""\n'
    '    r, slovami = _itog_mesta(m)\n'
    '    if not slovami:\n'
    '        return ""\n'
    '    c = "#7c8b99" if r is None else ("#3ddc6b" if r > 0 else "#ff5c5c")\n'
    '    return (f\'<span style="color:{c}; font-weight:700; \'\n'
    '            f\'font-size:0.82rem;">{slovami}</span>\')\n'
    '\n'
    '\n'
    'def _kartochka(ceh: str, papka: Path, nomer: int, m: dict):\n'
)

# ── 4. итог в шапке ──
STAROE_5 = (
    "            + f'<span style=\"color:#ff5c5c;\">без приказа: '\n"
    '              f\'<b>{schet["БЕЗ ПРИКАЗА"]}</b></span>\'\n'
    "            + '</div>')\n"
)
NOVOE_5 = (
    "            + f'<span style=\"color:#ff5c5c;\">без приказа: '\n"
    '              f\'<b>{schet["БЕЗ ПРИКАЗА"]}</b></span>\'\n'
    "            + '</div>')\n"
    '\n'
    '        # OTCHYOT_PRAVDU_I_R_V1: ИТОГ ПО СДЕЛКАМ. Раньше отчёт не\n'
    '        # давал ни одного показателя — только текст.\n'
    '        _ry = []\n'
    '        for _m in mesta:\n'
    '            _r, _ = _itog_mesta(_m)\n'
    '            if _r is not None:\n'
    '                _ry.append(_r)\n'
    '        if _ry:\n'
    '            _pl = [x for x in _ry if x > 0]\n'
    '            _mi = [x for x in _ry if x < 0]\n'
    '            _obshchiy = sum(_ry)\n'
    '            _sredniy = _obshchiy / len(_ry)\n'
    '            _c_ob = "#3ddc6b" if _obshchiy > 0 else "#ff5c5c"\n'
    '            _c_sr = "#3ddc6b" if _sredniy > 0 else "#ff5c5c"\n'
    '            ui.html(\n'
    '                \'<div style="margin-top:8px; padding-top:8px; \'\n'
    '                \'border-top:1px solid rgba(255,255,255,0.08); \'\n'
    '                \'display:flex; gap:18px; flex-wrap:wrap; \'\n'
    '                \'font-size:0.82rem;">\'\n'
    '                + f\'<span style="color:rgba(255,255,255,0.75);">\'\n'
    '                  f\'сделок закрыто: <b>{len(_ry)}</b></span>\'\n'
    '                + f\'<span style="color:#3ddc6b;">в плюс: \'\n'
    '                  f\'<b>{len(_pl)}</b></span>\'\n'
    '                + f\'<span style="color:#ff5c5c;">в минус: \'\n'
    '                  f\'<b>{len(_mi)}</b></span>\'\n'
    '                + f\'<span style="color:{_c_ob};">общий: \'\n'
    '                  f\'<b>{_obshchiy:+.2f}R</b></span>\'\n'
    '                + f\'<span style="color:{_c_sr};">средний: \'\n'
    '                  f\'<b>{_sredniy:+.2f}R</b></span>\'\n'
    '                + \'</div>\')\n'
)

PRAVKI = [(STAROE_2, NOVOE_2), (STAROE_1, NOVOE_1),
          (STAROE_4, NOVOE_4), (STAROE_3, NOVOE_3),
          (STAROE_5, NOVOE_5)]


def podozhdat():
    try:
        input("\nГотово. Нажми Enter, чтобы закрыть окно.")
    except Exception:
        pass


def nayti():
    prosto = KOREN / "Биржа" / "ui_otchyot.py"
    if prosto.exists():
        return prosto
    musor = ("_ARCHIVE", "_OLD", "_АРХИВ", "_УБОРКА", ".bak")
    nashlos = [p for p in KOREN.rglob("ui_otchyot.py")
               if not any(m in str(p) for m in musor)]
    if len(nashlos) == 1:
        print(f"Нашёл: {nashlos[0]}")
        return nashlos[0]
    if len(nashlos) > 1:
        print("Нашёл несколько:")
        for nomer, p in enumerate(nashlos, 1):
            print(f"  {nomer}. {p}")
        otvet = input("Какой правим? номер: ").strip()
        if otvet.isdigit() and 1 <= int(otvet) <= len(nashlos):
            return nashlos[int(otvet) - 1]
    return None


def main():
    put = nayti()
    if put is None:
        print("✗ не нашёл Биржа/ui_otchyot.py — запускай из корня репо")
        return 1

    tekst = put.read_text(encoding="utf-8")
    if MARKER in tekst:
        print("· уже сделано")
        return 0

    novyy = tekst
    for nomer, (staroe, novoe) in enumerate(PRAVKI, 1):
        if novyy.count(staroe) != 1:
            print(f"✗ правка {nomer}: нашёл {novyy.count(staroe)} мест "
                  f"вместо одного. Ничего не тронул.")
            print("  Скажи Брату, поправим по месту.")
            return 1
        novyy = novyy.replace(staroe, novoe, 1)

    try:
        ast.parse(novyy)
    except SyntaxError as beda:
        print(f"✗ после правки файл поломался (строка {beda.lineno}): "
              f"{beda.msg}")
        print("  Ничего не записал, оригинал цел.")
        return 1

    kopiya = put.with_suffix(put.suffix + ".bak_pravda")
    if not kopiya.exists():
        shutil.copy2(put, kopiya)
        print(f"  (копия старого: {kopiya.name})")
    put.write_text(novyy, encoding="utf-8")

    print("✓ отчёт исправлен:")
    print("    · ведение больше не подписывается как вход")
    print("    · у каждого входа свой R и чем кончилось")
    print("    · в шапке итог: сделок, в плюс, в минус, общий R, средний R")
    print()
    print("Перезапусти Кабинет (main.py) и открой любой прошлый отчёт —")
    print("пересчитывать ничего не надо, он читает то, что уже записано.")
    return 0


if __name__ == "__main__":
    kod = main()
    podozhdat()
    sys.exit(kod)
