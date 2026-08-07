# -*- coding: utf-8 -*-
# KABINET_GRAFIK_V1
"""
ГРАФИК В КАБИНЕТЕ БИРЖИ — правая часть делится по горизонтали.

РЕШЕНИЕ ШЕФА (06.08): график не над чатом, а рядом с отчётами — правая
часть стола делится пополам по горизонтали. Сверху кадр, снизу отчёты.

ЗАЧЕМ ИМЕННО ТУДА. Трейдер теперь смотрит на картинку первым (движок
vzglyad.py). Шеф обязан видеть ТУ ЖЕ САМУЮ, иначе проверить трейдера
нечем — как сегодня в Академии, где ученик описывал страницу, а Шеф
видел ту же страницу и правил.

ЧТО ПОЯВЛЯЕТСЯ
    • панель кадра над вьюером отчётов, обе на половину высоты;
    • кнопка «📈 кадр» — нарисовать и посмотреть, НИКОГО не будя и
      модель не тратя. Шеф смотрит, трейдер спит;
    • кнопка «👁 взгляд» — трейдер смотрит и решает (movok vzglyad).

ПОЧЕМУ КАРТИНКА, А НЕ ИНТЕРАКТИВНЫЙ ВИДЖЕТ. Один и тот же PNG идёт и
на экран, и в запрос модели со зрением. Виджет красивее человеку, но
модель его не видит — и тогда Шеф с трейдером смотрят на разное.

ЧТО НУЖНО РЯДОМ: grafik.py и vzglyad.py в папке Биржа/,
плюс один раз  pip install matplotlib

ЗАПУСК из корня репо:
    python patch_kabinet_grafik.py
"""
import ast
import py_compile
import shutil
import sys
from pathlib import Path

MARKER = "KABINET_GRAFIK_V1"
TARGET = Path("Биржа") / "ui_torg.py"
BAK = Path("Биржа") / "ui_torg.py.bak_kabinet_grafik"

# ═══════════════════════════════════════════════════════════
# ЯКОРЬ 1 — разметка: правая часть делится по горизонтали
# ═══════════════════════════════════════════════════════════
A1_OLD = '''                        viewer_ref["element"] = ui.element("div").classes("viewer").style(
                            "flex:1; min-height:0; overflow-y:auto;")
                        with viewer_ref["element"]:
                            ui.label("Отчёты агентов появятся здесь")
'''

A1_NEW = '''                        # KABINET_GRAFIK_V1: правая часть — две половины
                        # по горизонтали: сверху кадр, снизу отчёты.
                        with ui.element("div").style(
                                "flex:1; min-height:0; display:flex; "
                                "flex-direction:column; gap:8px;"):
                            kadr_ref["element"] = ui.element("div").classes("viewer").style(
                                "flex:1; min-height:0; overflow:auto; "
                                "display:flex; align-items:center; "
                                "justify-content:center;")
                            with kadr_ref["element"]:
                                ui.label("Кадр появится здесь — жми «📈 кадр»")
                            viewer_ref["element"] = ui.element("div").classes("viewer").style(
                                "flex:1; min-height:0; overflow-y:auto;")
                            with viewer_ref["element"]:
                                ui.label("Отчёты агентов появятся здесь")
'''

# ═══════════════════════════════════════════════════════════
# ЯКОРЬ 2 — ссылка на панель кадра рядом с остальными
# ═══════════════════════════════════════════════════════════
A2_OLD = '''    viewer_ref:   dict[str, Any] = {"element": None}
'''

A2_NEW = '''    viewer_ref:   dict[str, Any] = {"element": None}
    kadr_ref:     dict[str, Any] = {"element": None}   # KABINET_GRAFIK_V1
'''

# ═══════════════════════════════════════════════════════════
# ЯКОРЬ 3 — показ кадра и две кнопки
# ═══════════════════════════════════════════════════════════
A3_OLD = '''    def update_viewer(content: str):
'''

A3_NEW = '''    # ── KABINET_GRAFIK_V1: кадр ──────────────────────────────
    def _aktivnyy_rynok() -> tuple:
        """Что сейчас на полке: символ и рабочий этаж."""
        try:
            s = state.get("symbol") or state.get("актив") or "EURUSD"
            tf = state.get("timeframe") or state.get("tf") or "H1"
            return s, tf
        except Exception:
            return "EURUSD", "H1"

    def pokazat_kadr(put=None):
        """Рисует кадр и кладёт в верхнюю половину правой части.

        Модель не трогаем: Шеф смотрит, трейдер спит. Это и есть
        дешёвый способ проверить, читается ли картинка, ПЕРЕД тем как
        отдавать её глазу.
        """
        if not kadr_ref["element"]:
            return None
        symbol, tf = _aktivnyy_rynok()
        try:
            import grafik
            p = Path(put) if put else grafik.kadr(symbol, tf)
        except Exception as e:
            ui.notify(f"⚠ кадр не нарисовался: {e}", type="negative")
            return None
        if not p:
            ui.notify("⚠ кадр не нарисовался (нет matplotlib или баров)",
                      type="warning")
            return None
        kadr_ref["element"].clear()
        with kadr_ref["element"]:
            ui.image(str(p)).style("width:100%; height:auto;")
        return p

    async def vzglyad_treydera():
        """Активный трейдер смотрит на кадр и решает.

        Смотрит ТОТ, чей пузырёк выбран в шапке: трое работают
        независимо, каждый сам по себе. Хочешь три мнения на одну
        картинку — жми по очереди, переключая пузырёк.
        """
        symbol, tf = _aktivnyy_rynok()
        _slot = state.get("active_agent") or "A06"
        if _slot not in ("A06", "A07", "A08"):
            ui.notify("Выбери в шапке трейдера — смотрит он, не Архивариус",
                      type="warning")
            return
        _kto = _agent_label(roster, _slot)
        ui.notify(f"👁 {_kto} смотрит {symbol} {tf}…", type="info")
        try:
            import vzglyad as _vz
            # так же, как кабинет уже гоняет тестер: в исполнителе, чтобы
            # интерфейс не замирал на время двух вызовов модели
            _loop = asyncio.get_event_loop()
            itog = await _loop.run_in_executor(
                None, lambda: _vz.posmotret(symbol, tf, slot=_slot))
        except Exception as e:
            ui.notify(f"⚠ взгляд сорвался: {e}", type="negative")
            return
        if itog.get("кадр"):
            pokazat_kadr(itog["кадр"])
        chasti = [f"### 👁 {_kto} ({_slot}) — {symbol} {tf}\\n\\n{itog.get('взгляд','')}"]
        if itog.get("просил"):
            chasti.append(f"### 🙋 Попросил\\n\\n{itog['просил']}")
        if itog.get("приборы"):
            chasti.append(f"### 📐 Приборы\\n\\n{itog['приборы']}")
        if itog.get("решение") and itog.get("просил"):
            chasti.append(f"### ⚖️ Договорил\\n\\n{itog['решение']}")
        update_viewer("\\n\\n".join(chasti))
        ui.notify(f"👁 {_kto}: " + ("попросил приборы" if itog.get("просил")
                                    else "посмотрел"), type="info")

    def update_viewer(content: str):
'''

# ═══════════════════════════════════════════════════════════
# ЯКОРЬ 4 — сами кнопки рядом с SEND
# ═══════════════════════════════════════════════════════════
A4_OLD = '''                    ui.button("SEND", on_click=send_message).classes("send-button")
'''

A4_NEW = '''                    # KABINET_GRAFIK_V1: посмотреть самому / дать посмотреть
                    ui.button("📈 кадр", on_click=lambda: pokazat_kadr()).props(
                        "flat no-caps").style(
                        "font-size:0.75rem; padding:8px 14px; border-radius:20px; "
                        "color:rgba(139,233,253,0.9); background:rgba(139,233,253,0.10); "
                        "border:1px solid rgba(139,233,253,0.35); white-space:nowrap;")
                    ui.button("👁 взгляд", on_click=vzglyad_treydera).props(
                        "flat no-caps").style(
                        "font-size:0.75rem; padding:8px 14px; border-radius:20px; "
                        "color:rgba(255,214,102,0.95); background:rgba(255,214,102,0.10); "
                        "border:1px solid rgba(255,214,102,0.35); white-space:nowrap;")
                    ui.button("SEND", on_click=send_message).classes("send-button")
'''

PRAVKI = [
    ("ссылка на панель кадра", A2_OLD, A2_NEW),
    ("показ кадра и взгляд", A3_OLD, A3_NEW),
    ("правая часть делится по горизонтали", A1_OLD, A1_NEW),
    ("кнопки «кадр» и «взгляд»", A4_OLD, A4_NEW),
]


def main() -> int:
    if not TARGET.exists():
        print(f"✗ не нашёл {TARGET} — запускать из КОРНЯ репо")
        return 1

    src = TARGET.read_text(encoding="utf-8")
    if MARKER in src:
        print(f"✓ {MARKER} уже стоит — патч идемпотентен, ничего не делаю")
        return 0

    ryadom = Path("Биржа")
    for f in ("grafik.py", "vzglyad.py"):
        if not (ryadom / f).exists():
            print(f"⚠ рядом нет {ryadom / f} — кнопки будут ругаться, "
                  f"положи файл")

    novyy = src
    for imya, old, new in PRAVKI:
        n = novyy.count(old)
        if n != 1:
            print(f"✗ якорь «{imya}»: найден {n} раз (нужно 1). "
                  f"Файл изменился — патч НЕ применён, оригинал цел.")
            return 1
        novyy = novyy.replace(old, new, 1)
        print(f"  · {imya} — ок")

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ ast.parse упал: {e}. Ничего не записал.")
        return 1

    shutil.copy2(TARGET, BAK)
    TARGET.write_text(novyy, encoding="utf-8")

    try:
        py_compile.compile(str(TARGET), doraise=True)
    except py_compile.PyCompileError as e:
        shutil.copy2(BAK, TARGET)
        print(f"✗ py_compile упал: {e}. Откатил из {BAK.name}.")
        return 1

    print(f"\n✓ {MARKER} применён")
    print(f"  бэкап: {BAK}")
    print("\n  «📈 кадр»  — нарисовать и посмотреть самому, модель спит.")
    print("  «👁 взгляд» — трейдер смотрит и решает.")
    print("  Начинай с первой: если кадр нечитаемый, второй кнопке нечего")
    print("  показывать, и ответ будет выдуманный.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
