# -*- coding: utf-8 -*-
# MARKER: PUZYR_NE_OBRYVAETSYA_V3
"""
КЛИК ПО ПУЗЫРЬКУ НЕ ОБРЫВАЕТСЯ НА ПЕРВОЙ ОШИБКЕ.

ШЕФ (03.09): «везде пузырьки работают, а именно на бирже не работают».
Ключевая подсказка — в Академии тот же приём работает. Значит дело не
в браузере и не в стилях.

ЧТО ПРОВЕРЕНО ЖИВЬЁМ (не гипотеза — поставил nicegui 3.16 и прогнал)
    ui.element("div") и ui.button ведут себя ОДИНАКОВО:
        после .classes(replace="avatar") + .classes(add="active")
        оба дают ['avatar', 'active'].
    То есть класс навешивается исправно и на кнопке. Мои прошлые две
    догадки (div против кнопки, стили Quasar) — обе мимо, патчи
    PUZYR_KAK_V_AKADEMII_V1 и PUZYR_PODSVETKA_V2 били не туда.
    Косвенно это подтверждал и сам скриншот: зелёные кольца (.done) и
    пунктир вакансий (.vacant) на тех же кнопках рисуются прекрасно.

НАСТОЯЩАЯ ПРИЧИНА — В ПОРЯДКЕ ВЫЗОВОВ
    switch_agent зовёт четыре руки подряд и БЕЗ защиты:
        state["active_agent"] = agent_id
        update_avatar()          # 1
        update_vitals()          # 2
        update_avatar_states()   # 3  ← подсветка, третья в очереди
        update_stats_panel()     # 4
    Споткнулась любая из первых двух — выполнение обрывается, и до
    подсветки дело не доходит. В лог при этом уже напечатано
    «[ПУЗЫРЬ] нажали: A06» (печать идёт раньше switch_agent), поэтому
    снаружи выглядит как «клик прошёл, а пузырёк мёртвый».
    Сходится и со скриншотом Шефа: там же не показался кадр, хотя по
    коду клик должен рисовать его сразу — второй симптом того же
    обрыва. Всё, что стоит НИЖЕ в switch_agent, уже обёрнуто в
    try/except — потому и живёт.

ЧТО ДЕЛАЕТСЯ
────────────
    1. Подсветка идёт ПЕРВОЙ — она самая дешёвая и самая заметная,
       отклик на клик не должен зависеть от тяжёлых соседей.
    2. Каждый шаг — в своём try/except: споткнулся один, остальные
       делаются. Молчаливого обрыва больше нет.
    3. Виновник печатается в лог:
           [ПУЗЫРЬ] ⚠ update_vitals сорвалась: <причина>
       Раньше этой строки не было вовсе — оттого и не находилось.
    4. update_avatar_states пишет, что реально применила:
           [ПУЗЫРЬ] подсветка: A06=active A05=done A07=vacant
       Одна строка на клик — видно сразу, дошло или нет.

Правит Биржа/ui_torg.py. Идемпотентен. .bak рядом.

ПОРЯДОК: этот патч ставится ПОВЕРХ прежних. Если PUZYR_PODSVETKA_V2
уже накачен — он не мешает (inline-подсветка остаётся, просто теперь
до неё доходит очередь). Если стоит ошибочный PUZYR_KAK_V_AKADEMII_V1
(div вместо кнопки) — сперва прогони postavit_puzyr_podsvetka.py,
он вернёт кнопку.
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "PUZYR_NE_OBRYVAETSYA_V3"

# ── 1. switch_agent: подсветка первой, каждый шаг отдельно ──────────

SWITCH_STAR = '''        state["active_agent"] = agent_id
        update_avatar()
        update_vitals()
        update_avatar_states()
        update_stats_panel()'''

SWITCH_NOV = '''        state["active_agent"] = agent_id
        # PUZYR_NE_OBRYVAETSYA_V3: раньше эти четыре шли подряд и без
        # защиты — споткнулся первый, и подсветка (третья в очереди)
        # не наступала вовсе. Снаружи выглядело как мёртвый пузырёк.
        # Теперь подсветка первая, и каждый шаг сам за себя.
        for _imya_shaga, _shag in (("update_avatar_states", update_avatar_states),
                                   ("update_avatar", update_avatar),
                                   ("update_vitals", update_vitals),
                                   ("update_stats_panel", update_stats_panel)):
            try:
                _shag()
            except Exception as _e_shag:
                print(f"[ПУЗЫРЬ] ⚠ {_imya_shaga} сорвалась: {_e_shag}")'''

# ── 2. update_avatar_states: говорить, что применила ───────────────

STATES_STAR = '''            if aid == state["active_agent"]:
                el.classes(add="active")
            if aid in state["reports"]:
                el.classes(add="done")'''

STATES_NOV = '''            if aid == state["active_agent"]:
                el.classes(add="active")
            if aid in state["reports"]:
                el.classes(add="done")
            # PUZYR_NE_OBRYVAETSYA_V3: собираем, что применилось —
            # печать одной строкой ниже, после обхода всех.
            _vidno.append(f"{aid}=" + ("active" if aid == state["active_agent"]
                                       else "done" if aid in state["reports"]
                                       else "vacant" if "vacant" in base
                                       else "—"))'''

STATES_HEAD_STAR = '''    def update_avatar_states():
        for aid, el in avatars_ref["elements"].items():'''

STATES_HEAD_NOV = '''    def update_avatar_states():
        _vidno = []   # PUZYR_NE_OBRYVAETSYA_V3
        for aid, el in avatars_ref["elements"].items():'''

STATES_TAIL_ANCHOR = '''    def switch_agent(agent_id: str):'''

STATES_TAIL_NOV = '''        # PUZYR_NE_OBRYVAETSYA_V3: одна строка на клик — видно сразу,
        # дошла подсветка или нет, и к скольким пузырькам.
        if _vidno:
            print("[ПУЗЫРЬ] подсветка: " + " ".join(_vidno))
        else:
            print("[ПУЗЫРЬ] ⚠ подсветка: пузырьков в avatars_ref НЕТ")

    def switch_agent(agent_id: str):'''


def _nayti_birzhu() -> Path:
    for koren in (Path(__file__).resolve().parent, Path.cwd().resolve()):
        for p in (koren / "Биржа", koren):
            if (p / "ui_torg.py").exists():
                return p
    print("Не нашёл Биржа/ui_torg.py.")
    s = input("Перетащи сюда папку «Биржа» и нажми Enter:\n> ")
    p = Path(s.strip().strip('"').strip("'"))
    if (p / "ui_torg.py").exists():
        return p
    raise SystemExit("не та папка — там нет ui_torg.py")


def main():
    f = _nayti_birzhu() / "ui_torg.py"
    src = f.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"\n{f}: уже накачено")
        return

    novyy = src
    shagi = []

    # 1. switch_agent
    if SWITCH_STAR in novyy and novyy.count(SWITCH_STAR) == 1:
        novyy = novyy.replace(SWITCH_STAR, SWITCH_NOV)
        shagi.append("клик не обрывается на первой ошибке")
    else:
        print(f"\n{f}: ! не нашёл блок вызовов в switch_agent — не трогаю")
        return

    # 2. диагностика подсветки (необязательная — если не легла, не беда)
    if (STATES_HEAD_STAR in novyy and STATES_STAR in novyy
            and STATES_TAIL_ANCHOR in novyy
            and novyy.count(STATES_HEAD_STAR) == 1
            and novyy.count(STATES_STAR) == 1
            and novyy.count(STATES_TAIL_ANCHOR) == 1):
        novyy = novyy.replace(STATES_HEAD_STAR, STATES_HEAD_NOV)
        novyy = novyy.replace(STATES_STAR, STATES_NOV)
        novyy = novyy.replace(STATES_TAIL_ANCHOR, STATES_TAIL_NOV)
        shagi.append("подсветка отчитывается в лог")
    else:
        shagi.append("диагностику не ставил (update_avatar_states правили)")

    novyy = novyy.rstrip("\n") + f"\n\n# {MARKER} - marker\n"

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"\n{f}: ! после правки не разбирается ({e}) — файл НЕ тронут")
        return

    shutil.copy2(f, f.with_suffix(".py.bak_obryv"))
    f.write_text(novyy, encoding="utf-8")
    print(f"\n{f}:")
    for s in shagi:
        print(f"   · {s}")
    print("   (.bak_obryv рядом)")
    print("\nТеперь при клике в логе будет видно И виновника обрыва,")
    print("И что подсветка реально применила. Пришли эти строки Брату.")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        print(e)
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно ")
