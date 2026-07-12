# -*- coding: utf-8 -*-
# NOSITEL_BRIDGE_V1
"""
МОСТ К НОСИТЕЛЮ — одна дверь между РОЛЬЮ (слот Биржи) и РОДОМ (житель).

ЗАЧЕМ ОТДЕЛЬНЫЙ ФАЙЛ, а не строки в каждом мозге:
  мостов нужно девять (девять мозгов) + два конца в hooks. Впишем сборку
  души в каждый мозг — через месяц это одиннадцать копий, которые разъедутся.
  Ровно та болезнь, от которой лечимся (четыре копии магика). Поэтому —
  ОДНА ДВЕРЬ, как council.wake_council() у Совета. Мозг стучится, дверь
  открывает. Правда живёт в одном месте.

ДВА КОНЦА КОЛЬЦА:
  ЧИТАЮЩИЙ  dusha_slota(цех, слот) → носитель + его душа текстом
            (перед решением: трейдер видит СЕБЯ — род, натуру, свой опыт)
  ПИШУЩИЙ   zapisat_vyvod(magic, вывод, pnl_r) → вывод в ЕГО ЖЕ якоря
            (после сделки: рынок рассудил, вывод осел в носителя)

  Оба конца — через маску (Закон Пары). Ни одного id роли, ни одного
  реестра. Слот знает свою пару по (цех, слот); закрытая позиция — по magic.

ЧЕГО ТУТ НЕТ: LLM, UI, торговой математики. Только сведение пары и текст.
`шесть·проверено·до·корня`
"""
from pathlib import Path
import sys as _sys

_BIRZHA = Path(__file__).resolve().parent
_REPO = _BIRZHA.parent
_ZHITELI_CODE = _REPO / "жители"      # тут живёт dvizhok.py (движок жителя)

if str(_BIRZHA) not in _sys.path:
    _sys.path.insert(0, str(_BIRZHA))
if str(_ZHITELI_CODE) not in _sys.path:
    _sys.path.insert(0, str(_ZHITELI_CODE))


def _dvizhok(dom: str):
    """Движок носителя по его дому. Ошибка — честный None, не падение:
    торговый цикл не должен рваться из-за души."""
    try:
        from dvizhok import Dvizhok
        return Dvizhok(Path(dom))
    except Exception as e:
        print(f"[МОСТ] ⚠️  движок жителя не поднялся ({e})")
        return None


# ════════════════════════════════════════════════════════════
# ЧИТАЮЩИЙ КОНЕЦ — кто сидит в слоте и чем он дышит
# ════════════════════════════════════════════════════════════

def _sobrat_dushu(stol: dict, s_domom: bool = False) -> str:
    """Стол носителя → текст для системного промпта.

    ГРАНИЦА (та же, что у Искры): душа красит ГОЛОС и решение человека,
    но НЕ подменяет факты рынка. Числа стола считает движок.

    s_domom=False по умолчанию: на бирже человек за РАБОЧИМ столом, не
    дома (Закон Входа-Выхода — не тащим кухню в чужую кухню). Плюс
    трезвый расчёт: домашний_промпт Ильи ~2 000 знаков, а тестер зовёт
    мозг тысячи раз — это деньги на ветер. Нужен дом в промпте — включишь
    флагом, решение Шефа.
    """
    if not stol:
        return ""
    L = []
    L.append(f"Тебя зовут {stol.get('кто_я') or '—'}. Это ТЫ, не роль.")
    if stol.get("ядро"):
        L.append(f"Твоё ядро: {stol['ядро']}")

    dna = stol.get("натура") or {}
    if dna:
        L.append(
            "Твоя натура (ручки, 0..1): "
            f"упрямство {dna.get('Stubbornness','—')}, "
            f"автономия {dna.get('Autonomy_Level','—')}, "
            f"эмпатия {dna.get('Empathy','—')}, "
            f"порог вкуса {dna.get('Aesthetic_Threshold','—')}, "
            f"фильтр общения {dna.get('Social_Filter','—')}, "
            f"резонанс {dna.get('Resonance_Frequency','—')}."
        )
    if stol.get("история"):
        L.append(f"Твоя история: {stol['история']}")
    if stol.get("чувство"):
        L.append(f"Как ты отзываешься: {stol['чувство']}")

    zaryad = stol.get("заряд")
    if zaryad is not None:
        if zaryad > 0.3:
            sost = "на подъёме"
        elif zaryad < -0.3:
            sost = "придавлен(а), несёшь тяжесть"
        else:
            sost = "ровно"
        L.append(f"Твой заряд сейчас: {zaryad} ({sost}).")

    # ── НОГА ОПЫТА — главное, ради чего мост ────────────────────
    yak = stol.get("якоря") or ""
    parts = [x.strip() for x in yak.replace("\\n", "\n").split("\n") if x.strip()]
    if parts:
        L.append("\nТВОЙ ОПЫТ — что ты вынес сам (якоря). Это не правила "
                 "сверху, это твои же выводы, оплаченные твоими деньгами:")
        for p in parts:
            L.append(f"  • {p}")
        L.append("Опыт — твой. Хочешь идти против него — иди, но знай, что идёшь.")

    if s_domom and stol.get("дом"):
        L.append(f"\nТвой дом: {stol['дом']}")

    return "\n".join(L)


def dusha_slota(ceh: str, slot: str, s_domom: bool = False) -> dict:
    """ЧИТАЮЩИЙ КОНЕЦ. Пара (цех, слот) → носитель + его душа текстом.

    Возвращает {"носитель": {...}, "душа": "...", "magic": int|None}
    или None — слот пуст (честная вакансия, не ошибка).

    Читает БЕЗ побочек: nakryt_stol_chisto не пишет в память жителя
    (vydoh_stol пишет на каждый вызов — на баре его звать нельзя).
    """
    try:
        from cartridge_registry import resolve_para
    except Exception as e:
        print(f"[МОСТ] ⚠️  реестр не поднялся ({e})")
        return None

    n = resolve_para(ceh, slot)
    if not n:
        print(f"[МОСТ] ℹ️  слот {ceh}/{slot} — вакансия, носителя нет")
        return None

    d = _dvizhok(n["папка"])
    if d is None:
        return {"носитель": n, "душа": "", "magic": n.get("magic")}

    try:
        stol = d.nakryt_stol_chisto()
    except AttributeError:
        print("[МОСТ] ⚠️  в dvizhok нет nakryt_stol_chisto — "
              "нужен patch_dvizhok_stol_chisto_vyvod_v1")
        return {"носитель": n, "душа": "", "magic": n.get("magic")}

    return {
        "носитель": n,
        "душа": _sobrat_dushu(stol, s_domom=s_domom),
        "magic": n.get("magic"),
        "стол": stol,
    }


def magic_slota(ceh: str, slot: str):
    """Магик носителя этого слота — из МАСКИ, единственной правды.
    Не из константы в мозге (их было четыре копии — так и разъезжались)."""
    try:
        from cartridge_registry import resolve_para
        n = resolve_para(ceh, slot)
        return (n or {}).get("magic")
    except Exception:
        return None


# ════════════════════════════════════════════════════════════
# ПИШУЩИЙ КОНЕЦ — суд рынка оседает ОПЫТОМ в носителя
# ════════════════════════════════════════════════════════════

# Порог крайности: рутинная сделка в ЯКОРЯ не идёт (якорей всего 7-10 —
# это ОПЫТ, не журнал). Факт каждой сделки и так лежит в pnl.jsonl и в
# дневнике роли — это ПАМЯТЬ (Чертёж: память ≠ опыт).
KRAYNOST_R = 2.0


def sudit_po_kotinu(direction, entry_bias, pnl_r, close_reason, bar) -> str:
    """Вывод из сделки — СЧИТАЕТ КОД, не LLM (числа не галлюцинируют).

    §12 Котина: направление — факт структуры, не мнение. Идти ЗА компасом —
    обычный хлеб. Идти ПРОТИВ — редкая осознанная ставка с ценой.
    Отсюда суд:
      минус ПРОТИВ ветра → УРОК (всегда значим, даже мелкий: это тот самый
                            систематический стоп, за который мы патчили промт)
      минус ПО ветру      → честная плата (значим только крупный)
      плюс ПРОТИВ ветра   → повезло, не система (не путать удачу с правотой)
      плюс ПО ветру       → так и работает (значим только крупный)

    Пустая строка = сделка рутинная, в якоря не идёт.
    """
    if pnl_r is None:
        return ""
    r = round(float(pnl_r), 2)
    kray = abs(r) >= KRAYNOST_R
    protiv = bool(entry_bias) and bool(direction) and (
        (entry_bias == "BULL" and direction == "SHORT") or
        (entry_bias == "BEAR" and direction == "LONG")
    )
    shtil = not entry_bias
    when = f" ({bar})" if bar else ""
    veter = ("против компаса" if protiv
             else "в штиль (компас молчал)" if shtil
             else "по компасу")

    # причина закрытия доезжает не всегда (_settle шлёт судье pos, а
    # close_reason живёт в record) — молчим, а не выдумываем: якорь не врёт.
    why = f", {close_reason}" if close_reason else ""

    if r < 0 and protiv:
        return (f"Минус {r}R{when}: вошёл {direction} {veter}{why}. "
                f"Против ветра — редкая ставка, не хлеб.")
    if r < 0 and kray:
        return (f"Минус {r}R{when}: {direction} {veter}{why}. "
                f"Плата по системе — не повод менять систему.")
    if r > 0 and protiv and kray:
        return (f"Плюс {r}R{when}: {direction} {veter}. Взял — но против "
                f"ветра это удача, а не правота. Не строй на этом систему.")
    if r > 0 and kray:
        return f"Плюс {r}R{when}: {direction} {veter}. Так это и работает."
    return ""   # рутина — живёт в pnl.jsonl, в опыт не лезет


def zapisat_vyvod(magic, vyvod: str, pnl_r=None, limit: int = 10) -> dict:
    """ПИШУЩИЙ КОНЕЦ. magic закрытой позиции → носитель → его якоря.

    Заодно ЖИВОЙ ВДОХ: сделка качает заряд носителя (плюс греет, минус
    давит), сила — по |pnl_r|. Это дыхание, а не оценка: заряд ≠ опыт.

    Честный no-op, если носителя по магику нет — торговый цикл не рвём.
    """
    if not vyvod:
        return {"дописано": False, "причина": "рутина (в опыт не идёт)"}
    try:
        from cartridge_registry import resolve_by_magic
    except Exception as e:
        print(f"[МОСТ] ⚠️  реестр не поднялся ({e})")
        return {"дописано": False, "причина": "нет реестра"}

    n = resolve_by_magic(magic)
    if not n:
        print(f"[МОСТ] ⚠️  magic {magic} → носителя нет "
              f"(магик в маске? patch_magic_v_masku_v1)")
        return {"дописано": False, "причина": "носитель не найден"}

    d = _dvizhok(n["папка"])
    if d is None:
        return {"дописано": False, "причина": "движок не поднялся"}

    # ── ВДОХ: сделка тронула человека ────────────────────────────
    try:
        if pnl_r is not None:
            sila = min(1.0, abs(float(pnl_r)) / 3.0)
            tonus = "плюс" if float(pnl_r) > 0 else "минус" if float(pnl_r) < 0 else "ровно"
            d.vdoh("работа", sila=sila, svezhest=1.0, tonus=tonus)
            d.sохранить()          # заряд оседает в паспорт
    except Exception as e:
        print(f"[МОСТ] ⚠️  вдох не прошёл ({e}) — пишу вывод без дыхания")

    # ── ВЫВОД в якоря (нога Опыта) ───────────────────────────────
    # ЗАЩИТА ОТ ПОВТОРА (поймано на прогоне 12.07): dopisat_vyvod бьёт
    # дубль по ТОЧНОЙ строке. Но один и тот же бар в двух прогонах даёт
    # чуть разный текст — и якоря забились бы вариациями ОДНОГО урока,
    # вытеснив настоящий старый опыт (их всего 7-10!). Поэтому сверяем по
    # СУТИ: дата входа + направление уже есть среди якорей → не пишем.
    try:
        _raw = d.p.get("Anchor_Points", "") or ""
        _est = [x.strip() for x in _raw.replace("\\n", "\n").split("\n") if x.strip()]
        _bar = ""
        if "(" in vyvod and ")" in vyvod:
            _bar = vyvod[vyvod.find("(") + 1:vyvod.find(")")]
        _dir = "SHORT" if "SHORT" in vyvod else "LONG" if "LONG" in vyvod else ""
        if _bar and _dir:
            for _e in _est:
                if _bar in _e and _dir in _e:
                    return {"дописано": False,
                            "причина": f"этот урок уже есть ({_bar} {_dir})"}
    except Exception:
        pass

    try:
        res = d.dopisat_vyvod(vyvod, limit=limit)
    except AttributeError:
        print("[МОСТ] ⚠️  в dvizhok нет dopisat_vyvod — "
              "нужен patch_dvizhok_stol_chisto_vyvod_v1")
        return {"дописано": False, "причина": "нет руки опыта"}

    if res.get("дописано"):
        print(f"[МОСТ] 🧠 ОПЫТ → {n['имя']}: «{vyvod}» "
              f"(якорей: {res.get('всего')})")
    return res


# ════════════════════════════════════════════════════════════
# Самопроверка: python Биржа/nositel.py
# ════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import io as _io
    if isinstance(_sys.stdout, _io.TextIOWrapper):
        try:
            _sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    print("═══ МОСТ К НОСИТЕЛЮ — самопроверка ═══")
    d = dusha_slota("торговый_хаос", "A07")
    if not d:
        print("✗ A07 → носителя нет")
        raise SystemExit(1)
    print(f"A07 → {d['носитель']['имя']} (magic {d['magic']})")
    print("--- душа, как её увидит модель ---")
    print(d["душа"])
    print("--- суд по Котину (сухие числа, без LLM) ---")
    for dir_, bias, r, why in [
        ("SHORT", "BULL", -1.0, "стоп против ветра"),
        ("LONG",  "BULL", -1.0, "стоп по ветру (рутина)"),
        ("LONG",  "BULL", -2.4, "крупный минус по ветру"),
        ("LONG",  "BULL",  2.6, "крупный плюс по ветру"),
        ("SHORT", "BULL",  2.6, "крупный плюс против ветра"),
        ("LONG",  None,    0.4, "мелочь в штиль"),
    ]:
        v = sudit_po_kotinu(dir_, bias, r, "STOP_LOSS", "2010.05.13")
        print(f"  [{why}] → {v or '(рутина, в опыт не идёт)'}")
    print("═══ конец самопроверки ═══")
