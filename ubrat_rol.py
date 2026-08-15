# -*- coding: utf-8 -*-
"""
ubrat_rol.py · MARKER: ROL_V_RABOTU_V1

ЧТО ПРОСИЛ ШЕФ
──────────────
«Убери у Брата вкладку Роль, только смотри, к чему она ведёт ещё, и
перекинь на Работу — они по сути одинаковы».

ЧТО ПОКАЗАЛА ПРОВЕРКА
─────────────────────
По сути — да, но НЕ полностью. Прежде чем сносить, я сверил обе двери.

Хорошая новость: посты у них ОДНИ И ТЕ ЖЕ. «Роль» сажает через
`rezidenty.posadit`, Страница Работы — через `rabota.prinyat`, но обе
руки пишут в один файл `GRONDHEIM_CITY/посты/{id}/пост.json`. Правда
одна, рук две. Значит посадка при сносе не теряется.

А вот три вещи «Роль» умела, а Страница Работы — нет:

  1. ТИПЫ-ПОСТЫ. На Странице Работы список типов из четырёх:
     резидент, хранитель, воркер, студент. У «Роли» их восемь — ещё
     библиотекарь, хранитель_архива, ректор, хранитель_маяка. Снеси
     как есть — этих четырёх типов стало бы негде поставить.

  2. СТУДЕНТ → АКАДЕМИЯ. «Роль» при типе «студент» не только писала
     тип, но и занимала место в `GRONDHEIM_CITY/Академия/ученики.json`
     — том самом файле, который читает кабинет Академии. На Странице
     Работы тип «студент» выбрать можно, а место не занималось: тип
     стоял, а в Академии человека не было.

  3. Цех и слот руками (Workshop_ID / Turbo_Role). Это НЕ переношу
     намеренно: цех и слот теперь берутся из поста, а вписывать их в
     личность руками — тот самый старый путь, от которого ушли
     (кресло и жопа склеивались именно здесь).

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
1. Страница Работы получает все восемь типов и запись студента в
   Академию — той же рукой, что была у Брата, а не копией: зовём
   `ui_brat.zapisat_studenta`, чтобы не завести вторую правду о
   местах Академии.

2. У Брата убирается КНОПКА «Роль». Сам код (`naznachit_rol`,
   `naznachit_post_iz_roli`, `zapisat_studenta`, диалог) остаётся на
   месте: `zapisat_studenta` теперь зовёт Страница Работы, а
   остальное — чужой труд, выкидывать его не мне. Скажешь — вынесу
   отдельно уборщиком, обратимо.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py ubrat_rol.py   (или --suho)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "ROL_V_RABOTU_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "Брат" / "ui_brat.py").exists()
            and (p / "ГОРОД" / "ui_rabota.py").exists())


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


# ═══════════════════════════════════════════════════════════
# 1. Страница Работы принимает наследство «Роли»
# ═══════════════════════════════════════════════════════════
ST_TIPY = '''TIPY = ["резидент", "хранитель", "воркер", "студент"]'''

NOV_TIPY = '''# ROL_V_RABOTU_V1: четыре типа-поста приехали сюда со снесённой
# вкладки «Роль» у Брата — библиотекарь, хранитель_архива, ректор,
# хранитель_маяка. Без них эти четверо остались бы без типа: посадить
# на пост можно во вкладке МЕСТА, а назвать — было негде.
TIPY = ["резидент", "хранитель", "воркер", "студент",
        "библиотекарь", "хранитель_архива", "ректор", "хранитель_маяка"]

# Тип «студент» — не просто слово в паспорте: он занимает место в
# Академии. Раньше это делала «Роль», теперь мы, но ТОЙ ЖЕ рукой —
# не копией. Копия завела бы вторую правду о местах Академии, а
# правда одна: GRONDHEIM_CITY/Академия/ученики.json.
def _zapisat_v_akademiyu(imya: str) -> tuple:
    """(получилось, что сказать). Место занято/мест нет — честно вернём."""
    try:
        import sys as _s
        _repo = Path(__file__).resolve().parent.parent
        for _p in (str(_repo), str(_repo / "Брат")):
            if _p not in _s.path:
                _s.path.insert(0, _p)
        import ui_brat
        p, _dom = _pasport(imya)
        if p is None:
            return False, "паспорт не читается"
        zid = p.get("ID_Object", "")
        if not zid:
            return False, "у жителя нет ID"
        # уже сидит — второй раз не сажаем и место не занимаем
        try:
            uzhe = ui_brat._akademia_ucheniki_chitat().get("места", []) or []
            if any((z.get("ID") == zid or z.get("имя") == imya) for z in uzhe):
                return True, "уже числится в Академии"
        except Exception:
            pass
        return ui_brat.zapisat_studenta(zid)
    except Exception as e:
        return False, f"Академия недоступна ({e})"'''

ST_SOHR = '''            def _sohr():
                ok, msg = _sohranit_zhitelya(imya, (sel.value or "").strip(),
                                             (fr.value or "").strip())
                ui.notify(("🪑 " if ok else "⚠ ") + msg,
                          color="positive" if ok else "negative")'''

NOV_SOHR = '''            def _sohr():
                _tip_novyy = (sel.value or "").strip()
                ok, msg = _sohranit_zhitelya(imya, _tip_novyy,
                                             (fr.value or "").strip())
                # ROL_V_RABOTU_V1: студент — не только слово в паспорте.
                # Раньше место в Академии занимала «Роль»; теперь мы.
                if ok and _tip_novyy == "студент":
                    ok_ak, msg_ak = _zapisat_v_akademiyu(imya)
                    msg = f"{msg} · Академия: {msg_ak}"
                    ui.notify(("🎓 " if ok_ak else "⚠ Академия: ") + msg_ak,
                              color="positive" if ok_ak else "warning")
                ui.notify(("🪑 " if ok else "⚠ ") + msg,
                          color="positive" if ok else "negative")'''


# ═══════════════════════════════════════════════════════════
# 2. У Брата снимается кнопка
# ═══════════════════════════════════════════════════════════
ST_KNOPKA = '''                        ui.button("Роль",
                                  on_click=do_naznachit_rol  # PATCH_NAZNACHIT_ROL
                                  ).props("flat").classes("brat-gate")
'''
NOV_KNOPKA = '''                        # ROL_V_RABOTU_V1: кнопка «Роль» снята — она делала
                        # то же, что Страница Работы, только своей рукой.
                        # Наследство перенесено туда: четыре типа-поста и
                        # запись студента в Академию. Сам код «Роли» ниже
                        # по файлу оставлен: zapisat_studenta теперь зовёт
                        # Страница Работы.
'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    rabota = koren / "ГОРОД" / "ui_rabota.py"
    brat = koren / "Брат" / "ui_brat.py"

    # ── 1. Работа ──
    print("\n1. Страница Работы принимает наследство «Роли»")
    t = rabota.read_text(encoding="utf-8")
    if MARKER in t:
        print("  · маркер уже стоит")
    else:
        beda = []
        if t.count(ST_TIPY) != 1:
            beda.append(f"список типов ({t.count(ST_TIPY)} шт)")
        if t.count(ST_SOHR) != 1:
            beda.append(f"кнопка сохранить ({t.count(ST_SOHR)} шт)")
        if beda:
            print(f"  ✗ якоря не найдены дословно: {', '.join(beda)}")
            return 1
        novyy = (t.replace(ST_TIPY, NOV_TIPY, 1)
                  .replace(ST_SOHR, NOV_SOHR, 1)
                 + f"\n# {MARKER} - marker\n")
        try:
            ast.parse(novyy)
        except SyntaxError as e:
            print(f"  ✗ после правки не разбирается: {e}")
            return 1
        if SUHO:
            print("  · правка готова (сухой прогон)")
        else:
            shutil.copy2(rabota, rabota.with_suffix(
                f".py.bak_rol_{datetime.now():%Y%m%d_%H%M%S}"))
            rabota.write_text(novyy, encoding="utf-8")
            print("  ✓ восемь типов + запись студента в Академию")

    # ── 2. Брат ──
    print("\n2. У Брата снимается кнопка «Роль»")
    t = brat.read_text(encoding="utf-8")
    if MARKER in t:
        print("  · маркер уже стоит")
    else:
        if t.count(ST_KNOPKA) != 1:
            print(f"  ✗ кнопка найдена {t.count(ST_KNOPKA)} раз — жду одну")
            return 1
        novyy = t.replace(ST_KNOPKA, NOV_KNOPKA, 1) + f"\n# {MARKER} - marker\n"
        try:
            ast.parse(novyy)
        except SyntaxError as e:
            print(f"  ✗ после правки не разбирается: {e}")
            return 1
        if SUHO:
            print("  · правка готова (сухой прогон)")
        else:
            shutil.copy2(brat, brat.with_suffix(
                f".py.bak_rol_{datetime.now():%Y%m%d_%H%M%S}"))
            brat.write_text(novyy, encoding="utf-8")
            print("  ✓ кнопка снята, код «Роли» на месте")

    if not SUHO:
        import py_compile
        for f in (rabota, brat):
            try:
                py_compile.compile(str(f), doraise=True)
                print(f"  ✓ компилируется: {f.name}")
            except Exception as e:
                print(f"  ✗ НЕ компилируется {f.name}: {e}")
                return 1
        print("\nУ Брата осталось: Тик · Прописка · Работа · Перевозка.")
        print("Всё, что делала «Роль», теперь на Странице Работы:")
        print("  тип (все восемь) и коронная фраза — вкладка ЛЮДИ,")
        print("  посадка на пост и увольнение — вкладка МЕСТА,")
        print("  студент — сам занимает место в Академии при сохранении.")
        print("\nНе перенесено намеренно: вписывание цеха и слота руками.")
        print("Цех и слот берутся из поста — руками их вбивать больше не надо.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
