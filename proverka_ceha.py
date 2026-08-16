# -*- coding: utf-8 -*-
"""
proverka_ceha.py — почему цех молчит, а контора работает.

Ничего не чинит и не меняет. Проходит путь трейдера по шагам и
говорит, на каком именно обрыв:

    1. видит ли Совет слоты цеха (папка + мозг + рабочая функция)
    2. кто сидит на месте (пост)
    3. чем работает: инструмент · паттерн · этаж
    4. готов ли — и если нет, чего не хватает
    5. даёт ли кран котировки по его паре
    6. поднимается ли его мозг (импорт, без вызова модели)

Модель НЕ зовётся — проверка бесплатная.

Запуск из корня репо:  py proverka_ceha.py
                       py proverka_ceha.py контора      (другой цех)
"""
import sys
from pathlib import Path


def _eto_koren(p: Path) -> bool:
    return (p / "main.py").exists() and (p / "Биржа" / "council.py").exists()


def nayti_koren() -> Path:
    zdes = Path(__file__).resolve().parent
    for kand in (zdes, Path.cwd(), *zdes.parents):
        if _eto_koren(kand):
            return kand
    print("✗ Запусти из корня репо (там, где main.py)")
    sys.exit(1)


def main():
    koren = nayti_koren()
    ceh = sys.argv[1] if len(sys.argv) > 1 else "торговый_хаос"
    print(f"Город: {koren}")
    print(f"Цех:   {ceh}\n")

    for p in (koren / "Биржа", koren / "ГОРОД", koren / "жители", koren):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))

    import hooks
    hooks.postavit_ceh(ceh)

    # Откуда вообще берутся бары — без этого «пусто» не прочитать:
    # в РЕАЛЕ пусто значит «терминал молчит», в ТЕСТЕРЕ — «нет CSV».
    try:
        import feed_source as _fs
        _rezhim = _fs.get_feed_mode()
        print(f"Кран:  {'ТЕСТЕР (из файлов)' if _rezhim.get('mode') == 'tester' else 'РЕАЛ (из терминала)'}")
        try:
            import istoriya as _ist
            _m = _ist.gde_stoim()
            if _m:
                print(f"Время: стоим в истории на {_m}")
        except Exception:
            pass
    except Exception as e:
        print(f"Кран:  ✗ не спросить ({e})")
    print()

    # ── 1. кого видит Совет ──
    print("1. Кого Совет видит в цехе:")
    import council
    try:
        za_stolom = council._treydery(ceh)
    except Exception as e:
        print(f"   ✗ сканер слотов сорвался: {e}")
        return 1
    if not za_stolom:
        print("   ✗ НИ ОДНОГО. Совет сканирует папку цеха и берёт слоты,")
        print("     где лежит мозг.py с рабочей функцией. Проверь:")
        print(f"     {koren}/GRONDHEIM_CITY/Биржа/цеха/{ceh}/слоты/")
        return 1
    for aid, _c, slot, fn, _pre in za_stolom:
        print(f"   ✓ {slot}  ({aid}, зовётся {fn})")

    # ── 2-4. пара и готовность ──
    print("\n2. Чем работает каждый:")
    import vybor
    molchat = []
    for _aid, _c, slot, _fn, _pre in za_stolom:
        r = vybor.rabota_dlya(ceh, slot)
        kto = ""
        try:
            import rabota as R
            kto = R.kto_na_slote(ceh, slot) or ""
        except Exception:
            pass
        print(f"\n   {slot}  ·  {kto or 'на месте никого'}")
        print(f"      инструмент: {r.get('инструмент') or '—'} "
              f"({r.get('откуда_инструмент') or 'не задан'})")
        print(f"      этаж:       {r.get('этаж') or '—'} "
              f"({r.get('откуда_этаж') or 'не выбран'})")
        pat = (r.get("паттерн") or "").strip()
        print(f"      паттерн:    {(pat[:60] + '…') if len(pat) > 60 else (pat or '—')}")
        if r.get("готов"):
            print("      ГОТОВ ✓")
        else:
            prichina = vybor.pochemu_molchit(ceh, slot)
            print(f"      МОЛЧИТ ✗ — {prichina}")
            molchat.append((slot, prichina))
            continue

        # ── 5. котировки по его паре ──
        try:
            import feed_source as fs
            b, point = fs.bars(r["инструмент"], r["этаж"], 50)
            if b:
                print(f"      котировки:  {len(b)} баров, последний "
                      f"{b[-1].get('date','?')}")
            else:
                print("      котировки:  ✗ ПУСТО — краном ничего не дали")
                molchat.append((slot, "нет котировок по его паре"))
        except Exception as e:
            print(f"      котировки:  ✗ кран сорвался: {e}")

    # ── 6. поднимается ли мозг ──
    print("\n3. Поднимаются ли мозги (импорт, без вызова модели):")
    import importlib.util
    for _aid, _c, slot, fn, _pre in za_stolom:
        put = (koren / "GRONDHEIM_CITY" / "Биржа" / "цеха" / ceh / "слоты"
               / slot / "мозг.py")
        if not put.exists():
            print(f"   ✗ {slot}: нет файла мозг.py")
            continue
        try:
            spec = importlib.util.spec_from_file_location(f"_p_{slot}", put)
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
        except Exception as e:
            print(f"   ✗ {slot}: мозг не поднялся — {type(e).__name__}: {e}")
            molchat.append((slot, f"мозг не поднялся: {e}"))
            continue
        est = hasattr(m, fn)
        print(f"   {'✓' if est else '✗'} {slot}: "
              f"{'функция ' + fn + ' на месте' if est else 'НЕТ функции ' + fn}")

    # ── итог ──
    print("\n" + "-" * 60)
    if not molchat:
        print("✓ Все на ходу. Если цех всё равно молчит на кнопке РЫНОК —")
        print("  дело не в цехе: смотри консоль на строки [СОВЕТ] и ошибки")
        print("  вызова модели (пустой ответ, нет ключа, лимит).")
        return 0

    print("✗ Молчат и почему:")
    for slot, prichina in molchat:
        print(f"   {slot}: {prichina}")
    if any("этаж" in p for _, p in molchat):
        print("\n  Про этаж: накати otperet_treyderov.py — он ставит")
        print("  рабочий H4 по умолчанию (от комфорта), а выбор самого")
        print("  трейдера всё равно остаётся старше.")
    if any("котировок" in p for _, p in molchat):
        print("\n  Про котировки: в РЕАЛЕ это значит, что MetaTrader не")
        print("  отдал бары — проверь, запущен ли терминал и виден ли ему")
        print("  инструмент (кнопка ТЕРМИНАЛ в кабинете покажет, что есть).")
        print("  В ТЕСТЕРЕ — что нет файла истории по этой паре в")
        print("  Биржа/test_data (нужен файл вида XAUUSDH4.csv).")
    if any("инструмент" in p for _, p in molchat):
        print("\n  Про инструмент: он задаётся в кабинете — кликни пузырёк")
        print("  трейдера, потом инструмент слева. Ляжет в его пост.")
    return 1


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
