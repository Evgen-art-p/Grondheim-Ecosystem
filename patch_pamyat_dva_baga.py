# -*- coding: utf-8 -*-
"""
patch_pamyat_dva_baga.py
════════════════════════════════════════════════════════════════════
ДВА БАГА В ПУТИ MEMORY_REQUEST — оба ломали второй вызов LLM после
подъёма памяти, найдены в живом логе (Брут, EURUSD)

БАГ 1 — nositel.py, vspomnit_slotom: KeyError 'дом'
  Строка: d = _dvizhok(n["носитель"]["дом"])
  Но dusha_slota (та же самая функция, строкой раньше в файле!) читает
  папку резидента как n["папка"] (строка 167), НЕ n["носитель"]["дом"].
  "дом" — не то поле вообще: это домашняя локация (прописка) из
  _sobrat_dushu, не путь к папке резидента. Опечатка/путаница имён
  полей. Правильный ключ — "папка".

БАГ 2 — A06/A08 мозг.py: NameError name '_temp' is not defined
  Второй вызов chat() (после подъёма памяти) зовёт temperature=_temp —
  но _temp НИГДЕ не определена ни в A06, ни в A08 (там температура —
  функция _my_temp(), не переменная). Похоже, скопировано из A07 (там
  _temp — реальная локальная переменная, temperatura_slota(...)),
  без адаптации под то, как A06/A08 реально хранят температуру.

ПОСЛЕДСТВИЕ ОБОИХ: второй вызов (тот, где житель отвечает УЖЕ ЗНАЯ,
подняв память) падает в try/except, ответ остаётся ПЕРВЫМ, наивным —
подъём памяти происходит, но не долетает до решения. Тихая потеря
качества, не крах — оба обёрнуты в try/except, поэтому раньше не
замечалось.

ИДЕМПОТЕНТЕН. Бэкапы — по файлу.
Запуск из корня Grondheim-Ecosystem:
    python patch_pamyat_dva_baga.py
"""
import io
import sys
from pathlib import Path

MARKER = "PAMYAT_DVA_BAGA_V1"


def find_nositel():
    for base in (Path("Биржа"), Path("GRONDHEIM_CITY") / "Биржа"):
        p = base / "nositel.py"
        if p.exists():
            return p
    return None


def find_brain(aid):
    for base in (Path("GRONDHEIM_CITY") / "Биржа", Path("Биржа")):
        p = base / "цеха" / "торговый_хаос" / "слоты" / aid / "мозг.py"
        if p.exists():
            return p
    return None


def patch_nositel():
    path = find_nositel()
    if not path:
        print("[ПАТЧ] ⚠️  nositel.py не найден — пропуск бага 1")
        return
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("[ПАТЧ] ✓ nositel.py уже пропатчен")
        return

    old = '        d = _dvizhok(n["носитель"]["дом"])\n'
    new = ('        # ' + MARKER + ': было "дом" (не то поле — это прописка\n'
           '        # из _sobrat_dushu). Папка резидента — "папка" (см.\n'
           '        # dusha_slota выше в этом же файле, n["папка"]).\n'
           '        d = _dvizhok(n["носитель"]["папка"])\n')
    if old not in src:
        print("[ПАТЧ] ✗ nositel.py: якорь 'дом' не найден — проверь вручную")
        return

    new_src = src.replace(old, new, 1)
    import ast
    try:
        ast.parse(new_src)
    except SyntaxError as e:
        print(f"[ПАТЧ] ✗ nositel.py: правка ломает синтаксис ({e})")
        return

    bak = path.with_suffix(".py.bak_pamyat_baga")
    if not bak.exists():
        bak.write_text(src, encoding="utf-8")
    path.write_text(new_src, encoding="utf-8")
    print("[ПАТЧ] ✓ nositel.py: 'дом' → 'папка' (Баг 1 починен)")


def patch_brain(aid, anchor_line):
    path = find_brain(aid)
    if not path:
        print(f"[ПАТЧ] ⚠️  {aid}: мозг.py не найден — пропуск")
        return
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print(f"[ПАТЧ] ✓ {aid}: уже пропатчен")
        return

    old = anchor_line
    if old not in src:
        print(f"[ПАТЧ] ⚠️  {aid}: якорь 'temperature=_temp)' не найден — "
              f"проверь вручную")
        return

    new = old.replace("temperature=_temp)",
                       "temperature=_my_temp())  # " + MARKER)
    new_src = src.replace(old, new, 1)
    import ast
    try:
        ast.parse(new_src)
    except SyntaxError as e:
        print(f"[ПАТЧ] ✗ {aid}: правка ломает синтаксис ({e})")
        return

    bak = path.with_suffix(".py.bak_pamyat_baga")
    if not bak.exists():
        bak.write_text(src, encoding="utf-8")
    path.write_text(new_src, encoding="utf-8")
    print(f"[ПАТЧ] ✓ {aid}: temperature=_temp → _my_temp() (Баг 2 починен)")


def main():
    patch_nositel()
    # якорь у каждого свой отступ/контекст — берём последнюю строку
    # (второй, memory-request вызов), а не первую (уже верна у обоих)
    patch_brain("A06", "                temperature=_temp)\n")
    patch_brain("A08", "                temperature=_temp)\n")
    print("[ПАТЧ] ✅ Готово. Второй вызов после MEMORY_REQUEST теперь")
    print("[ПАТЧ]    реально долетает (память поднимается и участвует).")


if __name__ == "__main__":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass
    main()
