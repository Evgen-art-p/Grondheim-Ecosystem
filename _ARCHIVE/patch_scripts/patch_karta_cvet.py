# -*- coding: utf-8 -*-
"""
PATCH: КАРТА · ЦВЕТ ТОЧЕК — правка на проверенную палитру старого кабинета.
Маркер: KARTA_CVET_V1

ПРИЧИНА: первая версия точек использовала полупрозрачный градиент
(rgba(...,0.55)→rgba(...,0.12)) — на тёмном фоне карты это читалось
мутным, грязным пятном («поносного цвета» — точное слово Шефа).

ЧТО БЕРЁМ: точную, уже проверенную живьём в -2 палитру `.cab-map-agent`
(studio/cabinet/css.py) — насыщенный цвет без градиента, opacity 0.85,
чёткая точка 10px. Не выдумываю новую — беру то, что реально работало.

  дома (по умолчанию)  → зелёный  rgba(80,250,123,0.85)   — как база
                          агента в -2 (живой, на месте)
  активная (на смене)   → золотой  rgba(201,168,76,0.85)  — ровно цвет
                          состояния "walking" в -2, тот же пульс-кольцо
                          (box-shadow expanding ring, не transform:scale)

Идемпотентен: если новая палитра уже стоит (маркер "grondPulseWalk"
в файле) — патч не трогает файл. Иначе меняет ТОЛЬКО CSS-блок точек,
остального (JS, разметка, локации) не касается.

Требует: patch_karta_zhiteli.py уже накатан (файл содержит load_zhiteli
и старый блок .grond-zhitel — иначе патчить нечего).

Запуск из корня репо:  python patch_karta_cvet.py
"""
import sys
import ast
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = Path(__file__).resolve().parent
TARGET = REPO / "ГОРОД" / "ui_grondheim.py"

STARYI_BLOK = '''.grond-zhitel{
  position: absolute; border-radius: 50%; z-index: 3; box-sizing: border-box;
  background: radial-gradient(circle, rgba(201,168,76,0.55), rgba(201,168,76,0.12));
  border: 1px solid rgba(201,168,76,0.5);
}
.grond-zhitel--active{
  position: absolute; border-radius: 50%; z-index: 4; box-sizing: border-box;
  background: radial-gradient(circle, rgba(0,220,240,0.9), rgba(0,140,160,0.3));
  border: 1px solid rgba(0,220,240,0.9);
  box-shadow: 0 0 10px rgba(0,220,240,0.55);
  animation: grondPulse 1.6s ease-in-out infinite;
}
@keyframes grondPulse{
  0%,100%{ transform: scale(1); }
  50%{ transform: scale(1.3); }
}'''

NOVYI_BLOK = '''.grond-zhitel{
  position: absolute; border-radius: 50%; z-index: 3; box-sizing: border-box;
  background: rgba(80,250,123,0.85);
  border: 1px solid rgba(80,250,123,0.5);
  transition: transform 0.15s, box-shadow 0.15s;
}
.grond-zhitel:hover{
  transform: scale(1.4);
  box-shadow: 0 0 10px rgba(80,250,123,0.6);
  z-index: 6;
}
.grond-zhitel--active{
  position: absolute; border-radius: 50%; z-index: 4; box-sizing: border-box;
  background: rgba(201,168,76,0.85);
  border: 1px solid rgba(201,168,76,0.6);
  animation: grondPulseWalk 1.5s infinite;
}
.grond-zhitel--active:hover{
  transform: scale(1.4);
  z-index: 6;
}
@keyframes grondPulseWalk{
  0%,100%{ box-shadow: 0 0 0 0 rgba(201,168,76,0.5); }
  50%{ box-shadow: 0 0 0 6px rgba(201,168,76,0); }
}'''


def install():
    print("═══ PATCH KARTA_CVET_V1 — правка цвета точек ═══")
    print(f"репо: {REPO}")

    if not TARGET.exists():
        print(f"  ✖ не найден: {TARGET.relative_to(REPO)}")
        return False

    src = TARGET.read_text(encoding="utf-8")

    if "grondPulseWalk" in src:
        print("  ○ новая палитра уже стоит — не трогаю")
        return True

    if "load_zhiteli" not in src:
        print("  ✖ patch_karta_zhiteli.py ещё не накатан — сначала он, "
              "потом эта правка")
        return False

    if STARYI_BLOK not in src:
        print("  ✖ старый блок точек не найден в ожидаемом виде — "
              "файл менялся руками. Покажи мне текущий CSS-блок "
              ".grond-zhitel, поправлю точечно.")
        return False

    src = src.replace(STARYI_BLOK, NOVYI_BLOK)

    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"  ✖ СИНТАКСИС БИТЫЙ: {e}")
        return False

    TARGET.write_text(src, encoding="utf-8")
    print("  ✔ цвет заменён: зелёный (дома) / золотой-пульс (на смене)")
    print("  ✔ синтаксис чист")
    print("\n  Обнови /grondheim — точки станут яркими, не мутными.")
    return True


if __name__ == "__main__":
    ok = install()
    sys.exit(0 if ok else 1)
