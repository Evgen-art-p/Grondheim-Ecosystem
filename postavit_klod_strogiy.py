# -*- coding: utf-8 -*-
# KLOD_STROGIY_V1
"""
ПАТЧ: город учится говорить со строгим провайдером.

ЧТО ЧИНИТ (три вещи, все в Биржа/llm.py)

1. ПРАВДА ОБ ОШИБКЕ.
   OpenRouter присылает ДВЕ вещи: свою короткую отписку
   («Provider returned error») и рядом, в metadata, дословную жалобу
   провайдера. Код брал только первое и выбрасывал второе — причина
   каждый раз приезжала и каждый раз стиралась. Теперь печатаем и то
   и другое, вместе с именем модели, на которой упало.

2. ПОТОЛОК ТЕМПЕРАТУРЫ.
   stress_to_temperature() выдаёт до 1.2 — это законно для Gemini
   (потолок 2.0) и незаконно для Anthropic (потолок 1.0): запрос
   разворачивают с 400 ещё на входе. Прижимаем к 1.0 ТОЛЬКО на
   Anthropic; всем остальным натура жителя достаётся как была.

3. ПУСТОЕ СЛОВО ПРИ ВЫЗОВЕ РУКИ.
   Когда трейдер зовёт руку молча, в разговор клался пустой текст
   ("" вместо слов). Gemini это глотал, Anthropic пустой текстовый
   блок не принимает. Теперь: сказал словами — кладём слова, промолчал
   — не кладём ничего. Выдуманных слов за трейдера НЕ пишем.

ЧЕГО НЕ ДЕЛАЕТ
   Не трогает логику торговли, промпты, руки и их описания. Только
   разговор с провайдером.

ЗАПУСК: двойной клик или `python postavit_klod_strogiy.py` из корня.
Идемпотентен: второй запуск скажет «уже стоит» и ничего не тронет.
"""
import ast
import py_compile
import shutil
import sys
from pathlib import Path

MARKER = "KLOD_STROGIY_V1"
BAK = ".bak_klod_strogiy"


# ── найти репо САМ ────────────────────────────────────────────────
def _est_repo(p: Path) -> bool:
    try:
        return (p / "Биржа" / "llm.py").is_file()
    except Exception:
        return False


def _sobrat_kandidatov():
    tut = Path(__file__).resolve().parent
    spisok = []
    for k in [tut, Path.cwd(), *tut.parents]:
        if _est_repo(k) and k.resolve() not in spisok:
            spisok.append(k.resolve())
    for baza in (tut, tut.parent):
        try:
            for sosed in baza.iterdir():
                if sosed.is_dir() and _est_repo(sosed):
                    r = sosed.resolve()
                    if r not in spisok:
                        spisok.append(r)
        except Exception:
            pass
    return spisok


def nayti_repo() -> Path:
    spisok = _sobrat_kandidatov()

    if len(spisok) == 1:
        print(f"Нашёл репозиторий: {spisok[0]}")
        if input("Этот? [Enter — да, n — нет]: ").strip().lower() not in ("", "y", "д"):
            spisok = []
        else:
            return spisok[0]

    if len(spisok) > 1:
        print("Нашёл несколько репозиториев:")
        for i, p in enumerate(spisok, 1):
            print(f"  {i}) {p}")
        vybor = input("Какой? [цифра, Enter — первый]: ").strip()
        if not vybor:
            return spisok[0]
        if vybor.isdigit() and 1 <= int(vybor) <= len(spisok):
            return spisok[int(vybor) - 1]

    print("\nСам не нашёл. Перетащи папку репозитория в это окно и нажми Enter.")
    ruchnoy = input("Папка: ").strip().strip('"').strip("'")
    p = Path(ruchnoy).expanduser()
    if _est_repo(p):
        return p.resolve()
    print(f"✕ По этому пути нет Биржа/llm.py: {p}")
    return None


# ── что вставляем ─────────────────────────────────────────────────
YAKOR_HELPERY = "def stress_to_temperature(stress: float = 0.0, light: float = 0.8) -> float:"

HELPERY = '''# ══ KLOD_STROGIY_V1 ═══════════════════════════════════════════════
# Строгие провайдеры (Anthropic) отказывают там, где снисходительные
# (Google) догадываются. Две мелочи ниже — вся разница.

def _polnaya_zhaloba(r) -> str:
    """Настоящая причина отказа, а не отписка OpenRouter.

    В теле ответа лежит error.message (коротко, часто бесполезно:
    «Provider returned error») и error.metadata.raw — ДОСЛОВНО то,
    что сказал провайдер. Раньше брали только первое.
    """
    try:
        d = r.json()
    except Exception:
        return (r.text or "")[:800] or f"HTTP {r.status_code}"

    err = d.get("error")
    if not isinstance(err, dict):
        return (str(err) if err else (r.text or "")[:800]) or f"HTTP {r.status_code}"

    kuski = []
    soobshchenie = str(err.get("message") or "").strip()
    if soobshchenie:
        kuski.append(soobshchenie)

    meta = err.get("metadata")
    if isinstance(meta, dict):
        if meta.get("provider_name"):
            kuski.append(f"провайдер: {meta['provider_name']}")
        if meta.get("raw"):
            kuski.append(f"дословно: {str(meta['raw'])[:700]}")
        for _k in ("reasons", "flagged_input", "provider_response"):
            if meta.get(_k):
                kuski.append(f"{_k}: {str(meta[_k])[:300]}")

    if err.get("code") is not None:
        kuski.append(f"код: {err['code']}")

    return " · ".join(kuski) or (r.text or "")[:800] or f"HTTP {r.status_code}"


def _temp_pod_model(t):
    """Потолок температуры у провайдеров разный.

    Anthropic: строго 0..1 — выше кидает 400 ещё на входе.
    Google/OpenAI: до 2.0. Натура жителя (stress_to_temperature)
    доходит до 1.2 — значит нервный трейдер на Клоде не отвечал
    ВООБЩЕ. Прижимаем только там, где это закон провайдера.
    """
    if t is None:
        return t
    try:
        model = (_CURRENT_MODEL or "").lower()
        if "anthropic" in model or "claude" in model:
            return min(float(t), 1.0)
    except Exception:
        pass
    return t


'''

# (имя, старое, новое, сколько раз ждём)
ZAMENY = [
    (
        "жалоба · руки и кадр+руки",
        """            try:
                err = r.json().get("error", {}).get("message", r.text[:300])
            except Exception:
                err = r.text[:300]
            raise RuntimeError(f"OpenRouter [{r.status_code}]: {err}")""",
        """            err = _polnaya_zhaloba(r)   # KLOD_STROGIY_V1
            print(f"[LLM] \u2715 OpenRouter [{r.status_code}] "
                  f"модель={_CURRENT_MODEL} :: {err}")
            raise RuntimeError(f"OpenRouter [{r.status_code}]: {err}")""",
        2,
    ),
    (
        "жалоба · слово и кадр",
        """        try:
            err_data = r.json()
            err_msg = err_data.get("error", {}).get("message", r.text[:300])
        except Exception:
            err_msg = r.text[:300] if r.text else f"HTTP {r.status_code}"
        raise RuntimeError(f"OpenRouter API [{r.status_code}]: {err_msg}")""",
        """        err_msg = _polnaya_zhaloba(r)   # KLOD_STROGIY_V1
        print(f"[LLM] \u2715 OpenRouter [{r.status_code}] "
              f"модель={_CURRENT_MODEL} :: {err_msg}")
        raise RuntimeError(f"OpenRouter API [{r.status_code}]: {err_msg}")""",
        2,
    ),
    (
        "потолок температуры",
        '["temperature"] = temperature',
        '["temperature"] = _temp_pod_model(temperature)   # KLOD_STROGIY_V1',
        5,
    ),
    (
        "пустое слово · руки",
        """        messages.append({
            "role": "assistant",
            "content": msg.get("content") or "",
            "tool_calls": tool_calls,
        })""",
        """        # KLOD_STROGIY_V1: сказал словами — кладём слова; промолчал —
        # не кладём ничего. Пустой текст строгий провайдер не примет,
        # а выдумывать за трейдера слова мы не будем.
        _ego_otvet = {"role": "assistant", "tool_calls": tool_calls}
        _ego_slovo = (msg.get("content") or "").strip()
        if _ego_slovo:
            _ego_otvet["content"] = _ego_slovo
        messages.append(_ego_otvet)""",
        1,
    ),
    (
        "пустое слово · кадр+руки",
        """        messages.append({"role": "assistant",
                         "content": msg.get("content") or "",
                         "tool_calls": msg["tool_calls"]})""",
        """        # KLOD_STROGIY_V1: см. выше — пустого текста в разговоре быть
        # не должно, а придуманного за трейдера тем более.
        _ego_otvet = {"role": "assistant", "tool_calls": msg["tool_calls"]}
        if _skazal_seychas:
            _ego_otvet["content"] = _skazal_seychas
        messages.append(_ego_otvet)""",
        1,
    ),
]


def pochinit(put: Path) -> bool:
    tekst = put.read_text(encoding="utf-8")

    if MARKER in tekst:
        print(f"• {put.name}: уже стоит ({MARKER}) — не трогаю.")
        return True

    # сверка якорей ДО единой правки
    bedа = False
    for imya, staroe, _novoe, zhdyom in ZAMENY:
        est = tekst.count(staroe)
        if est != zhdyom:
            print(f"✕ якорь «{imya}»: ждал {zhdyom}, нашёл {est}")
            bedа = True
    if YAKOR_HELPERY not in tekst:
        print("✕ не нашёл места для вставки помощников")
        bedа = True
    if bedа:
        print("\nФайл отличается от ожидаемого — НИЧЕГО не менял.")
        return False

    novyy = tekst.replace(YAKOR_HELPERY, HELPERY + YAKOR_HELPERY, 1)
    for imya, staroe, novoe, _zh in ZAMENY:
        novyy = novyy.replace(staroe, novoe)
        print(f"  ✓ {imya}")

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✕ после правки получился нерабочий Python: {e}")
        return False

    bak = put.with_suffix(put.suffix + BAK)
    if not bak.exists():
        shutil.copy2(put, bak)
        print(f"  ✓ бэкап: {bak.name}")
    put.write_text(novyy, encoding="utf-8")

    try:
        py_compile.compile(str(put), doraise=True)
        print(f"  ✓ {put.name} компилируется")
    except Exception as e:
        shutil.copy2(bak, put)
        print(f"✕ не компилируется, откатил из бэкапа: {e}")
        return False
    return True


def main():
    print("═══ ПАТЧ: строгий провайдер (KLOD_STROGIY_V1) ═══\n")
    repo = nayti_repo()
    if repo is None:
        return 1
    llm = repo / "Биржа" / "llm.py"
    print(f"\nПравлю: {llm}\n")
    ok = pochinit(llm)
    print("\n" + ("═══ ГОТОВО ═══" if ok else "═══ НЕ ВЫШЛО ═══"))
    if ok:
        print("Перезапусти город и повтори то, на чём падали руки.\n"
              "В логе теперь будет строка [LLM] ✕ с дословной жалобой —\n"
              "пришли её мне, если 400 останется.")
    return 0 if ok else 1


if __name__ == "__main__":
    kod = main()
    try:
        input("\nEnter — закрыть окно...")
    except Exception:
        pass
    sys.exit(kod)
