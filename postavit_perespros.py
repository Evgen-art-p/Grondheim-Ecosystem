# -*- coding: utf-8 -*-
# PERESPROS_V1
"""
ПЕРЕСПРОС · решил — так отдай приказ

ТРИ ПРОГОНА ПОДРЯД трейдер разбирал верно, дважды прямо говорил «это
место для входа в лонг» — и приказа не отдавал. Напоминание в первом
сообщении не помогло: он видел его и всё равно отвечал словами.

Уговоры кончились. Дальше — устройство.

ЧТО ДЕЛАЕТ ПАТЧ. Ответ пришёл, а приказа на табло нет — город
спрашивает ОДИН раз, коротко и прямо: ты решил или нет; решил —
отдай приказ рукой, не решил — отдай WAIT. Руки при этом у него те
же, так что во втором заходе приказ ложится на табло по-настоящему.

Переспрос ровно один. Не ответил и во второй раз — значит и правда
не решил, идём дальше: молчание тоже ответ, но теперь оно стоило ему
вопроса в лицо.

ЦЕНА. Один лишний вызов модели на тот ответ, где не было приказа.
Пока трейдер не отдаёт приказов вовсе, это почти каждый ответ; когда
привыкнет — почти ни одного.

ПОЧЕМУ ТАК, А НЕ ЖЁСТЧЕ. Можно было бы не принимать ответ вовсе или
считать молчание за WAIT. Но первое ломает разговор, а второе врёт:
«не дошёл до решения» и «решил не работать» — разные вещи, и по
весам они разойдутся.

ТРЕБУЕТ: SLOVO_NE_PRIKAZ_V1.

БЕЗОПАСНОСТЬ: .bak_peres, идемпотентен, синтаксис до записи,
`--suho` не трогает диск.

    python postavit_perespros.py --suho
    python postavit_perespros.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "PERESPROS_V1"
SUHO = "--suho" in sys.argv

_REPO = Path(__file__).resolve().parent
SLOTY = _REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "слоты"

PARSER = {"A06": "_parse_brut", "A07": "_parse_avan", "A08": "_parse_cons"}

STAROE = '''    narrative, _slova, diary_entry = {PARSER}(response)
    # SLOVO_NE_PRIKAZ_V1: решение — только с руки
    signal = _signal_ot_ruki(md.get("bar_time"), _slova)
    signal = _sanitize(signal)'''

NOVOE = '''    narrative, _slova, diary_entry = {PARSER}(response)
    # SLOVO_NE_PRIKAZ_V1: решение — только с руки
    signal = _signal_ot_ruki(md.get("bar_time"), _slova)

    # PERESPROS_V1: приказа нет — спрашиваем в лицо, один раз.
    # Напоминания он видел и всё равно отвечал словами; уговоры
    # кончились. Руки те же, так что во втором заходе приказ ложится
    # на табло по-настоящему.
    if not signal:
        try:
            _peresp = (
                "\\n\\n— — —\\n"
                "СТОП. Ты сказал, что видишь, но приказа не отдал — "
                "значит НИЧЕГО НЕ ПРОИЗОШЛО: исполнитель слов не "
                "слышит, и в истории это останется разговором.\\n"
                "Ответь делом, не текстом: решил работать — позови "
                "руку otdat_prikaz с ENTER (сторона, цена, стоп). Не "
                "работаешь — позови её же с WAIT и причиной. Третьего "
                "нет.")
            _otvet2 = _chat_glazami(
                system=system_full, user=user_msg + _peresp,
                knowledge=knowledge, agent_id="{AGENT}", slot_id=_SLOT,
                temperature=_my_temp())
            signal = _signal_ot_ruki(md.get("bar_time"), None)
            if signal:
                print(f"[ПЕРЕСПРОС] отдал приказ со второго раза: "
                      f"{signal.get('{PREF}action')}")
                _n2, _s2, _d2 = {PARSER}(_otvet2)
                if _n2:
                    narrative = _n2
                if _d2:
                    diary_entry = _d2
            else:
                print("[ПЕРЕСПРОС] и во второй раз без приказа — "
                      "решения нет")
        except Exception as _e_per:
            print(f"[ПЕРЕСПРОС] не вышло ({_e_per}) — иду как есть")

    signal = _sanitize(signal)'''

AGENT = {"A06": "A06", "A07": "A07", "A08": "A08"}
PREF = {"A06": "brut_", "A07": "avan_", "A08": "cons_"}


def _pravka(slot: str) -> int:
    p = SLOTY / slot / "мозг.py"
    if not p.exists():
        print(f"  {slot}: файла нет")
        return 0
    txt = p.read_text(encoding="utf-8")
    if MARKER in txt:
        print(f"  {slot}: уже стоит")
        return 0
    if "SLOVO_NE_PRIKAZ_V1" not in txt:
        print(f"  {slot}: ОТКАЗ — сперва postavit_slovo_ne_prikaz.py")
        return -1

    staroe = STAROE.replace("{PARSER}", PARSER[slot])
    if txt.count(staroe) != 1:
        print(f"  {slot}: ОТКАЗ — якорь встречается {txt.count(staroe)} раз(а)")
        return 0

    novoe = (NOVOE.replace("{PARSER}", PARSER[slot])
                  .replace("{AGENT}", AGENT[slot])
                  .replace("{PREF}", PREF[slot]))
    novy = txt.replace(staroe, novoe, 1)
    novy = novy.rstrip("\n") + f"\n\n# {MARKER} - marker\n"
    try:
        ast.parse(novy)
    except SyntaxError as e:
        print(f"  {slot}: ОТКАЗ — синтаксис сломан ({e})")
        return 0
    if not SUHO:
        shutil.copy2(p, p.with_suffix(".py.bak_peres"))
        p.write_text(novy, encoding="utf-8")
    print(f"  {slot}: {'готов' if SUHO else 'поправлен'}")
    return 1


def main():
    print()
    print("ПЕРЕСПРОС" + ("  · СУХОЙ ПРОГОН" if SUHO else ""))
    print("корень:", _REPO)
    print()
    if not SLOTY.exists():
        print("!! слотов нет — запускать из корня репы")
        return
    vsego = 0
    for s in ("A06", "A07", "A08"):
        r = _pravka(s)
        if r < 0:
            return
        vsego += r
    print()
    if SUHO:
        print("Сухой прогон: на диске ничего не изменилось.")
    else:
        print(f"Тронуто мозгов: {vsego}. Бэкапы — .bak_peres")
    print("Сказал — спросят делом. Один раз.")
    print()


if __name__ == "__main__":
    main()
