# PATCH_PROXY_VEZDE_V1
"""
PATCH_PROXY_VEZDE_V1 -- чинит мой собственный недосмотр: во ВСЕХ
местах, которые я добавлял в этой сессии, httpx.AsyncClient() ходил
БЕЗ прокси, хотя весь остальной город (call_zhitel_llm, call_brat_llm,
bibliotekar.sprosit, khranitel_arkhiva.sprosit, rektor.sprosit) всегда
читает PROXY_URL из .env и передаёт его. Без прокси OpenRouter из
некоторых регионов честно отвечает 403 Forbidden -- это не проблема
ключа/аккаунта, это моя недоделка.

ЗАТРОНУТО:
  1. Академия/ui_rektor.py  -- do_otvet_kandidata() (ответ кандидата)
  2. Академия/ui_akademia.py -- _analiz_kartinki(), _zvat_llm_akademii(),
     _sprosit_uchenika() (три отдельных httpx-вызова)
  3. Архив/ui_arkhiv.py -- _analiz_kartinki()

Везде одна и та же правка: читаем PROXY_URL из окружения и передаём
его в httpx.AsyncClient(..., proxy=_proxy) -- тот же способ, что и в
остальном городе.

Идемпотентно: каждый из четырёх кусков патчится и проверяется отдельно
-- если маркер уже стоит в конкретном файле, тот файл пропускается
молча, остальные всё равно применяются. Бэкапы .bak по одному на файл.

Запуск из корня репо:  python patch_proxy_vezde.py
`шесть·проверено·до·корня`
"""
from pathlib import Path
import sys

MARKER = 'PATCH_PROXY_VEZDE_V1'

# ── 1. Ректор: ответ кандидата ───────────────────────────────
T1 = Path('Академия/ui_rektor.py')
OLD1 = '''        messages = [{"role": "system", "content": dusha + rol},
                   {"role": "user", "content": posledniy_rektor}]
        import httpx
        headers = {"Authorization": f"Bearer {_key}", "Content-Type": "application/json"}
        payload = {"model": state.get("model") or DEFAULT_MODEL, "messages": messages}
        try:
            async with httpx.AsyncClient(timeout=120) as client:'''
NEW1 = '''        messages = [{"role": "system", "content": dusha + rol},
                   {"role": "user", "content": posledniy_rektor}]
        import httpx
        # PATCH_PROXY_VEZDE_V1: без прокси OpenRouter честно отвечает 403
        # из некоторых регионов -- та же настройка, что и в остальном городе.
        _proxy = os.getenv("PROXY_URL", "") or None
        headers = {"Authorization": f"Bearer {_key}", "Content-Type": "application/json"}
        payload = {"model": state.get("model") or DEFAULT_MODEL, "messages": messages}
        try:
            async with httpx.AsyncClient(timeout=120, proxy=_proxy) as client:'''

# ── 2а. Академия: _analiz_kartinki ───────────────────────────
T2 = Path('Академия/ui_akademia.py')
OLD2A = '''    import httpx
    headers = {"Authorization": f"Bearer {_key}", "Content-Type": "application/json"}
    payload = {"model": model or DEFAULT_MODEL, "messages": messages}
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post("https://openrouter.ai/api/v1/chat/completions",
                                  headers=headers, json=payload)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠ разбор не удался: {e}"'''
NEW2A = '''    import httpx
    # PATCH_PROXY_VEZDE_V1: без прокси OpenRouter честно отвечает 403
    # из некоторых регионов -- та же настройка, что и в остальном городе.
    _proxy = os.getenv("PROXY_URL", "") or None
    headers = {"Authorization": f"Bearer {_key}", "Content-Type": "application/json"}
    payload = {"model": model or DEFAULT_MODEL, "messages": messages}
    try:
        async with httpx.AsyncClient(timeout=120, proxy=_proxy) as client:
            r = await client.post("https://openrouter.ai/api/v1/chat/completions",
                                  headers=headers, json=payload)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠ разбор не удался: {e}"'''

# ── 2б. Академия: _zvat_llm_akademii ─────────────────────────
OLD2B = '''    import httpx
    headers = {"Authorization": f"Bearer {_key}", "Content-Type": "application/json"}
    payload = {"model": model or DEFAULT_MODEL, "messages": messages}
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post("https://openrouter.ai/api/v1/chat/completions",
                                  headers=headers, json=payload)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠ не отозвался: {e}"'''
NEW2B = '''    import httpx
    # PATCH_PROXY_VEZDE_V1: без прокси OpenRouter честно отвечает 403
    # из некоторых регионов -- та же настройка, что и в остальном городе.
    _proxy = os.getenv("PROXY_URL", "") or None
    headers = {"Authorization": f"Bearer {_key}", "Content-Type": "application/json"}
    payload = {"model": model or DEFAULT_MODEL, "messages": messages}
    try:
        async with httpx.AsyncClient(timeout=120, proxy=_proxy) as client:
            r = await client.post("https://openrouter.ai/api/v1/chat/completions",
                                  headers=headers, json=payload)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠ не отозвался: {e}"'''

# ── 2в. Академия: _sprosit_uchenika (обычный чат студента) ───
OLD2C = '''        import httpx
        headers = {"Authorization": f"Bearer {_key}", "Content-Type": "application/json"}
        payload = {"model": model or DEFAULT_MODEL, "messages": messages}
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                r = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers, json=payload)
                r.raise_for_status()
                return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"⚠ не отозвался(лась): {e}"'''
NEW2C = '''        import httpx
        # PATCH_PROXY_VEZDE_V1: без прокси OpenRouter честно отвечает 403
        # из некоторых регионов -- та же настройка, что и в остальном городе.
        _proxy = os.getenv("PROXY_URL", "") or None
        headers = {"Authorization": f"Bearer {_key}", "Content-Type": "application/json"}
        payload = {"model": model or DEFAULT_MODEL, "messages": messages}
        try:
            async with httpx.AsyncClient(timeout=120, proxy=_proxy) as client:
                r = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers, json=payload)
                r.raise_for_status()
                return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"⚠ не отозвался(лась): {e}"'''

# ── 3. Архив: _analiz_kartinki ───────────────────────────────
T3 = Path('Архив/ui_arkhiv.py')
OLD3 = '''    import httpx
    headers = {"Authorization": f"Bearer {_key}", "Content-Type": "application/json"}
    payload = {"model": model or DEFAULT_MODEL, "messages": messages}
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post("https://openrouter.ai/api/v1/chat/completions",
                                  headers=headers, json=payload)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠ разбор не удался: {e}"'''
NEW3 = '''    import httpx
    # PATCH_PROXY_VEZDE_V1: без прокси OpenRouter честно отвечает 403
    # из некоторых регионов -- та же настройка, что и в остальном городе.
    _proxy = os.getenv("PROXY_URL", "") or None
    headers = {"Authorization": f"Bearer {_key}", "Content-Type": "application/json"}
    payload = {"model": model or DEFAULT_MODEL, "messages": messages}
    try:
        async with httpx.AsyncClient(timeout=120, proxy=_proxy) as client:
            r = await client.post("https://openrouter.ai/api/v1/chat/completions",
                                  headers=headers, json=payload)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠ разбор не удался: {e}"'''


def _primenit_fajl(target: Path, marker: str, kuski: list, bak_suffix: str):
    if not target.exists():
        print(f"⚠ не найден {target} — запускай из корня репо")
        return
    text = target.read_text(encoding="utf-8")
    if marker in text:
        print(f"✓ {marker} уже стоит в {target} — патч не нужен")
        return
    bak = target.with_suffix(target.suffix + bak_suffix)
    if not bak.exists():
        bak.write_text(text, encoding="utf-8")
    izmenilos = False
    for old, new, opisanie in kuski:
        text2 = target.read_text(encoding="utf-8")
        if old not in text2:
            print(f"⚠ {target}: не нашёл кусок для «{opisanie}» — файл изменился, пропускаю его")
            continue
        if text2.count(old) > 1:
            print(f"⚠ {target}: кусок «{opisanie}» встречается больше одного раза — пропускаю")
            continue
        text2 = text2.replace(old, new, 1)
        target.write_text(text2, encoding="utf-8")
        print(f"✓ {target}: {opisanie} — пропатчено")
        izmenilos = True
    if not izmenilos:
        print(f"⚠ {target}: ни один кусок не наложился")


def main():
    _primenit_fajl(T1, MARKER, [(OLD1, NEW1, "ответ кандидата")], ".bak_proxy_vezde")
    _primenit_fajl(T2, MARKER, [
        (OLD2A, NEW2A, "_analiz_kartinki"),
        (OLD2B, NEW2B, "_zvat_llm_akademii"),
        (OLD2C, NEW2C, "_sprosit_uchenika"),
    ], ".bak_proxy_vezde")
    _primenit_fajl(T3, MARKER, [(OLD3, NEW3, "_analiz_kartinki")], ".bak_proxy_vezde")


if __name__ == "__main__":
    main()
