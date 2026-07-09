# -*- coding: utf-8 -*-
# patch_zhitel_chtenie_maska.py — ZHITEL_CHTENIE_MASKA_V1
# ─────────────────────────────────────────────────────────────
# ДЕЛЬТА поверх ZHITEL_CHTENIE_V1. Закрывает дырку:
# «если житель не определён с профессией — как он читает на месте?»
#
# ЗАКОН (из Чертежа): линза = МЕСТО × РОЛЬ. Роль НЕ выдумываем
# из скрытой истории — её объявляет сам житель через активную маску
# (маски/работа/mask.json, "_активна": true — тот самый контракт,
# что пишет Брат при назначении роли). Три исхода:
#
#   • дома                       → линза «дом»   (читает человеком)
#   • на месте + маска активна   → линза «работа» с ИМЕНЕМ профессии
#   • на месте + маска пуста      → житель здесь ГОСТЬ (каноническая
#     маска ГОСТЬ) → читает человеком. Никого не выдумываем.
#
# Так самообъявление (Закон Картриджа) правит и чтением: нет объявленной
# роли — нет профессиональной линзы. Метка знания едет следом:
# профессионал → [Знание: Цех], гость/дом → [Знание: Дом].
#
# МЕНЯЕТ РОВНО 2 функции v1: _linza_chtenia (+ читает маску, отдаёт
# профессию) и _prompt_chtenia (+ подставляет профессию в промпт).
# do_chtenia не трогаем — метка уже вяжется к linza=="работа",
# а гость возвращает "дом", так что метка сама встанет верно.
#
# ЗАПУСК из корня:  python patch_zhitel_chtenie_maska.py
# Идемпотентен (маркер), бэкап .bak_*, py_compile. Требует, чтобы
# ZHITEL_CHTENIE_V1 был уже наложен.
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER   = "ZHITEL_CHTENIE_MASKA_V1"
REQUIRED = "ZHITEL_CHTENIE_V1"

ROOT   = Path(__file__).resolve().parent
TARGET = ROOT / "жители" / "ui_zhitel.py"

# ══════════════════════════════════════════════════════════════
# 1. _linza_chtenia — теперь спрашивает маску, отдаёт ТРИ значения
# ══════════════════════════════════════════════════════════════
OLD_LINZA = '''def _linza_chtenia(dom) -> tuple:
    """ZHITEL_CHTENIE_V1: линза восприятия по ЖИВОМУ месту (sostoyanie.gde_ya).
    Дома → «дом» (читает для себя). Не дома → «работа» (читает как
    профессионал на месте). Возвращает (линза, имя_локации)."""
    try:
        _repo = Path(__file__).resolve().parent.parent
        if str(_repo) not in sys.path:
            sys.path.insert(0, str(_repo))
        import sostoyanie as _sost
        r = _sost.gde_ya(dom)
        lok = r.get("локация") or ""
        try:
            lok_imya = _lokacia_name(lok) if lok else ""
        except Exception:
            lok_imya = str(lok)
        if r.get("дома", True):
            return "дом", lok_imya
        return "работа", lok_imya
    except Exception:
        return "дом", ""  # sostoyanie нет — тихий откат: читает как дома'''

NEW_LINZA = '''def _prochitat_masku(dom) -> dict:
    """ZHITEL_CHTENIE_MASKA_V1: активная маска жителя (маски/работа/mask.json).
    Тот же контракт, что пишет Брат при назначении роли: "_активна": true +
    Profession/Turbo_Role/Workshop_ID. Нет файла или _активна=false → {} .
    Никогда не выдумываем профессию — её объявляет житель (Закон Картриджа)."""
    try:
        mp = dom / "маски" / "работа" / "mask.json"
        if not mp.exists():
            return {}
        import json as _json
        m = _json.loads(mp.read_text(encoding="utf-8"))
        if not isinstance(m, dict) or not m.get("_активна"):
            return {}
        return m
    except Exception:
        return {}


def _linza_chtenia(dom) -> tuple:
    """ZHITEL_CHTENIE_MASKA_V1: линза = МЕСТО × РОЛЬ. Возвращает
    (линза, имя_локации, профессия).
      • дома                     → ("дом", лок, "")
      • на месте + маска активна → ("работа", лок, <профессия из маски>)
      • на месте + маска пуста    → ГОСТЬ: ("дом", лок, "")
        (нет объявленной роли — нет профессиональной линзы, не гадаем)."""
    try:
        _repo = Path(__file__).resolve().parent.parent
        if str(_repo) not in sys.path:
            sys.path.insert(0, str(_repo))
        import sostoyanie as _sost
        r = _sost.gde_ya(dom)
        lok = r.get("локация") or ""
        try:
            lok_imya = _lokacia_name(lok) if lok else ""
        except Exception:
            lok_imya = str(lok)
        if r.get("дома", True):
            return "дом", lok_imya, ""
        # НА МЕСТЕ — спрашиваем маску, кто он тут
        m = _prochitat_masku(dom)
        if not m:
            # роль не объявлена → житель здесь ГОСТЬ → читает человеком
            return "дом", lok_imya, ""
        prof = (m.get("Profession") or m.get("Turbo_Role")
                or m.get("Social_Rank") or "").strip()
        if not prof:
            # маска активна, но профессия пуста — тоже не выдумываем
            return "дом", lok_imya, ""
        return "работа", lok_imya, prof
    except Exception:
        return "дом", "", ""  # sostoyanie нет — тихий откат: читает как дома'''

# ══════════════════════════════════════════════════════════════
# 2. вызов линзы в do_chtenia — распаковка тройки + проброс профессии
# ══════════════════════════════════════════════════════════════
OLD_CALL = "        linza, lok_imya = _linza_chtenia(dom)"
NEW_CALL = ("        linza, lok_imya, professia = _linza_chtenia(dom)  # ZHITEL_CHTENIE_MASKA_V1")

OLD_NOTIFY = '''        ui.notify(f"📖 {name} читает {len(fajly)} файл(ов)"
                  + (f" — на месте «{lok_imya}»" if linza == "работа" else " — дома"),
                  color="info")'''
NEW_NOTIFY = '''        _kto = (f" — как {professia} на «{lok_imya}»" if linza == "работа"
                else (f" — гостем на «{lok_imya}»" if lok_imya else " — дома"))
        ui.notify(f"📖 {name} читает {len(fajly)} файл(ов){_kto}",
                  color="info")  # ZHITEL_CHTENIE_MASKA_V1'''

OLD_PROMPT_CALL = "                {\"role\": \"user\", \"content\": _prompt_chtenia(fp.name, tekst, linza, lok_imya)},"
NEW_PROMPT_CALL = "                {\"role\": \"user\", \"content\": _prompt_chtenia(fp.name, tekst, linza, lok_imya, professia)},  # ZHITEL_CHTENIE_MASKA_V1"

# ══════════════════════════════════════════════════════════════
# 3. _prompt_chtenia — принимает профессию, называет её в промпте
# ══════════════════════════════════════════════════════════════
OLD_PROMPT = '''def _prompt_chtenia(imya_fajla: str, tekst: str, linza: str, lok_imya: str) -> str:
    """ZHITEL_CHTENIE_V1: вопрос жителю по линзе места.
    РАБОТА — структурная польза в арсенал. ДОМ — смыслы и отклик.
    Не «оцени факты и найди связи» (это фильтр Брата), а
    «ты прочитал(а) — что усвоилось, что отзовётся в тебе»."""
    if linza == "работа":
        gde = (f"Ты сейчас на месте — {lok_imya}." if lok_imya
               else "Ты сейчас на работе, за делом.")
        zadacha = ("Прочитай это как профессионал за делом: вытащи структурную "
                   "пользу — алгоритмы, паттерны, приёмы, рабочие схемы, "
                   "которые пополнят твой арсенал.")
    else:
        gde = "Ты сейчас дома, читаешь для себя, в своём ритме."
        zadacha = ("Прочитай это как человек для себя: что тронуло, какие мысли "
                   "и смыслы отозвались, какая эстетика запомнилась, что из "
                   "этого отзовётся в тебе дальше.")'''

NEW_PROMPT = '''def _prompt_chtenia(imya_fajla: str, tekst: str, linza: str,
                    lok_imya: str, professia: str = "") -> str:
    """ZHITEL_CHTENIE_MASKA_V1: вопрос жителю по линзе МЕСТО × РОЛЬ.
    РАБОТА — читает как названная профессия (из активной маски),
    польза в арсенал. ДОМ/ГОСТЬ — смыслы и отклик человеком.
    Профессию не выдумываем: сюда приходит только объявленная маской."""
    if linza == "работа":
        _rol = f"как {professia}" if professia else "как профессионал"
        gde = (f"Ты сейчас на месте — {lok_imya}, ты здесь {_rol}." if lok_imya
               else f"Ты сейчас за делом, {_rol}.")
        zadacha = (f"Прочитай это {_rol}: вытащи структурную пользу — "
                   "алгоритмы, паттерны, приёмы, рабочие схемы, которые "
                   "пополнят твой профессиональный арсенал.")
    else:
        gde = ("Ты сейчас дома, читаешь для себя, в своём ритме."
               if not lok_imya
               else f"Ты сейчас на «{lok_imya}», но роли тебе тут не дано — "
                    "ты здесь гость и читаешь для себя, в своём ритме.")
        zadacha = ("Прочитай это как человек для себя: что тронуло, какие мысли "
                   "и смыслы отозвались, какая эстетика запомнилась, что из "
                   "этого отзовётся в тебе дальше.")'''

EOF_MARKER = "\n# ZHITEL_CHTENIE_MASKA_V1 — маркер идемпотентности\n"


def main():
    print("═" * 62)
    print(f"  ПАТЧ {MARKER}: линза чтения спрашивает маску")
    print("═" * 62)

    if not TARGET.exists():
        print(f"✗ не найден {TARGET}\n  Запусти из корня проекта (рядом с папкой жители/).")
        sys.exit(1)

    text = TARGET.read_text(encoding="utf-8")

    if REQUIRED not in text:
        print(f"✗ не наложен базовый патч {REQUIRED}.")
        print("  Сначала прогони patch_zhitel_chtenie.py — этот идёт поверх него.")
        sys.exit(1)

    if MARKER in text:
        print(f"• маркер {MARKER} уже стоит — дельта применена ранее. Выходим чисто.")
        sys.exit(0)

    anchors = [
        ("v1 _linza_chtenia",       OLD_LINZA),
        ("вызов линзы (распаковка)", OLD_CALL),
        ("notify чтения",           OLD_NOTIFY),
        ("вызов _prompt_chtenia",   OLD_PROMPT_CALL),
        ("v1 _prompt_chtenia",      OLD_PROMPT),
    ]
    ok = True
    for label, a in anchors:
        n = text.count(a)
        status = "✓" if n == 1 else "✗"
        print(f"  {status} якорь [{label}]: найден {n} раз (нужно ровно 1)")
        if n != 1:
            ok = False
    if not ok:
        print("✗ якоря не сошлись — файл отличается от ожидаемого v1. Ничего не режу.")
        sys.exit(1)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = TARGET.with_name(TARGET.name + f".bak_{ts}")
    shutil.copy2(TARGET, bak)
    print(f"• бэкап: {bak.name}")

    text = text.replace(OLD_LINZA, NEW_LINZA, 1)
    text = text.replace(OLD_CALL, NEW_CALL, 1)
    text = text.replace(OLD_NOTIFY, NEW_NOTIFY, 1)
    text = text.replace(OLD_PROMPT_CALL, NEW_PROMPT_CALL, 1)
    text = text.replace(OLD_PROMPT, NEW_PROMPT, 1)
    text += EOF_MARKER

    TARGET.write_text(text, encoding="utf-8")
    print("• правки внесены")

    try:
        py_compile.compile(str(TARGET), doraise=True)
        print("• py_compile: ЗЕЛЁНЫЙ")
    except Exception as e:
        shutil.copy2(bak, TARGET)
        print(f"✗ py_compile упал: {e}\n  Файл откатан из бэкапа.")
        sys.exit(1)

    print()
    print("  ГОТОВО. Линза теперь = МЕСТО × РОЛЬ:")
    print("  • дома                     → человеком")
    print("  • на месте + маска активна → как названная профессия")
    print("  • на месте без маски        → ГОСТЬ, человеком (не выдумываем)")
    print("═" * 62)


if __name__ == "__main__":
    main()
