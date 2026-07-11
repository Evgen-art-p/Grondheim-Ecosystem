# -*- coding: utf-8 -*-
"""
patch_magic_v_masku_v1.py
────────────────────────────────────────────────────────────────────
ФУНДАМЕНТ ЗАПИСИ (МОСТ К НОСИТЕЛЮ, шаг 1 · вариант Б).

ЗАЧЕМ: когда позиция закрывается, код знает только `magic` (у Ильи
  100002). Чтобы вывод из сделки лёг в ПРАВИЛЬНОГО носителя, нужен путь
  magic → житель. Вариант Б (решение Шефа): magic живёт В МАСКЕ жителя,
  рядом с Turbo_Role — правда в маске, отдельного реестра магиков нет
  (Закон Пары / Закон Картриджа).

  Разведка репо (11-12.07) показала: магик уже лежит ЧЕТЫРЬМЯ статическими
  копиями (дом-паспорт, _MY_MAGIC в мозге, MAGIC_NUMBERS в hooks, таблица
  в промте A09) + лор в домашнем_промпте. Этот патч кладёт ПЯТУЮ — но
  делает её ЕДИНСТВЕННОЙ ПРАВДОЙ: маска. Остальные копии станут
  производными или уйдут (следующими патчами эталона).

ЧТО ДЕЛАЕТ (чисто аддитивно, живую торговлю НЕ трогает):
  1. Кладёт "magic" в маску «работа» трёх трейдеров, рядом с Turbo_Role:
        Брут    A06 → 100001
        Илья    A07 → 100002
        Василий A08 → 100003
     Сенсорам (A01-A04) и конторе магик НЕ нужен — позиций не держат.
  2. cartridge_registry.py:
        • _scan_zhiteli_maski отдаёт ещё и "magic" (одна строка);
        • НОВАЯ resolve_by_magic(magic) → носитель — обратный мостик,
          близнец resolve_para, тот же скан. ОДИН ход (не magic→слот→
          resolve_para, а сразу magic→носитель: скан уже держит обоих).
        • самопроверка печатает resolve_by_magic(100002) → Илья.

БЕЗОПАСНОСТЬ: resolve_by_magic пока никем в рантайме не зовётся (её
  позовёт эталон Авана, следующий патч). Скан отдаёт лишний ключ —
  старые читатели его игнорируют. Ни строчки поведения не меняется.

Идемпотентно (маски — по значению, .py — по маркеру). .bak рядом с .py.
Запускать из КОРНЯ репы:
    python patch_magic_v_masku_v1.py
проверка:
    python Биржа/cartridge_registry.py     # ждём строку «magic 100002 → Илья»
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

MARKER = "MAGIC_IN_MASK_V1"

# резидент → (ожидаемый слот, магик). Источник значений — hooks.MAGIC_NUMBERS.
MASKS = [
    ("Брут",    "A06", 100001),
    ("Илья",    "A07", 100002),
    ("Василий", "A08", 100003),
]
MASK_ROOT = Path("GRONDHEIM_CITY") / "жители" / "ковчег"

REGISTRY = Path("Биржа") / "cartridge_registry.py"

# ── .py правка 1: скан отдаёт magic ─────────────────────────────────
SCAN_OLD = (
    '            "core_phrase": mask.get("Core_Phrase", ""),\n'
    "        })\n"
)
SCAN_NEW = (
    '            "core_phrase": mask.get("Core_Phrase", ""),\n'
    '            "magic": mask.get("magic"),   # ' + MARKER + ": обратный мостик\n"
    "        })\n"
)

# ── .py правка 2: новая функция resolve_by_magic перед list_nositeli ─
FUNC_ANCHOR = 'def list_nositeli(ceh_id: str, kvartal: str = "Биржа") -> list:'
FUNC_NEW = (
    "def resolve_by_magic(magic):\n"
    '    """ОБРАТНЫЙ мостик: magic закрытой позиции → носитель.\n'
    "    Близнец resolve_para, тот же скан масок — magic живёт В МАСКЕ\n"
    "    (Закон Пары), отдельного реестра магиков нет. Честный None:\n"
    "    магик не найден ни в одной активной маске. Приводит к int, чтобы\n"
    '    100002 и "100002" резолвились одинаково. # ' + MARKER + "\n"
    '    """\n'
    "    try:\n"
    "        m = int(magic)\n"
    "    except (TypeError, ValueError):\n"
    "        return None\n"
    "    for z in _scan_zhiteli_maski():\n"
    '        zm = z.get("magic")\n'
    "        if zm is None:\n"
    "            continue\n"
    "        try:\n"
    "            if int(zm) == m:\n"
    "                return z\n"
    "        except (TypeError, ValueError):\n"
    "            continue\n"
    "    return None\n"
    "\n"
    "\n"
    + FUNC_ANCHOR
)

# ── .py правка 3: самопроверка ──────────────────────────────────────
SELFCHECK_OLD = (
    "    print(f\"несуществующий слот → {resolve_para('торговый_хаос', 'A99')}\")\n"
    '    print("═══ конец самопроверки ═══")\n'
)
SELFCHECK_NEW = (
    "    print(f\"несуществующий слот → {resolve_para('торговый_хаос', 'A99')}\")\n"
    "    _by_magic = resolve_by_magic(100002)\n"
    "    print(f\"magic 100002 → {(_by_magic or {}).get('имя') or '— не найден —'}\")\n"
    '    print("═══ конец самопроверки ═══")\n'
)


def patch_masks() -> int:
    problems = 0
    for name, slot, magic in MASKS:
        path = MASK_ROOT / name / "маски" / "работа" / "mask.json"
        if not path.exists():
            print(f"  ⚠ {name}: маски нет по пути {path} — пропускаю "
                  f"(структура отличается от Ильи? проверь глазами).")
            problems += 1
            continue
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  ✗ {name}: маска не читается как JSON ({e}) — пропускаю.")
            problems += 1
            continue

        tr = (obj.get("Turbo_Role") or "").strip()
        if tr != slot:
            print(f"  ⚠ {name}: Turbo_Role='{tr}', ждал '{slot}' — НЕ трогаю "
                  f"(аномалия пары, разберись вручную).")
            problems += 1
            continue

        if obj.get("magic") == magic:
            print(f"  ✓ {name} ({slot}): magic {magic} уже стоит.")
            continue

        # переставляем magic ровно после Turbo_Role, старое значение выкидываем
        new_obj = {}
        for k, v in obj.items():
            if k == "magic":
                continue
            new_obj[k] = v
            if k == "Turbo_Role":
                new_obj["magic"] = magic
        if "magic" not in new_obj:      # на случай маски без Turbo_Role
            new_obj["magic"] = magic

        path.write_text(
            json.dumps(new_obj, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        print(f"  ✓ {name} ({slot}): magic {magic} вписан в маску.")
    return problems


def patch_registry() -> int:
    if not REGISTRY.exists():
        print(f"✗ не нашёл {REGISTRY} — запусти из КОРНЯ репы "
              f"(там, где папка «Биржа»).")
        return 1
    src = REGISTRY.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"✓ cartridge_registry.py уже пропатчен ({MARKER}).")
        return 0

    for old in (SCAN_OLD, FUNC_ANCHOR, SELFCHECK_OLD):
        if old not in src:
            print("✗ cartridge_registry.py: не нашёл ожидаемый блок:\n"
                  f"  ┌─\n  {old.splitlines()[0]}\n  └─\n"
                  "  Файл правился вручную? Сверь с разведкой и поправь блоки "
                  "OLD в этом патче.")
            return 2

    bak = REGISTRY.with_suffix(REGISTRY.suffix + ".bak")
    if not bak.exists():
        bak.write_text(src, encoding="utf-8")
        print(f"  • бэкап: {bak}")
    else:
        print(f"  • бэкап уже был: {bak} (не перезаписываю)")

    src = src.replace(SCAN_OLD, SCAN_NEW, 1)
    src = src.replace(FUNC_ANCHOR, FUNC_NEW, 1)
    src = src.replace(SELFCHECK_OLD, SELFCHECK_NEW, 1)
    REGISTRY.write_text(src, encoding="utf-8")
    print(f"✓ cartridge_registry.py: resolve_by_magic + magic в скане ({MARKER}).")
    return 0


def main() -> int:
    print("═══ ФУНДАМЕНТ ЗАПИСИ · magic в маску + resolve_by_magic ═══")
    print("• маски трёх трейдеров:")
    mp = patch_masks()
    print("• реестр:")
    rc = patch_registry()
    print("───")
    if rc == 0 and mp == 0:
        print("Готово. Проверка: python Биржа/cartridge_registry.py")
        print("Ждём в самопроверке строку: «magic 100002 → Илья».")
        return 0
    if rc != 0:
        print("Реестр НЕ пропатчен — см. выше. Мостик обратный не заработает.")
        return rc
    print(f"Реестр — ок, но по маскам {mp} замечани(е/я) — см. ⚠ выше.")
    return 0


if __name__ == "__main__":
    if isinstance(sys.stdout, __import__("io").TextIOWrapper):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    sys.exit(main())
