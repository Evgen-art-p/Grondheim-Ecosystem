# -*- coding: utf-8 -*-
"""
Патч: ГОРОД/ui_grondheim.py — клик по квадрату Биржи на карте /grondheim
ведёт в кабинет Совета /torg, а не в общий паспорт локации /lokacia/{id}.

ПРИЧИНА: Биржа (ID_Object = 0014_EXCHANGE) — не просто описанное место,
у неё есть свой рабочий кабинет (ui_torg.py, стол Совета с пузырьками,
Калибровкой и т.д.). Обычные локации (Высотка, Мастера...) пока живут
только паспортом — им и открывать нечего, кроме /lokacia/{id}.

РЕШЕНИЕ — по образу Закона Пары (самоописание, не растущий if-лес):
  словарь LOCATION_GATES: {id_локации: маршрут} — локация со своим
  кабинетом сама заявляет об этом здесь. Родится новый рабочий кабинет
  (скальперы, Храм...) — добавляется одна строка в словарь, не правится
  логика клика.

  on_open() сначала смотрит в LOCATION_GATES; если локации там нет —
  честный старый путь, /lokacia/{id}.

Идемпотентен: повторный запуск ничего не меняет.
"""
import sys
import py_compile
import shutil
from pathlib import Path
from datetime import datetime

TARGET = Path("ГОРОД/ui_grondheim.py")

OLD = '''    def on_open(e):
        loc_id = e.args
        if loc_id:
            # клик по локации -> открыть её страницу (ui_lokacia.py)
            ui.navigate.to(f"/lokacia/{loc_id}")'''

NEW = '''    def on_open(e):
        loc_id = e.args
        if loc_id:
            # клик по локации -> её рабочий кабинет, если есть (Закон Пары:
            # локация сама заявляет о своём кабинете в LOCATION_GATES),
            # иначе честный паспорт места (ui_lokacia.py)
            gate = LOCATION_GATES.get(loc_id)
            ui.navigate.to(gate if gate else f"/lokacia/{loc_id}")'''

MARKER_DECL = "LOCATION_GATES = {"
DECL = '''# ── ВРАТА РАБОЧИХ КАБИНЕТОВ — локация -> свой кабинет (не паспорт) ──
# Закон Пары: локация сама заявляет о кабинете. Нет записи -> /lokacia/{id}.
LOCATION_GATES = {
    "0014_EXCHANGE": "/torg",   # Биржа -> стол Совета (ui_torg.py)
}


'''


def main():
    if not TARGET.exists():
        print(f"НЕ НАЙДЕН: {TARGET} (запусти из корня Grondheim-Ecosystem)")
        sys.exit(1)

    src = TARGET.read_text(encoding="utf-8")

    if MARKER_DECL in src:
        print("Уже применено — идемпотентность держит, ничего не меняю.")
        return

    if OLD not in src:
        print("НЕ НАЙДЕН ожидаемый фрагмент on_open() — файл изменился с момента диагностики.")
        print("Ничего не трогаю, чтобы не сломать вслепую.")
        sys.exit(1)

    backup = TARGET.with_suffix(f".py.bak_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(TARGET, backup)
    print(f"Бэкап: {backup}")

    new_src = src.replace(OLD, NEW)

    # Кладём словарь LOCATION_GATES прямо перед def page_grondheim():
    anchor = "def page_grondheim():"
    if anchor not in new_src:
        print("НЕ НАЙДЕН якорь 'def page_grondheim():' — не могу вставить словарь.")
        sys.exit(1)
    new_src = new_src.replace(anchor, DECL + anchor, 1)

    TARGET.write_text(new_src, encoding="utf-8")

    py_compile.compile(str(TARGET), doraise=True)
    print("Синтаксис цел (py_compile прошёл).")
    print("Готово: клик по Бирже на карте -> /torg. Остальные локации -> как раньше.")


if __name__ == "__main__":
    main()
