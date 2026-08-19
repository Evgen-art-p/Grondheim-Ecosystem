# -*- coding: utf-8 -*-
"""
ruki_zhitelyu_doma.py · MARKER: RUKI_DOMA_V1

ЧЕГО НЕ БЫЛО У ЖИТЕЛЯ ДОМА
─────────────────────────
Рук в кабинете жителя не было НИ ОДНОЙ. Он мог выйти к Маяку строкой
MAYAK_REQUEST — и всё. Попросить картинку, заглянуть в учебник, по
которому его учили, — нечем.

Получилось несуразно: трейдер на работе может посмотреть рисунок из
книги, ученик в Академии теперь тоже, а дома тот же самый человек —
нет. Хотя дома он как раз и разбирает, думает, вспоминает.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
Даёт жителю дома те же две руки:

    uchebnik("приседающий бар")   — показать рисунок из учебника
    chemu_uchili()                — какие дисциплины есть в Академии

Он просит сам и ВИДИТ картинку — она досылается в разговор отдельным
сообщением, как у трейдера и ученика.

ПОЧЕМУ ИМЕННО ЭТИ РУКИ, А НЕ ВСЕ
────────────────────────────────
Руки трейдера (стол, растяжка, крайние точки) дома не нужны и были бы
враньём: дома человек не за рабочим инструментом. А учебник — его
собственная учёба, она с ним везде: жил, учился, помнит.

Выход к Маяку не трогаю: он там уже есть и работает своим приёмом.
Ломать рабочее ради единообразия не буду.

Учебник общий на весь город — тот же `Биржа/uchebnik.py`, что
сканирует дисциплины. Положишь новую книгу — увидят все трое: житель,
ученик, трейдер.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py ruki_zhitelyu_doma.py   (или --suho)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "RUKI_DOMA_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "жители" / "ui_zhitel.py").exists()
            and (p / "main.py").exists())


def nayti_koren() -> Path:
    zdes = Path(__file__).resolve().parent
    for kand in (zdes, Path.cwd(), *zdes.parents):
        if _eto_koren(kand):
            return kand
    kandidaty = []
    for baza in (zdes.parent, Path.cwd().parent):
        if not baza.is_dir():
            continue
        for d in baza.iterdir():
            if d.is_dir() and _eto_koren(d) and d not in kandidaty:
                kandidaty.append(d)
    if len(kandidaty) == 1:
        if input(f"Нашёл город здесь:\n  {kandidaty[0]}\nЭтот? [Enter=да] "
                 ).strip().lower() in ("", "y", "д", "да"):
            return kandidaty[0]
    elif len(kandidaty) > 1:
        print("Нашёл несколько городов:")
        for i, d in enumerate(kandidaty, 1):
            print(f"  {i}. {d}")
        nom = input("Какой? номер: ").strip()
        if nom.isdigit() and 1 <= int(nom) <= len(kandidaty):
            return kandidaty[int(nom) - 1]
    put = input("Не нашёл сам. Перетащи сюда папку репо и нажми Enter:\n> ")
    p = Path(put.strip().strip('"').strip("'"))
    if _eto_koren(p):
        return p
    print("✗ Это не корень репо")
    sys.exit(1)


ST = '''    headers = {"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"}
    payload = {"model": use_model, "messages": messages}
    try:
        async with httpx.AsyncClient(timeout=120, proxy=PROXY_URL) as client:
            r = await client.post("https://openrouter.ai/api/v1/chat/completions",
                                  headers=headers, json=payload)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠ Ошибка вызова {model or use_model}: {e}"'''

NOV = '''    headers = {"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"}
    messages = list(messages)

    # RUKI_DOMA_V1: рук у жителя дома не было НИ ОДНОЙ — только выход
    # к Маяку строкой. Вышло несуразно: трейдер на работе может
    # посмотреть рисунок из книги, ученик в Академии тоже, а дома тот
    # же человек — нет. Хотя дома он как раз и думает.
    # Даём только учебник: рабочие руки (стол, растяжка) дома были бы
    # враньём — человек не за инструментом. А учёба с ним везде.
    ruki_shema, ruki = _ruki_doma()
    for _krug in range(5):
        payload = {"model": use_model, "messages": messages}
        if ruki_shema and _krug < 4:
            payload["tools"] = ruki_shema
            payload["tool_choice"] = "auto"
        try:
            async with httpx.AsyncClient(timeout=120, proxy=PROXY_URL) as client:
                r = await client.post("https://openrouter.ai/api/v1/chat/completions",
                                      headers=headers, json=payload)
                r.raise_for_status()
                msg = r.json()["choices"][0]["message"]
        except Exception as e:
            return f"⚠ Ошибка вызова {model or use_model}: {e}"

        if not msg.get("tool_calls"):
            return msg.get("content") or ""

        messages.append({"role": "assistant",
                         "content": msg.get("content") or "",
                         "tool_calls": msg["tool_calls"]})
        for tc in msg["tool_calls"]:
            imya = tc["function"]["name"]
            try:
                args = json.loads(tc["function"].get("arguments", "{}"))
            except Exception:
                args = {}
            ruka = ruki.get(imya)
            otvet = str(ruka(args)) if ruka else f"такой руки нет: {imya}"
            print(f"[ЖИТЕЛЬ] 🖐 {imya}({args})")
            messages.append({"role": "tool", "tool_call_id": tc["id"],
                             "content": otvet})
            if otvet.startswith("[КАДР: "):
                try:
                    import base64 as _b64
                    _p = Path(otvet[7:otvet.index("]")])
                    if _p.exists():
                        _b = _b64.b64encode(_p.read_bytes()).decode("ascii")
                        _mime = ("image/png" if _p.suffix.lower() == ".png"
                                 else "image/jpeg")
                        messages.append({"role": "user", "content": [
                            {"type": "image_url", "image_url": {
                                "url": f"data:{_mime};base64,{_b}"}},
                            {"type": "text",
                             "text": "Вот рисунок, который ты попросил(а)."}]})
                        print(f"[ЖИТЕЛЬ] 🖼 показан {_p.name}")
                except Exception as _e:
                    print(f"[ЖИТЕЛЬ] картинка не дошла: {_e}")
    return "⚠ разговор с руками не сошёлся"


def _ruki_doma():
    """(схема, руки) — учебник Академии. Второго не заводим: тот же
    Биржа/uchebnik.py, что сканирует дисциплины. Новая книга — увидят
    все трое: житель, ученик, трейдер."""
    try:
        _repo = Path(__file__).resolve().parent.parent
        if str(_repo / "Биржа") not in sys.path:
            sys.path.insert(0, str(_repo / "Биржа"))
        import uchebnik as _u
    except Exception as e:
        print(f"[ЖИТЕЛЬ] учебник не подключился: {e}")
        return None, {}

    shema = [
        {"type": "function", "function": {
            "name": "uchebnik",
            "description": (
                "ПОКАЗАТЬ рисунок из книг, по которым ты учился(ась) в "
                "Академии. Скажи тему словами: «приседающий бар», «фрактал», "
                "«волны AO». Ты УВИДИШЬ сам рисунок и подпись автора. Проси, "
                "когда хочешь свериться с книгой, а не вспоминать по памяти."),
            "parameters": {"type": "object", "properties": {
                "о_чём": {"type": "string", "description": "тема словами"},
                "дисциплина": {"type": "string",
                               "description": "необязательно: сузить поиск"}},
                "required": ["о_чём"]}}},
        {"type": "function", "function": {
            "name": "chemu_uchili",
            "description": "Какие дисциплины и сколько рисунков есть.",
            "parameters": {"type": "object", "properties": {},
                           "required": []}}},
    ]

    def _pokazat(args):
        o = str(args.get("о_чём", "")).strip()
        tema = str(args.get("дисциплина", "")).strip()
        try:
            nashlos = _u.nayti(o, skolko=1, tema=tema)
        except Exception as e:
            return f"учебник не открылся: {e}"
        if not nashlos:
            return f"по «{o}» рисунка не нашёл. Что есть:\\n{_u.temy()}"
        p, t, glava, podpis = nashlos[0]
        hvost = f" · {glava}" if glava else ""
        podp = f"\\nподпись автора: {podpis}" if podpis else ""
        return f"[КАДР: {p}] учебник · {t}{hvost} · {p.name}{podp}"

    return shema, {"uchebnik": _pokazat,
                   "chemu_uchili": lambda a: "=== ДИСЦИПЛИНЫ ===\\n"
                                             + _u.temy()}'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    zh = koren / "жители" / "ui_zhitel.py"
    uch = koren / "Биржа" / "uchebnik.py"

    if not uch.exists():
        print("✗ Нет Биржа/uchebnik.py — накати сперва учебник")
        return 1

    t = zh.read_text(encoding="utf-8")
    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0
    if t.count(ST) != 1:
        print(f"✗ вызов LLM найден {t.count(ST)} раз — жду ровно один")
        return 1

    novyy = t.replace(ST, NOV, 1) + f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ после правки не разбирается: {e}")
        return 1

    if SUHO:
        print("· правка готова (сухой прогон)")
        return 0

    bak = zh.with_suffix(f".py.bak_ruki_doma_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(zh, bak)
    zh.write_text(novyy, encoding="utf-8")
    print(f"✓ житель получил руки (копия: {bak.name})")

    import py_compile
    try:
        py_compile.compile(str(zh), doraise=True)
        print("✓ компилируется")
    except Exception as e:
        print(f"✗ НЕ компилируется: {e}")
        return 1

    print("\nТеперь дома житель может сказать «покажи фрактал из")
    print("учебника» — и УВИДЕТЬ рисунок. В консоли: [ЖИТЕЛЬ] 🖐 🖼")
    print("\nКруг замкнулся: учебник доступен ученику в Академии,")
    print("трейдеру на работе и жителю дома — одному и тому же человеку")
    print("везде, где он бывает.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
