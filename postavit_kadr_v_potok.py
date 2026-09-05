# -*- coding: utf-8 -*-
# POKAZAT_KADR_NE_VESHAET_SERVER_V1
"""
НАЙДЕНО (06.09, разбор лога и кода вместе с Шефом): клик по пузырьку
трейдера (A06/A07/A08) внутри switch_agent() зовёт pokazat_kadr() без
аргумента — а та БЕЗ АРГУМЕНТА заново читает CSV инструмента (для
Ильи это GBPUSDH4.csv, 44 тысячи баров), считает Аллигатор/AO/фракталы
и рисует PNG через matplotlib. Всё это — СИНХРОННО, прямо в обработчике
клика, в том же потоке, что держит вебсокет со всеми клиентами.

Ровно эта же болезнь уже была найдена и вылечена в progon_po_istorii()
— в его собственном комментарии написано прямым текстом: «matplotlib
на секунды вешал сервер, и браузер обрывал связь: Connection lost».
Там кадр давно рисуется в фоновом потоке (run_in_executor). В
switch_agent() эту же починку забыли сделать — отсюда именно на
пузырьке трейдера (не конторы — тем рисовать нечего) периодически
пропадает подсветка и рвётся связь.

ЧТО ДЕЛАЕТ ПАТЧ:
  1. pokazat_kadr() становится async; тяжёлый вызов grafik.kadr()
     (когда картинку ещё не приготовили заранее) уходит в фоновый
     поток тем же приёмом run_in_executor, что уже стоит в
     progon_po_istorii().
  2. switch_agent() становится async, зовёт pokazat_kadr() через await.
  3. _nazhali (обработчик клика по пузырьку) становится async.
  4. Оба места в progon_po_istorii(), что уже зовут pokazat_kadr(_kadr)
     с готовой картинкой, получают await — без этого, после того как
     pokazat_kadr стала async, они перестали бы что-либо рисовать
     вовсе (тело функции не выполнится без await).

ЧЕГО ПАТЧ НЕ ТРОГАЕТ:
  Кнопка «👁 Взгляд» (on_click=lambda: pokazat_kadr()) — не нуждается
  в правке: NiceGUI сам дожидается корутину, которую вернёт лямбда,
  этот приём в файле уже используется для async-вызовов.

  _k_kandidatu() и _shagnut() (кадр «искателя» кандидатов) тоже зовут
  pokazat_kadr() без await — но, по всем следам в файле, на эти функции
  сейчас не повешена ни одна кнопка (мёртвый путь). Если это не так —
  дай знать, довожу отдельным патчем; трогать вслепую не стал.

Запускать из корня репозитория:
    python postavit_kadr_v_potok.py
Идемпотентен — смотрит по фразе "POKAZAT_KADR_NE_VESHAET_SERVER_V1"
внутри самого ui_torg.py. Второй раз ничего не тронет.
"""
from __future__ import annotations
from pathlib import Path

FAYL = "Биржа/ui_torg.py"
MARKER = "POKAZAT_KADR_NE_VESHAET_SERVER_V1"

ZAMENY = [
    # 1) сигнатура pokazat_kadr — становится async
    (
        "    def pokazat_kadr(put=None):",
        "    async def pokazat_kadr(put=None):",
    ),
    # 2) тяжёлый вызов grafik.kadr() — в фоновый поток
    (
        '        try:\n'
        '            import grafik\n'
        '            p = Path(put) if put else grafik.kadr(symbol, tf)\n'
        '        except Exception as e:\n'
        '            ui.notify(f"⚠ кадр не нарисовался: {e}", type="negative")\n'
        '            return None',
        '        try:\n'
        '            import grafik\n'
        '            if put:\n'
        '                p = Path(put)\n'
        '            else:\n'
        '                # POKAZAT_KADR_NE_VESHAET_SERVER_V1: тот же приём,\n'
        '                # что уже спасает progon_po_istorii — рисуем не в\n'
        '                # обработчике клика, а в фоновом потоке.\n'
        '                import asyncio\n'
        '                _loop = asyncio.get_event_loop()\n'
        '                p = await _loop.run_in_executor(\n'
        '                    None, grafik.kadr, symbol, tf)\n'
        '        except Exception as e:\n'
        '            ui.notify(f"⚠ кадр не нарисовался: {e}", type="negative")\n'
        '            return None',
    ),
    # 3) switch_agent — становится async
    (
        "    def switch_agent(agent_id: str):",
        "    async def switch_agent(agent_id: str):",
    ),
    # 4) вызов внутри switch_agent — через await
    (
        '        try:\n'
        '            pokazat_kadr()\n'
        '        except Exception as _e:\n'
        '            print(f"[ВЗГЛЯД] кадр не показался: {_e}")',
        '        try:\n'
        '            await pokazat_kadr()\n'
        '        except Exception as _e:\n'
        '            print(f"[ВЗГЛЯД] кадр не показался: {_e}")',
    ),
    # 5) обработчик клика по пузырьку — становится async
    (
        "                        def _nazhali(w=old_id):\n"
        '                            print(f"[ПУЗЫРЬ] нажали: {w}")\n'
        "                            switch_agent(w)",
        "                        async def _nazhali(w=old_id):\n"
        '                            print(f"[ПУЗЫРЬ] нажали: {w}")\n'
        "                            await switch_agent(w)",
    ),
    # 6a) progon_po_istorii, первое место с готовым кадром — await
    (
        "                try:\n"
        "                    pokazat_kadr(_kadr)\n"
        "                except Exception:\n"
        "                    pass",
        "                try:\n"
        "                    await pokazat_kadr(_kadr)\n"
        "                except Exception:\n"
        "                    pass",
    ),
    # 6b) progon_po_istorii, второе место с готовым кадром — await
    (
        "                    try:\n"
        "                        # PROGON_BEZ_OKNA_V1: показать — дело окна,\n"
        "                        # а его может уже не быть. Кадр всё равно\n"
        "                        # сохранён и попадёт в отчёт.\n"
        "                        pokazat_kadr(_kadr)\n"
        "                    except Exception as _ep:\n"
        '                        print(f"[ПРОГОН] кадр не показан ({_ep}) — "\n'
        '                              f"он в отчёте")',
        "                    try:\n"
        "                        # PROGON_BEZ_OKNA_V1: показать — дело окна,\n"
        "                        # а его может уже не быть. Кадр всё равно\n"
        "                        # сохранён и попадёт в отчёт.\n"
        "                        await pokazat_kadr(_kadr)\n"
        "                    except Exception as _ep:\n"
        '                        print(f"[ПРОГОН] кадр не показан ({_ep}) — "\n'
        '                              f"он в отчёте")',
    ),
]


def main() -> None:
    root = Path(__file__).resolve().parent
    path = root / FAYL
    if not path.exists():
        print(f"НЕ НАШЁЛ: {path}")
        return

    text = path.read_text(encoding="utf-8")

    if MARKER in text:
        print("уже накачен — маркер на месте, ничего не трогаю")
        return

    bak = path.with_suffix(path.suffix + ".bak_kadr_v_potok")
    if not bak.exists():
        bak.write_text(text, encoding="utf-8")

    ne_nashel = []
    for i, (old, new) in enumerate(ZAMENY, start=1):
        cnt = text.count(old)
        if cnt != 1:
            ne_nashel.append((i, cnt))
            continue
        text = text.replace(old, new, 1)
        print(f"правка {i}/7 применена")

    if ne_nashel:
        print("\n⚠ Не применено (файл на диске отличается от ожидаемого):")
        for i, cnt in ne_nashel:
            print(f"   правка {i}: найдено совпадений {cnt} (нужно ровно 1)")
        print("Ничего не сохраняю — сверь файл руками или пришли Брату.")
        return

    # маркер — в самый конец файла, как и у остальных патчей в репо
    text = text.rstrip("\n") + f"\n\n# {MARKER} - marker\n"
    path.write_text(text, encoding="utf-8")
    print(f"\nГотово: {FAYL} обновлён, 7 правок легли, маркер поставлен.")


if __name__ == "__main__":
    main()
