# -*- coding: utf-8 -*-
# MESTA_ZAVODYATSYA_SAMI_V1
"""
ПАТЧ · Должности заводятся сами, из манифеста.

ЗАЧЕМ
    Слот в манифесте — это уже решение: место есть, у него имя, роль,
    здание и судья. Бланк должности переписывает ровно те же слова.
    Просить человека подтвердить то, что картридж уже сказал, — обряд,
    а обрядов в городе не держим.

    Сейчас так только у копий: razmnozhit() обходит слоты и зовёт
    zavesti() сам. Картридж, положенный руками (контора Студии), остаётся
    без должностей — «должности ещё нет», и Шефу предлагают заполнить
    поля, которые уже заполнены в манифесте.

ЧТО ДЕЛАЕТ
    1. ГОРОД/rabota.py — новая функция zavesti_mesta_kartridzhey():
       проходит по всем картриджам города и заводит должность там, где
       её нет. Поля берёт из манифеста: роль → название и чем_занят,
       здание → локация, плюс квартал, цех, слот, судья.

    2. main.py — один вызов при старте, сразу после регистрации
       страницы Работы.

БЕЗОПАСНОСТЬ
    zavesti() заведённую должность НЕ перетирает — только дополняет
    пустые поля. Биржевые места не шелохнутся, Арчи и Сергей останутся
    сидеть. Функция ничего не удаляет и никого не сажает: посадка
    по-прежнему решение Шефа.

    Если проход почему-то споткнётся, приложение всё равно поднимется:
    вызов обёрнут — город важнее удобства.

ИДЕМПОТЕНТНОСТЬ
    Маркеры в обоих файлах, .bak перед правкой, всё-или-ничего.

    шесть·проверено·до·корня
"""
from __future__ import annotations

import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "MESTA_ZAVODYATSYA_SAMI_V1"

# ── 1. rabota.py: функция ────────────────────────────────────

R_STAR = '''def obnovit(post_id: str, polya: dict) -> tuple:'''

R_NOV = '''def zavesti_mesta_kartridzhey() -> tuple:
    """Завести должности всем слотам картриджей. MESTA_ZAVODYATSYA_SAMI_V1.

    Слот в манифесте — уже решение: место есть, и всё про него написано.
    Бланк лишь повторяет эти слова, поэтому заводим сам, а не просим
    Шефа подтвердить написанное.

    Заведённые не трогаем: zavesti() дополняет пустые поля и не
    перетирает занятые. Никого не сажаем — посадка остаётся решением.
    """
    zavedeno, bylo = 0, 0
    for k in kartridzhi():
        m = _chitat(Path(k["папка"]) / "manifest.json") or {} \\
            if k.get("папка") else {}
        for s in (k.get("слоты") or []):
            slot = s.get("слот")
            if not slot:
                continue
            pid = id_dlya_slota(k["цех"], slot)
            if _chitat(put_posta(pid)) is not None:
                bylo += 1
                continue
            rol = s.get("роль", "") or slot
            ok, _ = zavesti(pid, {
                "название": rol,
                "чем_занят": rol,
                "локация": k.get("здание", "") or k.get("квартал", ""),
                "квартал": k.get("папка_квартала", ""),
                "цех": k["цех"],
                "слот": slot,
                "судья": m.get("судья", ""),
            })
            if ok:
                zavedeno += 1
    return zavedeno, bylo


def obnovit(post_id: str, polya: dict) -> tuple:'''

# ── 2. main.py: вызов при старте ─────────────────────────────

M_STAR = '''from ui_rabota import page_rabota
@ui.page("/rabota")
def _rabota():
    page_rabota()'''

M_NOV = '''from ui_rabota import page_rabota
@ui.page("/rabota")
def _rabota():
    page_rabota()

# MESTA_ZAVODYATSYA_SAMI_V1: слот в манифесте — уже решение, что место
# есть. Заводим должности сами, чтобы не просить Шефа подтверждать то,
# что картридж уже сказал. Заведённые не трогаем, никого не сажаем.
try:
    import rabota as _rabota_mod
    _zav, _bylo = _rabota_mod.zavesti_mesta_kartridzhey()
    if _zav:
        print(f"[места] заведено должностей: {_zav} (было {_bylo})")
except Exception as _e:
    print(f"[места] проход не удался: {_e}")   # город важнее удобства'''


def _teper() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def naiti_koren() -> Path:
    starty = [Path(__file__).resolve().parent, Path.cwd().resolve()]
    for start in starty:
        for kand in [start, *start.parents]:
            if (kand / "GRONDHEIM_CITY" / "локации").is_dir() \
                    and (kand / "ГОРОД" / "rabota.py").is_file():
                return kand
    raise SystemExit("Не нашёл корень репо. Запусти из корня "
                     "Grondheim-Ecosystem.")


def patchit(put: Path, star: str, nov: str) -> str:
    if not put.exists():
        return f"нет файла {put.name}"
    tekst = put.read_text(encoding="utf-8")
    if MARKER in tekst:
        return "уже пропатчен, не трогал"
    if tekst.count(star) != 1:
        return (f"якорь встречается {tekst.count(star)} раз — не рискую. "
                f"Ничего не менял.")
    bak = put.with_suffix(put.suffix + f".bak_{_teper()}")
    shutil.copyfile(put, bak)
    put.write_text(tekst.replace(star, nov, 1), encoding="utf-8")
    return f"пропатчен, старый в {bak.name}"


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except Exception:
        pass

    koren = naiti_koren()
    print(f"Корень: {koren}\n")

    r = patchit(koren / "ГОРОД" / "rabota.py", R_STAR, R_NOV)
    print(f"rabota.py: {r}")
    if r.startswith(("якорь", "нет файла")):
        print("main.py не трогаю — половину правки не оставляем.")
        return
    print(f"main.py:   {patchit(koren / 'main.py', M_STAR, M_NOV)}")

    print("\nПрогоняю проход прямо сейчас:")
    import importlib.util
    try:
        spec = importlib.util.spec_from_file_location(
            "_r", koren / "ГОРОД" / "rabota.py")
        mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        zav, bylo = mod.zavesti_mesta_kartridzhey()
        print(f"  · заведено должностей: {zav}   (уже было: {bylo})")
        for m in mod.mesta():
            if m.get("цех") == "контора" and m.get("квартал") == "Студия":
                print(f"      {m['id']} · {m['название']} · "
                      f"должность {'есть' if m['есть_пост'] else 'НЕТ'} · "
                      f"{m.get('кто_сидит') or 'вакантно'}")
    except Exception as e:
        print(f"  · споткнулся: {e}\n    ОТКАТ: верни файлы из .bak рядом")
        return

    print("\nГотово. Перезапусти приложение — на Работе у приёмщика и\n"
          "монтажёра уже должности, полей не спросят.\n"
          "шесть·проверено·до·корня")


if __name__ == "__main__":
    main()
