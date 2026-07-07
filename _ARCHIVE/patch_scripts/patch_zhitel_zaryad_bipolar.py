# -*- coding: utf-8 -*-
"""
PATCH: ЖИТЕЛЬ · ДВУСТОРОННИЙ ЗАРЯД — полоса с нулём в центре.
Маркер: ZHITEL_ZARYAD_BIPOLAR_V1

ПРИЧИНА (поймал Шеф): заряд −1..+1 — число ДВУСТОРОННЕЕ, а полоса
рисовала только модуль (|заряд|) от 0 до 100% ВПРАВО. Минусу физически
некуда было деться — полоса могла только расти в одну сторону, знак
показывал лишь цвет. Не путаница восприятия — неверная форма для
двустороннего числа.

СТАЛО: центр полосы — видимая метка (тонкая линия) = заряд ровно 0.
  плюс  → заливка растёт ВПРАВО от центра
  минус → заливка растёт ВЛЕВО от центра
Сила (|заряд|) — на сколько ушла заливка от центра к краю (макс на
±1.0 = заливка ровно до края половины). Знак виден и по стороне,
и по цвету — надёжно, без чтения цифры.

ОПТИКА (нижняя полоса, модуль-шкала 0..100%) не трогаем — там как раз
нужна ОДНОСТОРОННЯЯ шкала (сила безотносительно знака), это осталось
верно как было.

Идемпотентен: маркер в файле → не трогаем.
Требует: patch_zhitel_panel.py (функция _pokazateli_html существует).

Запуск из корня репо:  python patch_zhitel_zaryad_bipolar.py
"""
import sys
import ast
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = Path(__file__).resolve().parent
TARGET = REPO / "жители" / "ui_zhitel.py"

# ── CSS: добавляем центр-метку и абсолютное позиционирование для заряда ──
CSS_ANCHOR = '''.zpok-fill{ height:100%; border-radius:4px; }'''
CSS_INSERT = '''.zpok-fill{ height:100%; border-radius:4px; }
.zpok-bar--zaryad{ position:relative; }
.zpok-bar--zaryad .zpok-fill{ position:absolute; top:0; bottom:0; }
.zpok-mid{ position:absolute; left:50%; top:-2px; bottom:-2px; width:1px;
  background:rgba(255,255,255,0.4); z-index:2; }'''

# ── Python: пересобираем расчёт и разметку заряда ──
FUNC_ANCHOR = '''    # полоса заряда: от центра, знак цветом
    znak = "+" if charge >= 0 else "−"
    zcolor = "rgba(80,250,123,0.9)" if charge >= 0 else "rgba(255,120,120,0.9)"
    zwidth = int(mut * 100)

    dna = p.get("DNA_Static", {}) or {}
    dna_str = " · ".join(f"{k.split('_')[0]} {v}" for k, v in dna.items())

    return (
        '<div class="zpok">'
        f'<div class="zpok-row"><div class="zpok-lab">заряд<b>{znak}{mut:.2f}</b></div>'
        f'<div class="zpok-bar"><div class="zpok-fill" '
        f'style="width:{zwidth}%; background:{zcolor};"></div></div></div>'''

FUNC_INSERT = '''    # ZHITEL_ZARYAD_BIPOLAR_V1: полоса ДВУСТОРОННЯЯ — ноль в центре,
    # плюс растёт вправо, минус растёт влево (не только модуль вправо)
    znak = "+" if charge >= 0 else "−"
    zcolor = "rgba(80,250,123,0.9)" if charge >= 0 else "rgba(255,120,120,0.9)"
    _half = min(1.0, mut) * 50  # половина шкалы = сила 0..1 -> 0..50%
    zleft = 50 if charge >= 0 else 50 - _half
    zwidth = _half

    dna = p.get("DNA_Static", {}) or {}
    dna_str = " · ".join(f"{k.split('_')[0]} {v}" for k, v in dna.items())

    return (
        '<div class="zpok">'
        f'<div class="zpok-row"><div class="zpok-lab">заряд<b>{znak}{mut:.2f}</b></div>'
        f'<div class="zpok-bar zpok-bar--zaryad"><div class="zpok-mid"></div>'
        f'<div class="zpok-fill" '
        f'style="left:{zleft}%; width:{zwidth}%; background:{zcolor};"></div></div></div>'''


def install():
    print("═══ PATCH ZHITEL_ZARYAD_BIPOLAR_V1 — двусторонний заряд ═══")
    print(f"репо: {REPO}")

    if not TARGET.exists():
        print(f"  ✖ не найден: {TARGET.relative_to(REPO)}")
        return False

    src = TARGET.read_text(encoding="utf-8")

    if "ZHITEL_ZARYAD_BIPOLAR" in src:
        print("  ○ уже накатано — не трогаю")
        return True

    if CSS_ANCHOR not in src or FUNC_ANCHOR not in src:
        print("  ✖ якорь не найден — файл менялся, останавливаюсь. "
              "Покажи текущую _pokazateli_html.")
        return False

    src = src.replace(CSS_ANCHOR, CSS_INSERT)
    src = src.replace(FUNC_ANCHOR, FUNC_INSERT)

    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"  ✖ СИНТАКСИС БИТЫЙ: {e}")
        return False

    TARGET.write_text(src, encoding="utf-8")
    print("  ✔ полоса заряда: ноль в центре, минус растёт влево, плюс вправо")
    print("  ✔ синтаксис чист")
    return True


if __name__ == "__main__":
    ok = install()
    sys.exit(0 if ok else 1)
