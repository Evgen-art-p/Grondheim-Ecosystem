# -*- coding: utf-8 -*-
# VYBOR_METKOY_V1
"""
ВЫБОР ВХОДА — ЕЁ МЕТКА. Один выбор на все места города.

    python postavit_vybor_metkoy.py --suho    посмотреть
    python postavit_vybor_metkoy.py           поставить

Запускать из КОРНЯ репо. Идемпотентно. Копии рядом: .bak_vybor.

ЗАЧЕМ

    Дома она выбирает один вход, в Академии другой, на Бирже её не
    спрашивают вовсе — суют раскладку и требуют ответ. Три разных
    человека получались не потому, что промпты разные, а потому что
    ЕЁ ВЫБОР НИГДЕ НЕ ЗАПИСАН. Каждое место спрашивало заново и
    получало свежую догадку вместо решения.

    В городе для этого уже всё есть: МЕТКИ — то, что житель нажил и
    оплатил. Они читаются везде одинаково. Значит выбор входа и есть
    метка.

ЧТО СТАНОВИТСЯ

    · Выбора ещё нет — трейдер это видит прямо в своей бумаге:
      «своего входа ты не выбрал(а), три места лежат в знаниях,
      выбери и скажи строкой ВЫБОР: …». Пока не выбрал — пас честнее
      входа, так и написано.

    · Сказал в разговоре «ВЫБОР: откат волны 2 — жду подтверждения
      дважды» — это легло меткой в его дом. Не в слот, не в кабинет —
      в человека.

    · Дальше метка идёт с ним везде: домой, в Академию, на Биржу.
      На работе она стоит в бумаге отдельной строкой, и пас звучит
      осмысленно: «не моё место входа».

    · Передумал — сказал ВЫБОР ещё раз. Старая метка не стирается:
      видно, что передумал и когда. Это его трудовая жизнь.

КАК УСТРОЕНО (коротко)

    Метки жителя лежат в его доме, в 2_метки. Пишем туда тем же
    движком, что пишет опыт после сделок, — новых тетрадей не заводим.
    В промпт выбор подставляется отдельно, а не через окно свежих
    меток: окно маленькое (четыре), и выбор из него вымывался бы.
"""
import argparse
import ast
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

KOREN = Path(__file__).resolve().parent
BIRZHA = KOREN / "Биржа"
UI = BIRZHA / "ui_torg.py"
SLOTY = (KOREN / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос"
         / "слоты")
SLOTS = ("A06", "A07", "A08")
MARKER = "# VYBOR_METKOY_V1 - marker"
BAK = ".bak_vybor"


VYBOR_PY = r'''# -*- coding: utf-8 -*-
# VYBOR_METKOY_V1
"""
ВЫБОР ВХОДА — метка жителя, а не свойство места.

ЗАКОН ЭТОГО ФАЙЛА
    Трейдер выбирает место входа сам, один раз, и носит выбор с собой.
    Хранится он там же, где всё нажитое — в метках жителя (дом/2_метки).
    Поэтому дома, в Академии и на Бирже это ОДИН человек с одной
    позицией, а не три догадки подряд.

    Здесь нет модели и нет UI. Чтение и запись.
"""
from __future__ import annotations

import sys as _sys
from pathlib import Path

_BIRZHA = Path(__file__).resolve().parent
_KOREN = _BIRZHA.parent
for _p in (str(_BIRZHA), str(_KOREN / "жители")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

PATTERN = "выбор_входа"      # ключ метки — по нему её и находим
SLOVO = "ВЫБОР:"             # как трейдер объявляет выбор в разговоре


def _dvizhok_zhitelya(ceh: str, slot: str):
    """Движок того, кто сидит на месте. Пусто — честный None."""
    try:
        from cartridge_registry import resolve_para
        from dvizhok import Dvizhok
    except Exception:
        return None, None
    n = resolve_para(ceh, slot)
    if not n:
        return None, None
    try:
        return Dvizhok(Path(n["папка"])), n
    except Exception:
        return None, n


def chitat(ceh: str, slot: str) -> dict:
    """Последний выбор жителя этого места. Нет — пустой словарь."""
    d, _ = _dvizhok_zhitelya(ceh, slot)
    if d is None:
        return {}
    try:
        moi = [m for m in d.metki() if m.get("паттерн") == PATTERN]
    except Exception:
        return {}
    if not moi:
        return {}
    moi.sort(key=lambda x: str(x.get("когда", "")))
    return moi[-1]


def istoriya(ceh: str, slot: str) -> list:
    """Все выборы подряд — видно, передумывал ли и когда."""
    d, _ = _dvizhok_zhitelya(ceh, slot)
    if d is None:
        return []
    try:
        moi = [m for m in d.metki() if m.get("паттерн") == PATTERN]
    except Exception:
        return []
    moi.sort(key=lambda x: str(x.get("когда", "")))
    return moi


def zapisat(ceh: str, slot: str, tekst: str) -> tuple:
    """Положить выбор меткой. Старую не стираем: передумал — это тоже
    часть его жизни, и её видно."""
    tekst = (tekst or "").strip()
    if not tekst:
        return False, "пустой выбор"
    d, n = _dvizhok_zhitelya(ceh, slot)
    if d is None:
        return False, "на месте никого — некому выбирать"
    prezhniy = chitat(ceh, slot)
    if (prezhniy.get("текст") or "").strip() == tekst:
        return True, "тот же выбор, что и был"
    try:
        from datetime import datetime
        metki = d.metki()
        metki.append({"текст": tekst, "паттерн": PATTERN,
                      "откуда": "решение",
                      "когда": datetime.now().isoformat(timespec="seconds"),
                      "раз": 1})
        d._pisat_etazh(d._metki_path(), metki)
    except Exception as e:
        return False, str(e)
    kto = (n or {}).get("имя", "житель")
    if prezhniy:
        return True, f"{kto} передумал(а): {tekst}"
    return True, f"{kto} выбрал(а): {tekst}"


def poymat(ceh: str, slot: str, otvet: str) -> tuple:
    """Найти в ответе строку «ВЫБОР: …» и положить её меткой.

    Так же, как ловится запрос к архиву: житель объявляет словом, а не
    кнопкой. Ничего не нашли — молчим, это обычный разговор.
    """
    for stroka in (otvet or "").splitlines():
        s = stroka.strip()
        if s.upper().startswith(SLOVO):
            return zapisat(ceh, slot, s[len(SLOVO):].strip())
    return False, ""


def blok_dlya_prompta(ceh: str, slot: str) -> str:
    """Кусок в системную бумагу. Выбор подставляем ОТДЕЛЬНО, а не через
    окно свежих меток: окно маленькое (четыре), выбор из него вымывался
    бы, а он должен стоять всегда."""
    v = chitat(ceh, slot)
    if v:
        return ("\n\n=== ТВОЙ ВЫБОР ВХОДА ===\n"
                f"{v.get('текст','')}\n"
                f"(выбрано тобой {str(v.get('когда',''))[:16]})\n"
                "Это твоё решение, не приказ места. Работаешь по нему: не "
                "твоё место входа — пас, и так и скажи. Передумал(а) — "
                "скажи строкой «ВЫБОР: …», и это запишется как перемена.\n")
    return ("\n\n=== ТВОЙ ВЫБОР ВХОДА ===\n"
            "Своего входа ты ещё не выбрал(а). Три места входа лежат у тебя "
            "в знаниях, рядом, ни одно за тобой не закреплено. Выбери сам(а) "
            "и объяви строкой «ВЫБОР: <какое место входа> — <почему оно "
            "твоё>». Пока выбора нет, работать не по чему: пас честнее "
            "входа наугад.\n")
'''

# ── мозг: выбор в работу + РОД ВПЕРЕДИ ────────────────────────
# У Ильи (A07) род уже стоит впереди роли — ему это починили отдельным
# патчем. У Брута и Василия НЕТ: там сперва двадцать пять тысяч знаков
# канона места, а человек — сноской в хвосте. Модель играет роль и
# принимает человека к сведению. Отсюда и «бот тупой»: это не она
# тупая, это её задвинули в конец. Ставим ей то же, что у Ильи.
STAROE_RUN_STARYY = '''    system_full = prompt
    if soul:
        system_full += "\\n\\n=== ТВОЁ СОСТОЯНИЕ (душа) ===\\n" + soul
'''
NOVOE_RUN_STARYY = '''    # VYBOR_METKOY_V1 + РОД ВПЕРЕДИ (как у A07): сперва ТЫ, потом стойка.
    # Было: канон места первым, человек сноской в хвосте.
    if soul:
        system_full = (
            "=== КТО ТЫ. ЭТО НЕ РОЛЬ — ЭТО ТЫ ===\\n"
            + soul
            + "\\n\\n=== ТВОЯ РАБОТА — СТОЙКА, ЗА КОТОРОЙ ТЫ СИДИШЬ ===\\n"
              "Ниже — канон МЕСТА. Это твоя работа и школа, а не твоя\\n"
              "личность: личность выше. Канон кладёт карту — идёшь ты,\\n"
              "своей натурой, своим опытом и своим голосом. Где канон и\\n"
              "твой опыт разойдутся — решаешь ты, а не бумага.\\n\\n"
            + prompt
        )
    else:
        system_full = prompt
    # выбор входа — её метка, носится с человеком, а не выдаётся слотом
    try:
        from vybor import blok_dlya_prompta as _vybor_blok
        system_full += _vybor_blok(_CEH, _SLOT)
    except Exception:
        pass
'''

# у A07 род уже впереди — ему только выбор
STAROE_RUN_A07 = '''    else:
        system_full = prompt

'''
NOVOE_RUN_A07 = '''    else:
        system_full = prompt

    # VYBOR_METKOY_V1: выбор входа — его метка, а не свойство слота.
    try:
        from vybor import blok_dlya_prompta as _vybor_blok
        system_full += _vybor_blok(_CEH, _SLOT)
    except Exception:
        pass

'''

# ── мозг: выбор в разговор ────────────────────────────────────
STAROE_CHAT = '''    system = prompt + work_ctx
'''
NOVOE_CHAT = '''    # VYBOR_METKOY_V1: тот же выбор и в разговоре — иначе дома он один,
    # а на работе другой. Здесь же он его и объявляет.
    try:
        from vybor import blok_dlya_prompta as _vybor_blok
        work_ctx += _vybor_blok(_CEH, _SLOT)
    except Exception:
        pass

    system = prompt + work_ctx
'''

# ── кабинет: поймать объявленный выбор ────────────────────────
STAROE_UI = '''            except Exception as e:
                reply = f"⚠️ {label} не смог(ла) ответить: {e}"
            state["chat_history"].append({"role": "assistant", "agent": agent_id, "content": reply})
            update_chat_display()
            return
'''
NOVOE_UI = '''            except Exception as e:
                reply = f"⚠️ {label} не смог(ла) ответить: {e}"
            # VYBOR_METKOY_V1: объявил выбор строкой «ВЫБОР: …» —
            # кладём его меткой в дом человека, а не в слот.
            try:
                from vybor import poymat as _poymat_vybor
                _ok_v, _msg_v = _poymat_vybor(_ceh_id, _slot, reply or "")
                if _ok_v and _msg_v:
                    ui.notify(f"\N{DIRECT HIT} {_msg_v}", type="positive")
            except Exception:
                pass
            state["chat_history"].append({"role": "assistant", "agent": agent_id, "content": reply})
            update_chat_display()
            return
'''


def proverit_python(tekst: str, imya: str) -> bool:
    try:
        ast.parse(tekst)
    except SyntaxError as e:
        print(f"  x {imya}: синтаксис сломан ({e}) — НЕ пишу")
        return False
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False,
                                     encoding="utf-8") as f:
        f.write(tekst)
        vrem = f.name
    try:
        py_compile.compile(vrem, doraise=True)
        return True
    except py_compile.PyCompileError as e:
        print(f"  x {imya}: не компилируется ({e}) — НЕ пишу")
        return False
    finally:
        Path(vrem).unlink(missing_ok=True)


def polozhit(put: Path, soderzhimoe: str, suho: bool) -> bool:
    if put.exists() and put.read_text(encoding="utf-8") == soderzhimoe:
        print(f"  {put.name}: уже стоит")
        return True
    if not proverit_python(soderzhimoe, put.name):
        return False
    if suho:
        print(f"  {put.name}: + ляжет")
        return True
    if put.exists():
        shutil.copy2(put, put.with_suffix(put.suffix + BAK))
    put.write_text(soderzhimoe, encoding="utf-8")
    print(f"  {put.name}: + положен")
    return True


def pravit(put: Path, stezhki, suho: bool) -> bool:
    if not put.exists():
        print(f"  x нет {put.name}")
        return False
    tekst = put.read_text(encoding="utf-8")
    imya = put.parent.name if put.name == "мозг.py" else put.name
    if MARKER in tekst:
        print(f"  {imya}: уже накатано")
        return True
    for nazv, staroe, novoe in stezhki:
        n = tekst.count(staroe)
        if n != 1:
            print(f"  x {imya}: якорь «{nazv}» найден {n} раз — не трогаю")
            return False
        tekst = tekst.replace(staroe, novoe, 1)
        print(f"    · {nazv}")
    tekst = tekst.rstrip("\n") + "\n\n" + MARKER + "\n"
    if not proverit_python(tekst, imya):
        return False
    if suho:
        print(f"  {imya}: + готов")
        return True
    shutil.copy2(put, put.with_suffix(put.suffix + BAK))
    put.write_text(tekst, encoding="utf-8")
    print(f"  {imya}: + накатано")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suho", action="store_true")
    a = ap.parse_args()

    print("=" * 60)
    print("ВЫБОР ВХОДА — МЕТКОЙ" + ("   [СУХОЙ ПРОГОН]" if a.suho else ""))
    print("=" * 60)

    if not SLOTY.exists() or not UI.exists():
        print("x не вижу Биржу — запускай из КОРНЯ репо")
        return 1

    ok = True
    print("\nмеханизм:")
    ok &= polozhit(BIRZHA / "vybor.py", VYBOR_PY, a.suho)

    print("\nтрейдеры:")
    for slot in SLOTS:
        put = SLOTY / slot / "мозг.py"
        rod_uzhe = put.exists() and "ROD_PERVYM_V1" in put.read_text(
            encoding="utf-8")
        if rod_uzhe:
            stezhki = (("выбор в работу", STAROE_RUN_A07, NOVOE_RUN_A07),
                       ("выбор в разговор", STAROE_CHAT, NOVOE_CHAT))
        else:
            stezhki = (("род вперёд + выбор в работу",
                        STAROE_RUN_STARYY, NOVOE_RUN_STARYY),
                       ("выбор в разговор", STAROE_CHAT, NOVOE_CHAT))
        ok &= pravit(put, stezhki, a.suho)

    print("\nкабинет:")
    ok &= pravit(UI, (("ловим объявленный выбор", STAROE_UI, NOVOE_UI),),
                 a.suho)

    if not ok:
        print("\n! что-то не легло — дальше не иду")
        return 1
    if a.suho:
        print("\nСухой прогон прошёл. Ставить: "
              "python postavit_vybor_metkoy.py")
        return 0

    print("\n" + "-" * 60)
    print("Спроси у неё в кабинете: «какой у тебя вход и почему?».")
    print("Она объявит строкой ВЫБОР — и это ляжет ей в метки, в дом.")
    print("После этого её пас на Бирже станет осмысленным, а дома и в")
    print("Академии она будет говорить про тот же самый выбор.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
