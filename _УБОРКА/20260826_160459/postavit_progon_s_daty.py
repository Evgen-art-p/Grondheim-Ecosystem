# -*- coding: utf-8 -*-
"""
postavit_progon_s_daty.py · MARKER: PROGON_S_DATY_V1

ЗАЧЕМ
─────
Прогон всегда искал места от СЕГОДНЯ назад и брал самые свежие. Значит
попасть в конкретный кусок истории было нельзя: чтобы дойти до апреля,
пришлось бы ставить полсотни мест и платить за все.

А смотреть в конкретное место надо. Замер показал, где структура
проходит целиком — от точки до отката:

    точка 2026.04.27 12:00 → волна 30.04 00:00 → откат 30.04 20:00
    точка 2026.07.09 08:00 → волна 13.07 04:00 → откат 15.07 04:00

Двенадцать таких мест за полтора года. Дойти до них через «свежие
пять» невозможно.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
Рядом с полем «ловить» встаёт поле «с даты». Пусто — всё как было,
ищем от сегодня. Заполнено — искатель встаёт в этот момент истории и
ищет назад от него.

Формат свободный, как пишет терминал:

    2026.05.05          (начало дня)
    2026.05.05 12:00
    2026-05-05 12:00
    05.05.2026

Дата уходит искателю тем же полем `do_momenta`, которое у него было с
самого начала, — ничего нового в поиске не появилось, просто до него
дотянулась рука из кабинета.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py postavit_progon_s_daty.py   (или --suho)
"""
import ast
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "PROGON_S_DATY_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return (p / "Биржа" / "ui_torg.py").exists()


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


# ── 1. поле в шапке, рядом с «ловить» ────────────────────────

YAKOR_POLE = '''                        toolbar_refs["bars_input"] = ui.element("div").style("display:none;align-items:center;")'''

NOV_POLE = '''                        # PROGON_S_DATY_V1: поле «с даты». Пусто — ищем
                        # от сегодня, как было. Заполнено — искатель
                        # встаёт в этот момент истории и ищет назад.
                        toolbar_refs["ot_daty_label"] = ui.element("div").style("display:none;align-items:center;gap:5px;")
                        with toolbar_refs["ot_daty_label"]:
                            ui.label("с даты:").style("color:rgba(255,255,255,0.45);font-size:11px;")
                        toolbar_refs["ot_daty_input"] = ui.element("div").style("display:none;align-items:center;")
                        with toolbar_refs["ot_daty_input"]:
                            def _on_daty_change(e):   # PROGON_S_DATY_V1
                                state["progon_ot_daty"] = (e.value or "").strip()
                            ui.input(
                                value="", placeholder="2026.04.28",
                                on_change=_on_daty_change,
                            ).props(
                                'dense outlined '
                                'input-style="color:rgba(0,204,255,0.95);'
                                'font-family:JetBrains Mono;font-size:12px;'
                                'text-align:center;padding:0 2px;"'
                            ).style("width:140px;")

                        toolbar_refs["bars_input"] = ui.element("div").style("display:none;align-items:center;")'''

# ── 2. показывать поле там же, где «ловить» ──────────────────

YAKOR_VID = '''        skolko = int(state.get("bars_to_live") or 1)'''

NOV_VID = '''        skolko = int(state.get("bars_to_live") or 1)
        _ot_daty = _razobrat_datu(state.get("progon_ot_daty") or "")'''

# ── 3. отдать дату искателю ──────────────────────────────────

YAKOR_ISKAT = '''                spisok = await loop.run_in_executor(
                    None, lambda s=_sym, t=_tf: _kd.iskat(
                        s, t, skolko=skolko, govorit=print))'''

NOV_ISKAT = '''                # PROGON_S_DATY_V1: пусто — от сегодня, как было.
                spisok = await loop.run_in_executor(
                    None, lambda s=_sym, t=_tf: (
                        _kd.iskat(s, t, skolko=skolko, govorit=print,
                                  do_momenta=_ot_daty)
                        if _ot_daty else
                        _kd.iskat(s, t, skolko=skolko, govorit=print)))'''

# ── 4. поле видно там же, где «ловить» ──────────────────────

YAKOR_VIDIMOST = '''        for key in ("bars_input", "stop_btn", "bars_label",
                    "learn_btn"):   # TORG_LEARN_SWITCH_V1'''

NOV_VIDIMOST = '''        for key in ("bars_input", "stop_btn", "bars_label",
                    "ot_daty_label", "ot_daty_input",   # PROGON_S_DATY_V1
                    "learn_btn"):   # TORG_LEARN_SWITCH_V1'''

# ── 5. разбор даты, как пишет терминал ───────────────────────

YAKOR_RUKA = '''    def _shagnut(skolko):'''

NOV_RUKA = '''    def _razobrat_datu(s: str) -> str:
        """PROGON_S_DATY_V1: понять дату, как её пишет человек.

        Отдаём в том виде, в каком её держит история: «ГГГГ.ММ.ДД ЧЧ:ММ».
        Не разобралась — возвращаем пусто, и прогон идёт от сегодня, как
        и раньше. Ругаться на человека за формат мы не будем.
        """
        s = (s or "").strip().replace("-", ".").replace("/", ".")
        if not s:
            return ""
        chasti = s.split()
        d = chasti[0]
        vremya = chasti[1] if len(chasti) > 1 else "00:00"
        kuski = [k for k in d.split(".") if k]
        if len(kuski) != 3:
            print(f"[ПРОГОН] дату «{s}» не разобрал — иду от сегодня")
            return ""
        if len(kuski[0]) == 4:                 # 2026.04.28
            god, mes, den = kuski
        else:                                  # 28.04.2026
            den, mes, god = kuski
        if ":" not in vremya:
            vremya = "00:00"
        try:
            itog = f"{int(god):04d}.{int(mes):02d}.{int(den):02d} {vremya}"
        except ValueError:
            print(f"[ПРОГОН] дату «{s}» не разобрал — иду от сегодня")
            return ""
        print(f"[ПРОГОН] ищу места до {itog}")
        return itog

    def _shagnut(skolko):'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}\n")
    f = koren / "Биржа" / "ui_torg.py"
    t = f.read_text(encoding="utf-8")

    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0

    pary = [(YAKOR_RUKA, NOV_RUKA), (YAKOR_POLE, NOV_POLE),
            (YAKOR_VIDIMOST, NOV_VIDIMOST),
            (YAKOR_VID, NOV_VID), (YAKOR_ISKAT, NOV_ISKAT)]
    for yakor, _ in pary:
        n = t.count(yakor)
        if n != 1:
            print(f"✗ якорь найден {n} раз — жду ровно один")
            print(f"  {yakor.strip().splitlines()[0][:70]}")
            return 1

    novyy = t
    for yakor, zamena in pary:
        novyy = novyy.replace(yakor, zamena, 1)

    novyy += f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ после правки не разбирается: {e}")
        return 1
    if SUHO:
        print("· правка готова (сухой прогон)")
        return 0

    bak = f.with_suffix(f".py.bak_sdaty_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(f, bak)
    f.write_text(novyy, encoding="utf-8")
    try:
        py_compile.compile(str(f), doraise=True)
    except Exception as e:
        shutil.copy2(bak, f)
        print(f"✗ НЕ компилируется ({e}) — откатил из {bak.name}")
        return 1
    print(f"✓ поле «с даты» встало (копия: {bak.name})")
    print("\nВ шапке кабинета, рядом с «ловить», появилось поле «с даты».")
    print("Пусто — прогон идёт от сегодня, как раньше.")
    print("\nЧтобы увидеть всю структуру целиком, поставь:")
    print("   с даты: 2026.05.01        ловить: 2")
    print("   (точка 27.04 → волна 30.04 00:00 → откат 30.04 20:00)")
    print("\nВ консоли будет строка «[ПРОГОН] ищу места до 2026.05.01 00:00».")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
