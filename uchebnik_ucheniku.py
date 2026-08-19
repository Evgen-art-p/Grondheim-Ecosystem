# -*- coding: utf-8 -*-
"""
uchebnik_ucheniku.py · MARKER: UCHEBNIK_UCHENIKU_V1

СМЕШНОЕ, ЧТО ВЫШЛО
──────────────────
Картинки Академии стали доступны ТРЕЙДЕРАМ на Бирже — и остались
недоступны УЧЕНИКУ в самой Академии. Там, где по этим рисункам и
учат, попросить рисунок было нельзя: ученику показывает Ректор, когда
сочтёт нужным, а сам он заглянуть в учебник не мог.

Шеф спросил «это только для Нины? а остальные жители?» — и оказалось,
что нужнее всего это как раз ученику.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
Даёт ученику в Академии две руки — те же, что у трейдера:

    uchebnik("приседающий бар")   — показать рисунок из учебника
    chemu_uchili()                — какие дисциплины вообще есть

Ученик просит сам и ВИДИТ картинку: она досылается в тот же разговор
отдельным сообщением, как у трейдера. Не пересказ, не описание —
сам рисунок с авторской подписью.

ПОЧЕМУ ЭТО ВАЖНО ИМЕННО ДЛЯ УЧЁБЫ
─────────────────────────────────
Наблюдение Шефа от 05.08, записанное в БИРЖА.md: «в память ложится не
картинка, а СОБСТВЕННЫЙ ТЕКСТ ученика о ней — завтра он помнит свои
слова, а не то, что видел».

Пока ученик не мог вернуться к рисунку, это было приговором: посмотрел
один раз, пересказал — и дальше живёт с пересказом. Теперь может
посмотреть снова, сравнить, поправить себя. Насмотренность перестаёт
быть однократной.

КАК УСТРОЕНО
────────────
Вызов LLM в Академии был однопроходным — без рук вовсе. Он получает
их тем же приёмом, что и везде в городе: круг «попросил → исполнили →
ответ вернулся в разговор», и метка [КАДР: путь] досылает картинку.

Учебник не дублируется: зовём тот же `Биржа/uchebnik.py`, который
сканирует дисциплины. Положишь новую книгу — увидят и ученик, и
трейдер, разом.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py uchebnik_ucheniku.py   (или --suho)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "UCHEBNIK_UCHENIKU_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "Академия" / "ui_akademia.py").exists()
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


ST = '''    _proxy = os.getenv("PROXY_URL", "") or None
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

NOV = '''    _proxy = os.getenv("PROXY_URL", "") or None
    headers = {"Authorization": f"Bearer {_key}", "Content-Type": "application/json"}
    messages = list(messages)

    # UCHEBNIK_UCHENIKU_V1: руки ученика. Картинки Академии были
    # доступны трейдерам на Бирже и НЕДОСТУПНЫ ученику в самой
    # Академии — там, где по ним и учат. Показывал Ректор, когда сочтёт
    # нужным; сам ученик заглянуть в учебник не мог.
    # Важно для учёбы: в память ложится не картинка, а его СОБСТВЕННЫЙ
    # текст о ней (наблюдение Шефа 05.08). Пока вернуться к рисунку
    # было нельзя, это был приговор: посмотрел раз, пересказал — и
    # живёшь с пересказом.
    ruki_shema, ruki = _ruki_uchenika()
    for _krug in range(5):
        payload = {"model": model or DEFAULT_MODEL, "messages": messages}
        if ruki_shema and _krug < 4:
            payload["tools"] = ruki_shema
            payload["tool_choice"] = "auto"
        try:
            async with httpx.AsyncClient(timeout=120, proxy=_proxy) as client:
                r = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers, json=payload)
                r.raise_for_status()
                msg = r.json()["choices"][0]["message"]
        except Exception as e:
            return f"⚠ не отозвался: {e}"

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
            otvet = ruka(args) if ruka else f"такой руки нет: {imya}"
            print(f"[УЧЕНИК] 🖐 {imya}({args})")
            messages.append({"role": "tool", "tool_call_id": tc["id"],
                             "content": str(otvet)})
            # метка кадра — досылаем саму КАРТИНКУ, иначе ученик
            # получит путь к файлу вместо рисунка
            if isinstance(otvet, str) and otvet.startswith("[КАДР: "):
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
                             "text": "Вот рисунок из учебника, который ты "
                                     "попросил(а). Смотри внимательно."}]})
                        print(f"[УЧЕНИК] 🖼 показан {_p.name}")
                except Exception as _e:
                    print(f"[УЧЕНИК] картинка не дошла: {_e}")
    return "⚠ разговор с руками не сошёлся"


def _ruki_uchenika():
    """(схема, руки) — учебник Академии. Не заводим второй: зовём тот
    же Биржа/uchebnik.py, что сканирует дисциплины. Положишь новую
    книгу — увидят и ученик, и трейдер, разом."""
    try:
        _repo = Path(__file__).resolve().parent.parent
        if str(_repo / "Биржа") not in sys.path:
            sys.path.insert(0, str(_repo / "Биржа"))
        import uchebnik as _u
    except Exception as e:
        print(f"[УЧЕНИК] учебник не подключился: {e}")
        return None, {}

    shema = [
        {"type": "function", "function": {
            "name": "uchebnik",
            "description": (
                "ПОКАЗАТЬ рисунок из учебника, по которому тебя учат. "
                "Скажи тему словами: «приседающий бар», «фрактал», «волны "
                "AO». Ты УВИДИШЬ сам рисунок и авторскую подпись. Проси, "
                "когда хочешь свериться с книгой, а не вспоминать."),
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
            return (f"по «{o}» рисунка не нашёл. Что есть:\\n{_u.temy()}")
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
    ak = koren / "Академия" / "ui_akademia.py"
    uch = koren / "Биржа" / "uchebnik.py"

    if not uch.exists():
        print("✗ Нет Биржа/uchebnik.py — накати сперва "
              "postavit_ruku_uchebnika.py и uchebnik_po_disciplinam.py")
        return 1

    t = ak.read_text(encoding="utf-8")
    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0
    if t.count(ST) != 1:
        print(f"✗ вызов LLM найден {t.count(ST)} раз — жду ровно один")
        return 1
    if "\nimport json" not in t and "\nimport json," not in t:
        print("⚠ в кабинете Академии нет import json — добавляю")
        t = t.replace("\nimport os", "\nimport json\nimport os", 1)

    novyy = t.replace(ST, NOV, 1) + f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ после правки не разбирается: {e}")
        return 1

    if SUHO:
        print("· правка готова (сухой прогон)")
        return 0

    bak = ak.with_suffix(f".py.bak_uchebnik_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(ak, bak)
    ak.write_text(novyy, encoding="utf-8")
    print(f"✓ ученик получил руки (копия: {bak.name})")

    import py_compile
    try:
        py_compile.compile(str(ak), doraise=True)
        print("✓ компилируется")
    except Exception as e:
        print(f"✗ НЕ компилируется: {e}")
        return 1

    print("\nТеперь ученик может сам сказать «покажи приседающий бар»")
    print("и УВИДЕТЬ рисунок — там, где по этим рисункам и учат.")
    print("В консоли будет видно: [УЧЕНИК] 🖐 и [УЧЕНИК] 🖼")
    print("\nУчебник общий: положишь новую книгу в дисциплины —")
    print("увидят и ученик, и трейдер, разом.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
