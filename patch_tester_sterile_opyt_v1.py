# -*- coding: utf-8 -*-
"""
patch_tester_sterile_opyt_v1.py
────────────────────────────────────────────────────────────────────
СТЕРИЛЬНОСТЬ ТЕСТЕРА РАСПРОСТРАНЯЕТСЯ НА НОГУ ОПЫТА.

ПОЙМАНО ДО ПРОГОНА (12.07). Тестер держит договор TESTER_STERILE_V1:
  learn=False (УМОЛЧАНИЕ) → «бэктест не калечит живых»: sync_to_dna
  глушится заглушкой, ДНК агентов не мутирует. Смотрим, не калеча.

Но нога Опыта (patch_etalon_avana_v1) идёт МИМО этой заглушки — через
nositel.zapisat_vyvod, о которой тестер не знает. Итог без этого патча:
  ОБЫЧНЫЙ стерильный прогон на 145 кандидатах ПО-НАСТОЯЩЕМУ переписывает
  паспорт Ильи — заряд едет, а его пять рождённых якорей («вхожу на open
  … виню только себя») вытесняются тестовыми выводами в архив.
  Бэктест, который калечит жителя. Ровно то, от чего ставился STERILE_V1.

ЛЕЧЕНИЕ: тот же рубильник, что у sync_to_dna.
  без --learn → zapisat_vyvod заглушена: Совет думает, сделки считаются,
                трейдер ЧИТАЕТ свою душу (чтение безвредно) — но в паспорт
                никто не пишет. Стерильно.
  с  --learn  → нога Опыта работает: якоря растут, заряд качается.
                Учебный прогон, как в реале.

Читающий конец (душа в промпте) работает ВСЕГДА — он ничего не пишет.
Опыт Ильи виден модели и на стерильном прогоне: смотреть можно, калечить нет.

Идемпотентно. .bak рядом. Из КОРНЯ репы:
    python patch_tester_sterile_opyt_v1.py
"""
from __future__ import annotations
import io
import sys
from pathlib import Path

MARKER = "TESTER_STERILE_OPYT_V1"
TARGET = Path("Биржа") / "tester_express.py"
NEED = "JUDGE_TRADER_NOSITEL_V1"        # нога Опыта должна стоять в hooks

OLD_STUB = """    _orig_sync = _gm.sync_to_dna
    if not learn:
        _gm.sync_to_dna = lambda *a, **k: None   # заглушка-микрофон
        print('[TESTER] 🧪 стерильный прогон: ДНК агентов НЕ мутирует '
              '(--learn чтобы учить)')
    else:
        print('[TESTER] 🎓 учебный прогон: ДНК агентов мутирует, как в реале')
"""

NEW_STUB = """    _orig_sync = _gm.sync_to_dna
    if not learn:
        _gm.sync_to_dna = lambda *a, **k: None   # заглушка-микрофон
        print('[TESTER] 🧪 стерильный прогон: ДНК агентов НЕ мутирует '
              '(--learn чтобы учить)')
    else:
        print('[TESTER] 🎓 учебный прогон: ДНК агентов мутирует, как в реале')

    # ── """ + MARKER + """: НОГА ОПЫТА подчиняется тому же рубильнику ──
    # hooks._judge_trader_by_result пишет вывод из сделки в ЖИВОЙ паспорт
    # жителя (Anchor_Points + заряд) через nositel.zapisat_vyvod. Это мимо
    # заглушки sync_to_dna выше — значит стерильный прогон молча калечил бы
    # Илью: его пять рождённых якорей вытеснялись бы тестовыми выводами.
    # Глушим тем же рубильником. ЧИТАЮЩИЙ конец (душа в промпте) не трогаем —
    # чтение безвредно, трейдер и в стерильном прогоне сидит за столом собой.
    try:
        import nositel as _nos
    except Exception as _e:
        _nos = None
        print(f'[TESTER] ℹ️  мост к носителю не поднялся ({_e})')
    _orig_vyvod = _nos.zapisat_vyvod if _nos is not None else None
    if _nos is not None and not learn:
        _nos.zapisat_vyvod = (lambda *a, **k:
                              {'дописано': False, 'причина': 'стерильный прогон'})
        print('[TESTER] 🧪 стерильно: нога Опыта молчит — '
              'паспорта жителей НЕ трогаем (--learn чтобы учить)')
    elif _nos is not None:
        print('[TESTER] 🎓 учебно: нога Опыта пишет — '
              'якоря жителей будут расти, заряд качаться')
"""

OLD_RESTORE = """        _gm.sync_to_dna = _orig_sync   # TESTER_STERILE_V1: вернуть обучение
"""
NEW_RESTORE = """        _gm.sync_to_dna = _orig_sync   # TESTER_STERILE_V1: вернуть обучение
        if _nos is not None and _orig_vyvod is not None:
            _nos.zapisat_vyvod = _orig_vyvod   # """ + MARKER + """: вернуть ногу Опыта
"""


def main() -> int:
    if isinstance(sys.stdout, io.TextIOWrapper):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    if not TARGET.exists():
        print(f"✗ не нашёл {TARGET} — запусти из КОРНЯ репы.")
        return 1

    hooks = Path("Биржа") / "hooks.py"
    if hooks.exists() and NEED not in hooks.read_text(encoding="utf-8"):
        print("✗ сначала patch_etalon_avana_v1.py (нога Опыта в hooks).")
        return 2

    src = TARGET.read_text(encoding="utf-8")
    if MARKER in src:
        print(f"✓ уже пропатчено ({MARKER}) — ничего не делаю.")
        return 0

    for old, what in ((OLD_STUB, "блок стерильности (заглушка sync_to_dna)"),
                      (OLD_RESTORE, "возврат sync_to_dna в finally")):
        if old not in src:
            print(f"✗ не нашёл: {what}. Файл правился вручную? Сверь глазами.")
            return 3

    bak = TARGET.with_suffix(".py.bak2")
    if not bak.exists():
        bak.write_text(src, encoding="utf-8")
        print(f"• бэкап: {bak}")

    src = src.replace(OLD_STUB, NEW_STUB, 1)
    src = src.replace(OLD_RESTORE, NEW_RESTORE, 1)
    TARGET.write_text(src, encoding="utf-8")

    print(f"✓ {TARGET}: нога Опыта подчиняется стерильности.")
    print("   без --learn → паспорта жителей НЕ трогаются (смотрим, не калеча)")
    print("   с  --learn → якоря растут, заряд качается (учебный прогон)")
    print(f"   Маркер: {MARKER}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
