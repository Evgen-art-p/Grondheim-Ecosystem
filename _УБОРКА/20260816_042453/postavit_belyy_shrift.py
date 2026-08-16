# -*- coding: utf-8 -*-
"""
postavit_belyy_shrift.py · MARKER: BELYY_SHRIFT_V1

ЧТО ПРОСИЛ ШЕФ
──────────────
«Кнопка перевозка у Брата открывает окно, там шрифт не читается,
сделай белый. Вообще, везде сделай белый».

ПОЧЕМУ БЫЛО НЕ ВИДНО
────────────────────
Карточки диалогов у нас тёмные — их рисуем мы сами
(`background:#0d1117`). А подписи внутри — чекбоксы, поля, выпадающие
списки — рисует Quasar, и цвет он берёт из СВОЕЙ темы, а тема
светлая. Отсюда тёмно-серые буквы на почти чёрном фоне.

Заголовки и пояснения в том же окне читаются нормально — их цвет мы
задавали руками. Не читается ровно то, что отдано Quasar'у: в
перевозке это подписи жителей у галочек.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
Добавляет один общий кусок CSS во все страницы города, где мы уже
вставляем свои стили. Красит белым ИМЕННО то, что рисует Quasar
внутри наших тёмных карточек и панелей:

    подписи галочек и радио · текст в полях ввода · подсказки в них
    · выпадающие списки и пункты меню · вкладки · подписи полей

Кнопки, ссылки и наши собственные раскрашенные надписи НЕ трогает:
у них цвет задан руками, и перекрашивать их — значит сломать то, что
и так читается.

ГДЕ ПРИМЕНЕНО
─────────────
Во всех кабинетах города, которые вставляют свой CSS: Брат, реестр
Брата, житель, Академия, Ректор, Архив, Биржа, Маяк, карта, локация,
Страница Работы, цеха, главная.

Идемпотентен, .bak рядом, py_compile до записи.
Запуск: py postavit_belyy_shrift.py   (или --suho)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "BELYY_SHRIFT_V1"
SUHO = "--suho" in sys.argv

BELYY = """
/* BELYY_SHRIFT_V1 — читаемость на тёмном.
   Карточки диалогов рисуем мы (тёмные), а подписи внутри — Quasar по
   своей СВЕТЛОЙ теме. Отсюда тёмно-серые буквы на чёрном: в окне
   перевозки так пропадали имена жителей у галочек.
   Красим только то, что отдано Quasar'у. Кнопки и наши собственные
   раскрашенные надписи не трогаем — у них цвет задан руками. */
.q-dialog .q-card,
.q-dialog .q-card .q-item__label,
.q-dialog .q-card label,
.q-checkbox__label,
.q-radio__label,
.q-toggle__label,
.q-field__native,
.q-field__input,
.q-field__label,
.q-field__prefix,
.q-field__suffix,
.q-item__label,
.q-tab__label,
.q-select__dropdown-icon,
.q-menu .q-item,
.q-menu .q-item__label {
  color: rgba(255,255,255,0.92) !important;
}

/* Подсказка в пустом поле — белая, но приглушённая: она не должна
   спорить с тем, что человек уже вписал. */
.q-field__native::placeholder,
.q-field__input::placeholder,
.q-placeholder::placeholder {
  color: rgba(255,255,255,0.45) !important;
}

/* Выпадающий список Quasar рисует НЕ внутри нашей карточки, а
   отдельным слоем поверх страницы — своей темой. Без этого он
   оставался светлым пятном с белым текстом на белом. */
.q-menu {
  background: #0d1117 !important;
  border: 1px solid rgba(255,255,255,0.12) !important;
}
"""


def _eto_koren(p: Path) -> bool:
    return (p / "Брат" / "ui_brat.py").exists() and (p / "main.py").exists()


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


STRANICY = [
    ("Брат", "Брат/ui_brat.py"),
    ("реестр Брата", "Брат/ui_registry.py"),
    ("житель", "жители/ui_zhitel.py"),
    ("Академия", "Академия/ui_akademia.py"),
    ("Ректор", "Академия/ui_rektor.py"),
    ("Архив", "Архив/ui_arkhiv.py"),
    ("Биржа", "Биржа/ui_torg.py"),
    ("Маяк", "Маяк/ui_mayak.py"),
    ("карта", "ГОРОД/ui_karta.py"),
    ("город", "ГОРОД/ui_grondheim.py"),
    ("локация", "ГОРОД/ui_lokacia.py"),
    ("Работа", "ГОРОД/ui_rabota.py"),
    ("цеха", "ГОРОД/ui_ceha.py"),
]

VSTAVKA = ('        ui.add_head_html("<style>" + _BELYY_SHRIFT + "</style>")'
           '   # BELYY_SHRIFT_V1\n')


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    print("\nКрашу подписи, которые рисует Quasar, — они и пропадали:\n")

    tronuto, propuscheno = 0, []
    for imya, otn in STRANICY:
        f = koren / otn
        if not f.exists():
            propuscheno.append(f"{imya} (нет файла)")
            continue
        t = f.read_text(encoding="utf-8")
        if MARKER in t:
            print(f"  · {imya}: уже покрашено")
            continue
        if "ui.add_head_html" not in t:
            propuscheno.append(f"{imya} (не вставляет свой CSS)")
            continue

        # объявляем кусок рядом с импортами, вставляем при первом
        # add_head_html этой страницы
        stroki = t.split("\n")
        mesto_obyavleniya = 0
        for i, s in enumerate(stroki[:80]):
            if s.startswith(("import ", "from ")):
                mesto_obyavleniya = i + 1
        obyavlenie = ('\n# BELYY_SHRIFT_V1: читаемость на тёмном — см.\n'
                      '# postavit_belyy_shrift.py. Красим только то, что\n'
                      '# рисует Quasar своей светлой темой внутри наших\n'
                      '# тёмных карточек.\n'
                      '_BELYY_SHRIFT = r"""' + BELYY + '"""\n')
        stroki.insert(mesto_obyavleniya, obyavlenie)
        novyy = "\n".join(stroki)

        # первый add_head_html — сразу после него добавляем свой
        i = novyy.find("ui.add_head_html")
        if i < 0:
            propuscheno.append(f"{imya} (не нашёл, куда вставить)")
            continue
        konec = novyy.find("\n", i) + 1
        otstup = ""
        nachalo_stroki = novyy.rfind("\n", 0, i) + 1
        for ch in novyy[nachalo_stroki:i]:
            otstup += ch if ch in " \t" else ""
        novyy = (novyy[:konec]
                 + f'{otstup}ui.add_head_html("<style>" + _BELYY_SHRIFT '
                   f'+ "</style>")   # {MARKER}\n'
                 + novyy[konec:])

        try:
            ast.parse(novyy)
        except SyntaxError as e:
            propuscheno.append(f"{imya} (после правки не разбирается: {e})")
            continue
        if SUHO:
            print(f"  · {imya}: правка готова (сухой прогон)")
            continue
        shutil.copy2(f, f.with_suffix(
            f".py.bak_belyy_{datetime.now():%Y%m%d_%H%M%S}"))
        f.write_text(novyy, encoding="utf-8")
        print(f"  ✓ {imya}")
        tronuto += 1

    if propuscheno:
        print("\n⚠ не тронуто:")
        for s in propuscheno:
            print(f"    {s}")

    if not SUHO:
        import py_compile
        for imya, otn in STRANICY:
            f = koren / otn
            if not f.exists():
                continue
            try:
                py_compile.compile(str(f), doraise=True)
            except Exception as e:
                print(f"  ✗ НЕ компилируется {otn}: {e}")
                return 1
        print(f"\n✓ покрашено страниц: {tronuto} · все компилируются")
        print("\nЧто стало белым: подписи галочек и переключателей, текст")
        print("в полях ввода, выпадающие списки, вкладки, подписи полей.")
        print("Кнопки и наши собственные раскрашенные надписи не трогал —")
        print("у них цвет задан руками, и они и так читаются.")
        print("\nПроверь: Брат → Перевозка. Имена у галочек должны читаться.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
