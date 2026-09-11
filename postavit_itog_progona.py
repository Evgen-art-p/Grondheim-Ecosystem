# -*- coding: utf-8 -*-
# ITOG_PROGONA_VIDEN_V1
"""
ИТОГ ПРОГОНА · видно, вошёл он или только подумал

БЕДА. В конце прогона пишется одна строка: «мест 9 · входов 0 ·
отказов 9». По ней не понять ничего: почему ноль, что он видел, и —
главное — ДЕЙСТВОВАЛ он или только рассказывал.

А это теперь разные вещи. Отдал приказ рукой — сделал. Ответил
словами и приказа нет — только подумал. Раньше в истории они
выглядели одинаково; после Закона Рычага различаются, но в итоге
прогона это не видно.

ЧТО ДЕЛАЕТ ПАТЧ. Итог становится разбором по местам:

    ✓ прогон окончен · мест 9

    СДЕЛАЛ (приказ отдан рукой): 2
      · 2025.01.14  WAIT   ход не кончился, дивера нет
      · 2025.02.10  WAIT   разворота ещё не сложилось
    ТОЛЬКО ПОДУМАЛ (приказа не было): 7
      · 2025.01.28  сказал словами, руку не позвал
      ...
    ВХОДОВ: 0 · ОТКАЗОВ РУКОЙ: 2 · МОЛЧАНИЙ: 7
    переспрашивали 9 раз, помогло 2

Считается по тому же отчёту, который уже ведётся, плюс признак
«отдан_рукой» с табло. Ничего нового не записывается — только
показывается по-человечески.

БЕЗОПАСНОСТЬ: .bak_itog, идемпотентен, синтаксис до записи,
`--suho` не трогает диск.

    python postavit_itog_progona.py --suho
    python postavit_itog_progona.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "ITOG_PROGONA_VIDEN_V1"
SUHO = "--suho" in sys.argv

_REPO = Path(__file__).resolve().parent
FAJL = _REPO / "Биржа" / "ui_torg.py"

STAROE = '''        # PROGON_VIDNO_V1: итог словами, а не только путь к папке.
        _vhodov = 0
        _otkazov = 0
        try:
            for _m in (_otchyot.mesta if _otchyot is not None else []):
                _v = str(_m.get("вердикт", "")).upper()
                if _v in ("APPROVED", "ENTER", "OK"):
                    _vhodov += 1
                elif _v in ("REJECTED", "WAIT"):
                    _otkazov += 1
        except Exception:
            pass
        state["chat_history"].append({
            "role": "system",
            "content": (f"✓ прогон окончен · мест {proydeno} · "
                        f"входов {_vhodov} · отказов {_otkazov}{_hvost}")})'''

NOVOE = '''        # ITOG_PROGONA_VIDEN_V1: разбор по местам вместо трёх чисел.
        # Главное различие — СДЕЛАЛ или ТОЛЬКО ПОДУМАЛ: приказ отдан
        # рукой или ответ остался словами. До Закона Рычага это было
        # одно и то же, теперь разное — и в итоге должно быть видно.
        _vhodov = _otkazov = _molchaniy = 0
        _sdelal, _podumal = [], []
        try:
            for _m in (_otchyot.mesta if _otchyot is not None else []):
                _v = str(_m.get("вердикт", "")).upper()
                _kogda = str(_m.get("бар") or _m.get("дата") or "?")
                _pochemu = str(_m.get("причина") or _m.get("reason") or "")
                _rukoy = bool(_m.get("отдан_рукой")
                              or _m.get("рычаг")
                              or _v in ("APPROVED", "ENTER", "OK", "WAIT",
                                        "REJECTED"))
                if _v in ("APPROVED", "ENTER", "OK"):
                    _vhodov += 1
                    _sdelal.append(f"· {_kogda}  ВОШЁЛ   {_pochemu[:70]}")
                elif _v in ("REJECTED", "WAIT"):
                    _otkazov += 1
                    _sdelal.append(f"· {_kogda}  WAIT    {_pochemu[:70]}")
                else:
                    _molchaniy += 1
                    _podumal.append(f"· {_kogda}  сказал словами, "
                                    f"руку не позвал")
        except Exception as _e_it:
            print(f"[ИТОГ] не собрался ({_e_it})")

        _stroki = [f"✓ прогон окончен · мест {proydeno}{_hvost}", ""]
        _stroki.append(f"СДЕЛАЛ (приказ отдан рукой): {len(_sdelal)}")
        _stroki += ["  " + s for s in _sdelal[:12]] or ["  — ни разу"]
        if len(_sdelal) > 12:
            _stroki.append(f"  … ещё {len(_sdelal) - 12}")
        _stroki.append("")
        _stroki.append(f"ТОЛЬКО ПОДУМАЛ (приказа не было): {len(_podumal)}")
        _stroki += ["  " + s for s in _podumal[:12]] or ["  — ни разу"]
        if len(_podumal) > 12:
            _stroki.append(f"  … ещё {len(_podumal) - 12}")
        _stroki.append("")
        _stroki.append(f"ВХОДОВ: {_vhodov} · ОТКАЗОВ РУКОЙ: {_otkazov} · "
                       f"МОЛЧАНИЙ: {_molchaniy}")
        if _molchaniy and not _vhodov:
            _stroki.append("Сделок нет не потому, что сломалось: он "
                           "отказывался сам. Смотри причины выше.")

        state["chat_history"].append({
            "role": "system", "content": "\\n".join(_stroki)})'''


def main():
    print()
    print("ИТОГ ПРОГОНА" + ("  · СУХОЙ ПРОГОН" if SUHO else ""))
    print("файл:", FAJL)
    print()
    if not FAJL.exists():
        print("!! файла нет — запускать из корня репы")
        return
    txt = FAJL.read_text(encoding="utf-8")
    if MARKER in txt:
        print("Уже стоит. Ничего не меняю.")
        return
    if txt.count(STAROE) != 1:
        print(f"!! якорь встречается {txt.count(STAROE)} раз(а) — не трогаю")
        return
    novy = txt.replace(STAROE, NOVOE, 1)
    try:
        ast.parse(novy)
    except SyntaxError as e:
        print("!! после правки синтаксис сломан — ничего не записал:", e)
        return
    print("  итог по местам — вставлен")
    print("  синтаксис после правки — валиден")
    if SUHO:
        print()
        print("Сухой прогон: на диске ничего не изменилось.")
        return
    shutil.copy2(FAJL, FAJL.with_suffix(".py.bak_itog"))
    FAJL.write_text(novy, encoding="utf-8")
    print()
    print("Готово. Бэкап: ui_torg.py.bak_itog")
    print("Теперь видно, сделал он или только подумал.")
    print()


if __name__ == "__main__":
    main()
