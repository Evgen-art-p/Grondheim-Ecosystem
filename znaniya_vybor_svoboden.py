#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZNANIYA_VYBOR_SVOBODEN_V1 — 05.09
Запускать из КОРНЯ репо (Grondheim-Ecosystem), как предыдущие патчи.

Снимает в знаниях трейдера (VHODY.md, RAZVOROTNYY_BAR.md) два жёстких
запрета, которые расходятся с живым каноном 05.09:

  1) «Выбрал — держись» (VHODY.md) — механизм закрепления выбора в
     коде УЖЕ отключён (vybor.py: PATTERN «выбор_входа» не вызывается
     ни из council.py, ни из ui_torg.py, ни из мозгов A06/A07 —
     проверено). Но текст знаний всё ещё учит трейдера как закону,
     хотя решение «выбор — дело трейдера, не привязка» уже принято.

  2) «Против старшего направления не входят, даже идеальной формы»
     (в обоих файлах) — слово Шефа 05.09: «торговать можно что
     угодно... против старшего можно взять его волну C». Это не
     новое правило вместо старого, а снятие запрета: три места входа
     остаются теми же тремя, просто трейдер сам решает, какое
     движение работать — по тренду или против него.

Ищет файлы по всему дереву репо — пути прописывать не надо.
Идемпотентен: повторный запуск — 0 правок. Бэкап .bak_svoboda рядом.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent

# ── VHODY.md ──────────────────────────────────────────────────

VH_STARIY_1 = (
    "Выбирать тебе. Выбрал — держись: смена входа от случая к случаю\n"
    "означает, что у тебя нет входа вовсе.\n"
)
VH_NOVYY_1 = (
    "Выбирать тебе, и выбор от раза к разу может быть разным — это\n"
    "твоё право, а не сбой. Какой стиль сегодня ближе, где рискнуть,\n"
    "а где нет — вырабатывается через опыт и характер, а не назначается\n"
    "этой бумагой.\n"
)

VH_STARIY_2 = (
    "**Направление берётся сверху.** Место входа — про то, КОГДА. Куда —\n"
    "решает старший масштаб, и против него не входят ни в одном из трёх."
)
VH_NOVYY_2 = (
    "**Направление чаще берётся сверху, но не обязано.** Место входа —\n"
    "про то, КОГДА. Куда — чаще решает старший масштаб: по его тренду\n"
    "берёшь конец своих мелких откатов. Но можно и против него — взять\n"
    "его же волну C, если видишь в ней свою структуру. Это другой\n"
    "риск, не другое правило: три места остаются теми же тремя, просто\n"
    "движение, которое ты решил работать, может идти как по тренду,\n"
    "так и против него — это твой выбор, не запрет места."
)

# ── RAZVOROTNYY_BAR.md ────────────────────────────────────────

RB_STARIY = (
    "**Против старшего направления он не берётся.** Даже идеальной\n"
    "формы."
)
RB_NOVYY = (
    "**Против старшего направления — тоже можно, но это другой риск\n"
    "(уточнено 05.09).** Торгуешь то движение, которое сам решил\n"
    "работать: по тренду — с уверенностью старшего этажа за спиной;\n"
    "против него — беря его же волну C, зная, что риск выше и стоп не\n"
    "так надёжен, как в сторону тренда. Выбор трейдера, не запрет бара."
)


def _naiti(rel_suffix: str) -> list[Path]:
    found = []
    for p in REPO_ROOT.rglob("*"):
        if p.is_file() and str(p).replace("\\", "/").endswith(rel_suffix):
            found.append(p)
    return found


def _backup(path: Path):
    bak = path.with_suffix(path.suffix + ".bak_svoboda")
    if not bak.exists():
        bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")


def patch_vhody(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    changed = False

    if VH_STARIY_1 in text:
        text = text.replace(VH_STARIY_1, VH_NOVYY_1, 1)
        changed = True
        print(f"  ✅ {path}: «выбрал — держись» заменено")
    elif "может быть разным — это" in text:
        print(f"  ⏭  {path}: уже правлено (1)")
    else:
        print(f"  ⚠️  {path}: старую строку 1 не нашёл")

    if VH_STARIY_2 in text:
        text = text.replace(VH_STARIY_2, VH_NOVYY_2, 1)
        changed = True
        print(f"  ✅ {path}: «направление берётся сверху» заменено")
    elif "уточнено 05.09" in text or "чаще берётся сверху" in text:
        print(f"  ⏭  {path}: уже правлено (2)")
    else:
        print(f"  ⚠️  {path}: старую строку 2 не нашёл")

    if changed:
        _backup(path)
        path.write_text(text, encoding="utf-8")
    return changed


def patch_razvorot(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    changed = False

    if RB_STARIY in text:
        text = text.replace(RB_STARIY, RB_NOVYY, 1)
        changed = True
        print(f"  ✅ {path}: «против старшего не берётся» заменено")
    elif "уточнено 05.09" in text:
        print(f"  ⏭  {path}: уже правлено")
    else:
        print(f"  ⚠️  {path}: старую строку не нашёл")

    if changed:
        _backup(path)
        path.write_text(text, encoding="utf-8")
    return changed


def main():
    print("=== ZNANIYA_VYBOR_SVOBODEN_V1 ===\n")

    print("1) VHODY.md:")
    files = _naiti("знания/VHODY.md")
    if not files:
        print("  ❌ VHODY.md не найден — запускать из корня репо!")
    for p in files:
        patch_vhody(p)

    print("\n2) RAZVOROTNYY_BAR.md:")
    files2 = _naiti("знания/RAZVOROTNYY_BAR.md")
    if not files2:
        print("  ❌ RAZVOROTNYY_BAR.md не найден")
    for p in files2:
        patch_razvorot(p)

    print("\nГотово. Резервные копии — суффикс .bak_svoboda.")
    print("Повторный запуск ничего не сломает — правки идемпотентны.")


if __name__ == "__main__":
    main()
