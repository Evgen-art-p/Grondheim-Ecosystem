# -*- coding: utf-8 -*-
# RAZGOVOR_SO_STOLOM_V1
"""
В РАЗГОВОРЕ ОН ВИДИТ ТО ЖЕ, ЧТО И В РАБОТЕ.

    python patch_razgovor_so_stolom.py --suho    посмотреть
    python patch_razgovor_so_stolom.py           накатить

Запускать из КОРНЯ репо. Идемпотентно. Копии рядом: .bak_razgovor.

ЧТО БЫЛО НЕ ТАК

    Разговор и работа были разными комнатами. Когда трейдер работает
    по кнопке РЫНОК, ему накрывают стол и показывают кадр. Когда Шеф
    заговаривает с ним в кабинете — не дают ни того, ни другого: в
    разговор уходил только пересказ его же прошлого решения.

    Оттого и вышел случай 08.08:
        ШЕФ: илья, найди два самых больших отрицательных AO
        A07: если предоставишь график, помогу точнее
        ШЕФ: стол видишь?
        A07: нет, не вижу
    Он не отговаривался — он честно ослеп. Спрашивать у слепого, что
    на графике, бессмысленно; проверить роль в разговоре — нечем.

ЧТО СТАЛО

    Разговор получает стол и глаз — тот же стол и тот же кадр, что и
    работа, по тому же инструменту, что выбран на полке. Кабинет
    передаёт ему выбор вместе с вопросом; выбора нет — берётся
    инструмент его прошлого решения.

    Это ровно то, о чём мы уговорились: смотрят одно и то же, и видно,
    что именно.

    Заодно чинится тихая пропажа: когда работал глаз, до модели не
    доходили ни история разговора, ни температура из натуры — обёртка
    их роняла. Значит в разговоре с картинкой он забывал предыдущие
    реплики и говорил средним голосом, а не своим.

ЧЕГО ПАТЧ НЕ ДЕЛАЕТ
    Не трогает промпты и рецепты входа — это отдельный разговор.
    Прочие агенты (морж, паникёр, ганс, архивариус, исполнитель)
    остаются как были: кабинет спросит их по-старому.
"""
import argparse
import ast
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

KOREN = Path(__file__).resolve().parent
UI = KOREN / "Биржа" / "ui_torg.py"
SLOTY = (KOREN / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос"
         / "слоты")
SLOTS = ("A06", "A07", "A08")
MARKER = "# RAZGOVOR_SO_STOLOM_V1 - marker"
BAK = ".bak_razgovor"

# ── мозг 1: обёртка глаза больше не роняет историю и голос ────
STAROE_GLAZ = '''                    agent_id=kw.get("agent_id", slot),
                    slot_id=kw.get("slot_id", slot))
'''
NOVOE_GLAZ = '''                    # RAZGOVOR_SO_STOLOM_V1: история и температура
                    # ронялись здесь — с картинкой он забывал разговор
                    # и говорил средним голосом вместо своего.
                    history=kw.get("history"),
                    temperature=kw.get("temperature"),
                    agent_id=kw.get("agent_id", slot),
                    slot_id=kw.get("slot_id", slot))
'''

# ── мозг 2: разговор принимает выбранный рынок ────────────────
STAROE_PODPIS = '''                   dialog: Optional[list] = None) -> str:
    prompt = PROMPT_PATH.read_text(encoding="utf-8") if PROMPT_PATH.exists() else ""
'''
NOVOE_PODPIS = '''                   dialog: Optional[list] = None,
                   rynok: Optional[tuple] = None) -> str:
    # RAZGOVOR_SO_STOLOM_V1: rynok — (инструмент, этаж) с полки кабинета.
    # Не передали — возьмём инструмент его прошлого решения.
    prompt = PROMPT_PATH.read_text(encoding="utf-8") if PROMPT_PATH.exists() else ""
'''

# ── мозг 3: стол в разговор ───────────────────────────────────
STAROE_SYSTEM = '''    system = prompt + work_ctx
'''
NOVOE_SYSTEM = '''    # RAZGOVOR_SO_STOLOM_V1: живой стол в разговор. Раньше сюда шёл
    # только пересказ прошлого решения — и на вопрос «что на графике»
    # он честно отвечал, что ничего не видит.
    _sym = _tf = ""
    if rynok:
        _p = list(rynok) + ["", ""]
        _sym, _tf = str(_p[0] or ""), str(_p[1] or "")
    if (not _sym or not _tf) and last_run:
        _mk = last_run.get("market", {}) or {}
        _sym = str(_mk.get("symbol", "") or "")
        _tf = str(_mk.get("timeframe", "") or "")
    if _sym and _tf:
        try:
            import stol as _stol
            _t = _stol.nakryt(_sym, _tf, self_key=_SELF_KEY)
            work_ctx += (
                f"\\n\\n=== СТОЛ ПРЯМО СЕЙЧАС · {_sym} {_tf} ===\\n"
                + json.dumps(_t, ensure_ascii=False, indent=2)
                + "\\n=== КОНЕЦ СТОЛА ===\\n"
                "Это живые числа ЭТОГО мгновения, а не память о прошлом "
                "решении, и картинка перед тобой — та же, что у Шефа. "
                "Спрашивают про рынок — смотри и отвечай, а не проси "
                "прислать данные.\\n")
        except Exception as _e:
            work_ctx += f"\\n\\n(стол накрыть не вышло: {_e})\\n"

    system = prompt + work_ctx
'''

# ── мозг 4: глаз в разговоре ──────────────────────────────────
STAROE_ZOV = '''        return chat(system=system, user=question, history=history,
'''
NOVOE_ZOV = '''        # RAZGOVOR_SO_STOLOM_V1: с кадром, если знаем, на что смотрим.
        _chat_fn = _glaz(chat, _sym, _tf, _SLOT) if (_sym and _tf) else chat
        return _chat_fn(system=system, user=question, history=history,
'''

MOZG_STEZHKI = (
    ("глаз не роняет историю и голос", STAROE_GLAZ, NOVOE_GLAZ),
    ("разговор принимает рынок", STAROE_PODPIS, NOVOE_PODPIS),
    ("стол в разговор", STAROE_SYSTEM, NOVOE_SYSTEM),
    ("кадр в разговор", STAROE_ZOV, NOVOE_ZOV),
)

# ── кабинет: передаёт выбор с полки вместе с вопросом ─────────
STAROE_UI = '''                reply = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: _chat(msg, state.get(_last_key), dialog))
'''
NOVOE_UI = '''                # RAZGOVOR_SO_STOLOM_V1: отдаём собеседнику тот же
                # инструмент, что выбран на полке, — чтобы он смотрел
                # на то же, что и Шеф. Кто ещё не умеет принимать
                # рынок (морж, паникёр, ганс, архивариус, исполнитель)
                # — спрашиваем по-старому.
                _rynok_seychas = _aktivnyy_rynok()
                try:
                    reply = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: _chat(msg, state.get(_last_key), dialog,
                                            rynok=_rynok_seychas))
                except TypeError:
                    reply = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: _chat(msg, state.get(_last_key), dialog))
'''

UI_STEZHKI = (("кабинет передаёт выбор", STAROE_UI, NOVOE_UI),)


def proverit_python(tekst: str, imya: str) -> bool:
    try:
        ast.parse(tekst)
    except SyntaxError as e:
        print(f"    ✗ {imya}: синтаксис сломан ({e}) — НЕ пишу")
        return False
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False,
                                     encoding="utf-8") as f:
        f.write(tekst)
        vrem = f.name
    try:
        py_compile.compile(vrem, doraise=True)
        return True
    except py_compile.PyCompileError as e:
        print(f"    ✗ {imya}: не компилируется ({e}) — НЕ пишу")
        return False
    finally:
        Path(vrem).unlink(missing_ok=True)


def odin_fail(put: Path, stezhki, suho: bool) -> str:
    imya = put.parent.name if put.name == "мозг.py" else put.name
    if not put.exists():
        print(f"  {imya}: файла нет — пропускаю")
        return "нет"
    tekst = put.read_text(encoding="utf-8")
    if MARKER in tekst:
        print(f"  {imya}: уже накатано")
        return "уже"
    for nazv, staroe, novoe in stezhki:
        n = tekst.count(staroe)
        if n != 1:
            print(f"    ✗ {imya}: якорь «{nazv}» найден {n} раз — "
                  f"файл не трогаю")
            return "сбой"
        tekst = tekst.replace(staroe, novoe, 1)
        print(f"    · {nazv} — заменено")
    tekst = tekst.rstrip("\n") + "\n\n" + MARKER + "\n"
    if not proverit_python(tekst, imya):
        return "сбой"
    if suho:
        print(f"  {imya}: ✓ готов к накатке (сухой прогон)")
        return "готово"
    shutil.copy2(put, put.with_suffix(put.suffix + BAK))
    put.write_text(tekst, encoding="utf-8")
    print(f"  {imya}: ✓ накатано (копия рядом: *{BAK})")
    return "готово"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suho", action="store_true")
    a = ap.parse_args()

    if not SLOTY.exists() or not UI.exists():
        print("✗ не вижу Биржу — запускай из КОРНЯ репо")
        return 1

    print("═" * 58)
    print("РАЗГОВОР СО СТОЛОМ" + ("   [СУХОЙ ПРОГОН]" if a.suho else ""))
    print("═" * 58)

    itogi = {}
    print("\nтрейдеры:")
    for slot in SLOTS:
        itogi[slot] = odin_fail(SLOTY / slot / "мозг.py", MOZG_STEZHKI, a.suho)
    print("\nкабинет:")
    itogi["ui_torg.py"] = odin_fail(UI, UI_STEZHKI, a.suho)

    print("\n" + "─" * 58)
    sboi = [k for k, v in itogi.items() if v == "сбой"]
    if sboi:
        print(f"⚠ не тронуты: {', '.join(sboi)} — якоря разошлись, "
              f"покажи мне эти файлы")
        return 1
    if a.suho:
        print("Сухой прогон прошёл. Накатывать: "
              "python patch_razgovor_so_stolom.py")
        return 0
    print("Готово. Проверить просто: выбери актив на полке и, НЕ нажимая")
    print("РЫНОК, спроси у него «что видишь на графике?». Слепой ответ")
    print("«пришли данные» больше не должен появляться.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
