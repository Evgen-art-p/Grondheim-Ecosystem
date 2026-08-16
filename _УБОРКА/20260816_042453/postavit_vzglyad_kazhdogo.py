# -*- coding: utf-8 -*-
"""
postavit_vzglyad_kazhdogo.py · MARKER: VZGLYAD_KAZHDOGO_V1

Две просьбы Шефа, которые я записал и не сделал. Делаю ровно их,
ничего попутно не строю.

═══ ПРОСЬБА 1: «взгляд каждого, как кликнул» ═══

БЫЛО. Кадр рисуется ТОЛЬКО кнопкой «👁 Взгляд» и всегда по полке —
`pokazat_kadr()` берёт `_aktivnyy_rynok()`, то есть выбранную слева
строку. Клик по пузырьку трейдера (`switch_agent`) кадр не трогает
вовсе: меняет аватар, показатели, отчёт — и всё.

Значит взгляд был один общий, левый, как Шеф и сказал. У Нины на
евро, у Синди на золоте, у Веры на фунте — а на экране один кадр
того, что выбрано на полке, и он не про них.

СТАЛО. Кликнул пузырёк — сразу видишь кадр ЕГО пары: его инструмент,
его этаж. Подпись под кадром говорит, чей это взгляд. Кнопка «Взгляд»
работает как работала, но тоже по активному трейдеру.

Нет пары (инструмент не задан или этаж не выбран) — кадра нет и
честно написано, чего не хватает. Чужой кадр вместо своего не
подсовываем: это ровно то враньё, из-за которого Шеф и заметил.

═══ ПРОСЬБА 2: «котировки на M15 сброс» ═══

БЫЛО. Выбранный на полке актив хранится НОМЕРОМ строки
(`state["active_asset"] = i`). Кнопка ТЕРМИНАЛ кладёт свежее в НАЧАЛО
списка (`aktivy + bylo`), старое съезжает вниз, а номер остаётся
прежним. Список сдвинулся под неподвижным номером — и выбор
указывает уже на другую строку. Терминал опрашивает этажи по порядку
`M15, M30, H1, H4, D1, W1`, первым идёт M15 — вот он и «сбрасывался».

СТАЛО. Перед перестройкой полки запоминаем выбор ИМЕНЕМ (символ +
этаж + источник) и после перестройки возвращаем курсор на него же.
Ушёл с полки — говорим об этом, а не подсовываем соседа. Номер
остался внутри как был, менять пол-кабинета не пришлось.

Та же защита поставлена загрузчику CSV и пересканированию папки —
они перестраивают тот же список и роняли выбор так же молча.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py postavit_vzglyad_kazhdogo.py   (или --suho)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "VZGLYAD_KAZHDOGO_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "Биржа" / "ui_torg.py").exists()
            and (p / "main.py").exists())


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
# 1. ПАМЯТЬ ПОЛКИ — выбор именем, а не номером
# ═══════════════════════════════════════════════════════════
ST_KADR = '''    def pokazat_kadr(put=None):
        """Рисует кадр и кладёт в верхнюю половину правой части.

        Модель не трогаем: Шеф смотрит, трейдер спит. Это и есть
        дешёвый способ проверить, читается ли картинка, ПЕРЕД тем как
        отдавать её глазу.
        """
        if not kadr_ref["element"]:
            return None
        symbol, tf = _aktivnyy_rynok()'''

NOV_KADR = '''    # ── VZGLYAD_KAZHDOGO_V1: память полки и пара активного ──
    def _klyuch_aktiva(a: dict) -> str:
        """Имя строки полки. Номер строки для этого не годится:
        ТЕРМИНАЛ кладёт свежее в НАЧАЛО списка, всё съезжает вниз, а
        номер остаётся — и выбор указывает уже на чужую строку. Так и
        получался вечный сброс на M15: он первый в опросе этажей."""
        if not a:
            return ""
        return (f"{a.get('symbol', '')}|{a.get('timeframe', '')}"
                f"|{a.get('источник', '')}")

    def _zapomnit_vybor() -> str:
        aktivy = state.get("loaded_assets") or []
        i = state.get("active_asset")
        if i is None or not (0 <= i < len(aktivy)):
            return ""
        return _klyuch_aktiva(aktivy[i])

    def _vernut_vybor(klyuch: str, tiho: bool = False):
        """Вернуть курсор на ту же строку после перестройки полки."""
        aktivy = state.get("loaded_assets") or []
        if not aktivy:
            state["active_asset"] = None
            return
        if klyuch:
            for j, a in enumerate(aktivy):
                if _klyuch_aktiva(a) == klyuch:
                    state["active_asset"] = j
                    return
            if not tiho:
                _tiho(ui.notify, "⚠ прежний актив с полки ушёл — "
                                 "выбери заново", type="warning")
                state["active_asset"] = None
                return
        if state.get("active_asset") is None:
            state["active_asset"] = 0

    def _para_aktivnogo() -> tuple:
        """(инструмент, этаж, чей, чего не хватает) активного трейдера.

        Взгляд принадлежит трейдеру, а не полке: у каждого свой
        инструмент и свой этаж, и смотреть Шеф должен именно на его
        картинку, иначе проверить его нечем.
        """
        aid = state.get("active_agent") or ""
        imya = _agent_label(roster, aid) or aid
        if aid not in ("A06", "A07", "A08"):
            s, t = _aktivnyy_rynok()
            return s, t, "", ""
        try:
            import vybor
            r = vybor.rabota_dlya(tseh_id, aid)
            if r.get("инструмент") and r.get("этаж"):
                return r["инструмент"], r["этаж"], imya, ""
            return "", "", imya, vybor.pochemu_molchit(tseh_id, aid)
        except Exception as e:
            return "", "", imya, f"пара не прочиталась ({e})"

    def pokazat_kadr(put=None):
        """Рисует кадр АКТИВНОГО ТРЕЙДЕРА и кладёт направо.

        VZGLYAD_KAZHDOGO_V1: раньше брали пару с полки — и на экране
        висел один общий кадр, одинаковый для всех троих, хотя
        работают они разными инструментами. Теперь кадр про того,
        чей пузырёк нажат.

        Модель не трогаем: Шеф смотрит, трейдер спит.
        """
        if not kadr_ref["element"]:
            return None
        symbol, tf, chey, nehvatka = _para_aktivnogo()
        if nehvatka:
            kadr_ref["element"].clear()
            with kadr_ref["element"]:
                ui.label(f"👁 {chey}: смотреть нечего").style(
                    "color:rgba(255,180,120,0.85); font-size:13px;")
                ui.label(nehvatka).style(
                    "color:rgba(255,255,255,0.55); font-size:11px;")
            return None'''

ST_PODPIS = '''            ui.label(f"👁 {symbol} · {tf} · {_kran}{_kogda}").style('''
NOV_PODPIS = '''            # VZGLYAD_KAZHDOGO_V1: чей это взгляд — теперь в подписи,
            # иначе три разных кадра не отличить друг от друга.
            _chey = f"{chey} · " if chey else ""
            ui.label(f"👁 {_chey}{symbol} · {tf} · {_kran}{_kogda}").style('''

ST_KOGDA = '''                _bs, _ = _src_bars(symbol, tf, 3)'''
NOV_KOGDA = '''                _bs, _ = _src_bars(symbol, tf, 3)   # VZGLYAD_KAZHDOGO_V1'''

# ── клик по пузырьку рисует его кадр ──
ST_SWITCH = '''        label = _agent_label(roster, agent_id)
        if agent_id in state["reports"]:
            update_viewer(f"# {label} ({agent_id})\\n\\n{state['reports'][agent_id]}")
        else:
            update_viewer(f"# {label} ({agent_id})\\n\\n*Отчёт пока не создан.*")'''

NOV_SWITCH = '''        label = _agent_label(roster, agent_id)
        if agent_id in state["reports"]:
            update_viewer(f"# {label} ({agent_id})\\n\\n{state['reports'][agent_id]}")
        else:
            update_viewer(f"# {label} ({agent_id})\\n\\n*Отчёт пока не создан.*")
        # VZGLYAD_KAZHDOGO_V1: кликнул трейдера — сразу его взгляд.
        # Кадр рисуется из готовых баров, модель не зовётся: это
        # по-прежнему бесплатный просмотр для Шефа.
        try:
            pokazat_kadr()
        except Exception as _e:
            print(f"[ВЗГЛЯД] кадр не показался: {_e}")'''

# ── ТЕРМИНАЛ: не ронять выбор ──
ST_TERM = '''        bylo = [x for x in state.get("loaded_assets", [])
                if x.get("источник") != "терминал"]
        state["loaded_assets"] = aktivy + bylo
        if state.get("active_asset") is None and aktivy:
            state["active_asset"] = 0'''

NOV_TERM = '''        bylo = [x for x in state.get("loaded_assets", [])
                if x.get("источник") != "терминал"]
        # VZGLYAD_KAZHDOGO_V1: запомнили выбор ИМЕНЕМ до перестройки.
        # Свежее ложится в начало, всё съезжает вниз — и прежний
        # номер строки начинает показывать на чужой актив. Первым в
        # опросе этажей идёт M15, поэтому сброс всегда выглядел как
        # «скинуло на M15».
        _bylo_vybrano = _zapomnit_vybor()
        state["loaded_assets"] = aktivy + bylo
        _vernut_vybor(_bylo_vybrano)'''

# ── загрузчик и пересканирование: та же болезнь ──
ST_SCAN = '''        state["loaded_assets"] = assets
        state["active_asset"] = 0 if assets else None'''

NOV_SCAN = '''        # VZGLYAD_KAZHDOGO_V1: пересканирование папки роняло выбор
        # так же молча, как ТЕРМИНАЛ.
        _bylo_vybrano = _zapomnit_vybor()
        state["loaded_assets"] = assets
        _vernut_vybor(_bylo_vybrano, tiho=True)'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    ui_torg = koren / "Биржа" / "ui_torg.py"
    t = ui_torg.read_text(encoding="utf-8")

    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0

    yakorya = [
        ("кадр", ST_KADR), ("подпись", ST_PODPIS), ("дата бара", ST_KOGDA),
        ("клик по пузырьку", ST_SWITCH), ("терминал", ST_TERM),
        ("пересканирование", ST_SCAN),
    ]
    beda = [imya for imya, y in yakorya if t.count(y) != 1]
    if beda:
        print(f"✗ не нашёл дословно (или нашёл дважды): {', '.join(beda)}")
        print("  Кабинет правили — не трогаю, чтобы не сломать.")
        return 1

    if "def page_torg(tseh_id" not in t:
        print("✗ в кабинете нет tseh_id — не пойму, какой цех спрашивать")
        return 1

    novyy = (t.replace(ST_KADR, NOV_KADR, 1)
              .replace(ST_KOGDA, NOV_KOGDA, 1)
              .replace(ST_PODPIS, NOV_PODPIS, 1)
              .replace(ST_SWITCH, NOV_SWITCH, 1)
              .replace(ST_TERM, NOV_TERM, 1)
              .replace(ST_SCAN, NOV_SCAN, 1)
             + f"\n# {MARKER} - marker\n")
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ после правки не разбирается: {e}")
        return 1

    if SUHO:
        print("· правка готова (сухой прогон, не пишу)")
        return 0

    bak = ui_torg.with_suffix(
        f".py.bak_vzglyad_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(ui_torg, bak)
    ui_torg.write_text(novyy, encoding="utf-8")
    print(f"✓ кабинет поправлен (копия: {bak.name})")

    import py_compile
    try:
        py_compile.compile(str(ui_torg), doraise=True)
        print("✓ компилируется")
    except Exception as e:
        print(f"✗ НЕ компилируется: {e}")
        return 1

    print("\nЧто проверить руками:")
    print("  1. Кликай пузырьки трейдеров — кадр справа должен меняться")
    print("     под каждого: свой инструмент, свой этаж, имя в подписи.")
    print("  2. Жми ТЕРМИНАЛ — выбранная слева строка должна остаться")
    print("     той же, а не прыгнуть на M15.")
    print("\nУ кого нет пары — вместо кадра будет написано, чего не хватает.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
