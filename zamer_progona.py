# -*- coding: utf-8 -*-
# ZAMERSHCHIK_PROGONA_V2
"""
ЗАМЕРЩИК ПРОГОНА v2 — весь ПУСТОЙ бар целиком.

Запускать из КОРНЯ РЕПО:
    python zamer_progona.py

НИЧЕГО НЕ ПРАВИТ. Не патч: читает, считает, печатает итог и уходит.
Стол он трогает так же, как трогает обычный прогон (иначе замер
был бы враньём), но кода не меняет и бэкапов не плодит.

ЧТО МЕРЯЕТ
    Пятьдесят баров подряд, машинная часть одного бара:
      · build_market_data — полный пересчёт Вильямса по 300 барам
      · запись стола на диск и чтение его обратно
      · ведение точки и стопов (то, что крутится, пока точка жива)
      · печать в консоль
    Плюс общее время и разброс по барам.

ЧЕГО НЕ МЕРЯЕТ — и это важно
    Илью. LLM не зовётся вообще. Если вся машинерия даст полсекунды
    на бар, а в живом прогоне у тебя пять, — значит секунды съедает
    вызов модели, и половина подозреваемых отсекается сразу. Это
    тоже ответ.

`шесть·проверено·до·корня`
"""
import builtins
import sys
import time
from pathlib import Path

_KOREN = Path(__file__).resolve().parent
BAROV = 50          # сколько баров прогнать
OKNO = 300          # сколько баров в окне — как в rynok_novyy_bar
SIMVOL = "EURUSD"
ETAZH = "H1"


def _nayti_birzhu():
    """Находим папку Биржи по приметам, путей руками не вписываем."""
    for p in sorted(_KOREN.iterdir()):
        if p.is_dir() and (p / "hooks.py").is_file() \
                and (p / "williams_core.py").is_file():
            return p
    return None


# ── секундомеры ────────────────────────────────────────────
ITOG = {}


def _kopilka(imya):
    ITOG.setdefault(imya, [0.0, 0])
    return ITOG[imya]


def _obernut(modul, imya_f, imya_zamera):
    """Обернуть функцию секундомером. Нет такой — честно скажем."""
    staro = getattr(modul, imya_f, None)
    if staro is None or not callable(staro):
        return False

    def novo(*a, **kw):
        k = _kopilka(imya_zamera)
        t = time.perf_counter()
        try:
            return staro(*a, **kw)
        finally:
            k[0] += time.perf_counter() - t
            k[1] += 1

    setattr(modul, imya_f, novo)
    return True


def main():
    print("=" * 62)
    print("ЗАМЕРЩИК ПРОГОНА")
    print("=" * 62)

    birzha = _nayti_birzhu()
    if birzha is None:
        print("⚠ не нашёл папку Биржи рядом (ищу hooks.py + williams_core.py).")
        print("  Запускай из корня репозитория.")
        return
    print(f"\nБиржа: {birzha.name}")
    sys.path.insert(0, str(birzha))

    try:
        import hooks
    except Exception as e:
        print(f"⚠ hooks не импортировался: {e}")
        return

    # ── бары: берём тем же краном, что и город ──
    print(f"беру бары: {SIMVOL} {ETAZH} …")
    try:
        from feed_source import bars as _src_bars
        vse, point = _src_bars(SIMVOL, ETAZH, OKNO + BAROV + 5)
    except Exception as e:
        print(f"⚠ кран молчит: {e}")
        print("  (в тестере бары берутся из CSV — проверь, что режим ТЕСТЕР)")
        return

    if not vse or len(vse) < OKNO + BAROV:
        print(f"⚠ баров мало: {len(vse) if vse else 0}, "
              f"нужно {OKNO + BAROV}")
        return
    print(f"взял: {len(vse)} баров")

    # ── вешаем секундомеры ──
    try:
        import tester_express as te
    except Exception as _e:
        te = None
        _staryy = builtins.print
        _staryy(f"  (tester_express не импортировался: {_e} — "
                f"меряю только ядро)")

    povesheno, netu = [], []
    for modul, imya_f, zamer in [
        (hooks, "build_market_data", "Вильямс (build_market_data)"),
        (hooks, "save_trading_state", "запись стола на диск"),
        (hooks, "load_trading_state", "чтение стола с диска"),
        (hooks, "_vesti_tochku", "ведение точки"),
        (hooks, "_vesti_stopy", "ведение стопов"),
    ] + ([
        (te, "_settle_bar", "ШАГ: _settle_bar (300 баров)"),
        (te, "_vesti_poziciyu", "ШАГ: _vesti_poziciyu (300 баров)"),
        (te, "_feed_check_closures", "ШАГ: лента закрытий"),
        (te, "build_market_data", "ШАГ: build_market_data (120 баров)"),
        (te, "proverit_tochku", "ШАГ: проверка точки"),
        (te, "proverit_nogu", "ШАГ: наблюдатель ног"),
        (te, "_hans_breakout", "ШАГ: пробой Ганса"),
    ] if te is not None else []):
        (povesheno if _obernut(modul, imya_f, zamer) else netu).append(imya_f)

    # печать меряем настоящую, в консоль: её стоимость и есть консоль
    _staryy_print = builtins.print

    def _print_s_chasami(*a, **kw):
        k = _kopilka("печать в консоль")
        t = time.perf_counter()
        try:
            return _staryy_print(*a, **kw)
        finally:
            k[0] += time.perf_counter() - t
            k[1] += 1

    if netu:
        _staryy_print(f"  (не нашёл и не мерю: {', '.join(netu)})")
    _staryy_print(f"\nиду по {BAROV} барам, это пара минут…\n")

    # ── прогон ──
    builtins.print = _print_s_chasami
    po_baram = []
    t_vsego = time.perf_counter()
    try:
        for i in range(BAROV):
            okno = vse[i:i + OKNO]
            t_bar = time.perf_counter()
            try:
                if te is not None:
                    # ровно то, что шаг делает ДО проверки «тихий бар»
                    te._settle_bar(okno, SIMVOL, ETAZH, point)
                    try:
                        te._vesti_poziciyu(okno, SIMVOL, ETAZH, point, None)
                    except Exception:
                        pass
                    _md = te.build_market_data(okno[-120:], symbol=SIMVOL,
                                               timeframe=ETAZH, point=point)
                    if _md:
                        te.proverit_tochku(_md)
                        te.proverit_nogu(_md)
                else:
                    hooks.rynok_novyy_bar(SIMVOL, ETAZH,
                                          window=okno, point=point)
            except Exception as e:
                builtins.print = _staryy_print
                print(f"⚠ бар {i}: {e}")
                builtins.print = _print_s_chasami
            po_baram.append(time.perf_counter() - t_bar)
    finally:
        builtins.print = _staryy_print
        vsego = time.perf_counter() - t_vsego

    # ── итог ──
    print()
    print("=" * 62)
    print(f"{BAROV} баров · всего {vsego:.1f} сек · "
          f"{vsego / BAROV:.2f} сек на бар")
    print("=" * 62)

    stroki = sorted(ITOG.items(), key=lambda x: -x[1][0])
    uchteno = 0.0
    for imya, (sek, raz) in stroki:
        # вложенные замеры не складываем вслепую: помечаем их
        dolya = sek / vsego * 100 if vsego else 0
        print(f"  {imya:32} {sek:7.2f} сек  {dolya:5.1f}%   "
              f"вызовов: {raz}  ({raz / BAROV:.1f} на бар)")
        if imya in ("Вильямс (build_market_data)", "запись стола на диск",
                    "чтение стола с диска", "печать в консоль"):
            uchteno += sek
    print(f"  {'— из них посчитано прямо':32} {uchteno:7.2f} сек")
    print(f"  {'— остальное (сам цикл)':32} {max(vsego - uchteno, 0):7.2f} сек")

    po_baram.sort()
    print()
    print(f"  самый быстрый бар: {po_baram[0]:.3f} сек")
    print(f"  середина:          {po_baram[len(po_baram) // 2]:.3f} сек")
    print(f"  самый долгий бар:  {po_baram[-1]:.3f} сек")
    print()
    print("  «ведение точки» и «ведение стопов» считаются ВНУТРИ бара —")
    print("  они частично перекрываются с записью стола, складывать их")
    print("  со всем остальным нельзя, смотри на них отдельно.")
    print("=" * 62)
    print("\nПришли это Брату целиком.")


if __name__ == "__main__":
    main()
    try:
        input("\nEnter — закрыть: ")
    except Exception:
        pass

# ZAMERSHCHIK_PROGONA_V2 - marker
