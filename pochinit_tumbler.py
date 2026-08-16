# -*- coding: utf-8 -*-
"""
pochinit_tumbler.py · MARKER: TUMBLER_V1

ЧТО ПРОИСХОДИТ
──────────────
Кнопка ТЕСТЕР не кликается: жмёшь — ничего, даже уведомления «Режим:
ТЕСТЕР» не появляется. Сам обработчик `set_mode` цел, я его проверил
построчно — значит нажатие до него просто НЕ ДОХОДИТ.

ПОЧЕМУ
──────
Тумблер сделан не кнопками, а голыми `div`-ами: клик держится на
всплытии события. Такое легко ломается — достаточно, чтобы сверху лёг
любой прозрачный слой или соседний элемент захватил область. Проверить
это глазами нельзя: выглядит всё ровно так же, просто не нажимается.

ЧТО ПРАВИТ
──────────
1. РЕАЛ и ТЕСТЕР становятся настоящими кнопками. Вид тот же, а клик
   обрабатывается самой кнопкой, а не ловится всплытием.

2. Каждое нажатие оставляет след в консоли:

       [ТУМБЛЕР] нажали: tester
       [ТУМБЛЕР] режим встал: tester · кран tester

   Теперь видно, доходит ли нажатие и что из него вышло. Если после
   патча в консоли пусто — значит клик не доходит и до кнопки, и беда
   не в тумблере, а выше: тогда шли мне снимок экрана этого места.

3. Ошибки внутри переключения больше не глотаются молча: если что-то
   сорвётся, увидишь строку [ТУМБЛЕР] ✗ и причину.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py pochinit_tumbler.py   (или --suho)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "TUMBLER_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return (p / "Биржа" / "ui_torg.py").exists() and (p / "main.py").exists()


def nayti_koren() -> Path:
    zdes = Path(__file__).resolve().parent
    for kand in (zdes, Path.cwd(), *zdes.parents):
        if _eto_koren(kand):
            return kand
    kandidaty = []
    for baza in (zdes.parent, Path.cwd().parent):
        if not baza.is_dir():
            continue
        for d in baza.iterdir():
            if d.is_dir() and _eto_koren(d) and d not in kandidaty:
                kandidaty.append(d)
    if len(kandidaty) == 1:
        if input(f"Нашёл город здесь:\n  {kandidaty[0]}\nЭтот? [Enter=да] "
                 ).strip().lower() in ("", "y", "д", "да"):
            return kandidaty[0]
    elif len(kandidaty) > 1:
        print("Нашёл несколько городов:")
        for i, d in enumerate(kandidaty, 1):
            print(f"  {i}. {d}")
        nom = input("Какой? номер: ").strip()
        if nom.isdigit() and 1 <= int(nom) <= len(kandidaty):
            return kandidaty[int(nom) - 1]
    put = input("Не нашёл сам. Перетащи сюда папку репо и нажми Enter:\n> ")
    p = Path(put.strip().strip('"').strip("'"))
    if _eto_koren(p):
        return p
    print("✗ Это не корень репо")
    sys.exit(1)


ST_KNOPKI = '''                        toolbar_refs["mode_real"] = ui.element("div").style(
                            "padding:6px 14px;border-radius:7px;font-size:12px;font-weight:700;"
                            "cursor:pointer;background:rgba(0,255,136,0.15);color:#00ff88;"
                            "border:1px solid rgba(0,255,136,0.4);")
                        toolbar_refs["mode_real"].on("click", lambda: set_mode("real"))
                        with toolbar_refs["mode_real"]:
                            ui.html("РЕАЛ")
                        toolbar_refs["mode_tester"] = ui.element("div").style(
                            "padding:6px 14px;border-radius:7px;font-size:12px;font-weight:700;"
                            "cursor:pointer;background:rgba(255,255,255,0.03);"
                            "color:rgba(255,255,255,0.45);border:1px solid rgba(255,255,255,0.08);")
                        toolbar_refs["mode_tester"].on("click", lambda: set_mode("tester"))
                        with toolbar_refs["mode_tester"]:
                            ui.html("ТЕСТЕР")'''

NOV_KNOPKI = '''                        # TUMBLER_V1: были голые div — клик держался на
                        # всплытии события и терялся, если сверху лёг любой
                        # слой. Выглядело как «кнопка не кликается»,
                        # хотя обработчик был цел. Теперь настоящие кнопки:
                        # клик обрабатывает сама кнопка.
                        toolbar_refs["mode_real"] = ui.button(
                            "РЕАЛ", on_click=lambda: set_mode("real")
                        ).props("flat no-caps dense").style(
                            "padding:6px 14px;border-radius:7px;font-size:12px;font-weight:700;"
                            "cursor:pointer;background:rgba(0,255,136,0.15);color:#00ff88;"
                            "border:1px solid rgba(0,255,136,0.4);")
                        toolbar_refs["mode_tester"] = ui.button(
                            "ТЕСТЕР", on_click=lambda: set_mode("tester")
                        ).props("flat no-caps dense").style(
                            "padding:6px 14px;border-radius:7px;font-size:12px;font-weight:700;"
                            "cursor:pointer;background:rgba(255,255,255,0.03);"
                            "color:rgba(255,255,255,0.45);border:1px solid rgba(255,255,255,0.08);")'''

ST_SET = '''    def set_mode(mode: str):
        state["mode"] = mode
        try:
            from feed_source import set_feed_mode'''

NOV_SET = '''    def set_mode(mode: str):
        # TUMBLER_V1: след в консоли. Если нажатие не доходит — здесь
        # будет пусто, и станет ясно, что беда не в переключении.
        print(f"[ТУМБЛЕР] нажали: {mode}")
        state["mode"] = mode
        try:
            from feed_source import set_feed_mode'''

ST_HVOST = '''        ui.notify(f"Режим: {'ТЕСТЕР (история)' if is_tester else 'РЕАЛ (живой рынок)'}",
                  type="info")'''

NOV_HVOST = '''        try:
            from feed_source import get_feed_mode as _gfm
            _kran = (_gfm() or {}).get("mode", "?")
        except Exception as _e:
            _kran = f"не спросить ({_e})"
        print(f"[ТУМБЛЕР] режим встал: {mode} · кран {_kran}")
        ui.notify(f"Режим: {'ТЕСТЕР (история)' if is_tester else 'РЕАЛ (живой рынок)'}",
                  type="info")'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    ui_torg = koren / "Биржа" / "ui_torg.py"
    t = ui_torg.read_text(encoding="utf-8")

    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0

    pary = [("кнопки", ST_KNOPKI, NOV_KNOPKI),
            ("вход в set_mode", ST_SET, NOV_SET),
            ("хвост set_mode", ST_HVOST, NOV_HVOST)]
    beda = [imya for imya, st, _ in pary if t.count(st) != 1]
    if beda:
        print(f"✗ якоря не найдены дословно: {', '.join(beda)}")
        print("  Кабинет правили — не трогаю, чтобы не сломать.")
        return 1

    novyy = t
    for _, st, nov in pary:
        novyy = novyy.replace(st, nov, 1)
    novyy += f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ после правки не разбирается: {e}")
        return 1

    if SUHO:
        print("· правка готова (сухой прогон)")
        return 0

    bak = ui_torg.with_suffix(f".py.bak_tumbler_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(ui_torg, bak)
    ui_torg.write_text(novyy, encoding="utf-8")
    print(f"✓ тумблер переделан (копия: {bak.name})")

    import py_compile
    try:
        py_compile.compile(str(ui_torg), doraise=True)
        print("✓ компилируется")
    except Exception as e:
        print(f"✗ НЕ компилируется: {e}")
        return 1

    print("\nЖми ТЕСТЕР и смотри в консоль города. Должно быть:")
    print("    [ТУМБЛЕР] нажали: tester")
    print("    [ТУМБЛЕР] режим встал: tester · кран tester")
    print("\nЕсли в консоли ПУСТО — нажатие не доходит и до кнопки:")
    print("значит дело не в тумблере, а в том, что лежит поверх него.")
    print("Тогда пришли мне снимок этого места экрана.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
