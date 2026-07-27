# DVIZHOK_MKDIR_FIX_V1
"""
DVIZHOK_MKDIR_FIX_V1 -- каждый слой памяти (sensory/resonance/archive)
сам создаёт свою папку перед записью. Раньше запись тихо терялась
в except, если папка ещё не существовала.

Идемпотентно: если маркер DVIZHOK_MKDIR_FIX_V1 уже стоит в файле — патч
молча выходит, повторно не наложится. Бэкап .bak делается один раз,
при первом применении.

Запуск из корня репо:  python patch_dvizhok_mkdir_fix.py
`шесть·проверено·до·корня`
"""
from pathlib import Path
import sys

TARGET = Path('жители/dvizhok.py')
MARKER = 'DVIZHOK_MKDIR_FIX_V1'

REPLACEMENTS = [
    ('        try:\n            if sloy == "sensory":\n                # sensory_memory.json — JSON-объект с массивом entries\n                p = self.dom / "sensory" / "sensory_memory.json"\n                data = {"entries": []}\n                if p.exists():\n                    try:\n                        data = json.loads(p.read_text(encoding="utf-8"))\n                    except Exception:\n                        data = {"entries": []}\n                data.setdefault("entries", []).append(zapis)\n                p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")\n            elif sloy == "resonance":\n                # event_log.jsonl — JSONL, дозапись строкой\n                p = self.dom / "resonance" / "event_log.jsonl"\n                with open(p, "a", encoding="utf-8") as f:\n                    f.write(json.dumps(zapis, ensure_ascii=False) + "\\n")\n            elif sloy == "archive":\n                # archive.jsonl — JSONL, дозапись строкой\n                p = self.dom / "archive" / "archive.jsonl"\n                with open(p, "a", encoding="utf-8") as f:\n                    f.write(json.dumps(zapis, ensure_ascii=False) + "\\n")\n        except Exception:\n            pass  # память не должна ронять дыхание — пропускаем тихо', '        try:\n            # DVIZHOK_MKDIR_FIX_V1: каждый слой сам заводит свою папку —\n            # раньше запись тихо проваливалась в except, если "sensory"/\n            # "resonance"/"archive" ещё не были созданы при рождении\n            # жителя (у настоящих резидентов это не всплывало — папки\n            # заводятся при рождении, но память не должна на это надеяться).\n            if sloy == "sensory":\n                # sensory_memory.json — JSON-объект с массивом entries\n                (self.dom / "sensory").mkdir(parents=True, exist_ok=True)\n                p = self.dom / "sensory" / "sensory_memory.json"\n                data = {"entries": []}\n                if p.exists():\n                    try:\n                        data = json.loads(p.read_text(encoding="utf-8"))\n                    except Exception:\n                        data = {"entries": []}\n                data.setdefault("entries", []).append(zapis)\n                p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")\n            elif sloy == "resonance":\n                # event_log.jsonl — JSONL, дозапись строкой\n                (self.dom / "resonance").mkdir(parents=True, exist_ok=True)\n                p = self.dom / "resonance" / "event_log.jsonl"\n                with open(p, "a", encoding="utf-8") as f:\n                    f.write(json.dumps(zapis, ensure_ascii=False) + "\\n")\n            elif sloy == "archive":\n                # archive.jsonl — JSONL, дозапись строкой\n                (self.dom / "archive").mkdir(parents=True, exist_ok=True)\n                p = self.dom / "archive" / "archive.jsonl"\n                with open(p, "a", encoding="utf-8") as f:\n                    f.write(json.dumps(zapis, ensure_ascii=False) + "\\n")\n        except Exception:\n            pass  # память не должна ронять дыхание — пропускаем тихо'),
]

# REPLACE_ALL — можно встречаться много раз, меняем ВСЕ вхождения
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
    bak = TARGET.with_suffix(TARGET.suffix + ".bak")
    if not bak.exists():
        bak.write_text(TARGET.read_text(encoding="utf-8"), encoding="utf-8")
    TARGET.write_text(text, encoding="utf-8")
    print(f"✓ пропатчено: {TARGET} (бэкап: {bak})")

if __name__ == "__main__":
    main()

# DVIZHOK_MKDIR_FIX_V1 — маркер идемпотентности