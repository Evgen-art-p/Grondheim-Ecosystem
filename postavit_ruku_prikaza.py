# -*- coding: utf-8 -*-
# POSTAVIT_RUKU_PRIKAZA_V1 — рука на вход: приказ исполнителю
"""
РУКА НА ВХОД · трейдер отдаёт приказ Сергею САМ

ЗАЧЕМ. Сегодня приказ рождается не у трейдера. Трейдер говорит
словами, код вылавливает цифры из его текста и кладёт на табло, а
Сергей исполняет табло. Сергей чист — он делает ровно то, что там
написано. Врёт середина: вылов из текста. Отсюда «сказал и не
вошёл» неотличимо от «вошёл» — именно на этом трейдера поймали
09.09.

ЧТО ДЕЛАЕТ ПАТЧ. Добавляет трейдеру руку `otdat_prikaz` — по тому
же шву, каким уже вставлена рука Маяка (`_ruka_mayaka_shema` /
`_ruka_mayaka_ruki`). Рука кладёт приказ на табло НАПРЯМУЮ, теми же
полями, что и раньше писал разбор, и оставляет след с двумя
ключами: чей приказ и кому отдан.

    трейдер зовёт руку → приказ на табло → Сергей исполняет

ЧЕГО ПАТЧ НЕ ДЕЛАЕТ (сознательно, отдельным заходом):
 · НЕ убирает старый вылов из текста. Сперва надо увидеть живьём,
   что трейдер руку зовёт. Уберём — и если рука почему-то не
   сработает, он не сможет войти вовсе. Закроем вторым патчем,
   после живой проверки;
 · НЕ трогает промпты — тем же вторым заходом;
 · НЕ трогает Сергея и брокера. Режим прежний, город бумажный.

БЕЗОПАСНОСТЬ:
 · .bak_prikaz рядом с правленым файлом;
 · идемпотентен (маркер RUKA_PRIKAZA_V1);
 · после правки проверяет синтаксис — не собралось, вернёт из бэкапа;
 · `--suho` — показать и не трогать диск.

    python postavit_ruku_prikaza.py --suho
    python postavit_ruku_prikaza.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "RUKA_PRIKAZA_V1"
SUHO = "--suho" in sys.argv

_REPO = Path(__file__).resolve().parent
FAJL = _REPO / "Биржа" / "ruki_treydera.py"

# ── шов 1: схема руки рядом со схемой Маяка ──────────────────
YAKOR_SHEMA = "        *_ruka_mayaka_shema(),"
VSTAVKA_SHEMA = "        *_ruka_prikaza_shema(),          # RUKA_PRIKAZA_V1"

# ── шов 2: сама рука рядом с рукой Маяка ─────────────────────
YAKOR_RUKI = "    itog.update(_ruka_mayaka_ruki(slot))   # RUKA_MAYAKA_V1"
VSTAVKA_RUKI = ("    itog.update(_ruka_prikaza_ruki(          # RUKA_PRIKAZA_V1\n"
                "        symbol, slot, imya_zhitelya, rabochiy_etazh))")

# ── шов 3: тело в конец файла ────────────────────────────────
TELO = '''

# ── RUKA_PRIKAZA_V1: приказ исполнителю ──────────────────────
# Единственный способ что-то СДЕЛАТЬ. Всё остальное у трейдера —
# смотреть и вспоминать. Закон Рычага: сказал, напрягся, сделал.
#
# Приказ ложится на то же табло (trading_state), которое читает
# Сергей-исполнитель, и теми же полями, что раньше писал разбор
# текста. Разница одна и главная: кладёт ТРЕЙДЕР, а не парсер.
#
# Бар рука проставляет САМА, из состояния города — трейдер не может
# ни соврать про бар, ни забыть его. Без отметки бара исполнитель
# приказ не берёт вовсе (SVEZHEST_V1).

_TABLO_PO_SLOTU = {"A06": "brut", "A07": "avan", "A08": "cons"}
_PRIKAZY = ("ENTER", "WAIT", "HOLD", "MOVE_STOP", "ADD", "CLOSE")


def _ruka_prikaza_shema() -> list:
    return [
        {"type": "function", "function": {
            "name": "otdat_prikaz",
            "description": (
                "Отдать приказ исполнителю. Это ЕДИНСТВЕННЫЙ способ "
                "войти, передвинуть стоп, долить или закрыть. Сказать "
                "словами — не приказ: исполнитель слов не слышит, он "
                "читает только то, что положено этой рукой. Не позвал "
                "— ничего не произошло, сколько ни рассказывай. "
                "ENTER без направления, цены и стопа не принимается: "
                "это не строгость, а то же правило — приказ должен "
                "быть исполним. Рука ничего не советует и не проверяет "
                "рынок: она передаёт твоё решение и отвечает, принято "
                "оно или нет."),
            "parameters": {"type": "object", "properties": {
                "что": {"type": "string",
                        "description": ("ENTER — войти · WAIT — не работаю · "
                                        "HOLD — держу как есть · MOVE_STOP — "
                                        "передвинуть стоп · ADD — долить · "
                                        "CLOSE — закрыть")},
                "направление": {"type": "string",
                                "description": "LONG или SHORT (для ENTER)"},
                "цена": {"type": "number",
                         "description": "цена заявки (для ENTER)"},
                "стоп": {"type": "number",
                         "description": "цена стопа (для ENTER)"},
                "лот": {"type": "number", "description": "объём, если знаешь"},
                "новый_стоп": {"type": "number",
                               "description": "для MOVE_STOP"},
                "долить": {"type": "number", "description": "для ADD"},
                "почему": {"type": "string",
                           "description": "коротко, своими словами"}},
                "required": ["что"]}}},
    ]


def _klyuch_po_imeni(imya: str) -> str:
    """Ключ жителя. Нет модуля или нет такого — пустая строка."""
    try:
        import sys as _s
        from pathlib import Path as _P
        _g = str(_P(__file__).resolve().parent.parent / "ГОРОД")
        if _g not in _s.path:
            _s.path.insert(0, _g)
        import klyuch
        return klyuch.klyuch_zhitelya(imya)
    except Exception:
        return ""


def _ispolnitel() -> tuple:
    """(имя, ключ) того, кто сидит казначеем. Пусто — приказ всё равно
    ложится: место работает, даже когда пост пуст."""
    try:
        import sys as _s
        from pathlib import Path as _P
        _g = str(_P(__file__).resolve().parent.parent / "ГОРОД")
        if _g not in _s.path:
            _s.path.insert(0, _g)
        import rezidenty
        imya = rezidenty.kto_na_postu("контора__исполнитель") or ""
        return imya, _klyuch_po_imeni(imya)
    except Exception:
        return "", ""


def _sled_prikaza(zapis: dict) -> None:
    """След приказа — у того, КОМУ он отдан. Один факт, два ключа."""
    try:
        import json as _j
        from pathlib import Path as _P
        p = (_P(__file__).resolve().parent / "цеха" / "контора" /
             "слоты" / "исполнитель" / "данные" / "приказы.jsonl")
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(_j.dumps(zapis, ensure_ascii=False) + "\\n")
    except Exception:
        pass          # след не лёг — приказ всё равно отдан


def _ruka_prikaza_ruki(symbol: str, slot: str, imya_zhitelya: str,
                       rabochiy_etazh: str) -> dict:
    tablo = _TABLO_PO_SLOTU.get(str(slot).upper())
    if not tablo:
        return {}     # не торговое место — руки нет

    def _otdat(args: dict) -> str:
        from datetime import datetime, timezone
        chto = str(args.get("что", "")).upper().strip()
        if chto not in _PRIKAZY:
            return ("Такого приказа нет: " + (chto or "пусто") +
                    ". Есть: " + ", ".join(_PRIKAZY) + ". Ничего не отдано.")

        napravlenie = str(args.get("направление", "")).upper().strip() or None
        cena = args.get("цена")
        stop = args.get("стоп")

        if chto == "ENTER":
            net = []
            if napravlenie not in ("LONG", "SHORT"):
                net.append("направление (LONG или SHORT)")
            if not isinstance(cena, (int, float)):
                net.append("цена")
            if not isinstance(stop, (int, float)):
                net.append("стоп")
            if net:
                return ("Приказ НЕ отдан: не хватает " + ", ".join(net) +
                        ". Войти вслепую нельзя — назови и позови снова.")
        if chto == "MOVE_STOP" and not isinstance(args.get("новый_стоп"),
                                                  (int, float)):
            return "Приказ НЕ отдан: MOVE_STOP без нового стопа."
        if chto == "ADD" and not isinstance(args.get("долить"), (int, float)):
            return "Приказ НЕ отдан: ADD без объёма долива."

        try:
            from hooks import load_trading_state, save_trading_state
            t = load_trading_state()
        except Exception as e:
            return f"Табло не открылось ({e}) — приказ не отдан."

        # бар город ставит сам; трейдер про него не спрашивается
        bar = str((t.get("рынок") or {}).get("бар") or t.get("бар") or "")

        v = t.setdefault(tablo, {})
        v["бар"] = bar
        v["action"] = chto
        v["verdict"] = ("APPROVED" if chto == "ENTER"
                        else ("REJECTED" if chto == "WAIT"
                              else v.get("verdict")))
        v["reason"] = str(args.get("почему", "")).strip()
        if chto == "WAIT":
            # не работаю — значит и цены моей на табло нет. Иначе
            # вчерашняя цена лежит рядом с сегодняшним отказом и
            # ждёт, пока кто-нибудь её подберёт.
            for pole in ("direction", "entry", "stop", "lot",
                         "new_stop", "add_lot"):
                v.pop(pole, None)
        if chto == "ENTER":
            v["direction"] = napravlenie
            v["entry"] = cena
            v["stop"] = stop
            if isinstance(args.get("лот"), (int, float)):
                v["lot"] = args["лот"]
        if chto == "MOVE_STOP":
            v["new_stop"] = args.get("новый_стоп")
        if chto == "ADD":
            v["add_lot"] = args.get("долить")
        v["отдан_рукой"] = True
        v["кто_отдал"] = imya_zhitelya or ""
        v["ключ_отдавшего"] = _klyuch_po_imeni(imya_zhitelya)

        try:
            save_trading_state(t)
        except Exception as e:
            return f"Табло не записалось ({e}) — приказ не отдан."

        komu, klyuch_komu = _ispolnitel()
        _sled_prikaza({
            "когда": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "бар": bar,
            "инструмент": symbol,
            "этаж": rabochiy_etazh,
            "место": slot,
            "от_кого": imya_zhitelya or "",
            "ключ": v["ключ_отдавшего"],
            "кому": komu,
            "ключ_кому": klyuch_komu,
            "что": chto,
            "направление": napravlenie,
            "цена": cena,
            "стоп": stop,
            "лот": args.get("лот"),
            "новый_стоп": args.get("новый_стоп"),
            "долить": args.get("долить"),
            "почему": v["reason"],
        })

        adresat = komu or "исполнитель"
        if chto == "ENTER":
            return (f"Приказ отдан: {adresat} принял ENTER {napravlenie} "
                    f"{symbol} по {cena}, стоп {stop}"
                    + (f", бар {bar}" if bar else "")
                    + ". Заявка на табло.")
        if chto == "WAIT":
            return f"Принято: не работаешь на этом баре{', ' + bar if bar else ''}."
        return (f"Приказ отдан: {adresat} принял {chto}"
                + (f", бар {bar}" if bar else "") + ".")

    return {"otdat_prikaz": _otdat}


# RUKA_PRIKAZA_V1 - marker
'''


def main():
    print()
    print("РУКА НА ВХОД" + ("  · СУХОЙ ПРОГОН" if SUHO else ""))
    print("файл:", FAJL)
    print()

    if not FAJL.exists():
        print("!! файла нет — запускать из корня репы")
        return

    txt = FAJL.read_text(encoding="utf-8")

    if MARKER in txt:
        print("Уже стоит (маркер на месте). Ничего не меняю.")
        return

    beda = []
    if YAKOR_SHEMA not in txt:
        beda.append("не нашёл шов схемы (строка со схемой Маяка)")
    if YAKOR_RUKI not in txt:
        beda.append("не нашёл шов рук (строка с рукой Маяка)")
    if txt.count(YAKOR_SHEMA) > 1 or txt.count(YAKOR_RUKI) > 1:
        beda.append("шов встречается больше раза — не рискую")
    if beda:
        print("ОТКАЗЫВАЮСЬ работать, файл не тронут:")
        for b in beda:
            print("  ·", b)
        return

    novy = txt.replace(YAKOR_SHEMA, YAKOR_SHEMA + "\n" + VSTAVKA_SHEMA, 1)
    novy = novy.replace(YAKOR_RUKI, YAKOR_RUKI + "\n" + VSTAVKA_RUKI, 1)
    novy = novy.rstrip("\n") + "\n" + TELO

    try:
        ast.parse(novy)
    except SyntaxError as e:
        print("!! после правки синтаксис сломался — НИЧЕГО не записал")
        print("  ", e)
        return

    print("  шов схемы  — вставлено")
    print("  шов рук    — вставлено")
    print("  тело руки  — дописано в конец")
    print("  синтаксис после правки — валиден")

    if SUHO:
        print()
        print("Сухой прогон: на диске ничего не изменилось.")
        return

    shutil.copy2(FAJL, FAJL.with_suffix(".py.bak_prikaz"))
    FAJL.write_text(novy, encoding="utf-8")
    print()
    print("Готово. Бэкап: ruki_treydera.py.bak_prikaz")
    print("Рука называется otdat_prikaz. Старый путь через текст пока")
    print("работает — закроем вторым патчем, когда увидим руку живьём.")
    print()


if __name__ == "__main__":
    main()
