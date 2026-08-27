# -*- coding: utf-8 -*-
# MARKER: KABINET_ZHIVYOT_PRI_GORODE_V1
"""
КАБИНЕТ ПЕРЕСТАЁТ ТЕРЯТЬ ВСЁ ПРИ ОБНОВЛЕНИИ СТРАНИЦЫ.

ЧТО БЫЛО СЛОМАНО
────────────────
Вся память кабинета — лента разговоров, полка активов, найденные
места, режим — лежала в словаре state, созданном ВНУТРИ страницы.
Значит она жила ровно столько, сколько живёт открытая вкладка.

Моргнула связь, обновилась страница, уснул компьютер — рождался
новый ПУСТОЙ state. На экране чисто, будто ничего не было. А прогон
в это время продолжал крутиться и писать в СТАРЫЙ state, которого на
экране уже нет.

Отсюда ровно то, что видел Шеф: лог в терминале идёт, браузер пустой,
пузырьки трейдеров не нажимаются (они привязаны к элементам мёртвой
страницы).

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
1. Состояние кабинета переезжает НА ГОРОД, а не на вкладку: один
   кабинет на цех, как один стол и один момент истории. Обновил
   страницу — открылось то же самое, с лентой и полкой на месте.

2. Лента сама догоняет. Раз в секунду страница смотрит, не выросла
   ли лента, и дорисовывает новое. Поэтому после обновления страницы
   прогон, идущий в фоне, снова виден на экране — а не пишет в
   пустоту.

Ничего не считает и не решает — только показ и память окна.

ЧЕГО ПАТЧ НЕ ДЕЛАЕТ
───────────────────
Не трогает механику: точку, волну, откат, воду. Не трогает MT5 —
это отдельный патч (SOVET_CHEREZ_KRAN_V1).

Идемпотентен. .bak рядом. Путь ищет сам.
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "KABINET_ZHIVYOT_PRI_GORODE_V1"


def _nayti_birzhu() -> Path:
    primety = ("ui_torg.py",)
    nashli = []
    korni = []
    for k in (Path(__file__).resolve().parent, Path.cwd().resolve()):
        if k not in korni:
            korni.append(k)
    for koren in korni:
        mesta = [koren]
        try:
            mesta += [x for x in koren.iterdir() if x.is_dir()]
        except OSError:
            pass
        for p in mesta:
            if all((p / f).exists() for f in primety) and p not in nashli:
                nashli.append(p)
    if len(nashli) == 1:
        return nashli[0]
    if not nashli:
        print("Не нашёл папку Биржа рядом со скриптом.")
        s = input("Перетащи сюда папку Биржа и нажми Enter:\n> ")
        p = Path(s.strip().strip('"').strip("'"))
        if (p / "ui_torg.py").exists():
            return p
        raise SystemExit("не та папка — там нет ui_torg.py")
    print("Нашёл несколько:")
    for i, p in enumerate(nashli, 1):
        print(f"  {i}. {p}")
    return nashli[int((input("которая? ").strip() or "1")) - 1]


A1_ST = 'def page_torg(tseh_id: str = "торговый_хаос") -> None:\n'
A1_NO = '# KABINET_ZHIVYOT_PRI_GORODE_V1: память кабинета живёт ПРИ ГОРОДЕ,\n# а не при вкладке. Раньше state рождался внутри страницы: моргнула\n# связь или обновилась страница — рождался новый пустой, лента\n# исчезала с экрана, а прогон продолжал писать в старый, которого\n# уже никто не видит. Один кабинет на цех — как один стол и один\n# момент истории.\n_KABINETY: dict = {}\n\n\ndef page_torg(tseh_id: str = "торговый_хаос") -> None:\n'
A2_ST = '    state = {\n'
A2_NO = '    _svezhee = {\n'
A3_ST = '        "vahta": False,\n        "vahta_bar": "",\n    }\n\n    llm.set_model(state["model"])'
A3_NO = '        "vahta": False,\n        "vahta_bar": "",\n    }\n\n    # KABINET_ZHIVYOT_PRI_GORODE_V1: берём кабинет этого цеха, если он\n    # уже открыт был — тогда лента, полка и режим на месте. Первый\n    # раз — кладём свежий. Новые ключи (после патчей) доливаем, чтобы\n    # старый кабинет не падал на том, чего в нём ещё нет.\n    state = _KABINETY.setdefault(tseh_id, _svezhee)\n    for _k, _v in _svezhee.items():\n        state.setdefault(_k, _v)\n\n    llm.set_model(state["model"])'
A4_ST = '                    if role == "user":\n                        ui.html(f\'<div class="chat-msg-user"><b>ШЕФ:</b> {content}</div>\')\n                    else:\n                        ui.html(f\'<div class="chat-msg-assistant"><b>{who}:</b> {content}</div>\')\n'
A4_NO = '                    if role == "user":\n                        ui.html(f\'<div class="chat-msg-user"><b>ШЕФ:</b> {content}</div>\')\n                    else:\n                        ui.html(f\'<div class="chat-msg-assistant"><b>{who}:</b> {content}</div>\')\n\n    # KABINET_ZHIVYOT_PRI_GORODE_V1: лента сама догоняет.\n    # Прогон, начатый в другой вкладке (или до обновления страницы),\n    # держит ссылку на СТАРОЕ окно и в это уже не пишет. Раз в\n    # секунду смотрим, не выросла ли лента, и дорисовываем — тогда\n    # фоновый прогон снова виден на экране.\n    _lenta_vidno = {"skolko": -1}\n\n    def _dognat_lentu():\n        try:\n            n = len(state.get("chat_history") or [])\n            if n != _lenta_vidno["skolko"]:\n                _lenta_vidno["skolko"] = n\n                _risovat_chat()\n        except Exception:\n            pass\n\n    try:\n        ui.timer(1.0, _dognat_lentu)\n    except Exception as _e_tmr:\n        print(f"[КАБИНЕТ] лента не догоняет ({_e_tmr}) — не беда")\n'

PARY = [
    ("объявление страницы", A1_ST, A1_NO),
    ("начало словаря state", A2_ST, A2_NO),
    ("хвост словаря state", A3_ST, A3_NO),
    ("конец рисования ленты", A4_ST, A4_NO),
]



def main():
    b = _nayti_birzhu()
    print(f"\nБиржа: {b}\n")
    p = b / "ui_torg.py"
    text = p.read_text(encoding="utf-8")

    if MARKER in text:
        print("  . ui_torg.py: уже накачен, пропускаю")
    else:
        novyy = text
        for nazv, staroe, novoe in PARY:
            if novyy.count(staroe) != 1:
                raise SystemExit(
                    f"  X ui_torg.py: якорь «{nazv}» не найден или не один "
                    f"({novyy.count(staroe)}). Файл НЕ ТРОНУТ.")
            novyy = novyy.replace(staroe, novoe)
        novyy = novyy.rstrip() + "\n\n# " + MARKER + " - marker\n"
        ast.parse(novyy)
        shutil.copy2(p, p.with_suffix(".py.bak"))
        p.write_text(novyy, encoding="utf-8")
        print("  + ui_torg.py: кабинет живёт при городе (.bak рядом)")

    print("\nГотово. Перезапусти город и открой кабинет заново.")
    print("Теперь обновление страницы не стирает ленту, а прогон,")
    print("идущий в фоне, снова виден на экране.")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        print(e)
    except Exception:
        import traceback
        traceback.print_exc()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно ")
