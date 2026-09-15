# -*- coding: utf-8 -*-
# POSTAVIT_SKLAD_V_ZAGRUZCHIK_V1
"""
ПАТЧ: загрузчик Академии кладёт КАРТОЧКИ на склад, а не файлы в кучу.

Запускать из КОРНЯ РЕПО:
    python postavit_sklad_v_zagruzchik.py

ЧТО МЕНЯЕТ (Академия/ui_akademia.py):

  1. ПОДПИСЬ ПРИ УКЛАДКЕ. Над загрузчиком появляются три поля:
     источник (коротко, из него собирается ключ), подпись (что тут
     нарисовано/написано) и тема. Подписывает ТОЛЬКО Шеф — машина за
     него не сочиняет. Не заполнил — карточка честно ляжет без
     подписи и будет искаться по источнику.

  2. СТОЛ ЖИВЁТ ПРИ ЖИТЕЛЕ, а не при окне. Раньше стол был списком
     той сессии: закрыл кабинет — стол пуст, а файлы на диске
     остались навсегда. Отсюда и «две картинки загрузил, и всё».
     Теперь стол лежит в доме студента (стол_академии.json) и ждёт
     его на месте хоть через неделю.

  3. КАРТИНКА БОЛЬШЕ НЕ ЛОЖИТСЯ В ИСТОРИЮ ЧАТА СЫРЬЁМ. Вчерашняя
     починка клала её отдельным сообщением, а рисовалка чата умеет
     показывать только строку — и вываливала на экран весь PNG
     буквами. Картинка теперь живёт на складе и достаётся по ключу.

ЧЕГО НЕ ТРОГАЕТ
    Старая руда на диске стоит нетронутой. Чтение («📖 Прочитать»),
    уроки, библиотека, чат — работают как работали: записи стола
    сохранили прежнюю форму (путь, вид), к ним только добавился ключ.
    Сносить рабочее до того, как заработала замена, мы уже обжигались.

ПОРЯДОК
    Идемпотентен: накатывать можно сколько угодно раз.
    Бэкап рядом с файлом (.bak_sklad), проверка ast.parse перед
    записью — битый файл на диск не ляжет.

`шесть·проверено·до·корня`
"""
import ast
import shutil
import sys
from pathlib import Path

_KOREN = Path(__file__).resolve().parent
MARKER = "# SKLAD_V_ZAGRUZCHIKE_V1"


def _nayti_kabinet() -> Path:
    """Находим ui_akademia.py сами — путей руками не вписываем."""
    kandidaty = [p for p in _KOREN.rglob("ui_akademia.py")
                 if "_АРХИВ" not in str(p) and "_УБОРКА" not in str(p)]
    if not kandidaty:
        print("⚠ не нашёл ui_akademia.py. Запускай из корня репозитория.")
        return None
    if len(kandidaty) > 1:
        print("Нашёл несколько:")
        for i, p in enumerate(kandidaty, 1):
            print(f"  {i}. {p.relative_to(_KOREN)}")
        try:
            n = int(input("Который? номер: ").strip())
            return kandidaty[n - 1]
        except Exception:
            print("Не понял — беру первый.")
    return kandidaty[0]


# ═══════════════════════════════════════════════════════════
# ЗАМЕНЫ — точные якоря, по одному совпадению каждый
# ═══════════════════════════════════════════════════════════

# 1. подключение склада ─────────────────────────────────────
STARO_1 = '''# CHTENIE_KNIGI_V1: общая рука чтения города'''

NOVO_1 = '''# SKLAD_V_ZAGRUZCHIKE_V1: склад Академии — карточки и ключи.
# Своя точка входа, модуль лежит рядом (Академия/sklad.py).
try:
    import sklad as _sklad
except Exception:
    try:
        _sys_sk = __import__("sys")
        _put_sk = str(Path(__file__).resolve().parent)
        if _put_sk not in _sys_sk.path:
            _sys_sk.path.insert(0, _put_sk)
        import sklad as _sklad
    except Exception as _e_sk:
        _sklad = None
        print(f"[СКЛАД] не подключился: {_e_sk}")


# CHTENIE_KNIGI_V1: общая рука чтения города'''


# 2. стол при жителе ────────────────────────────────────────
STARO_2 = '''def _dom_zhitelya(imya: str) -> Path:
    return _KOVCHEG / imya'''

NOVO_2 = '''def _dom_zhitelya(imya: str) -> Path:
    return _KOVCHEG / imya


# SKLAD_V_ZAGRUZCHIKE_V1 -- СТОЛ ЖИВЁТ ПРИ ЖИТЕЛЕ.
# Раньше стол был списком сессии: закрыл окно -- пусто, а файлы на
# диске остались навсегда. Стол -- это то, что человек сейчас
# разбирает, значит и лежать он должен при человеке.
_STOL_IMYA = "стол_академии.json"


def _stol_chitat(dom: Path) -> list:
    if not dom:
        return []
    return _read_json(dom / _STOL_IMYA, []) or []


def _stol_pisat(dom: Path, stol: list) -> None:
    if not dom:
        return
    try:
        _write_json(dom / _STOL_IMYA, stol)
    except Exception as e:
        print(f"[СТОЛ] не сохранился: {e}")'''


# 3. состояние: стол вместо списка сессии ───────────────────
STARO_3 = '''        "руда": [],          # что принял загрузчик за эту сессию'''

NOVO_3 = '''        # SKLAD_V_ZAGRUZCHIKE_V1: имя поля прежнее -- чтение и уроки
        # его знают и менять их этим патчем незачем. Изменилось, ОТКУДА
        # оно берётся: не список сессии, а стол из дома студента.
        "руда": [],
        "источник": "", "подпись": "", "тема": "",'''


# 4. показ стола: ключ виден ────────────────────────────────
STARO_4 = '''                ikona = "🖼" if r["вид"] == "изображение" else "📄"
                cvet = "rgba(189,0,255,0.9)" if r["вид"] == "изображение" else "rgba(0,204,255,0.9)"'''

NOVO_4 = '''                ikona = "🖼" if r["вид"] == "изображение" else "📄"
                cvet = "rgba(189,0,255,0.9)" if r["вид"] == "изображение" else "rgba(0,204,255,0.9)"
                # SKLAD_V_ZAGRUZCHIKE_V1: ключ карточки виден глазами --
                # по нему житель её и достанет потом рукой.
                _kl = r.get("ключ", "")
                _pd = r.get("подпись", "")'''


STARO_5 = '''                    <div style="color:rgba(255,255,255,0.6);font-size:9px;margin-top:2px;
                                word-break:break-all;">{r["имя"]}</div>
                  </div>\'\'\')'''

NOVO_5 = '''                    <div style="color:rgba(255,255,255,0.6);font-size:9px;margin-top:2px;
                                word-break:break-all;">{r["имя"]}</div>
                    {f'<div style="color:rgba(0,255,136,0.65);font-size:9px;margin-top:2px;word-break:break-all;">🔑 {_kl}</div>' if _kl else ''}
                    {f'<div style="color:rgba(255,255,255,0.45);font-size:9px;margin-top:1px;">{_pd}</div>' if _pd else ''}
                  </div>\'\'\')'''


# 5. приёмка -> карточка на склад ───────────────────────────
STARO_6 = '''        kb = len(data) / 1024
        state["руда"].append({
            "имя": imya, "вид": vid, "путь": str(dest),
            "размер": f"{kb:.0f} КБ",
            "когда": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        })
        update_ruda_list()'''

NOVO_6 = '''        kb = len(data) / 1024

        # SKLAD_V_ZAGRUZCHIKE_V1: файл лёг на диск -- теперь заводим на
        # него КАРТОЧКУ. Подпись ставит только Шеф: не заполнил поля --
        # карточка ляжет без подписи и будет искаться по источнику.
        # Машина за него не сочиняет.
        _klyuch, _put_karty = "", str(dest)
        if _sklad is not None:
            try:
                _ist = (state.get("источник") or "").strip()
                _klyuch = _sklad.polozhit(
                    put_faila=dest,
                    otkuda=_ist or f"положено в Академии: {imya}",
                    podpis=(state.get("подпись") or "").strip(),
                    tema=(state.get("тема") or "").strip(),
                    podpisal="Шеф",
                    klyuch=_sklad.sdelat_klyuch(_ist or "академия", "",
                                                Path(imya).stem))
                _k = _sklad.kartochka(_klyuch)
                if _k.get("файл"):
                    _put_karty = str(_sklad._MATERIALY / _k["файл"])
            except Exception as _e_sk2:
                print(f"[СКЛАД] карточка не легла ({_e_sk2}) -- "
                      f"файл на диске остался")

        _zapis = {
            "имя": imya, "вид": vid, "путь": _put_karty,
            "размер": f"{kb:.0f} КБ",
            "ключ": _klyuch,
            "подпись": (state.get("подпись") or "").strip(),
            "когда": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        state["руда"].append(_zapis)
        _m_stol = _mesto_row(mesta, state["активное_место"])
        if _m_stol and _m_stol["занято"]:
            _stol_pisat(_m_stol["дом"], state["руда"])
        update_ruda_list()'''


# 6. картинка больше не валится в историю сырьём ────────────
STARO_7 = '''            # AKADEMIA_KARTINKA_V_ISTORII_V1 (15.09, Шеф+София): сама
            # картинка ложится в историю ОДИН раз, здесь, как обычное
            # сообщение — молча, без слов. Дальше она едет с историей
            # естественно, её не нужно объяснять заново на каждый вызов.
            try:
                _mime_p = _KARTINKA_MIME_STOL.get(ext, "image/png")
                _url_p = (f"data:{_mime_p};base64,"
                          f"{base64.b64encode(dest.read_bytes()).decode('ascii')}")
                state["чат"].append({"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": _url_p}},
                ]})
            except Exception as _ie:
                print(f"[СТОЛ] картинка не легла в историю ({_ie})")
            ui.notify(f"🖼 Принято: {imya}", type="info")'''

NOVO_7 = '''            # SKLAD_V_ZAGRUZCHIKE_V1 (15.09): СНЯТО.
            # Здесь картинка клалась в историю чата отдельным
            # сообщением -- и рисовалка чата, умеющая показывать только
            # строку, вываливала на экран весь PNG буквами. Замысел был
            # верный (картинка должна жить в истории, а не собираться
            # заново на каждый вызов), но хранить её надо на складе и
            # доставать по ключу, а не держать сырьём в ленте.
            ui.notify(f"🖼 Принято: {imya}", type="info")'''


# 7. CLEAR убирает стол и у жителя тоже ─────────────────────
STARO_8 = '''    def clear_ruda():
        state["руда"] = []
        update_ruda_list()
        ui.notify("Список очищен (файлы на диске остались)", type="info")'''

NOVO_8 = '''    def clear_ruda():
        # SKLAD_V_ZAGRUZCHIKE_V1: со стола убираем, со СКЛАДА -- нет.
        # Карточки остаются: склад не расходуется, и то, что один убрал
        # со своего стола, другому по-прежнему доступно.
        state["руда"] = []
        _m_cl = _mesto_row(mesta, state["активное_место"])
        if _m_cl and _m_cl["занято"]:
            _stol_pisat(_m_cl["дом"], [])
        update_ruda_list()
        ui.notify("Стол убран (карточки на складе остались)", type="info")'''


# 8. смена места -> свой стол ───────────────────────────────
STARO_9 = '''    def switch_mesto(n: int):
        m = _mesto_row(mesta, n)
        state["активное_место"] = n
        update_avatar()'''

NOVO_9 = '''    def switch_mesto(n: int):
        m = _mesto_row(mesta, n)
        state["активное_место"] = n
        # SKLAD_V_ZAGRUZCHIKE_V1: у каждого студента свой стол, и он
        # ждёт его на месте -- хоть через неделю.
        state["руда"] = _stol_chitat(m["дом"]) if (m and m["занято"]) else []
        update_ruda_list()
        update_avatar()'''


# 9. поля подписи над загрузчиком ───────────────────────────
STARO_10 = '''                    ui.html('<div style="padding:4px 16px 6px 16px;color:rgba(255,255,255,0.35);'
                            'font-size:9px;line-height:1.5;">текст → на просев · '
                            'изображение → на разбор</div>')'''

NOVO_10 = '''                    # SKLAD_V_ZAGRUZCHIKE_V1: подпись ставит ТОЛЬКО Шеф.
                    # Источник -- короткое имя, из него собирается ключ
                    # («вильямс» + «gl07_str11» = вильямс/gl07_str11).
                    ui.html('<div style="padding:4px 16px 2px 16px;color:rgba(255,255,255,0.35);'
                            'font-size:9px;line-height:1.5;">подпишу сам — '
                            'машина за меня не сочиняет</div>')

                    def _pole(imya_polya, podskazka):
                        def _menyat(e, k=imya_polya):
                            state[k] = e.value or ""
                        return ui.input(placeholder=podskazka,
                                        on_change=_menyat).props(
                            "dense borderless dark").style(
                            "margin:2px 12px; width:calc(100% - 24px); "
                            "font-size:11px; color:rgba(255,255,255,0.85); "
                            "background:rgba(255,255,255,0.05); "
                            "border:1px solid rgba(255,255,255,0.10); "
                            "border-radius:8px; padding:1px 8px;")

                    _pole("источник", "источник: вильямс, котин, скрин…")
                    _pole("подпись", "подпись: что тут нарисовано")
                    _pole("тема", "тема: трейдинг, психология…")'''


ZAMENY = [
    ("подключение склада", STARO_1, NOVO_1),
    ("стол при жителе", STARO_2, NOVO_2),
    ("состояние", STARO_3, NOVO_3),
    ("показ стола: ключ", STARO_4, NOVO_4),
    ("показ стола: строки", STARO_5, NOVO_5),
    ("приёмка -> карточка", STARO_6, NOVO_6),
    ("картинка не в историю", STARO_7, NOVO_7),
    ("CLEAR", STARO_8, NOVO_8),
    ("смена места -> свой стол", STARO_9, NOVO_9),
    ("поля подписи", STARO_10, NOVO_10),
]


def main():
    print("=" * 58)
    print("СКЛАД В ЗАГРУЗЧИК АКАДЕМИИ")
    print("=" * 58)

    fajl = _nayti_kabinet()
    if fajl is None:
        return
    print(f"\nфайл: {fajl.relative_to(_KOREN)}")

    tekst = fajl.read_text(encoding="utf-8")

    if MARKER in tekst:
        print("\n✓ патч уже стоит — ничего не делаю.")
        return

    # проверка, что склад лежит рядом
    sklad_py = fajl.parent / "sklad.py"
    if not sklad_py.exists():
        print(f"\n⚠ рядом нет sklad.py ({sklad_py.parent.name}/sklad.py).")
        print("  Положи его туда и запусти снова — без него патч бессмыслен.")
        return
    print(f"склад: {sklad_py.relative_to(_KOREN)} — на месте")

    print("\n--- ЗАМЕНЫ ---")
    ne_nashlos = []
    for imya, staro, _novo in ZAMENY:
        n = tekst.count(staro)
        znak = "✓" if n == 1 else ("⚠ НЕ НАЙДЕНО" if n == 0 else f"⚠ {n} совпадений")
        print(f"  {znak}  {imya}")
        if n != 1:
            ne_nashlos.append(imya)

    if ne_nashlos:
        print(f"\n⚠ не сошлось: {', '.join(ne_nashlos)}")
        print("  Файл отличается от того, по которому патч собран.")
        print("  Ничего не тронул — покажи мне файл, пересоберу.")
        return

    novyy = tekst
    for _imya, staro, novo in ZAMENY:
        novyy = novyy.replace(staro, novo, 1)
    novyy = novyy.rstrip() + f"\n\n{MARKER} - marker\n"

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"\n⚠ после правок файл не разбирается: строка {e.lineno}: {e.msg}")
        print("  На диск НЕ писал. Ничего не сломано.")
        return
    print("\n  ast.parse — чисто")

    bak = fajl.with_suffix(fajl.suffix + ".bak_sklad")
    shutil.copy2(fajl, bak)
    fajl.write_text(novyy, encoding="utf-8")
    print(f"  бэкап:  {bak.name}")
    print(f"  записан: {fajl.name}")

    print("\n✓ готово. Что смотреть глазами:")
    print("  1. Открой /akademia — над загрузчиком три поля.")
    print("  2. Впиши источник и подпись, закинь картинку.")
    print("     В списке слева под именем появится 🔑 ключ.")
    print("  3. Простыни из букв в чате больше нет.")
    print("  4. Закрой окно, открой заново — стол на месте.")
    print("  5. python proverka_sklada.py — карточка лежит на складе.")
    print("=" * 58)


if __name__ == "__main__":
    main()
    try:
        input("\nEnter — закрыть: ")
    except Exception:
        pass

# POSTAVIT_SKLAD_V_ZAGRUZCHIK_V1 - marker
