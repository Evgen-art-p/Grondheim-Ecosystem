# PATCH_PAMYAT_VEZDE_V1
"""
PATCH_PAMYAT_VEZDE_V1 -- слово Шефа: "всё должно в память отпечаток
вносить". Нашлось ПЯТЬ мест, где житель говорит своим голосом, но
ничего не оседает в его личную память (dvizhok):

  1. Библиотекарь (Академия/bibliotekar.py, sprosit())
  2. Хранитель Архива (Архив/khranitel_arkhiva.py, sprosit())
  3. Ректор -- сам, когда говорит с Шефом (Академия/rektor.py, sprosit())
  4. Кандидат на собеседовании -- её собственный ответ
     (Академия/ui_rektor.py, do_otvet_kandidata(), добавлена
     PATCH_REKTOR_KANDIDAT_GOLOS_V1)
  5. Обычный чат со студентом в Академии
     (Академия/ui_akademia.py, send_message())

ОДИН ПРИНЦИП ВЕЗДЕ: после того, как получен настоящий ответ (не
ошибка), житель ПРОЖИВАЕТ разговор через dvizhok -- vdoh(kontekst=
"работа" для постов / "общение" для остального) -> vydoh_stol(fakt=
вопрос+ответ) -> sохранить(). Не dopisat_vyvod -- это сырой опыт,
не готовый вывод; если Шеф захочет его когда-нибудь осмыслить в
метку -- для этого уже есть "🪞 Осмыслить" у жителя/студента.

Требует: patch_rektor_kandidat_golos.py (для файла 4) уже применён.
Остальные (1,2,3,5) независимы от других патчей.

Идемпотентно: каждый из пяти кусков патчится и проверяется отдельно
-- если маркер уже стоит в конкретном файле, тот файл пропускается
молча, остальные всё равно применяются. Бэкапы .bak по одному на
файл, делаются один раз.

Запуск из корня репо:  python patch_pamyat_vezde.py
`шесть·проверено·до·корня`
"""
from pathlib import Path
import sys

MARKER = 'PATCH_PAMYAT_VEZDE_V1'

# ── 1. Библиотекарь ──────────────────────────────────────────
T1 = Path('Академия/bibliotekar.py')
OLD1 = '''    try:
        async with httpx.AsyncClient(timeout=120, proxy=PROXY_URL) as client:
            r = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers, json=payload)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠ Библиотекарь не отозвался: {e}"'''
NEW1 = '''    try:
        async with httpx.AsyncClient(timeout=120, proxy=PROXY_URL) as client:
            r = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers, json=payload)
            r.raise_for_status()
            _otvet = r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠ Библиотекарь не отозвался: {e}"

    # PATCH_PAMYAT_VEZDE_V1: разговор на посту -- отпечаток в личной
    # памяти того, кто сейчас сидит библиотекарем. Пост не обезличивает
    # прожитое resident'ом. Свой sys.path -- модуль не подключает
    # жители/ в общем импорте наверху (только ГОРОД).
    try:
        _repo_pm = Path(__file__).resolve().parent.parent
        _zh_pm = _repo_pm / "жители"
        if str(_zh_pm) not in sys.path:
            sys.path.insert(0, str(_zh_pm))
        import rezidenty as _rez_pm
        _dom_pm = _rez_pm.dom_zhitelya(imya)
        if _dom_pm:
            from dvizhok import Dvizhok as _Dvizhok_pm
            _dv_pm = _Dvizhok_pm(_dom_pm)
            _vdoh_pm = _dv_pm.vdoh(kontekst="работа", sila=0.5, svezhest=1.0, tonus="ровно")
            _dv_pm.vydoh_stol(
                fakt=f"[Библиотека] {dlya_kogo} спросил(а): {vopros}\\nЯ ответил(а): {_otvet}",
                vdoh_result=_vdoh_pm)
            _dv_pm.sохранить()
    except Exception:
        pass
    return _otvet'''

# ── 2. Хранитель Архива ──────────────────────────────────────
T2 = Path('Архив/khranitel_arkhiva.py')
OLD2 = '''    try:
        async with httpx.AsyncClient(timeout=120, proxy=PROXY_URL) as client:
            r = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers, json=payload)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠ Хранитель не отозвался: {e}"'''
NEW2 = '''    try:
        async with httpx.AsyncClient(timeout=120, proxy=PROXY_URL) as client:
            r = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers, json=payload)
            r.raise_for_status()
            _otvet = r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠ Хранитель не отозвался: {e}"

    # PATCH_PAMYAT_VEZDE_V1: разговор на посту -- отпечаток в личной
    # памяти того, кто сейчас сидит Хранителем. Свой sys.path -- модуль
    # не подключает жители/ в общем импорте наверху (только ГОРОД).
    try:
        _repo_pm = Path(__file__).resolve().parent.parent
        _zh_pm = _repo_pm / "жители"
        if str(_zh_pm) not in sys.path:
            sys.path.insert(0, str(_zh_pm))
        import rezidenty as _rez_pm
        _dom_pm = _rez_pm.dom_zhitelya(imya)
        if _dom_pm:
            from dvizhok import Dvizhok as _Dvizhok_pm
            _dv_pm = _Dvizhok_pm(_dom_pm)
            _vdoh_pm = _dv_pm.vdoh(kontekst="работа", sila=0.5, svezhest=1.0, tonus="ровно")
            _dv_pm.vydoh_stol(
                fakt=f"[Архив] {dlya_kogo} спросил(а): {vopros}\\nЯ ответил(а): {_otvet}",
                vdoh_result=_vdoh_pm)
            _dv_pm.sохранить()
    except Exception:
        pass
    return _otvet'''

# ── 3. Ректор сам ─────────────────────────────────────────────
T3 = Path('Академия/rektor.py')
OLD3 = '''    try:
        async with httpx.AsyncClient(timeout=120, proxy=PROXY_URL) as client:
            r = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers, json=payload)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠ Ректор не отозвался: {e}"'''
NEW3 = '''    try:
        async with httpx.AsyncClient(timeout=120, proxy=PROXY_URL) as client:
            r = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers, json=payload)
            r.raise_for_status()
            _otvet = r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠ Ректор не отозвался: {e}"

    # PATCH_PAMYAT_VEZDE_V1: разговор на посту -- отпечаток в личной
    # памяти того, кто сейчас сидит Ректором.
    try:
        import rezidenty as _rez_pm
        _dom_pm = _rez_pm.dom_zhitelya(imya)
        if _dom_pm:
            from dvizhok import Dvizhok as _Dvizhok_pm
            _dv_pm = _Dvizhok_pm(_dom_pm)
            _vdoh_pm = _dv_pm.vdoh(kontekst="работа", sila=0.5, svezhest=1.0, tonus="ровно")
            _dv_pm.vydoh_stol(
                fakt=f"[Ректорская] {dlya_kogo} спросил(а): {vopros}\\nЯ ответил(а): {_otvet}",
                vdoh_result=_vdoh_pm)
            _dv_pm.sохранить()
    except Exception:
        pass
    return _otvet'''

# ── 4. Кандидат на собеседовании ─────────────────────────────
T4 = Path('Академия/ui_rektor.py')
OLD4 = '''        try:
            async with httpx.AsyncClient(timeout=120) as client:
                r = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers, json=payload)
                r.raise_for_status()
                otvet = r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            otvet = f"⚠ {kandidat_imya} не отозвалась: {e}"

        state["чат"].pop()
        state["чат"].append({"role": "assistant", "кто": kandidat_imya,
                             "content": otvet})
        update_chat()'''
NEW4 = '''        try:
            async with httpx.AsyncClient(timeout=120) as client:
                r = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers, json=payload)
                r.raise_for_status()
                otvet = r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            otvet = f"⚠ {kandidat_imya} не отозвалась: {e}"

        # PATCH_PAMYAT_VEZDE_V1: собственный ответ кандидата -- отпечаток
        # в её личной памяти (сырой опыт, не готовый вывод -- метку
        # поставит "🪞 Осмыслить" отдельно, если Шеф захочет).
        if kandidat_dom and not otvet.startswith("⚠"):
            try:
                from dvizhok import Dvizhok as _Dvizhok_pm
                _dv_pm = _Dvizhok_pm(kandidat_dom)
                _vdoh_pm = _dv_pm.vdoh(kontekst="общение", sila=0.5, svezhest=1.0, tonus="ровно")
                _dv_pm.vydoh_stol(
                    fakt=f"[Собеседование] Ректор спросил: {posledniy_rektor}\\nЯ ответила: {otvet}",
                    vdoh_result=_vdoh_pm)
                _dv_pm.sохранить()
            except Exception:
                pass

        state["чат"].pop()
        state["чат"].append({"role": "assistant", "кто": kandidat_imya,
                             "content": otvet})
        update_chat()'''

# ── 5. Чат со студентом в Академии ───────────────────────────
T5 = Path('Академия/ui_akademia.py')
OLD5 = '''        try:
            _otvet = await _sprosit_uchenika(m["дом"], msg, state["чат"][:-2],
                                             state.get("model"))
        except Exception as _e:
            _otvet = f"⚠ не отозвался(лась): {_e}"
        state["чат"].pop()
        state["чат"].append({"role": "assistant", "кто": m["имя"],
                             "content": _otvet})
        update_chat()'''
NEW5 = '''        try:
            _otvet = await _sprosit_uchenika(m["дом"], msg, state["чат"][:-2],
                                             state.get("model"))
        except Exception as _e:
            _otvet = f"⚠ не отозвался(лась): {_e}"

        # PATCH_PAMYAT_VEZDE_V1: разговор со студентом -- отпечаток в
        # его личной памяти (сырой опыт, не готовый вывод). Свой
        # sys.path -- на случай, если жители/ ещё не подключены (если
        # "Прочитать"/"Осмыслить" ни разу не нажимались в этой сессии).
        if m["дом"] and not _otvet.startswith("⚠"):
            try:
                _repo_pm = Path(__file__).resolve().parent.parent
                _zh_pm = _repo_pm / "жители"
                if str(_zh_pm) not in sys.path:
                    sys.path.insert(0, str(_zh_pm))
                from dvizhok import Dvizhok as _Dvizhok_pm
                _dv_pm = _Dvizhok_pm(m["дом"])
                _vdoh_pm = _dv_pm.vdoh(kontekst="общение", sila=0.5, svezhest=1.0, tonus="ровно")
                _dv_pm.vydoh_stol(
                    fakt=f"[Академия] Шеф спросил: {msg}\\nЯ ответил(а): {_otvet}",
                    vdoh_result=_vdoh_pm)
                _dv_pm.sохранить()
            except Exception:
                pass

        state["чат"].pop()
        state["чат"].append({"role": "assistant", "кто": m["имя"],
                             "content": _otvet})
        update_chat()'''

TASKS = [
    (T1, OLD1, NEW1, ".bak_pamyat_vezde"),
    (T2, OLD2, NEW2, ".bak_pamyat_vezde"),
    (T3, OLD3, NEW3, ".bak_pamyat_vezde"),
    (T4, OLD4, NEW4, ".bak_pamyat_vezde"),
    (T5, OLD5, NEW5, ".bak_pamyat_vezde"),
]


def _primenit(target: Path, old: str, new: str, bak_suffix: str):
    if not target.exists():
        print(f"⚠ не найден {target} — пропускаю")
        return
    text = target.read_text(encoding="utf-8")
    if MARKER in text:
        print(f"✓ {MARKER} уже стоит в {target} — патч не нужен")
        return
    if old not in text:
        print(f"⚠ {target}: не нашёл кусок для замены — файл изменился")
        return
    if text.count(old) > 1:
        print(f"⚠ {target}: кусок встречается больше одного раза — небезопасно")
        return
    text = text.replace(old, new, 1)
    bak = target.with_suffix(target.suffix + bak_suffix)
    if not bak.exists():
        bak.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    target.write_text(text, encoding="utf-8")
    print(f"✓ пропатчено: {target} (бэкап: {bak})")


def main():
    for target, old, new, suf in TASKS:
        _primenit(target, old, new, suf)


if __name__ == "__main__":
    main()
