# fix_passport_json.py
"""
Чинит паспорта жителей и локаций, если внутри JSON-строки затесался
живой control-character (перевод строки, таб и т.п. БЕЗ экранирования)
— типичная причина "JSONDecodeError: Invalid control character".

ПРАВКА: без аргументов командной строки вообще — не нужно печатать
кириллические пути в терминале (Windows PowerShell иногда бьёт буквы
при вставке). Скрипт САМ обходит GRONDHEIM_CITY/жители/ и
GRONDHEIM_CITY/локации/ рекурсивно, находит все passport.json,
чинит сломанные, остальные не трогает.

Не трогает структуру JSON вообще — только экранирует управляющие
символы ВНУТРИ строк (между кавычками). Делает бэкап рядом перед
правкой каждого файла.

Запуск из КОРНЯ репо, без аргументов:
    python fix_passport_json.py

Хочешь починить конкретный файл вручную — можно передать путь
аргументом (по-старому), но это уже не обязательно.
`шесть·проверено·до·корня`
"""
import sys
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
SCAN_DIRS = [
    _ROOT / "GRONDHEIM_CITY" / "жители",
    _ROOT / "GRONDHEIM_CITY" / "локации",
]


def sanitize_json_text(raw: str) -> str:
    """Экранирует голые control-символы (код < 0x20) внутри JSON-строк.
    Структуру JSON снаружи строк не трогает вообще."""
    out = []
    in_string = False
    escape = False
    for ch in raw:
        if in_string:
            if escape:
                out.append(ch)
                escape = False
                continue
            if ch == '\\':
                out.append(ch)
                escape = True
                continue
            if ch == '"':
                out.append(ch)
                in_string = False
                continue
            code = ord(ch)
            if code < 0x20:
                if ch == '\n':
                    out.append('\\n')
                elif ch == '\r':
                    out.append('\\r')
                elif ch == '\t':
                    out.append('\\t')
                else:
                    out.append('\\u%04x' % code)
                continue
            out.append(ch)
        else:
            if ch == '"':
                in_string = True
            out.append(ch)
    return ''.join(out)


def fix_one(target: Path) -> str:
    """Возвращает: 'ok' (уже валиден), 'fixed' (починен), 'failed' (не смог)."""
    raw = target.read_text(encoding="utf-8")

    try:
        json.loads(raw)
        return "ok"
    except json.JSONDecodeError as e:
        print(f"  сломан: {e}")

    fixed = sanitize_json_text(raw)
    try:
        data = json.loads(fixed)
    except json.JSONDecodeError as e:
        print(f"  ✗ не смог починить автоматически: {e}")
        return "failed"

    backup = target.with_suffix(target.suffix + ".bak_fix_json")
    backup.write_text(raw, encoding="utf-8")
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ✓ починено (бэкап: {backup.name})")
    return "fixed"


def scan_and_fix():
    found = []
    for base in SCAN_DIRS:
        if not base.exists():
            continue
        found.extend(base.rglob("passport.json"))

    if not found:
        print("✗ ни одного passport.json не найдено — проверь, что запускаешь из корня репо.")
        return

    print(f"Найдено паспортов: {len(found)}\n")
    counts = {"ok": 0, "fixed": 0, "failed": 0}
    for pf in found:
        # относительный путь только для печати — не для ввода
        rel = pf.relative_to(_ROOT)
        print(f"{rel}:")
        status = fix_one(pf)
        counts[status] += 1
        print()

    print("═" * 50)
    print(f"Уже были в порядке: {counts['ok']}")
    print(f"Починено:           {counts['fixed']}")
    print(f"Не удалось починить: {counts['failed']}")


def main():
    if len(sys.argv) > 1:
        # старый режим — конкретный путь аргументом, если кому-то удобнее
        for p in sys.argv[1:]:
            target = Path(p)
            if not target.exists():
                print(f"✗ не найден: {target}")
                continue
            print(f"{target}:")
            fix_one(target)
            print()
    else:
        scan_and_fix()


if __name__ == "__main__":
    main()
