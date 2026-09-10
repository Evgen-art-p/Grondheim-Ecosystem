# -*- coding: utf-8 -*-
# RUKI_ZAKLADOK_V1
"""
РУКИ ЖИТЕЛЮ ДЛЯ ЗАКЛАДОК.

Ключ мы сделали (METKA_KAK_KLYUCH_V1): у метки появились ярлыки своими
словами и имя того, от кого знание. Но повесить ярлык до сих пор мог
только код. Сам житель ни ярлык повесить, ни свой словарь посмотреть,
ни спросить по закладке не мог — вся работа лежала мёртвая.

Этот патч даёт три руки. Больше ничего.

═══ ЧТО ПОЯВЛЯЕТСЯ ═══

**`zapomnit_s_yarlykom`** — «запомни это, вот ярлыки, вот от кого».
Ложится сразу в метки как яркое (житель сам решил — минуя оба обычных
порога), с закладочной частью ключа.

**`moi_yarlyki`** — его собственный словарь закладок, частые первыми.
Нужно затем, что свободный ярлык за месяц расплодится в двести
вариантов вразнобой — «дивер», «диверы», «дивергенция». Перед тем как
вешать новый, житель смотрит, что у него уже есть, и берёт оттуда.
В описании руки это сказано прямо.

**`vspomnit_po_yarlyku`** — достать по закладке. Один ярлык достаёт
широко, два сужают, три бьют в точку — куча меток в куче тоже ключ.
Можно спросить и по имени: «что мне говорил Шеф».

═══ ЧЕГО ПАТЧ НЕ ДЕЛАЕТ ═══

Не трогает существующие руки, стол, кадр, промпт, знания, решения.
Не трогает `MEMORY_REQUEST` — старый способ попросить память остаётся
как был; закладка не вместо него, а рядом: он ищет словами, эта —
по имени.

Важность («ярко») по-прежнему ставит САМ ЖИТЕЛЬ и только он. Слово
Шефа: «важность обоим одинаково, я чего? У меня писька длиннее? Нет,
это его жизнь, пусть отвечает».

═══ ЗАВИСИМОСТЬ ═══

Требует накатанного `postavit_metku_klyuchom.py` — без него в движке
нет ни `yarlyki()`, ни приёма ярлыков. Патч это проверяет и честно
отказывается, если ключа ещё нет.

Запускать из корня репозитория:
    python postavit_ruki_zakladok.py

Идемпотентен (маркер RUKI_ZAKLADOK_V1). Рядом .bak.
"""
from __future__ import annotations
from pathlib import Path

MARKER = "RUKI_ZAKLADOK_V1"
RUKI = "Биржа/ruki_treydera.py"
DVIZHOK = "жители/dvizhok.py"


# ── 1) схема: три новые руки перед закрытием списка ─────────────────
SHEMA_OLD = '''        {"type": "function", "function": {
            "name": "moy_dnevnik",
            "description": (
                "Твои последние записи: что ты решал, чем кончилось. "
                "Своя память, не чужая."),
            "parameters": {"type": "object", "properties": {
                "сколько": {"type": "integer",
                            "description": "по умолчанию 5"}},
                "required": []}}},
    ]'''

SHEMA_NEW = '''        {"type": "function", "function": {
            "name": "moy_dnevnik",
            "description": (
                "Твои последние записи: что ты решал, чем кончилось. "
                "Своя память, не чужая."),
            "parameters": {"type": "object", "properties": {
                "сколько": {"type": "integer",
                            "description": "по умолчанию 5"}},
                "required": []}}},
        # ── RUKI_ZAKLADOK_V1: метка как закладка ────────────────
        {"type": "function", "function": {
            "name": "moi_yarlyki",
            "description": (
                "ТВОЙ СЛОВАРЬ ЗАКЛАДОК: какие ярлыки ты уже вешал и "
                "сколько раз. Смотри ПЕРЕД тем, как вешать новый, и "
                "бери из этого списка: иначе через месяц у тебя будет "
                "и «дивер», и «диверы», и «дивергенция» — и ты сам не "
                "вспомнишь, под каким что лежит."),
            "parameters": {"type": "object", "properties": {},
                           "required": []}}},
        {"type": "function", "function": {
            "name": "zapomnit_s_yarlykom",
            "description": (
                "Запомнить что-то надолго и повесить на это ЗАКЛАДКУ — "
                "чтобы потом достать по имени, а не угадывать слова. "
                "Вешай, когда сам считаешь важным: держится дольше "
                "обычного. Ярлыки — твои слова, сперва глянь "
                "moi_yarlyki. «От кого» — имя, если знание пришло от "
                "человека: знание одно, а чьё оно, решать тебе."),
            "parameters": {"type": "object", "properties": {
                "что": {"type": "string",
                        "description": "сам вывод, одно-два предложения"},
                "ярлыки": {"type": "string",
                           "description": "через запятую, например «дивер, ao»"},
                "от_кого": {"type": "string",
                            "description": "необязательно: имя, например «Шеф»"}},
                "required": ["что"]}}},
        {"type": "function", "function": {
            "name": "vspomnit_po_yarlyku",
            "description": (
                "Достать из своей памяти по закладке. Один ярлык даёт "
                "широко, два сужают, три бьют в точку. Можно спросить и "
                "по имени — «что мне говорил Шеф». Пусто — значит следа "
                "нет, и это честный ответ."),
            "parameters": {"type": "object", "properties": {
                "по": {"type": "string",
                       "description": "ярлык, несколько ярлыков или имя"},
                "сколько": {"type": "integer",
                            "description": "по умолчанию 6"}},
                "required": ["по"]}}},
    ]'''


# ── 2) исполнители ──────────────────────────────────────────────────
ISPOLN_OLD = '''    itog = {"stol_na_etazhe": _stol,'''

ISPOLN_NEW = '''    # ── RUKI_ZAKLADOK_V1: закладки ──────────────────────────
    # Ключ метки: ОБЩЕЕ (когда, откуда, от кого) + ЛИЧНОЕ (ярлыки
    # своими словами, важность своими глазами). Общее нужно, чтобы
    # город понимал всех одинаково; личное — чтобы жители отличались.
    def _dusha():
        """Движок памяти того, кто сидит в этом слоте."""
        from nositel import dusha_slota, _dvizhok
        n = dusha_slota(ceh, slot)
        if not n:
            return None
        return _dvizhok(n["носитель"]["папка"])

    def _moi_yarlyki(args: dict) -> str:
        try:
            d = _dusha()
            if d is None:
                return "память недоступна"
            spisok = d.yarlyki()
        except Exception as e:
            return f"словарь не прочитался: {e}"
        if not spisok:
            return ("Закладок пока нет. Первую заведёшь сам — "
                    "zapomnit_s_yarlykom.")
        return ("=== ТВОИ ЗАКЛАДКИ ===\\n"
                + "\\n".join(f"  {y} · {n}" for y, n in spisok[:40])
                + "\\nБери отсюда, новый заводи только если правда новый.")

    def _zapomnit_s_yarlykom(args: dict) -> str:
        chto = str(args.get("что") or "").strip()
        if not chto:
            return "нечего запоминать: пусто"
        try:
            d = _dusha()
            if d is None:
                return "память недоступна"
            res = d.otmetit_yarkim(
                chto[:600], otkuda="работа",
                yarlyki=args.get("ярлыки"),
                ot_kogo=str(args.get("от_кого") or "").strip())
        except TypeError:
            return ("движок ещё не знает закладок — нужен "
                    "postavit_metku_klyuchom.py")
        except Exception as e:
            return f"не запомнилось: {e}"
        if res.get("дописано"):
            _y = str(args.get("ярлыки") or "").strip()
            return "Запомнил." + (f" Закладка: {_y}." if _y else "")
        return "Не записано: " + str(res.get("причина", "—"))

    def _vspomnit_po_yarlyku(args: dict) -> str:
        po = str(args.get("по") or "").strip()
        if not po:
            return "по чему вспоминать не сказано"
        try:
            d = _dusha()
            if d is None:
                return "память недоступна"
            n = int(args.get("сколько") or 6)
            nayd = d.vspomnit(po, limit=n, o_chyom="работа") or ""
        except Exception as e:
            return f"вспомнить не вышло: {e}"
        if not nayd:
            return (f"По «{po}» следа нет. Такого с тобой не было — или "
                    "ты не повесил закладку. Решай без этого.")
        return f"=== ПО ЗАКЛАДКЕ «{po}» ===\\n{nayd}"

    itog = {"moi_yarlyki": _moi_yarlyki,                # RUKI_ZAKLADOK_V1
            "zapomnit_s_yarlykom": _zapomnit_s_yarlykom,
            "vspomnit_po_yarlyku": _vspomnit_po_yarlyku,
            "stol_na_etazhe": _stol,'''


def main() -> None:
    root = Path(__file__).resolve().parent
    put_ruki = root / RUKI
    put_dv = root / DVIZHOK

    if not put_ruki.exists():
        print(f"НЕ НАШЁЛ: {put_ruki}")
        print("Запускать из корня репозитория (там, где лежит main.py).")
        return

    # зависимость: без ключа руки повиснут
    if put_dv.exists():
        if "METKA_KAK_KLYUCH_V1" not in put_dv.read_text(encoding="utf-8"):
            print("⚠ Сперва накати postavit_metku_klyuchom.py —")
            print("  без него в движке нет ни yarlyki(), ни приёма ярлыков,")
            print("  и эти руки будут падать. Ничего не меняю.")
            return
    else:
        print(f"⚠ Не вижу {DVIZHOK} — не могу проверить, есть ли ключ.")
        print("  Если postavit_metku_klyuchom.py уже накачен, запусти")
        print("  этот патч из той же папки, где лежит папка «жители».")
        return

    text = put_ruki.read_text(encoding="utf-8")
    if MARKER in text:
        print("уже накачен — маркер на месте, ничего не трогаю")
        return

    bracket = []
    for imya, old in (("схема рук", SHEMA_OLD), ("исполнители", ISPOLN_OLD)):
        if text.count(old) != 1:
            bracket.append((imya, text.count(old)))
    if bracket:
        print("⚠ Файл на диске отличается от ожидаемого — НИЧЕГО не меняю:")
        for imya, cnt in bracket:
            print(f"   «{imya}»: совпадений {cnt} (нужно ровно 1)")
        print("Пришли Брату свой Биржа/ruki_treydera.py — доведу под него.")
        return

    text = text.replace(SHEMA_OLD, SHEMA_NEW, 1)
    text = text.replace(ISPOLN_OLD, ISPOLN_NEW, 1)
    text = text.rstrip("\n") + f"\n\n# {MARKER} - marker\n"

    try:
        import ast
        ast.parse(text)
    except SyntaxError as e:
        print(f"⚠ СИНТАКСИС СЛОМАН: {e} — НЕ сохраняю")
        return

    bak = put_ruki.with_suffix(put_ruki.suffix + ".bak_ruki_zakladok")
    if not bak.exists():
        bak.write_text(put_ruki.read_text(encoding="utf-8"), encoding="utf-8")
    put_ruki.write_text(text, encoding="utf-8")

    print(f"✔ {RUKI} — три руки встали, синтаксис цел")
    print("  Бэкап рядом:", bak.name)
    print("\nЧто теперь может сам житель:")
    print("  · moi_yarlyki          — свой словарь закладок")
    print("  · zapomnit_s_yarlykom  — запомнить и повесить закладку")
    print("  · vspomnit_po_yarlyku  — достать по закладке или по имени")
    print("\nПроверить: спроси в чате «какие у тебя есть закладки?» —")
    print("должен позвать руку, а не рассказывать из головы.")


if __name__ == "__main__":
    main()
