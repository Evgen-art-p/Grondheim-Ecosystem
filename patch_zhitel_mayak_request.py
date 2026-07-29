# PATCH_ZHITEL_MAYAK_REQUEST_V1
"""
PATCH_ZHITEL_MAYAK_REQUEST_V1 -- житель сам может попросить выйти на
Маяк, тем же жестом, что уже есть для памяти (MEMORY_REQUEST).

Слово Шефа: "житель может выйти в интернет где?" -> ответ был "нигде,
кроме постов и твоего /mayak" -> "сделай" (MAYAK_REQUEST по аналогии).

КАК РАБОТАЕТ (один подъём за ход, без петель -- тот же приём, что и
у памяти): в системный промпт добавлена строка-разрешение. Если
модель в ответе пишет "MAYAK_REQUEST: <запрос>" -- код ловит это,
зовёт mayak.poisk() (Маяк/mayak.py, уже существует и работает), даёт
житель\ю пропустить находку через себя ещё одним вызовом, и стирает
техническую строку из видимого ответа -- Шеф не видит "MAYAK_REQUEST",
только естественный ответ.

ПАМЯТЬ: то, что принёс Маяк, оседает как факт через vdoh(kontekst=
"факт") -- то самое единственное, что реально пишет в sensory (до
этого патча sensory был вечно пуст, потому что ни один код не звал
"факт"/"дом" -- см. разговор про пустой sensory_memory.json). Внешний
свежий факт -- ровно то, для чего этот слой задуман.

Приоритет за один ход: если модель попросила и память, и Маяк разом
(редкость) -- обслуживается Маяк, память подождёт следующий ход. Не
усложняем один ход двумя подъёмами.

Идемпотентно: если маркер PATCH_ZHITEL_MAYAK_REQUEST_V1 уже стоит в
файле -- патч молча выходит, повторно не наложится. Бэкап .bak
делается один раз, при первом применении.

Запуск из корня репо:  python patch_zhitel_mayak_request.py
`шесть·проверено·до·корня`
"""
from pathlib import Path
import sys

TARGET = Path('жители/ui_zhitel.py')
MARKER = 'PATCH_ZHITEL_MAYAK_REQUEST_V1'

OLD_UBRAT_MEMORY = '''def _ubrat_memory_request(text: str) -> str:
    """PATCH_ZHITEL_VSPOMINAET: технические строки MEMORY_REQUEST вычищаются из видимого ответа."""
    lines = [l for l in (text or "").splitlines() if "MEMORY_REQUEST:" not in l]
    return "\\n".join(lines).strip()'''

NEW_UBRAT_MEMORY = '''def _ubrat_memory_request(text: str) -> str:
    """PATCH_ZHITEL_VSPOMINAET: технические строки MEMORY_REQUEST вычищаются из видимого ответа."""
    lines = [l for l in (text or "").splitlines() if "MEMORY_REQUEST:" not in l]
    return "\\n".join(lines).strip()


# PATCH_ZHITEL_MAYAK_REQUEST_V1: тот же приём, что MEMORY_REQUEST, только
# наружу -- к Маяку Пробуждения, не внутрь себя.
def _izvlech_mayak_request(text: str) -> str:
    for line in (text or "").splitlines():
        if "MAYAK_REQUEST:" in line:
            return line.split("MAYAK_REQUEST:", 1)[1].strip()
    return ""


def _ubrat_mayak_request(text: str) -> str:
    lines = [l for l in (text or "").splitlines() if "MAYAK_REQUEST:" not in l]
    return "\\n".join(lines).strip()'''

OLD_SOUL_MEMORY_INSTR = '''            soul += (
                "\\nУ тебя есть своя память — события прошлых разговоров. Если "
                "что-то кажется знакомым, но не помнишь точно — напиши в ответе "
                "отдельной строкой MEMORY_REQUEST: <что вспомнить> и тебе "
                "поднимется это из твоей памяти."
            )'''

NEW_SOUL_MEMORY_INSTR = '''            soul += (
                "\\nУ тебя есть своя память — события прошлых разговоров. Если "
                "что-то кажется знакомым, но не помнишь точно — напиши в ответе "
                "отдельной строкой MEMORY_REQUEST: <что вспомнить> и тебе "
                "поднимется это из твоей памяти."
            )
            # PATCH_ZHITEL_MAYAK_REQUEST_V1
            soul += (
                "\\nЕсли для ответа не хватает свежих фактов из внешнего мира "
                "(то, чего ты сам знать не можешь — новости, текущие события, "
                "актуальные данные) — напиши отдельной строкой "
                "MAYAK_REQUEST: <что узнать> и Маяк Пробуждения принесёт ответ."
            )'''

OLD_MEM_HANDLING = '''            _mem_q = _izvlech_memory_request(reply)
            if _mem_q and dvizhok is not None:
                try:
                    _naydeno = dvizhok.vspomnit(_mem_q)
                except Exception:
                    _naydeno = ""
                _vtoroy = list(messages)
                _vtoroy.append({"role": "assistant", "content": reply})
                if _naydeno:
                    _vtoroy.append({"role": "user", "content": (
                        f"(Из твоей памяти поднято по запросу «{_mem_q}»:\\n"
                        f"{_naydeno}\\n"
                        f"Ответь заново, уже помня это, живым голосом. "
                        f"Механизм памяти не упоминай.)")})
                else:
                    _vtoroy.append({"role": "user", "content": (
                        f"(В твоей памяти по запросу «{_mem_q}» ничего не нашлось — "
                        f"этого следа нет. Ответь заново честно, не выдумывая. "
                        f"Механизм памяти не упоминай.)")})
                reply = await call_zhitel_llm(_vtoroy, state.get("model"))
            reply = _ubrat_memory_request(reply) or reply'''

NEW_MEM_HANDLING = '''            _mem_q = _izvlech_memory_request(reply)
            _mayak_q = _izvlech_mayak_request(reply)  # PATCH_ZHITEL_MAYAK_REQUEST_V1

            if _mayak_q:
                # PATCH_ZHITEL_MAYAK_REQUEST_V1: наружу, к Маяку. Приоритет
                # над памятью за этот ход -- один подъём, без петель.
                _naydeno_mayak = ""
                _nashlos = False
                try:
                    _repo_m = Path(__file__).resolve().parent.parent
                    _mayak_dir = _repo_m / "Маяк"
                    if str(_mayak_dir) not in sys.path:
                        sys.path.insert(0, str(_mayak_dir))
                    import mayak
                    _rez = await mayak.poisk(_mayak_q)
                    _naydeno_mayak = mayak.dlya_promta(_rez)
                    _nashlos = bool(_rez.get("ok"))
                    try:
                        mayak.zapisat_vizit(name, _mayak_q, _nashlos)
                    except Exception:
                        pass
                except Exception as _e:
                    _naydeno_mayak = f"(маяк не откликнулся: {_e})"
                _vtoroy = list(messages)
                _vtoroy.append({"role": "assistant", "content": reply})
                _vtoroy.append({"role": "user", "content": (
                    f"(С Маяка Пробуждения принесли по запросу «{_mayak_q}»:\\n"
                    f"{_naydeno_mayak}\\n"
                    f"Пропусти через себя и ответь заново своими словами, живым "
                    f"голосом — не пересказывай источники. Маяк не упоминай.)")})
                reply = await call_zhitel_llm(_vtoroy, state.get("model"))
                # PATCH_ZHITEL_MAYAK_REQUEST_V1: свежий факт извне — в sensory
                # (kontekst="факт"), не "учёба" — это не прожитый урок, а то,
                # что принёс луч сейчас.
                if dvizhok is not None and _nashlos:
                    try:
                        _chistyy = reply.strip()[:400]
                        _vdoh_m = dvizhok.vdoh(kontekst="факт", sila=0.7,
                                               svezhest=1.0, tonus="ровно")
                        dvizhok.vydoh_stol(
                            fakt=f"[Маяк] «{_mayak_q}»: {_chistyy}",
                            vdoh_result=_vdoh_m)
                    except Exception:
                        pass
            elif _mem_q and dvizhok is not None:
                try:
                    _naydeno = dvizhok.vspomnit(_mem_q)
                except Exception:
                    _naydeno = ""
                _vtoroy = list(messages)
                _vtoroy.append({"role": "assistant", "content": reply})
                if _naydeno:
                    _vtoroy.append({"role": "user", "content": (
                        f"(Из твоей памяти поднято по запросу «{_mem_q}»:\\n"
                        f"{_naydeno}\\n"
                        f"Ответь заново, уже помня это, живым голосом. "
                        f"Механизм памяти не упоминай.)")})
                else:
                    _vtoroy.append({"role": "user", "content": (
                        f"(В твоей памяти по запросу «{_mem_q}» ничего не нашлось — "
                        f"этого следа нет. Ответь заново честно, не выдумывая. "
                        f"Механизм памяти не упоминай.)")})
                reply = await call_zhitel_llm(_vtoroy, state.get("model"))
            reply = _ubrat_mayak_request(_ubrat_memory_request(reply)) or reply'''

REPLACEMENTS = [
    (OLD_UBRAT_MEMORY, NEW_UBRAT_MEMORY),
    (OLD_SOUL_MEMORY_INSTR, NEW_SOUL_MEMORY_INSTR),
    (OLD_MEM_HANDLING, NEW_MEM_HANDLING),
]

REPLACE_ALL = [
]


def main():
    if not TARGET.exists():
        print(f"⚠ не найден {TARGET} — запускай из корня репо")
        sys.exit(1)
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        print(f"✓ {MARKER} уже стоит в {TARGET} — патч не нужен")
        return
    for old, new in REPLACEMENTS:
        if old not in text:
            print("⚠ не нашёл кусок для замены — файл изменился с момента патча:")
            print(old[:200])
            sys.exit(1)
        if text.count(old) > 1:
            print("⚠ кусок встречается больше одного раза — небезопасно патчить:")
            print(old[:200])
            sys.exit(1)
        text = text.replace(old, new, 1)
    for old, new in REPLACE_ALL:
        if old not in text:
            print("⚠ не нашёл кусок для повсеместной замены — файл изменился:")
            print(old[:200])
            sys.exit(1)
        text = text.replace(old, new)
    bak = TARGET.with_suffix(TARGET.suffix + ".bak_mayak_request")
    if not bak.exists():
        bak.write_text(TARGET.read_text(encoding="utf-8"), encoding="utf-8")
    TARGET.write_text(text, encoding="utf-8")
    print(f"✓ пропатчено: {TARGET} (бэкап: {bak})")


if __name__ == "__main__":
    main()
