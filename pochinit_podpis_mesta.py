# -*- coding: utf-8 -*-
# PODPIS_PO_BARU_GORODA_V1
"""
ПОДПИСЬ МЕСТА — ПО БАРУ ГОРОДА, А НЕ ПО ДАТЕ КАНДИДАТА

РАЗБОР 11.09. Казалось, что кадр отстаёт на час: в чате «📍 2025.02.04
02:00», а под кадром «01:00». Полезли чинить кадр — и оказалось, что
кадр ПРАВ.

В том же логе исполнитель говорит: «сейчас 2025.02.04 01:00». Город
стоит на 01:00, кадр нарисован по 01:00, трейдера спросили на 01:00.
А в чат ушло 02:00 — потому что подпись берёт дату из списка мест, а
место датируется баром, на котором признак СТАЛ ВИДЕН, то есть на
шаг вперёд.

Врала подпись. Кадр не подглядывал.

ЧТО ДЕЛАЕТ ПАТЧ. Подпись места в чате берёт бар, на котором город
стоит НА САМОМ ДЕЛЕ — оттуда же, откуда его берут исполнитель и
рисовалка. Дата кандидата при этом не пропадает: если она отличается,
она пишется рядом, в скобках, чтобы было видно и то и другое.

    📍 2025.02.04 01:00 · разворотный бар BEAR @ 1.03504 → спрашиваю Илья
    📍 2025.02.04 01:00 (место найдено на 02:00) · излом низ …

Города не спросили — пишем как раньше.

БЕЗОПАСНОСТЬ: .bak_podpis, идемпотентен, синтаксис до записи,
`--suho` не трогает диск.

    python pochinit_podpis_mesta.py --suho
    python pochinit_podpis_mesta.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "PODPIS_PO_BARU_GORODA_V1"
SUHO = "--suho" in sys.argv

_REPO = Path(__file__).resolve().parent
FAJL = _REPO / "Биржа" / "ui_torg.py"

STAROE = '''                state["chat_history"].append({
                    "role": "system",
                    # PROGON_PODRYAD_V2: на сплошном ходу говорим, ЧТО
                    # случилось на баре, а не «разворотный None @ None».
                    "content": (f"📍 {data} · {k.get('почему')} "
                                f"→ спрашиваю {imya}"
                                if k.get("подряд")
                                else f"📍 {_kd.slovami(k)} → спрашиваю {imya}")})'''

NOVOE = '''                # PODPIS_PO_BARU_GORODA_V1: подписываем баром, на
                # котором город стоит НА САМОМ ДЕЛЕ. Дата места —
                # это бар, где признак стал ВИДЕН, она на шаг вперёд,
                # и из-за неё казалось, будто кадр отстаёт.
                _podpis_bar = data
                _hvost_mesta = ""
                try:
                    from hooks import load_trading_state as _lts_p
                    _bg = str(((_lts_p() or {}).get("рынок") or {})
                              .get("бар") or "")
                    if _bg:
                        _podpis_bar = _bg
                        if str(data) and str(data) != _bg:
                            _hvost_mesta = f" (место найдено на {data})"
                except Exception:
                    pass

                state["chat_history"].append({
                    "role": "system",
                    # PROGON_PODRYAD_V2: на сплошном ходу говорим, ЧТО
                    # случилось на баре, а не «разворотный None @ None».
                    "content": (f"📍 {_podpis_bar}{_hvost_mesta} · "
                                f"{k.get('почему')} → спрашиваю {imya}"
                                if k.get("подряд")
                                else f"📍 {_podpis_bar}{_hvost_mesta} · "
                                     f"{_kd.slovami(k)} → спрашиваю {imya}")})'''


def main():
    print()
    print("ПОДПИСЬ ПО БАРУ ГОРОДА" + ("  · СУХОЙ ПРОГОН" if SUHO else ""))
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
    print("  подпись места — поправлена")
    print("  синтаксис после правки — валиден")
    if SUHO:
        print()
        print("Сухой прогон: на диске ничего не изменилось.")
        return
    shutil.copy2(FAJL, FAJL.with_suffix(".py.bak_podpis"))
    FAJL.write_text(novy, encoding="utf-8")
    print()
    print("Готово. Бэкап: ui_torg.py.bak_podpis")
    print("Теперь дата в чате — тот же бар, что под кадром.")
    print()


if __name__ == "__main__":
    main()
