# -*- coding: utf-8 -*-
"""
СМОТРЕЛЕЦ ПУЗЫРЬКОВ — ничего не правит, только показывает.

Брат за вечер выдал четыре патча по пузырькам, и три из них были
мимо. Дальше гадать нельзя: надо увидеть, что РЕАЛЬНО лежит в файле
после всех накаток, а не предполагать.

Запусти двойным щелчком из корня репо (или из папки Биржа) и пришли
Брату всё, что напечатает. Файл не меняется — можно запускать смело.
"""
import re
import sys
from pathlib import Path


def _nayti() -> Path:
    for koren in (Path(__file__).resolve().parent, Path.cwd().resolve()):
        for p in (koren / "Биржа", koren):
            if (p / "ui_torg.py").exists():
                return p / "ui_torg.py"
    print("Не нашёл Биржа/ui_torg.py.")
    s = input("Перетащи сюда файл ui_torg.py и нажми Enter:\n> ")
    p = Path(s.strip().strip('"').strip("'"))
    if p.exists():
        return p
    raise SystemExit("не нашёл файл")


def main():
    f = _nayti()
    src = f.read_text(encoding="utf-8")
    print(f"\nФайл: {f}")
    print(f"Строк: {len(src.splitlines())}\n")

    print("═══ 1. КАКИЕ ПАТЧИ ПО ПУЗЫРЬКАМ НАКАЧЕНЫ ═══")
    markery = ["PUZYRI_V1", "PUZYR_KAK_V_AKADEMII_V1", "PUZYR_PODSVETKA_V2",
               "PUZYR_NE_OBRYVAETSYA_V3", "PUZYR_STILEM_I_UPDATE_V4",
               "RAZGOVOR_PRO_SVOY_INSTRUMENT_V1", "AGENT_LIVE_SWITCH_V1"]
    for m in markery:
        est = f"# {m} - marker" in src
        upom = src.count(m)
        print(f"  {'ДА ' if est else 'нет'}  {m}"
              + (f"   (упоминаний в тексте: {upom})" if upom else ""))

    print("\n═══ 2. ЧЕМ НАРИСОВАН ПУЗЫРЁК ═══")
    if 'avatar = ui.element("div").classes(cls)' in src:
        print("  div  — ui.element(\"div\") + .on(\"click\")")
    elif "avatar = ui.button(on_click=_nazhali).classes(cls)" in src:
        print("  КНОПКА — ui.button(on_click=...) + props(flat dense no-caps)")
    else:
        print("  ! не узнал ни один из двух видов — покажу как есть:")
        for i, l in enumerate(src.splitlines(), 1):
            if "avatar = ui." in l:
                print(f"     строка {i}: {l.strip()}")

    print("\n═══ 3. ЕСТЬ ЛИ CSS КОЛЬЦА ═══")
    for sel in [".avatar{", ".avatar.active{", ".avatar.done{", ".avatar.vacant{"]:
        print(f"  {'ДА ' if sel in src else 'нет'}  {sel}")
    m = re.search(r"ui\.add_head_html\([^)]*TORG_CSS[^)]*\)", src)
    print(f"  CSS отдаётся странице: {'ДА' if m else 'НЕТ — вот это была бы причина!'}")

    print("\n═══ 4. ЧТО ДЕЛАЕТ КЛИК (switch_agent) ═══")
    i = src.find("def switch_agent(")
    if i == -1:
        print("  ! switch_agent не найдена")
    else:
        j = src.find("\n    def ", i + 10)
        telo = src[i:j if j > 0 else i + 2000]
        for l in telo.splitlines()[:30]:
            print("   " + l.rstrip())

    print("\n═══ 5. ФУНКЦИЯ ПОДСВЕТКИ ═══")
    i = src.find("def update_avatar_states(")
    if i == -1:
        print("  ! update_avatar_states не найдена")
    else:
        j = src.find("\n    def ", i + 10)
        telo = src[i:j if j > 0 else i + 3000]
        for l in telo.splitlines()[:40]:
            print("   " + l.rstrip())

    print("\n═══ 6. СКОЛЬКО РАЗ РИСУЮТСЯ ПУЗЫРЬКИ ═══")
    print(f"  'for r in roster' встречается: {src.count('for r in roster')} раз")
    print(f"  avatars_ref[\"elements\"][ ... ] = : "
          f"{src.count('avatars_ref[')} обращений всего")

    print("\nГотово. Пришли Брату всё, что выше.")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        print(e)
    except Exception as e:
        print(f"смотрелец споткнулся: {e}")
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно ")
