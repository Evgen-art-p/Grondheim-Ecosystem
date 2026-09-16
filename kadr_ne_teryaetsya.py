# -*- coding: utf-8 -*-
# kadr_ne_teryaetsya.py — лента перестаёт забивать браузер,
#                         кадр перестаёт теряться.
#
# Кладётся в КОРЕНЬ репозитория, рядом с main.py.
# Запуск из PowerShell, из корня:
#     python kadr_ne_teryaetsya.py
#
# ВАЖНО: сперва должен быть накатан kadr_bez_okna.py.
#
# ═══ ОТЧЕГО БОЛЕЛО ═══
#
# Лента перерисовывалась ЦЕЛИКОМ. Раз в секунду окно стирало всю
# историю разговора и рисовало заново — каждое сообщение, каждую
# миниатюру кадра. На длинном прогоне это сотни элементов в секунду.
# Браузер не выдерживал и рвал связь: вкладка умирала.
#
# А как только вкладка умерла, кадр прогона пропадал совсем. Прогон
# продолжал считать и держал ссылку на СТАРОЕ окно. Новая вкладка про
# его кадр ничего не знала — у ленты догонялка была, у кадра нет.
#
# ═══ ЧТО СТАВИМ ═══
#
# 1. ФИЛЬТР НА ЛЕНТУ. Рисуем последние 80 сообщений вместо всех.
#    Сверху строчка: сколько ещё выше и что полное лежит в отчёте.
#    Ничего не теряется — история в state как была, на диск пишется
#    как писалась. Не рисуем то, что всё равно за краем экрана.
#
# 2. ДОГОНЯЛКА КАДРА. Кадр запоминается ДО отрисовки, в общей на все
#    вкладки памяти. Окно живо — рисуем сразу, как раньше. Окно
#    умерло — кадр всё равно запомнен, и новая вкладка подхватит его
#    за секунду. Тот же приём, которым уже живёт лента.
#
# БЕЗОПАСНО. Собирает новый текст в памяти, проверяет ast.parse и
# только потом пишет. Рядом кладёт ui_torg.py.bak_ne_teryaetsya.
# Запускать можно сколько угодно раз.

import ast
import shutil
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent
MARKER = "KADR_NE_TERYAETSYA_V1"
NUZHEN = "KADR_BEZ_OKNA_V1"

PRAVKI = []

# ── 1. общая память и размер хвоста ──────────────────────────
PRAVKI.append((
    'KVARTAL = "Биржа"\n',
    'KVARTAL = "Биржа"\n'
    '\n'
    '# LENTA_NE_ZABIVAET_BRAUZER_V1: сколько последних сообщений\n'
    '# рисуем. Остальное никуда не девается — оно в памяти и в\n'
    '# отчёте, просто не перерисовывается каждую секунду.\n'
    'LENTA_HVOST = 80\n'
    '\n'
    '# KADR_NE_TERYAETSYA_V1: последний кадр, общий на ВСЕ вкладки.\n'
    '# Прогон мог начаться в одном окне, а смотрят из другого —\n'
    '# счёт растёт, и любое живое окно видит, что кадр сменился.\n'
    '_KADR_NA_VIDU = {"put": None, "podpis": "", "schet": 0}\n',
))

# ── 2. фильтр на ленту ───────────────────────────────────────
PRAVKI.append((
    '            else:\n'
    '                for msg in state["chat_history"]:\n',

    '            else:\n'
    '                # LENTA_NE_ZABIVAET_BRAUZER_V1: рисуем ХВОСТ, а не\n'
    '                # всю ленту. Перерисовывать сотни сообщений с\n'
    '                # картинками раз в секунду — от этого браузер и\n'
    '                # рвал связь, а с ней умирала вкладка.\n'
    '                _vsya = state["chat_history"]\n'
    '                _hvost = _vsya[-LENTA_HVOST:]\n'
    '                _skryto = len(_vsya) - len(_hvost)\n'
    '                if _skryto > 0:\n'
    '                    ui.html(\n'
    '                        \'<div class="chat-msg-system">SYSTEM: выше \'\n'
    '                        f\'ещё {_skryto} сообщ. — полная лента в \'\n'
    '                        \'отчёте на диске.</div>\')\n'
    '                for msg in _hvost:\n',
))

# ── 3. догонялка кадра рядом с догонялкой живого кадра ───────
PRAVKI.append((
    '    try:\n'
    '        ui.timer(1.0, _dognat_zhivoy_kadr)\n'
    '    except Exception as _e_zk:\n'
    '        print(f"[КАБИНЕТ] живой кадр не догоняет ({_e_zk}) — не беда")\n',

    '    try:\n'
    '        ui.timer(1.0, _dognat_zhivoy_kadr)\n'
    '    except Exception as _e_zk:\n'
    '        print(f"[КАБИНЕТ] живой кадр не догоняет ({_e_zk}) — не беда")\n'
    '\n'
    '    # KADR_NE_TERYAETSYA_V1: кадр ПРОГОНА тоже догоняем.\n'
    '    # Прогон мог начаться в другой вкладке или до обновления\n'
    '    # страницы — он держит ссылку на старое окно и в это уже не\n'
    '    # пишет. Раз в секунду смотрим, не сменился ли кадр.\n'
    '    _kadr_progona_vidno = {"schet": -1}\n'
    '\n'
    '    def _dognat_kadr_progona():\n'
    '        try:\n'
    '            if not kadr_ref["element"]:\n'
    '                return\n'
    '            if _KADR_NA_VIDU["schet"] == _kadr_progona_vidno["schet"]:\n'
    '                return\n'
    '            _put = _KADR_NA_VIDU.get("put")\n'
    '            if not _put or not Path(_put).exists():\n'
    '                return\n'
    '            _kadr_progona_vidno["schet"] = _KADR_NA_VIDU["schet"]\n'
    '            kadr_ref["element"].clear()\n'
    '            with kadr_ref["element"]:\n'
    '                ui.image(str(_put)).style(\n'
    '                    "width:100%; height:100%; object-fit:contain; "\n'
    '                    "flex:1; min-height:0;")\n'
    '                ui.label(\n'
    '                    f"👁 {_KADR_NA_VIDU.get(\'podpis\') or \'\'}").style(\n'
    '                    "color:rgba(139,233,253,0.75); font-size:11px; "\n'
    '                    "letter-spacing:0.06em; padding-top:6px; "\n'
    '                    "flex-shrink:0; width:100%; text-align:center;")\n'
    '        except Exception:\n'
    '            pass\n'
    '\n'
    '    try:\n'
    '        ui.timer(1.0, _dognat_kadr_progona)\n'
    '    except Exception as _e_kp:\n'
    '        print(f"[КАБИНЕТ] кадр прогона не догоняет ({_e_kp}) — не беда")\n',
))

# ── 4. ранний выход убираем: кадр надо ЗАПОМНИТЬ ─────────────
PRAVKI.append((
    '        # KADR_BEZ_OKNA_V1: вкладка умерла — рисовать некуда.\n'
    '        # Тот же уговор, что у ленты: работаем молча, отчёт всё\n'
    '        # равно пишется на диск.\n'
    '        if not _kadr_zhivoy():\n'
    '            print("[ПРОГОН] окно не принимает кадр — "\n'
    '                  "работаю молча, отчёт пишется на диск")\n'
    '            return None\n',

    '        # KADR_NE_TERYAETSYA_V1: раньше здесь был ранний выход —\n'
    '        # окно мертво, уходим. Из-за него кадр прогона пропадал\n'
    '        # бесследно. Теперь сперва рисуем и ЗАПОМИНАЕМ кадр, а\n'
    '        # проверка живости стоит ниже, у самой отрисовки.\n',
))

# ── 5. запоминаем кадр до отрисовки, проверяем живость тут ───
PRAVKI.append((
    '        kadr_ref["element"].clear()\n'
    '        with kadr_ref["element"]:\n'
    '            # KADR_NA_VES_KVADRAT_V1: тянемся на всю клетку, но БЕЗ\n',

    '        # KADR_NE_TERYAETSYA_V1: запоминаем кадр ДО отрисовки.\n'
    '        # Даже если эта вкладка умерла — новая подхватит его\n'
    '        # таймером за секунду.\n'
    '        try:\n'
    '            _KADR_NA_VIDU["put"] = str(p)\n'
    '            _KADR_NA_VIDU["podpis"] = f"{chey + \' · \' if chey else \'\'}"\\\n'
    '                                      f"{symbol} · {tf}"\n'
    '            _KADR_NA_VIDU["schet"] += 1\n'
    '        except Exception:\n'
    '            pass\n'
    '        # KADR_BEZ_OKNA_V1: вкладка умерла — рисовать некуда.\n'
    '        if not _kadr_zhivoy():\n'
    '            print("[ПРОГОН] окно не принимает кадр — "\n'
    '                  "кадр запомнен, новая вкладка подхватит")\n'
    '            return p\n'
    '        # рисуем сами — значит догонялке тут делать нечего\n'
    '        try:\n'
    '            _kadr_progona_vidno["schet"] = _KADR_NA_VIDU["schet"]\n'
    '        except Exception:\n'
    '            pass\n'
    '        kadr_ref["element"].clear()\n'
    '        with kadr_ref["element"]:\n'
    '            # KADR_NA_VES_KVADRAT_V1: тянемся на всю клетку, но БЕЗ\n',
))


def podozhdat():
    """Чтобы окно не захлопнулось при запуске двойным кликом."""
    try:
        input("\nГотово. Нажми Enter, чтобы закрыть окно.")
    except Exception:
        pass


def nayti():
    """Ищет кабинет Биржи сам. Руками путь прописывать не надо."""
    prosto = KOREN / "Биржа" / "ui_torg.py"
    if prosto.exists():
        return prosto
    musor = ("_ARCHIVE", "_OLD", "_АРХИВ", "_УБОРКА", ".bak")
    nashlos = [p for p in KOREN.rglob("ui_torg.py")
               if not any(m in str(p) for m in musor)]
    if len(nashlos) == 1:
        print(f"Нашёл: {nashlos[0]}")
        return nashlos[0]
    if len(nashlos) > 1:
        print("Нашёл несколько:")
        for nomer, put in enumerate(nashlos, 1):
            print(f"  {nomer}. {put}")
        otvet = input("Какой правим? номер: ").strip()
        if otvet.isdigit() and 1 <= int(otvet) <= len(nashlos):
            return nashlos[int(otvet) - 1]
    return None


def main():
    put = nayti()
    if put is None:
        print("✗ не нашёл Биржа/ui_torg.py — запускай из корня репозитория")
        return 1

    tekst = put.read_text(encoding="utf-8")

    if MARKER in tekst:
        print("· уже сделано")
        return 0

    if NUZHEN not in tekst:
        print("✗ сперва накати kadr_bez_okna.py — этот патч идёт следом.")
        print("  Ничего не тронул.")
        return 1

    for nomer, (staroe, novoe) in enumerate(PRAVKI, 1):
        if tekst.count(staroe) != 1:
            print(f"✗ правка {nomer}: нашёл {tekst.count(staroe)} мест "
                  f"вместо одного — кабинет мог измениться.")
            print("  Ничего не тронул. Скажи Брату, поправим по месту.")
            return 1

    novyy = tekst
    for staroe, novoe in PRAVKI:
        novyy = novyy.replace(staroe, novoe, 1)

    try:
        ast.parse(novyy)
    except SyntaxError as beda:
        print(f"✗ после правки файл поломался (строка {beda.lineno}): {beda.msg}")
        print("  Ничего не записал, оригинал цел.")
        return 1

    kopiya = put.with_suffix(put.suffix + ".bak_ne_teryaetsya")
    if not kopiya.exists():
        shutil.copy2(put, kopiya)
        print(f"  (копия старого: {kopiya.name})")
    put.write_text(novyy, encoding="utf-8")

    print("✓ вылечено:")
    print("    · лента рисует последние 80 сообщений, а не всю историю")
    print("    · кадр запоминается до отрисовки, общий на все вкладки")
    print("    · новая вкладка подхватывает кадр прогона за секунду")
    print()
    print("Перезапусти Кабинет (main.py) и запусти прогон.")
    print("Вкладка теперь не должна умирать вовсе. А если умрёт —")
    print("обнови страницу: кадр и лента подтянутся сами, без перезапуска.")
    return 0


if __name__ == "__main__":
    kod = main()
    podozhdat()
    sys.exit(kod)
