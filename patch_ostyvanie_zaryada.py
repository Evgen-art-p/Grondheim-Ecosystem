# patch_ostyvanie_zaryada.py
# OSTYVANIE_ZARYADA_V1 · заряд тает к нулю с каждым вдохом, не застывает
# ─────────────────────────────────────────────────────────────
# Закон (Шеф, 28.06): остывание — на фиксированный процент за каждый
# вдох (не по реальному времени — иначе без диалога обида не пройдёт
# сама за неделю тишины). Упрямство (Stubbornness) держит заряд дольше:
# упрямый таёт медленнее, как и сопротивляется новому удару медленнее.
#
# Делает в dvizhok.py:
#   1. Добавляет константу OSTYVANIE_BAZA — базовый процент остывания
#      за один вдох (10%), который упрямство масштабирует.
#   2. vdoh() в самом начале — ДО сдвига от нового входа — остужает уже
#      набранный заряд к нулю на (1 - упрямство) долю базового процента.
#      Сначала маятник чуть качнулся обратно сам, потом пришёл новый
#      толчок — порядок важен, иначе вдох толкает ещё неостывший заряд.
#
# Формула остывания:
#   реальный_коэф = OSTYVANIE_BAZA * (1.0 - 0.7 * stubborn)
#   (упрямый stubborn=1.0 теряет только 30% базовой скорости остывания;
#    послушный stubborn=0.0 остывает на полный базовый процент)
#   self.charge *= (1.0 - реальный_коэф)
#
# Идемпотентно. Бэкап в .bak_ostyvanie_zaryada.
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import ast, shutil, sys
from pathlib import Path

MARKER = "OSTYVANIE_ZARYADA_V1"
TARGET = Path(__file__).resolve().parent / "dvizhok.py"


def main():
    if not TARGET.exists():
        print(f"✗ не нашёл {TARGET} — положи патч в корень репо рядом с dvizhok.py")
        sys.exit(1)
    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"✓ {MARKER} уже на месте — пропускаю")
        return

    # ── 1) Константа остывания — рядом с _znak ──
    anchor_const = '''# знак входа: что тянет вверх (+), что вниз (−)
# но РЕШАЕТ не это — это лишь куда качнуло маятник
def _znak(tonus: str) -> float:
    return {"плюс": 1.0, "минус": -1.0, "ровно": 0.0}.get(tonus, 0.0)'''
    if anchor_const not in src:
        print("✗ шаг 1: не нашёл def _znak — стоп")
        sys.exit(1)
    new_const = '''# знак входа: что тянет вверх (+), что вниз (−)
# но РЕШАЕТ не это — это лишь куда качнуло маятник
def _znak(tonus: str) -> float:
    return {"плюс": 1.0, "минус": -1.0, "ровно": 0.0}.get(tonus, 0.0)


# OSTYVANIE_ZARYADA_V1: заряд тает к нулю с каждым вдохом, не застывает.
# Не по реальному времени — на фиксированный процент за вдох (иначе без
# диалога обида не пройдёт сама за неделю тишины). Упрямство держит
# заряд дольше: упрямый таёт медленнее.
OSTYVANIE_BAZA = 0.10   # базовый процент остывания за один вдох (10%)'''
    src = src.replace(anchor_const, new_const, 1)

    # ── 2) vdoh(): остывание ДО сдвига от нового входа ──
    anchor_vdoh = '''        # насколько тронуло = сила × свежесть × резонанс ядра.
        # эмпатия усиливает удар (чужое чувствуется как своё).
        trogaet = sila * svezhest * (0.5 + self.resonance) * (0.5 + self.empathy)'''
    if anchor_vdoh not in src:
        print("✗ шаг 2: не нашёл начало расчёта trogaet в vdoh() — стоп")
        sys.exit(1)
    new_vdoh = '''        # OSTYVANIE_ZARYADA_V1: маятник сначала чуть качнулся обратно к
        # покою САМ (до нового толчка) — упрямый тает медленнее.
        _ostyv_koef = OSTYVANIE_BAZA * (1.0 - 0.7 * self.stubborn)
        self.charge *= (1.0 - _ostyv_koef)

        # насколько тронуло = сила × свежесть × резонанс ядра.
        # эмпатия усиливает удар (чужое чувствуется как своё).
        trogaet = sila * svezhest * (0.5 + self.resonance) * (0.5 + self.empathy)'''
    src = src.replace(anchor_vdoh, new_vdoh, 1)

    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"✗ синтаксис: {e}")
        sys.exit(1)

    if not TARGET.with_suffix(".py.bak_ostyvanie_zaryada").exists():
        shutil.copy2(TARGET, TARGET.with_suffix(".py.bak_ostyvanie_zaryada"))
    TARGET.write_text(src, encoding="utf-8")
    print(f"✓ {MARKER}: заряд остывает на фикс. процент за вдох, упрямый — медленнее")


if __name__ == "__main__":
    main()
