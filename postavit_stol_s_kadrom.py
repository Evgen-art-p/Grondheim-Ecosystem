# -*- coding: utf-8 -*-
# STOL_S_KADROM_V1 — стол на этаже отдаёт кадр вместе с числами
"""
СТОЛ И КАДР — ОДНОЙ РУКОЙ

БЕДА, КОТОРУЮ ЛЕЧИМ. Трейдер сходил на этаж рукой `stol_na_etazhe`,
рука честно отработала — а картинка у Шефа не сменилась. И это не
поломка: эта рука кадра не рисует вовсе, она отдаёт числа. Кадр
рисуют только `pokazat_etazh`, `rastyanut_volnu` и `uchebnik`.

Получалось, что трейдер должен ЗНАТЬ, какой рукой позвать, чтобы
его увидели. Слово Шефа: путаница лишняя, кадр важнее.

ЧТО ДЕЛАЕТ ПАТЧ, две правки:

 1. `Биржа/ruki_treydera.py` — рука `stol_na_etazhe` теперь сперва
    рисует кадр этого этажа, а числа кладёт следом, одним ответом:

        [КАДР: путь] EURUSD M15 · стол ниже
        === СТОЛ · EURUSD M15 ===
        ...числа...

    Кадр не нарисовался — числа всё равно уходят, как раньше. Рука
    не падает из-за картинки.

 2. Мозги A06/A07/A08 — подпись живого кадра берётся ПЕРВОЙ СТРОКОЙ
    ответа, а не первыми ста двадцатью знаками. Иначе на панель
    Шефа поехал бы кусок таблицы чисел вместо подписи.

Почему это безопасно: весь ответ руки и раньше уходил модели
текстом, а картинка досылалась отдельным сообщением, если ответ
начинался с `[КАДР: `. Мы не меняем механику — мы даём этой руке то
же право, что уже есть у трёх других.

БЕЗОПАСНОСТЬ:
 · .bak_stol_kadr рядом с каждым правленым файлом;
 · идемпотентен (маркер STOL_S_KADROM_V1);
 · синтаксис проверяется до записи;
 · `--suho` — показать и не трогать диск.

    python postavit_stol_s_kadrom.py --suho
    python postavit_stol_s_kadrom.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "STOL_S_KADROM_V1"
SUHO = "--suho" in sys.argv

_REPO = Path(__file__).resolve().parent
RUKI = _REPO / "Биржа" / "ruki_treydera.py"
SLOTY = _REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "слоты"

# ── правка 1: рука стола ─────────────────────────────────────
STARYY_STOL = '''            import stol as _s
            t = _s.nakryt(symbol, tf, self_key=self_key)
            return f"=== СТОЛ · {symbol} {tf} ===\\n" + _s.slovami(t)'''

NOVYY_STOL = '''            import stol as _s
            t = _s.nakryt(symbol, tf, self_key=self_key)
            chisla = f"=== СТОЛ · {symbol} {tf} ===\\n" + _s.slovami(t)
            # STOL_S_KADROM_V1: кадр важнее чисел, и просить его
            # отдельной рукой трейдер не обязан. Рисуем этот же этаж
            # и кладём числа следом. Картинка не вышла — уходят одни
            # числа, как было: рука из-за кадра не падает.
            try:
                import grafik
                put = grafik.kadr(symbol, tf)
            except Exception as _ek:
                put = None
                print(f"[СТОЛ] кадр {tf} не нарисовался ({_ek}) — только числа")
            if put:
                return (f"[КАДР: {put}] {symbol} {tf} · стол ниже\\n"
                        + chisla)
            return chisla'''

# ── правка 2: подпись живого кадра — первой строкой ──────────
STARAYA_PODPIS = '            _podpis = s[s.index("]") + 1:].strip()[:120]'
NOVAYA_PODPIS = ('            # STOL_S_KADROM_V1: подпись — ПЕРВАЯ строка. За ней\n'
                 '            # теперь может идти таблица чисел, и без этого на\n'
                 '            # панель Шефа поехал бы её кусок.\n'
                 '            _hvost = s[s.index("]") + 1:].strip().splitlines()\n'
                 '            _podpis = (_hvost[0] if _hvost else "")[:120]')


def _pravka(p: Path, staroe: str, novoe: str, imya: str) -> bool:
    """Одна замена в одном файле. Возвращает, тронули ли."""
    if not p.exists():
        print(f"  {imya}: файла нет — пропускаю")
        return False
    txt = p.read_text(encoding="utf-8")
    if MARKER in txt:
        print(f"  {imya}: уже стоит")
        return False
    if txt.count(staroe) != 1:
        print(f"  {imya}: ОТКАЗ — якорь встречается {txt.count(staroe)} раз(а), "
              f"не трогаю")
        return False
    novy = txt.replace(staroe, novoe, 1)
    try:
        ast.parse(novy)
    except SyntaxError as e:
        print(f"  {imya}: ОТКАЗ — после правки синтаксис сломан ({e})")
        return False
    if SUHO:
        print(f"  {imya}: готово к правке (сухой прогон)")
        return True
    shutil.copy2(p, p.with_suffix(p.suffix + ".bak_stol_kadr"))
    p.write_text(novy, encoding="utf-8")
    print(f"  {imya}: поправлено")
    return True


def main():
    print()
    print("СТОЛ И КАДР ОДНОЙ РУКОЙ" + ("  · СУХОЙ ПРОГОН" if SUHO else ""))
    print("корень:", _REPO)
    print()

    tronuto = 0

    print("1. РУКА СТОЛА:")
    tronuto += _pravka(RUKI, STARYY_STOL, NOVYY_STOL, "ruki_treydera.py")

    print()
    print("2. ПОДПИСЬ ЖИВОГО КАДРА В МОЗГАХ:")
    if not SLOTY.exists():
        print("  слотов нет — запускать из корня репы")
    else:
        for slot in ("A06", "A07", "A08"):
            tronuto += _pravka(SLOTY / slot / "мозг.py",
                               STARAYA_PODPIS, NOVAYA_PODPIS,
                               f"{slot}/мозг.py")

    print()
    if SUHO:
        print("Сухой прогон: на диске ничего не изменилось.")
    else:
        print(f"Тронуто файлов: {tronuto}. Бэкапы — .bak_stol_kadr")
    print("Теперь любой поход на этаж за числами показывает и картинку.")
    print()


if __name__ == "__main__":
    main()
