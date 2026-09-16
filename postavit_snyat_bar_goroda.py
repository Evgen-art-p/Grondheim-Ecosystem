# -*- coding: utf-8 -*-
# POSTAVIT_SNYAT_BAR_GORODA_V1
"""
ПАТЧ: в РЕАЛЕ снимается и бар города, а не только курсор истории.

Запускать из КОРНЯ РЕПО:
    python postavit_snyat_bar_goroda.py

ЧТО БЫЛО НЕ ТАК
    Кадр обрезается по полю `рынок.бар` в столе — правильная защита:
    она не даёт трейдеру подглядывать в будущее, показывая только то,
    что было на бару, где город стоит.

    Но после прогона в этом поле остаётся последний бар прогона
    (2025.01.20). Все бары живого рынка СВЕЖЕЕ — значит после обрезки
    не остаётся ни одного, и кадр не рисуется вовсе:

        [КАДР] по бару города 2025.01.20 00:00 баров нет — кадра не будет

    Тумблер РЕАЛ тут не помогал: он снимает КУРСОР ИСТОРИИ, а это
    другое поле. `рынок.бар` никто не убирал, и он лежал с прошлого
    прогона.

ЧТО ДЕЛАЕТ
    Ушли в реал — снимаем и его, рядом с курсором. Одной защиты это
    не отменяет: в прогоне бар города ставится на каждом шаге заново,
    и подглядывать в будущее по-прежнему нельзя.

ПОРЯДОК
    Идемпотентен. Бэкап .bak_bar_goroda, ast.parse перед записью.

`шесть·проверено·до·корня`
"""
import ast
import shutil
from pathlib import Path

_KOREN = Path(__file__).resolve().parent
MARKER = "# SNYAT_BAR_GORODA_V1"


def _nayti():
    kand = [p for p in _KOREN.rglob("ui_torg.py")
            if "_АРХИВ" not in str(p) and "_УБОРКА" not in str(p)
            and ".bak" not in p.name]
    if not kand:
        print("⚠ не нашёл ui_torg.py. Запускай из корня репозитория.")
        return None
    if len(kand) > 1:
        print("Нашёл несколько:")
        for i, p in enumerate(kand, 1):
            print(f"  {i}. {p.relative_to(_KOREN)}")
        try:
            return kand[int(input("Который? номер: ").strip()) - 1]
        except Exception:
            print("Не понял — беру первый.")
    return kand[0]


STARO = '''        if not is_tester:
            try:
                import istoriya
                if istoriya.gde_stoim():
                    istoriya.postavit("")
                    print("[ВРЕМЯ] курсор истории снят — вернулись в реал")
            except Exception:
                pass'''

NOVO = '''        if not is_tester:
            try:
                import istoriya
                if istoriya.gde_stoim():
                    istoriya.postavit("")
                    print("[ВРЕМЯ] курсор истории снят — вернулись в реал")
            except Exception:
                pass
            # SNYAT_BAR_GORODA_V1: и бар города тоже. Кадр обрезается
            # по полю `рынок.бар` (чтобы трейдер не подглядывал в
            # будущее), но после прогона там остаётся его последний
            # бар. Все бары живого рынка свежее — после обрезки не
            # остаётся ни одного, и кадр не рисуется совсем:
            #   «по бару города 2025.01.20 баров нет — кадра не будет»
            # Курсор истории — другое поле, тумблер его снимал, а это
            # лежало с прошлого раза.
            # Защиту не отменяем: в прогоне бар города ставится заново
            # на каждом шаге.
            try:
                from hooks import (load_trading_state as _lts_r,
                                   save_trading_state as _sts_r)
                _t_r = _lts_r() or {}
                _ryn_r = dict(_t_r.get("рынок") or {})
                if _ryn_r.get("бар"):
                    _staryy_bar = _ryn_r.get("бар")
                    _ryn_r["бар"] = ""
                    _t_r["рынок"] = _ryn_r
                    _sts_r(_t_r)
                    print(f"[ВРЕМЯ] бар города снят ({_staryy_bar}) — "
                          f"живой кадр больше не обрезается прошлым")
            except Exception as _e_bg:
                print(f"[ВРЕМЯ] бар города не снялся: {_e_bg}")'''


def main():
    print("=" * 58)
    print("СНЯТЬ БАР ГОРОДА В РЕАЛЕ")
    print("=" * 58)

    fajl = _nayti()
    if fajl is None:
        return
    print(f"\nфайл: {fajl.relative_to(_KOREN)}")

    tekst = fajl.read_text(encoding="utf-8")
    if MARKER in tekst:
        print("\n✓ патч уже стоит — ничего не делаю.")
        return

    n = tekst.count(STARO)
    print("\n--- ЗАМЕНА ---")
    print(f"  {'✓' if n == 1 else '⚠ ' + str(n)}  снятие бара города в реале")
    if n != 1:
        print("\n⚠ не сошлось — ничего не тронул. Покажи файл, пересоберу.")
        return

    novyy = tekst.replace(STARO, NOVO, 1).rstrip() + f"\n\n{MARKER} - marker\n"

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"\n⚠ не разбирается: строка {e.lineno}: {e.msg}")
        print("  На диск НЕ писал.")
        return
    print("\n  ast.parse — чисто")

    bak = fajl.with_suffix(fajl.suffix + ".bak_bar_goroda")
    shutil.copy2(fajl, bak)
    fajl.write_text(novyy, encoding="utf-8")
    print(f"  бэкап:  {bak.name}")
    print(f"  записан: {fajl.name}")

    print("\n✓ готово. Перезапусти город и жми РЕАЛ:")
    print("  В консоли должно мелькнуть:")
    print("    [ВРЕМЯ] бар города снят (2025.01.20 00:00) — …")
    print("  После этого кадр USDCNH должен нарисоваться.")
    print("  Если снова «баров нет» — причина другая, скажи.")
    print("=" * 58)


if __name__ == "__main__":
    main()
    try:
        input("\nEnter — закрыть: ")
    except Exception:
        pass

# POSTAVIT_SNYAT_BAR_GORODA_V1 - marker
