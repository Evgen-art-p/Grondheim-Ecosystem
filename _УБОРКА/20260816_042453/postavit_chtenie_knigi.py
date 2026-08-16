# -*- coding: utf-8 -*-
"""
postavit_chtenie_knigi.py · MARKER: CHTENIE_KNIGI_V1

ЧТО БЫЛО НЕ ТАК
───────────────
Длинный текст резался МОЛЧА.

    житель дома / Брат — первые 50 000 знаков (≈25 страниц)
    Академия           — первые 20 000 знаков (≈10 страниц)

Всё, что дальше, просто не доходило. Ни предупреждения, ни строки в
чате: житель честно рассказывал, что понял из начала, и даже не знал,
что была ещё книга. Самое неприятное тут — не потолок, а тишина.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
1. `ГОРОД/chtenie.py` — общая рука чтения на весь город:
   · честно читает файл (UTF-8 → cp1251 для русских книг из Windows),
     бинарь отсекает;
   · режет длинный текст на части ПО АБЗАЦАМ, а не по счёту знаков —
     мысль не рвётся посреди фразы;
   · говорит вслух, сколько частей и сколько знаков.

2. Житель ЧИТАЕТ КНИГУ ЦЕЛИКОМ. Файл больше части — читает по
   очереди, помня, что было в предыдущих, и в конце сводит всё в один
   вывод. В память ложится ОДИН осадок на книгу, а не двадцать
   обрывков. В чате видно ход: «часть 3 из 12».

3. Академия — то же самое, и её потолок подтянут к общему: ученику
   давали вдвое меньше, чем жителю дома, безо всякой причины.

ЧЕГО ПАТЧ НЕ ТРОГАЕТ
────────────────────
Размер части (50 000 знаков) не меняю: у нынешней модели окно много
больше, но части заодно держат внимание — по опыту Академии 05.08
сжатие вредит определениям, а не объёму. Захочешь другой размер —
одна строка в `chtenie.py`.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py postavit_chtenie_knigi.py   (или --suho)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "CHTENIE_KNIGI_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "жители" / "ui_zhitel.py").exists()
            and (p / "Академия" / "ui_akademia.py").exists())


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


CHTENIE_PY = '''# -*- coding: utf-8 -*-
# CHTENIE_KNIGI_V1
"""
ЧТЕНИЕ ДЛИННОГО — общая рука города.

ЗАЧЕМ
    Раньше длинный текст резался молча: житель получал первые 50 000
    знаков, Академия — 20 000, а хвост исчезал без единого слова.
    Человек честно рассказывал, что понял из начала, и не знал, что
    была ещё книга. Тишина здесь хуже потолка.

ЗАКОН ЭТОГО ФАЙЛА
    Рука ЧИТАЕТ И РЕЖЕТ. Она не думает и не выжимает — думает тот,
    кому текст принесли. Режет по абзацам: мысль не должна рваться
    посреди фразы ради ровного счёта знаков.
"""
from __future__ import annotations

from pathlib import Path

# Размер одной части. Не потолок книги — книга читается целиком,
# просто по частям. У нынешних моделей окно много больше, но части
# держат внимание и дают ровный осадок в память.
KUSOK = 50000


def prochitat(path) -> str:
    """Честный текст файла. Не текст — пустая строка, без выдумок.

    UTF-8 строго → cp1251 (русские книги из Windows) → utf-8 с
    заменой. Нули или море замен — это не книга, а картинка или архив.
    """
    try:
        raw = Path(path).read_bytes()
    except Exception:
        return ""
    t = ""
    try:
        t = raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            t = raw.decode("cp1251")
        except UnicodeDecodeError:
            t = raw.decode("utf-8", errors="replace")
    if "\\x00" in t:
        return ""
    if "\\ufffd" in t and len(t) > 200 and t.count("\\ufffd") / len(t) > 0.10:
        return ""
    return t


def narezat(tekst: str, kusok: int = KUSOK) -> list:
    """Порезать по абзацам на части не длиннее kusok.

    Абзац длиннее части (сплошная простыня без пустых строк) режется
    по предложениям, а уж если и предложение великанское — по счёту.
    Лучше грубый разрез, чем потерянный хвост.
    """
    tekst = tekst or ""
    if len(tekst) <= kusok:
        return [tekst] if tekst.strip() else []

    chasti, tek = [], ""
    for abzac in tekst.split("\\n\\n"):
        if len(abzac) > kusok:
            if tek:
                chasti.append(tek)
                tek = ""
            fraza = ""
            for kus in abzac.replace("! ", "!\\x01").replace("? ", "?\\x01") \\
                            .replace(". ", ".\\x01").split("\\x01"):
                if len(fraza) + len(kus) + 1 > kusok:
                    if fraza:
                        chasti.append(fraza)
                    while len(kus) > kusok:
                        chasti.append(kus[:kusok])
                        kus = kus[kusok:]
                    fraza = kus
                else:
                    fraza = (fraza + " " + kus).strip()
            if fraza:
                tek = fraza
            continue
        if len(tek) + len(abzac) + 2 > kusok:
            chasti.append(tek)
            tek = abzac
        else:
            tek = (tek + "\\n\\n" + abzac) if tek else abzac
    if tek.strip():
        chasti.append(tek)
    return [c for c in chasti if c.strip()]


def skazat_o_razmere(imya_fajla: str, tekst: str, chastey: int) -> str:
    """Строка для чата: сколько знаков и на сколько частей поделили."""
    znakov = len(tekst)
    stranic = max(1, znakov // 2000)
    if chastey <= 1:
        return f"«{imya_fajla}» · {znakov} знаков (≈{stranic} стр.)"
    return (f"«{imya_fajla}» · {znakov} знаков (≈{stranic} стр.) — "
            f"читаю целиком, по частям: {chastey}")


# CHTENIE_KNIGI_V1 - marker
'''


# ═══════════════════════════════════════════════════════════
# ЖИТЕЛЬ: книга читается целиком
# ═══════════════════════════════════════════════════════════
ST_ZH = '''            else:
                tekst = _prochitat_fail(fp)
                if not tekst.strip():
                    ui.notify(f"⚠ {fp.name}: пусто или не текст — пропускаю", color="warning")
                    continue
                messages = [
                    {"role": "system", "content": dusha},
                    {"role": "user", "content": _prompt_chtenia(fp.name, tekst, linza, lok_imya, professia)},  # ZHITEL_CHTENIE_MASKA_V1
                ]
            vyzhimka = await call_zhitel_llm(messages, state.get("model"))'''

NOV_ZH = '''            else:
                # CHTENIE_KNIGI_V1: читаем ЦЕЛИКОМ. Раньше брали первые
                # 50 000 знаков и молчали об остальном — житель даже не
                # знал, что была ещё книга.
                tekst = _chtenie.prochitat(fp)
                if not tekst.strip():
                    ui.notify(f"⚠ {fp.name}: пусто или не текст — пропускаю", color="warning")
                    continue
                _chasti = _chtenie.narezat(tekst)
                _skazano = _chtenie.skazat_o_razmere(fp.name, tekst,
                                                     len(_chasti))
                state["chat"].append({"role": "system", "content":
                                      f"📖 {_skazano}"})
                update_chat()
                if len(_chasti) > 1:
                    ui.notify(f"📖 {fp.name}: {len(_chasti)} частей",
                              color="info")
                messages = [
                    {"role": "system", "content": dusha},
                    {"role": "user", "content": _prompt_chtenia(fp.name, _chasti[0], linza, lok_imya, professia)},  # ZHITEL_CHTENIE_MASKA_V1
                ]
            vyzhimka = await call_zhitel_llm(messages, state.get("model"))
            # CHTENIE_KNIGI_V1: остальные части — по очереди, помня
            # прочитанное. В конце один общий вывод: в память должен
            # лечь ОДИН осадок на книгу, а не двадцать обрывков.
            if fp.suffix.lower() not in KARTINKA_EXT and len(_chasti) > 1:
                _kuski_vyvodov = [vyzhimka or ""]
                for _n, _ch in enumerate(_chasti[1:], 2):
                    state["chat"].append({"role": "system", "content":
                                          f"… часть {_n} из {len(_chasti)}"})
                    update_chat()
                    _msg = [
                        {"role": "system", "content": dusha},
                        {"role": "user", "content": (
                            f"Ты читаешь «{fp.name}» по частям. "
                            f"Это часть {_n} из {len(_chasti)}.\\n\\n"
                            f"Что ты вынес(ла) из прочитанного раньше:\\n"
                            + "\\n".join(f"— {x.strip()[:600]}"
                                        for x in _kuski_vyvodov if x.strip())
                            + f"\\n\\nПродолжение текста:\\n{_ch}\\n\\n"
                            f"Вынеси суть ЭТОЙ части своими словами. Не "
                            f"пересказывай то, что уже сказал(а) раньше.")},
                    ]
                    _v = await call_zhitel_llm(_msg, state.get("model"))
                    if _v and not _v.startswith("⚠"):
                        _kuski_vyvodov.append(_v)
                if len(_kuski_vyvodov) > 1:
                    _svod = [
                        {"role": "system", "content": dusha},
                        {"role": "user", "content": (
                            f"Ты дочитал(а) «{fp.name}» целиком — "
                            f"{len(_chasti)} частей. Вот что ты выносил(а) "
                            f"по ходу:\\n\\n"
                            + "\\n\\n".join(f"Часть {i}: {x.strip()}"
                                           for i, x in
                                           enumerate(_kuski_vyvodov, 1))
                            + "\\n\\nТеперь скажи одним куском, что ты вынес(ла) "
                            "из книги В ЦЕЛОМ — своими словами, живым "
                            "голосом. Это и останется у тебя в памяти.")},
                    ]
                    _itog = await call_zhitel_llm(_svod, state.get("model"))
                    if _itog and not _itog.startswith("⚠"):
                        vyzhimka = _itog'''


# ═══════════════════════════════════════════════════════════
# АКАДЕМИЯ: тот же потолок и то же чтение целиком
# ═══════════════════════════════════════════════════════════
ST_AK = '''                try:
                    tekst = fp.read_bytes().decode("utf-8", errors="replace")
                except Exception:
                    tekst = ""
                if not tekst.strip():
                    ui.notify(f"⚠ {fp.name}: пусто — пропускаю", type="warning")
                    continue
                vopros = (f"Материал: {fp.name}\\n{tekst[:20000]}\\n\\n"
                         f"Прочитай и вынеси концентрат — 5-8 строк, суть плюс твой "
                         f"личный отклик через свою натуру.")'''

NOV_AK = '''                # CHTENIE_KNIGI_V1: читаем честно и ЦЕЛИКОМ. Раньше
                # ученику доставались первые 20 000 знаков — вдвое
                # меньше, чем жителю дома, и молча.
                tekst = _chtenie.prochitat(fp)
                if not tekst.strip():
                    ui.notify(f"⚠ {fp.name}: пусто — пропускаю", type="warning")
                    continue
                _chasti = _chtenie.narezat(tekst)
                state["чат"].append({"role": "system", "content":
                                     "📖 " + _chtenie.skazat_o_razmere(
                                         fp.name, tekst, len(_chasti))})
                update_chat()
                _hvost = ("" if len(_chasti) == 1 else
                          f" Это часть 1 из {len(_chasti)}, продолжение "
                          f"будет дальше.")
                vopros = (f"Материал: {fp.name}\\n{_chasti[0]}\\n\\n"
                         f"Прочитай и вынеси концентрат — 5-8 строк, суть плюс твой "
                         f"личный отклик через свою натуру.{_hvost}")'''

ST_AK_ZOV = '''            vyzhimka = await _zvat_llm_akademii(messages, state.get("model"))
            if not vyzhimka or vyzhimka.startswith("⚠"):'''

NOV_AK_ZOV = '''            vyzhimka = await _zvat_llm_akademii(messages, state.get("model"))
            # CHTENIE_KNIGI_V1: остальные части — по очереди, с памятью
            # о прочитанном, и общий свод в конце.
            if vid == "текст" and len(_chasti) > 1 and vyzhimka \\
                    and not vyzhimka.startswith("⚠"):
                _vyvody = [vyzhimka]
                for _n, _ch in enumerate(_chasti[1:], 2):
                    state["чат"].append({"role": "system", "content":
                                         f"… часть {_n} из {len(_chasti)}"})
                    update_chat()
                    _m = [{"role": "system", "content": dusha + rol},
                          {"role": "user", "content": (
                              f"Продолжаешь «{fp.name}», часть {_n} из "
                              f"{len(_chasti)}.\\n\\nЧто вынес(ла) раньше:\\n"
                              + "\\n".join(f"— {x.strip()[:600]}"
                                          for x in _vyvody)
                              + f"\\n\\nДальше:\\n{_ch}\\n\\nКонцентрат ЭТОЙ "
                              f"части — 5-8 строк, без повтора прежнего.")}]
                    _v = await _zvat_llm_akademii(_m, state.get("model"))
                    if _v and not _v.startswith("⚠"):
                        _vyvody.append(_v)
                _m2 = [{"role": "system", "content": dusha + rol},
                       {"role": "user", "content": (
                           f"Ты дочитал(а) «{fp.name}» целиком. По ходу "
                           f"выносил(а):\\n\\n"
                           + "\\n\\n".join(f"Часть {i}: {x.strip()}"
                                          for i, x in enumerate(_vyvody, 1))
                           + "\\n\\nСкажи одним куском, что вынес(ла) из "
                           "материала В ЦЕЛОМ. Это и останется в памяти.")}]
                _itog = await _zvat_llm_akademii(_m2, state.get("model"))
                if _itog and not _itog.startswith("⚠"):
                    vyzhimka = _itog
            if not vyzhimka or vyzhimka.startswith("⚠"):'''


def _import_stroka(imya_modulya: str) -> str:
    return (f'\n# CHTENIE_KNIGI_V1: общая рука чтения города\n'
            f'try:\n'
            f'    import sys as _sys_ch\n'
            f'    from pathlib import Path as _Path_ch\n'
            f'    _gorod_ch = str(_Path_ch(__file__).resolve().parent.parent '
            f'/ "ГОРОД")\n'
            f'    if _gorod_ch not in _sys_ch.path:\n'
            f'        _sys_ch.path.insert(0, _gorod_ch)\n'
            f'    import chtenie as _chtenie\n'
            f'except Exception as _e_ch:  # пусть кабинет живёт и без неё\n'
            f'    _chtenie = None\n'
            f'    print(f"[ЧТЕНИЕ] рука чтения не подключилась: {{_e_ch}}")\n')


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    chtenie = koren / "ГОРОД" / "chtenie.py"
    zhitel = koren / "жители" / "ui_zhitel.py"
    akadem = koren / "Академия" / "ui_akademia.py"

    print("\n1. Общая рука чтения — ГОРОД/chtenie.py")
    if chtenie.exists() and MARKER in chtenie.read_text(encoding="utf-8"):
        print("  · уже лежит")
    else:
        ast.parse(CHTENIE_PY)
        if not SUHO:
            chtenie.write_text(CHTENIE_PY, encoding="utf-8")
        print("  ✓ положена (читает, режет по абзацам, говорит вслух)")

    for put, imya, pary in ((zhitel, "житель", [(ST_ZH, NOV_ZH)]),
                            (akadem, "Академия", [(ST_AK, NOV_AK),
                                                  (ST_AK_ZOV, NOV_AK_ZOV)])):
        print(f"\n{'2' if imya == 'житель' else '3'}. {imya.capitalize()}: "
              f"книга читается целиком")
        t = put.read_text(encoding="utf-8")
        if MARKER in t:
            print("  · маркер уже стоит")
            continue
        beda = [st[:40].replace("\n", " ") for st, _ in pary
                if t.count(st) != 1]
        if beda:
            for b in beda:
                print(f"  ✗ якорь не найден дословно → «{b}…»")
            return 1
        novyy = t
        for st, nov in pary:
            novyy = novyy.replace(st, nov, 1)
        # импорт руки — после последней строки импортов сверху файла
        stroki = novyy.split("\n")
        vstavka = 0
        for i, s in enumerate(stroki[:80]):
            if s.startswith(("import ", "from ")):
                vstavka = i + 1
        stroki.insert(vstavka, _import_stroka(imya))
        novyy = "\n".join(stroki) + f"\n# {MARKER} - marker\n"
        try:
            ast.parse(novyy)
        except SyntaxError as e:
            print(f"  ✗ после правки не разбирается: {e}")
            return 1
        if SUHO:
            print("  · правка готова (сухой прогон)")
            continue
        shutil.copy2(put, put.with_suffix(
            f".py.bak_kniga_{datetime.now():%Y%m%d_%H%M%S}"))
        put.write_text(novyy, encoding="utf-8")
        print("  ✓ легло")

    if not SUHO:
        import py_compile
        for f in (chtenie, zhitel, akadem):
            try:
                py_compile.compile(str(f), doraise=True)
                print(f"  ✓ компилируется: {f.name}")
            except Exception as e:
                print(f"  ✗ НЕ компилируется {f.name}: {e}")
                return 1
        print("\nТеперь книга читается ЦЕЛИКОМ:")
        print("  в чате видно «12 частей», потом ход «часть 3 из 12»,")
        print("  в конце — один общий вывод, он и ложится в память.")
        print("  Академия сравнялась с домом: было 20 000, стало столько же.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
