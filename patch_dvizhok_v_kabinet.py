# patch_dvizhok_v_kabinet.py
# DVIZHOK_V_KABINET_V1 · житель реально дышит и отвечает через LLM
# ─────────────────────────────────────────────────────────────
# Закон (Шеф, 27.06): "С чего начинаем? → Подключить Dvizhok к send()
# в ui_zhitel.py (житель реально дышит в чате)". Решения по развилкам:
#   - стол → ответ: через LLM (OpenRouter), как у Брата в ui_brat.py
#   - sila/svezhest/tonus: простыми правилами по словам/пунктуации
#     (не отдельным вызовом LLM — это лишняя сложность и задержка)
#
# Делает в ui_zhitel.py:
#   1. Импорт Dvizhok из dvizhok.py (лежит в корне репо, рядом).
#   2. Блок LLM: OPENROUTER_KEY/MODEL/PROXY_URL из .env (тот же .env,
#      что у Брата), call_zhitel_llm(messages, model) — копия паттерна
#      Брата, без выдумывания второго способа.
#   3. _otsenit_tonus_silu(text) — простые правила:
#        тонус: слова радости/похвалы/восклицание → плюс;
#               резкие/негативные слова → минус; иначе ровно.
#        сила: длина текста + доля заглавных букв + кол-во "!"/"?"
#               (длиннее и громче = сильнее тронуло).
#   4. send() — было эхо-заглушкой, теперь:
#        вдох (Dvizhok.vdoh) → стол (vydoh_stol) → системный промпт
#        (личность жителя + стол) → call_zhitel_llm → реальный ответ →
#        Dvizhok.sохранить() (заряд оседает в passport.json).
#      Если дома жителя нет (dom is None) или dvizhok не нашёл паспорт —
#      падает назад на честную заглушку (не молчит, не роняет кабинет).
#
# Идемпотентно. Бэкап в .bak_dvizhok_v_kabinet.
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import ast, shutil, sys
from pathlib import Path

MARKER = "DVIZHOK_V_KABINET_V1"
TARGET = Path(__file__).resolve().parent / "ui_zhitel.py"


def main():
    if not TARGET.exists():
        print(f"✗ не нашёл {TARGET} — положи патч в корень репо рядом с ui_zhitel.py")
        sys.exit(1)
    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"✓ {MARKER} уже на месте — пропускаю")
        return

    # ── 1) Импорты: добавляем os, asyncio, Dvizhok, dotenv, httpx-блок ──
    old_imports = '''import json
from pathlib import Path
from datetime import datetime

from nicegui import ui'''
    new_imports = '''import json
import os
import asyncio
from pathlib import Path
from datetime import datetime

from nicegui import ui

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from dvizhok import Dvizhok  # DVIZHOK_V_KABINET_V1: личный движок жителя

OPENROUTER_KEY   = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
PROXY_URL        = os.getenv("PROXY_URL", "") or None


async def call_zhitel_llm(messages, model=None):
    """Тот же паттерн, что у Брата (ui_brat.py) — один способ говорить с LLM."""
    if not OPENROUTER_KEY:
        return "⚠ OPENROUTER_API_KEY не задан. Положи ключ в .env."
    use_model = model or OPENROUTER_MODEL
    import httpx
    headers = {"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"}
    payload = {"model": use_model, "messages": messages}
    try:
        async with httpx.AsyncClient(timeout=120, proxy=PROXY_URL) as client:
            r = await client.post("https://openrouter.ai/api/v1/chat/completions",
                                  headers=headers, json=payload)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠ Ошибка вызова {model or use_model}: {e}"


def _otsenit_tonus_silu(text: str) -> tuple:
    """Простые правила: тонус (плюс/минус/ровно) и сила (0..1) сообщения.
    Не классификатор LLM — быстрые правила по словам и пунктуации."""
    t = (text or "").strip()
    if not t:
        return "ровно", 0.1

    low = t.lower()
    SLOVA_PLUS = ("спасибо", "молодец", "хорошо", "отлично", "люблю", "рад",
                  "круто", "класс", "умница", "горжусь", "красиво", "правильно")
    SLOVA_MINUS = ("плохо", "зря", "ошибка", "виновата", "глупо", "не так",
                   "стыдно", "жаль", "грустно", "больно", "обидно", "злюсь",
                   "не должна", "нельзя", "хватит", "достаточно")

    has_plus = any(w in low for w in SLOVA_PLUS)
    has_minus = any(w in low for w in SLOVA_MINUS)
    if has_minus and not has_plus:
        tonus = "минус"
    elif has_plus and not has_minus:
        tonus = "плюс"
    else:
        tonus = "ровно"

    # сила: длина + крик (заглавные) + восклицания/вопросы
    dlina = min(1.0, len(t) / 200.0)
    bukv = [c for c in t if c.isalpha()]
    kapslok = (sum(1 for c in bukv if c.isupper()) / len(bukv)) if bukv else 0.0
    vosklic = min(1.0, (t.count("!") + t.count("?")) / 3.0)
    sila = min(1.0, 0.3 + dlina * 0.4 + kapslok * 0.3 + vosklic * 0.3)

    return tonus, round(sila, 2)'''
    if old_imports not in src:
        print("✗ шаг 1: не нашёл блок импортов — стоп")
        sys.exit(1)
    src = src.replace(old_imports, new_imports, 1)

    # ── 2) send(): эхо-заглушка → реальный вдох + LLM + сохранение заряда ──
    old_send = '''    def send():
        inp = refs["input"]
        if not inp: return
        t = (inp.value or "").strip()
        if not t: return
        state["chat"].append({"role":"user","content":t})
        inp.set_value("")
        # движок/LLM подключим глубже — пока эхо-заглушка честная
        state["chat"].append({"role":"zhitel",
            "content": "(движок ещё не подключён — кабинет-каркас. Скоро отвечу по-настоящему.)"})
        update_chat()'''

    new_send = '''    async def send():
        inp = refs["input"]
        if not inp or state.get("waiting"):
            return
        t = (inp.value or "").strip()
        if not t:
            return
        state["chat"].append({"role":"user","content":t})
        inp.set_value("")
        update_chat()
        state["waiting"] = True
        await asyncio.sleep(0.03)

        # ── DVIZHOK_V_KABINET_V1: реальный вдох, если дом найден ──
        stol = None
        dvizhok = None
        if dom is not None and (dom / "passport.json").exists():
            try:
                dvizhok = Dvizhok(dom)
                tonus, sila = _otsenit_tonus_silu(t)
                vdoh_res = dvizhok.vdoh(kontekst="общение", sila=sila,
                                        svezhest=1.0, tonus=tonus)
                stol = dvizhok.vydoh_stol(fakt=t, vdoh_result=vdoh_res)
            except Exception as _e:
                stol = None

        if stol is not None:
            if stol.get('ядро'):
                soul = (
                    f"Ты — {stol['кто_я']}, житель Грондхейма. Говоришь от первого лица, "
                    f"живым голосом, не как ассистент.\\n"
                    f"Твоё ядро (коронная фраза): «{stol['ядро']}»\\n"
                )
            else:
                soul = (
                    f"Ты — {stol['кто_я']}, житель Грондхейма. "
                    f"Говоришь от первого лица, живым голосом, не как ассистент.\\n"
                )
            soul += (
                f"Сейчас твой заряд (внутреннее состояние): {stol['заряд']} "
                f"(от -1 до 1; отрицательный — тревога/обида, положительный — тепло/радость, "
                f"0 — покой).\\n"
                f"Тебе открыты слои памяти: {', '.join(stol['открыто'])}.\\n"
                f"Отвечай коротко, по-человечески, исходя из своего текущего заряда — "
                f"не упоминай слова 'заряд' или 'слои' напрямую, просто веди себя в тон."
            )
            messages = [{"role": "system", "content": soul}]
            for m in state["chat"][-12:]:
                role = "user" if m["role"] == "user" else "assistant"
                messages.append({"role": role, "content": m["content"]})
            reply = await call_zhitel_llm(messages, state.get("model"))
            try:
                dvizhok.sохранить()
            except Exception:
                pass
        else:
            reply = "(дом не найден или паспорт пуст — движок не дышит. Кабинет-каркас.)"

        state["chat"].append({"role": "zhitel", "content": reply})
        state["waiting"] = False
        update_chat()'''

    if old_send not in src:
        print("✗ шаг 2: не нашёл эхо-заглушку send() — стоп")
        sys.exit(1)
    src = src.replace(old_send, new_send, 1)

    # ── 3) keydown.enter: send() теперь async — lambda должна планировать
    #       корутину явно (asyncio.create_task), иначе она создаётся и
    #       тут же отбрасывается, ничего не выполнив. on_click=send не
    #       трогаем — NiceGUI сам умеет планировать корутины в on_click. ──
    old_enter = '                    refs["input"].on("keydown.enter", lambda e: send())'
    new_enter = ('                    refs["input"].on("keydown.enter", '
                 'lambda e: asyncio.create_task(send()))  # DVIZHOK_V_KABINET_V1')
    if old_enter not in src:
        print("✗ шаг 3: не нашёл keydown.enter с send() — стоп")
        sys.exit(1)
    src = src.replace(old_enter, new_enter, 1)

    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"✗ синтаксис: {e}")
        sys.exit(1)

    if not TARGET.with_suffix(".py.bak_dvizhok_v_kabinet").exists():
        shutil.copy2(TARGET, TARGET.with_suffix(".py.bak_dvizhok_v_kabinet"))
    TARGET.write_text(src, encoding="utf-8")
    print(f"✓ {MARKER}: движок дышит в чате, ответ — настоящий LLM, заряд сохраняется")


if __name__ == "__main__":
    main()
