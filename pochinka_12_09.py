# -*- coding: utf-8 -*-
# pochinka_12_09.py — разовая починка по замечаниям редактора (12.09).
#
# Кладётся в КОРЕНЬ репозитория (рядом с папками Биржа/ и GRONDHEIM_CITY/).
# Запуск из PowerShell, из корня:   python pochinka_12_09.py
#
# Чинит:
#   Биржа/ui_torg.py
#     1. строка ~1177 — звали несуществующее имя вместо ui.notify
#     2. строки ~2657 — подсказка про даты звала двух несуществующих
#        помощников и потому НИКОГДА не показывалась
#     3. подпись _bystryy_pasport: честно пишем, что бывает пусто
#   .../слоты/A06|A07|A08/мозг.py
#     4. опечатка _p вместо _put — список кадров ответа не наполнялся
#     5. A07: звал _my_temp(), которого у него нет — переспрос не работал
#     6. две подписи: честно пишем, что бывает пусто
#
# Ничего не удаляет. Перед правкой кладёт рядом копию файла с
# хвостом .bak_12_09. Запускать можно сколько угодно раз: уже
# починенное пропускается.

import shutil
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent

UI = KOREN / "Биржа" / "ui_torg.py"
SLOTY = (KOREN / "GRONDHEIM_CITY" / "Биржа" / "цеха" /
         "торговый_хаос" / "слоты")

# ── правки: (файл, что было, что стало, зачем) ───────────────────────

PRAVKI = []

# 1. ui_torg.py — вместо предупреждения было падение
PRAVKI.append((
    UI,
    '                _tiho(ui.notify, "⚠ прежний актив с полки ушёл — "\n'
    '                                 "выбери заново", type="warning")\n',
    '                ui.notify("⚠ прежний актив с полки ушёл — "\n'
    '                          "выбери заново", type="warning")\n',
    "ui_torg: предупреждение «актив ушёл с полки» больше не падает",
))

# 2. ui_torg.py — подсказка про даты на пустом прогоне
PRAVKI.append((
    UI,
    '                _kraya = []\n'
    '                for _sl2 in (state.get("tester_sloty") or []):\n'
    '                    _s2, _t2 = _para_slota(_sl2)\n'
    '                    _v2, _ = _src_bars(_s2, _t2, 0)\n',
    '                _kraya = []\n'
    '                from feed_source import bars as _src_bars\n'
    '                for _sl2, _s2, _t2 in rabotniki:\n'
    '                    _v2, _ = _src_bars(_s2, _t2, 0)\n',
    "ui_torg: на пустом прогоне город снова говорит, какая история есть",
))

# 3. ui_torg.py — честная подпись
PRAVKI.append((
    UI,
    "def _bystryy_pasport(p) -> dict:\n",
    "def _bystryy_pasport(p) -> dict | None:\n",
    "ui_torg: подпись быстрого паспорта (бывает пусто)",
))

for _slot in ("A06", "A07", "A08"):
    _mozg = SLOTY / _slot / "мозг.py"

    # 4. опечатка: путь к кадру лежит в _put, а не в _p
    PRAVKI.append((
        _mozg,
        "                if _p not in _spisok:\n"
        "                    _spisok.append(_p)\n",
        "                if _put not in _spisok:\n"
        "                    _spisok.append(_put)\n",
        f"{_slot}: кадры ответа снова копятся (чат и панель Шефа)",
    ))

    # 6. честные подписи
    PRAVKI.append((
        _mozg,
        "def _my_open_position(md: dict) -> dict:\n",
        "def _my_open_position(md: dict) -> dict | None:\n",
        f"{_slot}: подпись «моя позиция» (бывает пусто)",
    ))
    PRAVKI.append((
        _mozg,
        "def _signal_ot_ruki(bar_time=None, slova: dict = None) -> dict:\n",
        "def _signal_ot_ruki(bar_time=None, slova: dict | None = None"
        ") -> dict | None:\n",
        f"{_slot}: подпись «сигнал с руки» (бывает пусто)",
    ))

# 5. A07 — звал чужое имя, переспрос молча не работал
PRAVKI.append((
    SLOTY / "A07" / "мозг.py",
    "temperature=_my_temp())",
    "temperature=_temp)",
    "A07: переспрос («приказа нет — спрошу в лицо») наконец работает",
))


# ── работа ──────────────────────────────────────────────────────────

def _varianty(kusok: str, crlf: bool) -> str:
    """Тот же кусок под виндовые переводы строк, если файл такой."""
    return kusok.replace("\n", "\r\n") if crlf else kusok


def main() -> int:
    pochineno, uzhe, ne_nashlos, net_fayla = 0, 0, 0, 0
    kopii = set()

    # группируем по файлу, чтобы читать и писать по разу
    poryadok = []
    for put, *_ in PRAVKI:
        if put not in poryadok:
            poryadok.append(put)

    for put in poryadok:
        if not put.exists():
            print(f"✗ нет файла: {put}")
            net_fayla += 1
            continue

        with open(put, "r", encoding="utf-8", newline="") as _f:
            tekst = _f.read()
        crlf = "\r\n" in tekst
        ishodnyy = tekst

        for f, bylo, stalo, zachem in PRAVKI:
            if f != put:
                continue
            b = _varianty(bylo, crlf)
            s = _varianty(stalo, crlf)
            if b in tekst:
                tekst = tekst.replace(b, s, 1)
                print(f"✓ {zachem}")
                pochineno += 1
            elif s in tekst:
                print(f"· уже починено — {zachem}")
                uzhe += 1
            else:
                print(f"✗ не нашёл место — {zachem}")
                ne_nashlos += 1

        if tekst != ishodnyy:
            kopiya = put.with_suffix(put.suffix + ".bak_12_09")
            if kopiya not in kopii:
                shutil.copy2(put, kopiya)
                kopii.add(kopiya)
                print(f"  (копия старого: {kopiya.name})")
            with open(put, "w", encoding="utf-8", newline="") as _f:
                _f.write(tekst)

    print()
    print(f"ИТОГ: починено {pochineno}, было уже в порядке {uzhe}, "
          f"не нашлось мест {ne_nashlos}, файлов не найдено {net_fayla}")
    if ne_nashlos or net_fayla:
        print("Если что-то не нашлось — скажи Брату, поправим по месту.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
