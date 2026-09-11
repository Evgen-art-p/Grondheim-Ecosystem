# -*- coding: utf-8 -*-
# ZHURNAL_PROGONA_V1
"""
ИТОГ ПРОГОНА ЧИТАЕТСЯ КАК ЖУРНАЛ СДЕЛОК

ПРОГОН 11.09 дал одиннадцать строк, в которых Шеф не смог разобрать
ничего: даты «?», «держу лонг» помечено как WAIT, кадр справа от
другого бара. Три беды, все наши.

 1. ДАТЫ. Я брал их из полей «бар»/«дата», а отчёт кладёт дату в
    «когда_на_рынке». Отсюда одиннадцать вопросительных знаков.

 2. ДЕЙСТВИЕ ТЕРЯЛОСЬ. Отчёт сохранял только ВЕРДИКТ (APPROVED /
    REJECTED). А приказов у трейдера шесть: ENTER, WAIT, HOLD,
    MOVE_STOP, ADD, CLOSE. Всё, что не вход, сваливалось в «отказ» —
    и «держу открытую позицию» выглядело как «отказался работать».

 3. ЦЕНЫ НЕ БЫЛО. Вошёл — а по чём и с каким стопом, в итоге не
    видно.

ЧТО ДЕЛАЕТ ПАТЧ:

 · `Биржа/otchyot.py` — в каждое место кладутся действие, цена входа
   и стоп (они уже есть в решении, просто не сохранялись);
 · `Биржа/ui_torg.py` — итог печатается журналом, с датами, и делит
   места на ТРИ вещи, а не на две:

       ВОШЁЛ   — открыл позицию
       ВЕДУ    — держит, двигает стоп, доливает, закрывает
       ОТКАЗ   — работать не стал
       ПОДУМАЛ — приказа не было вовсе

   Внизу — сколько входов, сколько отказов, и где лежат кадры.

БЕЗОПАСНОСТЬ: .bak_zhurnal, идемпотентен, синтаксис до записи,
`--suho` не трогает диск.

    python postavit_zhurnal_progona.py --suho
    python postavit_zhurnal_progona.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "ZHURNAL_PROGONA_V1"
SUHO = "--suho" in sys.argv

_REPO = Path(__file__).resolve().parent
OTCHYOT = _REPO / "Биржа" / "otchyot.py"
TORG = _REPO / "Биржа" / "ui_torg.py"

# ── отчёт: сохраняем действие и цены ─────────────────────────
STAROE_OT = '''        skazal = ((otvet or {}).get("narrative") or "").strip()'''
NOVOE_OT = '''        # ZHURNAL_PROGONA_V1: сохраняем ДЕЙСТВИЕ и цены. Раньше в
        # место шёл только вердикт, и «держу позицию» (HOLD) было
        # неотличимо от «работать не стану» (WAIT).
        deystvie = ""
        cena_vhoda = None
        stop_vhoda = None
        for kl, zn in signal.items():
            if kl.endswith("_action") and zn:
                deystvie = str(zn).upper()
            if kl.endswith("_entry") and zn is not None:
                cena_vhoda = zn
            if kl.endswith("_stop") and zn is not None:
                stop_vhoda = zn
        skazal = ((otvet or {}).get("narrative") or "").strip()'''

STAROE_OT2 = '''            "причина": prichina,'''
NOVOE_OT2 = '''            "действие": deystvie,          # ZHURNAL_PROGONA_V1
            "цена_входа": cena_vhoda,
            "стоп_входа": stop_vhoda,
            "причина": prichina,'''

# ── кабинет: журнал вместо списка фраз ───────────────────────
NACHALO = "        # ITOG_PROGONA_VIDEN_V1: разбор по местам вместо трёх чисел."
KONEC = '''        update_chat_display()
        ui.notify(f"✓ прогон окончен · {proydeno} мест", type="positive")'''

NOVOE_ITOG = '''        # ZHURNAL_PROGONA_V1: журнал сделок вместо списка фраз.
        # Даты берём из «когда_на_рынке» (отчёт кладёт их туда), а
        # места делим по ДЕЙСТВИЮ: вход, ведение, отказ, молчание.
        _vhodov = _otkazov = _vedeniy = _molchaniy = 0
        _stroki_zhurnala = []
        _gde_kadry = ""
        try:
            for _m in (_otchyot.mesta if _otchyot is not None else []):
                _kogda = str(_m.get("когда_на_рынке")
                             or _m.get("место_найдено_на") or "?")[:16]
                _d = str(_m.get("действие") or "").upper()
                _v = str(_m.get("вердикт") or "").upper()
                _pochemu = str(_m.get("причина") or "").strip()
                _kadr = str(_m.get("кадр") or "")
                if _kadr and not _gde_kadry:
                    _gde_kadry = "кадры"

                if _d == "ENTER" or _v in ("APPROVED", "ENTER", "OK"):
                    _vhodov += 1
                    _c = _m.get("цена_входа")
                    _s = _m.get("стоп_входа")
                    _hv = (f" @ {_c}" if _c else "")
                    _hv += (f", стоп {_s}" if _s else "")
                    _metka = f"ВОШЁЛ {_hv}".strip()
                elif _d in ("HOLD", "MOVE_STOP", "ADD", "CLOSE"):
                    _vedeniy += 1
                    _metka = {"HOLD": "ДЕРЖУ", "MOVE_STOP": "СТОП ПЕРЕНЁС",
                              "ADD": "ДОЛИЛ", "CLOSE": "ЗАКРЫЛ"}[_d]
                elif _d == "WAIT" or _v in ("REJECTED", "WAIT"):
                    _otkazov += 1
                    _metka = "ОТКАЗ"
                else:
                    _molchaniy += 1
                    _metka = "ПОДУМАЛ, приказа не было"
                _stroki_zhurnala.append(
                    f"  {_kogda:16} {_metka:22} {_pochemu[:58]}")
        except Exception as _e_it:
            print(f"[ИТОГ] не собрался ({_e_it})")

        _stroki = [f"✓ прогон окончен · мест {proydeno}{_hvost}", ""]
        _stroki += _stroki_zhurnala[:40]
        if len(_stroki_zhurnala) > 40:
            _stroki.append(f"  … ещё {len(_stroki_zhurnala) - 40} "
                           f"(все — в отчёте)")
        _stroki.append("")
        _stroki.append(f"ВХОДОВ: {_vhodov} · ВЕДЕНИЕ: {_vedeniy} · "
                       f"ОТКАЗОВ: {_otkazov} · БЕЗ ПРИКАЗА: {_molchaniy}")
        if _gde_kadry:
            _stroki.append("Кадры каждого места — в папке отчёта, "
                           "подпапка «кадры».")
        if not _vhodov and not _molchaniy:
            _stroki.append("Входов нет, но все решения отданы рукой — "
                           "он отказывался сам, причины выше.")

        state["chat_history"].append({
            "role": "system", "content": "\\n".join(_stroki)})
'''


def _pravka(p: Path, pary: list, imya: str) -> int:
    if not p.exists():
        print(f"  {imya}: файла нет")
        return 0
    txt = p.read_text(encoding="utf-8")
    if MARKER in txt:
        print(f"  {imya}: уже стоит")
        return 0
    novy = txt
    for staroe, novoe in pary:
        if novy.count(staroe) != 1:
            print(f"  {imya}: ОТКАЗ — якорь встречается "
                  f"{novy.count(staroe)} раз(а)")
            return 0
        novy = novy.replace(staroe, novoe, 1)
    try:
        ast.parse(novy)
    except SyntaxError as e:
        print(f"  {imya}: ОТКАЗ — синтаксис сломан ({e})")
        return 0
    if not SUHO:
        shutil.copy2(p, p.with_suffix(".py.bak_zhurnal"))
        p.write_text(novy, encoding="utf-8")
    print(f"  {imya}: {'готов' if SUHO else 'поправлен'}")
    return 1


def main():
    print()
    print("ЖУРНАЛ ПРОГОНА" + ("  · СУХОЙ ПРОГОН" if SUHO else ""))
    print("корень:", _REPO)
    print()

    print("1. ОТЧЁТ — сохраняем действие и цены:")
    vsego = _pravka(OTCHYOT, [(STAROE_OT, NOVOE_OT),
                              (STAROE_OT2, NOVOE_OT2)], "otchyot.py")

    print()
    print("2. КАБИНЕТ — итог журналом:")
    if not TORG.exists():
        print("  ui_torg.py: файла нет")
    else:
        txt = TORG.read_text(encoding="utf-8")
        if MARKER in txt:
            print("  ui_torg.py: уже стоит")
        elif NACHALO not in txt or KONEC not in txt:
            print("  ui_torg.py: ОТКАЗ — сперва postavit_itog_progona.py")
        else:
            n1 = txt.index(NACHALO)
            n2 = txt.index(KONEC, n1)
            novy = txt[:n1] + NOVOE_ITOG + txt[n2:]
            try:
                ast.parse(novy)
                if not SUHO:
                    shutil.copy2(TORG, TORG.with_suffix(".py.bak_zhurnal"))
                    TORG.write_text(novy, encoding="utf-8")
                print(f"  ui_torg.py: {'готов' if SUHO else 'поправлен'}")
                vsego += 1
            except SyntaxError as e:
                print(f"  ui_torg.py: ОТКАЗ — синтаксис сломан ({e})")

    print()
    if SUHO:
        print("Сухой прогон: на диске ничего не изменилось.")
    else:
        print(f"Тронуто файлов: {vsego}. Бэкапы — .bak_zhurnal")
    print("Дата · что сделал · почему. И цена, если вошёл.")
    print()


if __name__ == "__main__":
    main()
