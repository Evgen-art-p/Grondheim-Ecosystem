# -*- coding: utf-8 -*-
"""
patch_disciplina_pyramidy.py
════════════════════════════════════════════════════════════════════
ДИСЦИПЛИНА РЕВЕРСИВНОЙ ПИРАМИДЫ + ОБРАТНАЯ СВЯЗЬ ТРЕЙДЕРУ

Канон шефа: реверсивная пирамида СУЖАЕТСЯ кверху. Каждый долив ≤
предыдущей ноги. Крупнее — риск-модель в пропасть. Наказание —
ПОЛНЫЙ ОТКАЗ (Б) + жёсткая обратная связь в стол: трейдер увидит
косяк на следующем баре, потеряет ход, вырастит метку.

ДВЕ ЧАСТИ:

  1. tester_express.py (_primenit_vedenie): ADD крупнее предыдущей
     ноги → отклонить, записать feedback в t[pref]["vedenie_feedback"].
     [Эта часть уже внесена патчем-исходником; здесь идемпотентно
      проверяется и, если нет, вносится.]

  2. Три мозга (A06/A07/A08): трейдер ЧИТАЕТ свою обратную связь.
     _read_table сейчас отдаёт только сенсоров — feedback летел в
     пустоту. Добавляем:
       • в _read_table — своё поле "self" с vedenie_feedback;
       • в user_msg — заметную строку «⛔ ОБРАТНАЯ СВЯЗЬ ПО ВЕДЕНИЮ»,
         если feedback есть, чтобы трейдер увидел и сделал вывод.
     После прочтения feedback гасится (одноразовый укол, не вечный).

Префикс по слоту: A06→brut, A07→avan, A08→cons.

ИДЕМПОТЕНТЕН (маркер DISCIPLINA_PYRAMIDY_V1). Бэкапы — по файлу.
Запуск из корня Grondheim-Ecosystem:
    python patch_disciplina_pyramidy.py
"""
import io
import sys
from pathlib import Path

MARKER = "DISCIPLINA_PYRAMIDY_V1"
TESTER_MARK = "REVERSE_PYRAMID_DISCIPLINE_V1"

SLOTS = {
    "A06": ("brut", "торговый_хаос"),
    "A07": ("avan", "торговый_хаос"),
    "A08": ("cons", "торговый_хаос"),
}


def base():
    for b in (Path("Биржа"), Path("GRONDHEIM_CITY") / "Биржа"):
        if (b / "hooks.py").exists():
            return b
    print("[ПАТЧ] ✗ не найдена папка Биржа — запусти из корня")
    sys.exit(1)


def slot_path(b, aid):
    # мозги лежат под GRONDHEIM_CITY/Биржа/цеха/..., а hooks/tester —
    # прямо в Биржа/. Ищем мозг в обоих корнях.
    candidates = [
        b / "цеха" / "торговый_хаос" / "слоты" / aid / "мозг.py",
        b.parent / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "слоты" / aid / "мозг.py",
        Path("GRONDHEIM_CITY") / "Биржа" / "цеха" / "торговый_хаос" / "слоты" / aid / "мозг.py",
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]  # для сообщения "не найден"


def patch_tester(b):
    """Дисциплина ноги в _primenit_vedenie (если ещё не внесена)."""
    path = b / "tester_express.py"
    src = path.read_text(encoding="utf-8")
    if TESTER_MARK in src:
        print("[ПАТЧ] ✓ tester: дисциплина ноги уже есть")
        return
    old = (
        '        elif action == "ADD" and add_lot is not None:\n'
        '            try:\n'
        '                al = float(add_lot)\n'
        '            except (TypeError, ValueError):\n'
        '                al = 0.0\n'
        '            if al > 0:\n'
    )
    new = (
        '        elif action == "ADD" and add_lot is not None:\n'
        '            try:\n'
        '                al = float(add_lot)\n'
        '            except (TypeError, ValueError):\n'
        '                al = 0.0\n'
        '            # ' + TESTER_MARK + ': реверсивная пирамида СУЖАЕТСЯ кверху.\n'
        '            # Долив > предыдущей ноги → полный ОТКАЗ + feedback в стол.\n'
        '            _last_leg = float(p.get("last_leg") or p.get("lot_base")\n'
        '                              or p.get("lot") or 0.0)\n'
        '            if al > 0 and _last_leg > 0 and al > _last_leg * 1.0001:\n'
        '                _pref = _VEDENIE_PREFIX.get(sid)\n'
        '                if _pref:\n'
        '                    ts.setdefault(_pref, {})\n'
        '                    ts[_pref]["vedenie_feedback"] = (\n'
        '                        f"Долив отклонён: превышен размер предыдущей ноги "\n'
        '                        f"({al} > {_last_leg}). Реверсивная пирамида только "\n'
        '                        f"сужается кверху.")\n'
        '                    changed = True\n'
        '                out(f"     └─ ⛔ ADD ОТКЛОНЁН: {al} > предыдущей ноги "\n'
        '                    f"{_last_leg} — дисциплина пирамиды (полный отказ)")\n'
        '            elif al > 0:\n'
    )
    if old not in src:
        print("[ПАТЧ] ⚠️  tester: якорь ADD не найден — часть 1 пропущена")
        return
    src = src.replace(old, new, 1)
    # запомнить размер ноги при успешном доливе
    old2 = '                p["dolivok"] = int(p.get("dolivok", 0)) + 1\n'
    new2 = ('                p["last_leg"] = round(al, 4)  # ' + TESTER_MARK
            + ': потолок для след. долива\n'
            '                p["dolivok"] = int(p.get("dolivok", 0)) + 1\n')
    if old2 in src:
        src = src.replace(old2, new2, 1)
    bak = path.with_suffix(".py.bak_disciplina")
    if not bak.exists():
        bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    path.write_text(src, encoding="utf-8")
    print("[ПАТЧ] ✓ tester: дисциплина ноги внесена")


def patch_brain(b, aid, pref):
    path = slot_path(b, aid)
    if not path.exists():
        print(f"[ПАТЧ] ⚠️  {aid}: мозг.py не найден — пропуск")
        return
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print(f"[ПАТЧ] ✓ {aid}: уже читает feedback")
        return
    orig = src

    # 1. _read_table: добавить "self" с feedback. Якорь — arkhiv строка.
    # У разных мозгов хвост-комментарий разный — цепляемся за общее ядро.
    import re as _re
    m = _re.search(r'(\n[ \t]*"arkhiv":[ \t]*t\.get\("arkhiv",[ \t]*\{\}\),[^\n]*\n)([ \t]*\})',
                   src)
    if m:
        indent = _re.match(r'[ \t]*', m.group(2)).group(0)
        add = (indent + '    # ' + MARKER + ': своя обратная связь по ведению\n'
               + indent + '    "self": t.get("' + pref + '", {}),\n')
        src = src[:m.end(1)] + add + src[m.start(2):]
    else:
        print(f"[ПАТЧ] ⚠️  {aid}: якорь _read_table не найден — пропуск мозга")
        return

    # 2. вложить feedback в user_msg заметной строкой. Якорь — начало user_msg.
    #    Ищем '=== НАКРЫТЫЙ СТОЛ' — она есть у всех троих.
    u_anchor = '        "=== НАКРЫТЫЙ СТОЛ (раскладка момента) ===\\n"'
    u_inject = (
        '        # ' + MARKER + ': если по прошлому ведению был укол — показать\n'
        '        # его трейдеру ОТДЕЛЬНОЙ строкой, чтобы увидел и сделал вывод.\n'
        '        + ((f"⛔ ОБРАТНАЯ СВЯЗЬ ПО ВЕДЕНИЮ (прошлый бар): "\n'
        '            f"{table.get(\'self\', {}).get(\'vedenie_feedback\')}\\n"\n'
        '            f"Учти это сейчас — дисциплина пирамиды железная.\\n\\n\")\n'
        '           if table.get(\'self\', {}).get(\'vedenie_feedback\') else "")\n'
        '        + "=== НАКРЫТЫЙ СТОЛ (раскладка момента) ===\\n"'
    )
    if u_anchor in src:
        src = src.replace(u_anchor, u_inject, 1)
    else:
        print(f"[ПАТЧ] ⚠️  {aid}: якорь user_msg не найден — feedback читается "
              f"в стол, но в промпт не вложен")

    # 3. погасить feedback после прочтения — в _save_verdict_to_table,
    #    рядом где пишется t[pref]. Якорь — save_trading_state(t) в этой ф-ции.
    g_anchor = '    save_trading_state(t)\n'
    g_inject = ('    # ' + MARKER + ': укол одноразовый — гасим после прочтения\n'
                '    if t.get("' + pref + '", {}).get("vedenie_feedback"):\n'
                '        t["' + pref + '"]["vedenie_feedback"] = None\n'
                '    save_trading_state(t)\n')
    if g_anchor in src:
        src = src.replace(g_anchor, g_inject, 1)

    bak = path.with_suffix(".py.bak_disciplina")
    if not bak.exists():
        bak.write_text(orig, encoding="utf-8")
    path.write_text(src, encoding="utf-8")
    print(f"[ПАТЧ] ✓ {aid}: читает и гасит feedback")


def main():
    b = base()
    patch_tester(b)
    for aid, (pref, _ceh) in SLOTS.items():
        patch_brain(b, aid, pref)
    print("[ПАТЧ] ✅ Дисциплина пирамиды + обратная связь построены.")
    print("[ПАТЧ]    Долив крупнее предыдущей ноги — полный отказ, и трейдер")
    print("[ПАТЧ]    увидит укол на следующем баре. Метка вырастет на косяке.")


if __name__ == "__main__":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass
    main()
