# -*- coding: utf-8 -*-
"""
kartinka_shefa.py — Шеф показывает жителю ЛЮБУЮ картинку через
загрузчик кабинета, и она не протухает.

Было: загрузчик брал только CSV котировок; «Взгляд» отдавал жителю
лишь кадр города и только 15 минут.

Стало:
  1. Биржа/ui_torg.py — перетащил в загрузчик .png/.jpg/.webp: файл
     ложится в Биржа/показанное/ и встаёт как «показал Шеф». Свой
     график из терминала, рисунок из книги, её же кадр с твоими
     линиями. CSV работает как раньше.
  2. Мозг A06 — срок 15 минут снят: показанное лежит, пока не
     покажешь другое. Взамен картинка идёт ТОЛЬКО в разговоре; в
     прогоне она ехала бы в каждое место и путалась с рабочим кадром.

Запуск: положить в корень репы, запустить. Сам находит оба файла,
сперва проверяет оба, потом пишет. Копии `.bak_kartinka_shefa`.
Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "KARTINKA_SHEFA_V1"
PUT_UI = os.path.join("Биржа", "ui_torg.py")
PUT_MOZG = os.path.join("GRONDHEIM_CITY", "Биржа", "цеха", "торговый_хаос",
                        "слоты", "A06", "мозг.py")
U_STAROE = '        if not name.lower().endswith(".csv"):\n            ui.notify("Нужен CSV экспорта MT5", type="warning")\n            return\n'
U_NOVOE = '        # KARTINKA_SHEFA_V1: картинку Шеф показывает жителю, а не\n        # заряжает как котировки. Уходит тем же путём, что «Взгляд».\n        if name.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):\n            try:\n                from pathlib import Path as _Pk\n                from datetime import datetime as _dtk\n                _pap = _Pk(__file__).resolve().parent / "показанное"\n                _pap.mkdir(parents=True, exist_ok=True)\n                _dest = _pap / name\n                _dest.write_bytes(content)\n                from hooks import load_trading_state, save_trading_state\n                _tk = load_trading_state()\n                _tk["vzglyad_shefa"] = {\n                    "путь": str(_dest),\n                    "подпись": _Pk(name).stem,\n                    "когда": _dtk.now().isoformat(timespec="seconds"),\n                }\n                save_trading_state(_tk)\n                ui.notify(f"\\U0001f5bc Показываю жителю: {_Pk(name).stem}",\n                          type="positive")\n            except Exception as _ke:\n                ui.notify(f"Картинка не дошла: {_ke}", type="negative")\n            _up = files_ref.get("uploader")\n            if _up:\n                try:\n                    _up.reset()\n                except Exception:\n                    pass\n            return\n        if not name.lower().endswith(".csv"):\n            ui.notify("Нужен CSV экспорта MT5 или картинка", type="warning")\n            return\n'
M_DEF_STAROE = 'def _kadr_shefa() -> list:\n    """Картинка со «Взгляда» Шефа, если она свежая. Иначе пусто."""\n'
M_DEF_NOVOE = 'def _kadr_shefa(razgovor: bool = True) -> list:\n    """Картинка, которую показал Шеф. В работе не подкладывается.\n\n    KARTINKA_SHEFA_V1: срок в 15 минут снят по слову Шефа —\n    показанное лежит, пока он не покажет другое. Взамен оно идёт\n    ТОЛЬКО в разговоре: в прогоне картинка ехала бы в каждое\n    место и путалась бы с рабочим кадром.\n    """\n    if not razgovor:\n        return []\n'
M_SROK_STAROE = '        try:\n            kogda = datetime.fromisoformat(str(v.get("когда")))\n            if datetime.now() - kogda > timedelta(minutes=15):\n                return []      # старое — не всплывает посреди работы\n        except Exception:\n            pass\n'
M_IMPORT_STAROE = '        from datetime import datetime, timedelta\n'
M_ZOV_STAROE = '                            + _kadr_shefa()),\n'
M_ZOV_NOVOE = '                            + _kadr_shefa(razgovor=preambula is not None)),\n'


def pauza():
    try:
        input("\nНажми Enter, чтобы закрыть окно...")
    except Exception:
        pass


def godnyy(papka):
    return papka if (os.path.isfile(os.path.join(papka, PUT_UI)) and
                     os.path.isfile(os.path.join(papka, PUT_MOZG))) else None


def nayti():
    zdes = os.path.dirname(os.path.abspath(__file__))
    for papka in (zdes, os.getcwd()):
        if godnyy(papka):
            return papka
    kandidaty = []
    for koren in {os.path.dirname(zdes), os.path.dirname(os.getcwd())}:
        try:
            for imya in os.listdir(koren):
                p = os.path.join(koren, imya)
                if godnyy(p) and p not in kandidaty:
                    kandidaty.append(p)
        except Exception:
            pass
    if len(kandidaty) == 1:
        otv = input(f"Нашёл: {kandidaty[0]}\nЭтот? (Enter — да, н — нет): ")
        if otv.strip().lower() not in ("н", "n", "нет", "no"):
            return kandidaty[0]
    elif len(kandidaty) > 1:
        print("Нашёл несколько:")
        for i, p in enumerate(kandidaty, 1):
            print(f"  {i}. {p}")
        otv = input("Какой? Цифра: ").strip()
        if otv.isdigit() and 1 <= int(otv) <= len(kandidaty):
            return kandidaty[int(otv) - 1]
    otv = input("Перетащи сюда папку репы и нажми Enter:\n").strip().strip('"').strip("'")
    return godnyy(otv)


def prochest(put):
    with open(put, "rb") as f:
        t = f.read().decode("utf-8")
    return t.replace("\r\n", "\n"), "\r\n" in t


def pravit_ui(t):
    if t.count(U_STAROE) != 1:
        return None
    return t.replace(U_STAROE, U_NOVOE, 1)


def pravit_mozg(t):
    if (t.count(M_DEF_STAROE) != 1 or t.count(M_SROK_STAROE) != 1
            or t.count(M_IMPORT_STAROE) != 1 or t.count(M_ZOV_STAROE) != 2):
        return None
    t = t.replace(M_DEF_STAROE, M_DEF_NOVOE, 1)
    t = t.replace(M_SROK_STAROE, "", 1)
    t = t.replace(M_IMPORT_STAROE, "", 1)
    return t.replace(M_ZOV_STAROE, M_ZOV_NOVOE)


def zapisat(put, t, crlf):
    bak = put + ".bak_kartinka_shefa"
    if not os.path.exists(bak):
        shutil.copy2(put, bak)
    with open(put, "wb") as f:
        f.write((t.replace("\n", "\r\n") if crlf else t).encode("utf-8"))
    return bak


def main():
    repo = nayti()
    if not repo:
        print("✗ Не нашёл репу (нужны Биржа/ui_torg.py и мозг.py A06). Ничего не менял.")
        return
    p_ui = os.path.join(repo, PUT_UI)
    p_mozg = os.path.join(repo, PUT_MOZG)
    t_ui, crlf_ui = prochest(p_ui)
    t_mozg, crlf_mozg = prochest(p_mozg)
    if METKA in t_ui and METKA in t_mozg:
        print("✓ Уже накатано раньше — ничего не менял.")
        return
    n_ui = t_ui if METKA in t_ui else pravit_ui(t_ui)
    n_mozg = t_mozg if METKA in t_mozg else pravit_mozg(t_mozg)
    if n_ui is None or n_mozg is None:
        print("✗ Места нашлись не так, как ожидалось "
              f"({'ui_torg.py' if n_ui is None else 'мозг.py'}). Ничего не менял. Покажи Брату.")
        return
    for imya, t in (("ui_torg.py", n_ui), ("мозг.py", n_mozg)):
        try:
            ast.parse(t)
        except SyntaxError as e:
            print(f"✗ {imya} после правки не собирается: {e}. Ничего не менял.")
            return
    zapisany = []
    for put, t, staroe, crlf in ((p_ui, n_ui, t_ui, crlf_ui),
                                 (p_mozg, n_mozg, t_mozg, crlf_mozg)):
        if t == staroe:
            continue
        bak = zapisat(put, t, crlf)
        zapisany.append((put, bak))
        try:
            py_compile.compile(put, doraise=True)
        except py_compile.PyCompileError as e:
            for p, b in zapisany:
                shutil.copy2(b, p)
            print(f"✗ Не скомпилировалось, вернул как было: {e}")
            return
    for put, bak in zapisany:
        print(f"✓ {put}\n  копия до правки: {bak}")
    print("  Перетащи картинку в загрузчик кабинета — и спрашивай её словами.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
