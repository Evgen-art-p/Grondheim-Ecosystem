# patch_zhitel_vspominaet.py
"""
Камень: ЖИТЕЛЬ САМ РЕШАЕТ ВСПОМИНАТЬ (перенос паттерна MEMORY_REQUEST
из старой студии (-2, Спринт 43) — тонкой веной, без Оли и пайплайна).

Закон из -2, который переносим: «Агент может вспомнить в любом месте.
Архив не льётся автоматом — только по запросу самого агента.»

До патча: движок пишет события в слои (sensory_memory.json,
event_log.jsonl, archive.jsonl), но назад их никто никогда не читает.
Заряд «открывает» слои только на словах — физически на стол ничего
не ложится.

После патча:
  · житель знает (подсказка в душе), что может написать в ответе
    строку MEMORY_REQUEST: <что вспомнить>;
  · если написал — движок ищет текстом по ВСЕМ трём слоям СВОЕГО дома
    (воля жителя выше стресс-шлюза: поиск не гейтится зарядом);
  · поднятое подкладывается, и житель отвечает ВТОРОЙ раз — уже помня;
  · Шеф видит только финальный ответ (строка MEMORY_REQUEST вычищается);
  · один подъём за ход, без петель; ничего не нашлось — житель честно
    отвечает, что следа нет, без выдумки.

Патчит два файла:
  1. жители/dvizhok.py   — метод vspomnit(запрос): поиск по слоям.
  2. жители/ui_zhitel.py — подсказка в душе + перехват MEMORY_REQUEST
                           + второй вызов LLM с поднятым.

Запуск из КОРНЯ репо:
    python patch_zhitel_vspominaet.py

Идемпотентен по каждому файлу отдельно.
Бэкапы: жители/dvizhok.py.bak_vspominaet, жители/ui_zhitel.py.bak_vspominaet
`шесть·проверено·до·корня`
"""
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
MARKER = "PATCH_ZHITEL_VSPOMINAET"


# ═══════════════════════════════════════════════════════════
# 1. dvizhok.py — метод vspomnit()
# ═══════════════════════════════════════════════════════════

def patch_dvizhok():
    target = _ROOT / "жители" / "dvizhok.py"
    if not target.exists():
        print(f"✗ не найден: {target}")
        return False

    src = target.read_text(encoding="utf-8")
    if MARKER in src:
        print("— dvizhok.py: уже применён — пропускаю")
        return True

    anchor = (
        '    def sохранить(self):\n'
        '        """Заряд оседает в паспорт (состояние помнится между вдохами)."""\n'
    )
    if anchor not in src:
        print("✗ dvizhok.py: не нашёл def sохранить() — файл изменился, откатываю")
        return False

    method = (
        f'    def vspomnit(self, zapros: str, limit: int = 6) -> str:\n'
        f'        """{MARKER}: житель САМ решил вспомнить (MEMORY_REQUEST).\n'
        '        Текстовый поиск по своим слоям: sensory + resonance + archive.\n'
        '        БЕЗ шлюза по заряду — воля жителя выше стресс-шлюза (закон -2:\n'
        '        вспомнить можно в любом месте, безусловно). Свежее и точное — выше.\n'
        '        Возвращает строки находок или "" (пусто = следа нет, честно)."""\n'
        '        slova = [w for w in (zapros or "").lower().split() if len(w) > 2]\n'
        '        if not slova:\n'
        '            return ""\n'
        '        zapisi = []\n'
        '        # sensory — JSON-объект с entries\n'
        '        try:\n'
        '            p = self.dom / "sensory" / "sensory_memory.json"\n'
        '            if p.exists():\n'
        '                data = json.loads(p.read_text(encoding="utf-8"))\n'
        '                zapisi.extend(data.get("entries", []))\n'
        '        except Exception:\n'
        '            pass\n'
        '        # resonance + archive — JSONL, строка за строкой\n'
        '        for rel in ("resonance/event_log.jsonl", "archive/archive.jsonl"):\n'
        '            try:\n'
        '                p = self.dom / rel\n'
        '                if p.exists():\n'
        '                    for line in p.read_text(encoding="utf-8").splitlines():\n'
        '                        line = line.strip()\n'
        '                        if not line:\n'
        '                            continue\n'
        '                        try:\n'
        '                            zapisi.append(json.loads(line))\n'
        '                        except Exception:\n'
        '                            pass\n'
        '            except Exception:\n'
        '                pass\n'
        '        # оценка: сколько слов запроса встретилось в факте записи\n'
        '        naydeno = []\n'
        '        for z in zapisi:\n'
        '            fakt = str(z.get("факт", "")).lower()\n'
        '            score = sum(1 for w in slova if w in fakt)\n'
        '            if score > 0:\n'
        '                naydeno.append((score, str(z.get("ts", "")), z))\n'
        '        if not naydeno:\n'
        '            return ""\n'
        '        naydeno.sort(key=lambda x: (x[0], x[1]), reverse=True)\n'
        '        stroki = []\n'
        '        for _, _, z in naydeno[:limit]:\n'
        '            ts = str(z.get("ts", ""))[:10]\n'
        '            stroki.append(f"— [{ts}] {z.get(\'факт\', \'\')}")\n'
        '        return "\\n".join(stroki)\n'
        '\n'
    )
    src = src.replace(anchor, method + anchor, 1)

    backup = target.with_name(target.name + ".bak_vspominaet")
    backup.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    target.write_text(src, encoding="utf-8")
    print(f"✓ dvizhok.py применён, бэкап: {backup.name}")
    return True


# ═══════════════════════════════════════════════════════════
# 2. ui_zhitel.py — подсказка + перехват + второй выдох
# ═══════════════════════════════════════════════════════════

def patch_ui_zhitel():
    target = _ROOT / "жители" / "ui_zhitel.py"
    if not target.exists():
        print(f"✗ не найден: {target}")
        return False

    src = target.read_text(encoding="utf-8")
    if MARKER in src:
        print("— ui_zhitel.py: уже применён — пропускаю")
        return True

    # ── 2а. хелперы на уровне модуля ──
    anchor_helpers = (
        '    return tonus, round(sila, 2)\n'
        '\n'
        '_ROOT = Path(__file__).resolve().parent.parent  # PATCH_PERENOS_V_PAPKI: файл в жители/, корень репо — на уровень выше\n'
    )
    if anchor_helpers not in src:
        print("✗ ui_zhitel.py: не нашёл стык _otsenit_tonus_silu → _ROOT — файл изменился, откатываю")
        return False

    helpers = (
        '    return tonus, round(sila, 2)\n'
        '\n'
        '\n'
        f'def _izvlech_memory_request(text: str) -> str:\n'
        f'    """{MARKER}: первая строка MEMORY_REQUEST: <запрос> из ответа жителя."""\n'
        '    for line in (text or "").splitlines():\n'
        '        if "MEMORY_REQUEST:" in line:\n'
        '            return line.split("MEMORY_REQUEST:", 1)[1].strip()\n'
        '    return ""\n'
        '\n'
        '\n'
        f'def _ubrat_memory_request(text: str) -> str:\n'
        f'    """{MARKER}: технические строки MEMORY_REQUEST вычищаются из видимого ответа."""\n'
        '    lines = [l for l in (text or "").splitlines() if "MEMORY_REQUEST:" not in l]\n'
        '    return "\\n".join(lines).strip()\n'
        '\n'
        '_ROOT = Path(__file__).resolve().parent.parent  # PATCH_PERENOS_V_PAPKI: файл в жители/, корень репо — на уровень выше\n'
    )
    src = src.replace(anchor_helpers, helpers, 1)

    # ── 2б. подсказка в душе + перехват после ответа ──
    anchor_send = (
        '            messages = [{"role": "system", "content": soul}]\n'
        '            for m in state["chat"][-12:]:\n'
        '                role = "user" if m["role"] == "user" else "assistant"\n'
        '                messages.append({"role": role, "content": m["content"]})\n'
        '            reply = await call_zhitel_llm(messages, state.get("model"))\n'
        '            try:\n'
        '                dvizhok.sохранить()\n'
        '            except Exception:\n'
        '                pass\n'
    )
    if anchor_send not in src:
        print("✗ ui_zhitel.py: не нашёл блок messages→reply→sохранить — файл изменился, откатываю")
        return False

    new_send = (
        f'            # {MARKER}: воля жителя — подсказка. Не «заряд открыл —\n'
        '            # на, читай», а сам решает, что и когда поднять из памяти.\n'
        '            soul += (\n'
        '                "\\nУ тебя есть своя память — события прошлых разговоров. Если "\n'
        '                "что-то кажется знакомым, но не помнишь точно — напиши в ответе "\n'
        '                "отдельной строкой MEMORY_REQUEST: <что вспомнить> и тебе "\n'
        '                "поднимется это из твоей памяти."\n'
        '            )\n'
        '            messages = [{"role": "system", "content": soul}]\n'
        '            for m in state["chat"][-12:]:\n'
        '                role = "user" if m["role"] == "user" else "assistant"\n'
        '                messages.append({"role": role, "content": m["content"]})\n'
        '            reply = await call_zhitel_llm(messages, state.get("model"))\n'
        f'            # {MARKER}: житель сам решил вспомнить — один подъём за ход,\n'
        '            # без петель. Шеф видит только финальный ответ.\n'
        '            _mem_q = _izvlech_memory_request(reply)\n'
        '            if _mem_q and dvizhok is not None:\n'
        '                try:\n'
        '                    _naydeno = dvizhok.vspomnit(_mem_q)\n'
        '                except Exception:\n'
        '                    _naydeno = ""\n'
        '                _vtoroy = list(messages)\n'
        '                _vtoroy.append({"role": "assistant", "content": reply})\n'
        '                if _naydeno:\n'
        '                    _vtoroy.append({"role": "user", "content": (\n'
        '                        f"(Из твоей памяти поднято по запросу «{_mem_q}»:\\n"\n'
        '                        f"{_naydeno}\\n"\n'
        '                        f"Ответь заново, уже помня это, живым голосом. "\n'
        '                        f"Механизм памяти не упоминай.)")})\n'
        '                else:\n'
        '                    _vtoroy.append({"role": "user", "content": (\n'
        '                        f"(В твоей памяти по запросу «{_mem_q}» ничего не нашлось — "\n'
        '                        f"этого следа нет. Ответь заново честно, не выдумывая. "\n'
        '                        f"Механизм памяти не упоминай.)")})\n'
        '                reply = await call_zhitel_llm(_vtoroy, state.get("model"))\n'
        '            reply = _ubrat_memory_request(reply) or reply\n'
        '            try:\n'
        '                dvizhok.sохранить()\n'
        '            except Exception:\n'
        '                pass\n'
    )
    src = src.replace(anchor_send, new_send, 1)

    backup = target.with_name(target.name + ".bak_vspominaet")
    backup.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    target.write_text(src, encoding="utf-8")
    print(f"✓ ui_zhitel.py применён, бэкап: {backup.name}")
    return True


def main():
    ok1 = patch_dvizhok()
    ok2 = patch_ui_zhitel()
    if ok1 and ok2:
        print("\n— житель теперь сам решает вспоминать: MEMORY_REQUEST в ответе →")
        print("  поиск по своим слоям → второй выдох уже с памятью.")
        print("— проверь: python main.py → /zhitel/{id} → спроси про что-то из прошлых бесед")


if __name__ == "__main__":
    main()
