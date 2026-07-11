# -*- coding: utf-8 -*-
"""
patch_dvizhok_stol_chisto_vyvod_v1.py
────────────────────────────────────────────────────────────────────
ФУНДАМЕНТ ДУШИ ТРЕЙДЕРА (МОСТ К НОСИТЕЛЮ, шаг для эталона).

ЗАЧЕМ (две находки разведки, которых не было в плане МОСТа):

  1. vydoh_stol УЖЕ отдаёт «якоря» = Anchor_Points — канал опыта на
     ЧТЕНИЕ построен. НО у vydoh_stol побочка: на КАЖДЫЙ вызов пишет
     событие в память (_zapisat_sobytie) и требует vdoh_result. Значит
     на баре его звать нельзя — читающий конец трейдера зовётся часто
     (взгляд на стол), на тестере это мусор в памяти + тормоз.
       → нужен ЧИСТЫЙ читатель личности: те же поля, ноль записи.

  2. Дописать вывод из сделки в Anchor_Points — ноги Опыта на ЗАПИСЬ —
     не умеет НИКТО: ни dvizhok, ни hooks. Это единственный по-настоящему
     новый кирпич, и жить ему в dvizhok: в паспорт пишет только движок
     самого жителя (Закон Входа-Выхода, «не лезь в чужую кухню»).

ЧТО ДЕЛАЕТ (чисто аддитивно — добавляет ДВА метода в класс Dvizhok,
  существующий код не трогает, живую торговлю не трогает):

  • nakryt_stol_chisto() → dict
        Стол БЕЗ дыхания: чистое чтение личности из паспорта. Те же поля,
        что vydoh_stol (кто_я, ядро, история, якоря, чувство, скрытый_вкус,
        тянет_к, дом, натура + текущий заряд на чтение), МИНУС запись в
        память и МИНУС требование vdoh_result. Для читающего конца.

  • dopisat_vyvod(vyvod, limit=10) → dict
        Дописывает ВЫВОД в Anchor_Points (нога Опыта, Чертёж §5.2/4.6.4).
        Лимит якорей — limit (Чертёж: 7-10). Переполнение — старейшее в
        archive/archive.jsonl (не в забвение). Дубликат не плодит строку.
        Для пишущего конца (раз на закрытую сделку).

Идемпотентно (маркер). .bak рядом. Запускать из КОРНЯ репы:
    python patch_dvizhok_stol_chisto_vyvod_v1.py
проверка (безопасная, только чтение) — из корня репы:
    python -c "import sys; sys.path.insert(0,'жители'); from dvizhok import Dvizhok; \
from pathlib import Path; d=Dvizhok(Path('GRONDHEIM_CITY/жители/ковчег/Илья')); \
s=d.nakryt_stol_chisto(); print('кто:',s['кто_я']); print('якоря:'); print(s['якоря'])"
"""
from __future__ import annotations
import sys
from pathlib import Path

MARKER = "DVIZHOK_STOL_CHISTO_VYVOD_V1"
TARGET = Path("жители") / "dvizhok.py"

ANCHOR = "    def vspomnit(self, zapros: str, limit: int = 6) -> str:"

METHODS = (
    "    def nakryt_stol_chisto(self) -> dict:\n"
    '        """Стол БЕЗ дыхания: чистое чтение личности из паспорта — ноль\n'
    "        записи в память, ноль vdoh_result. Для читающего конца, который\n"
    "        зовётся часто (на каждый бар/взгляд): vydoh_stol туда нельзя, он\n"
    "        пишет событие на каждый вызов. Те же поля личности, что vydoh_stol,\n"
    "        минус побочка. Заряд отдаём на ЧТЕНИЕ (в __init__ уже загружен,\n"
    '        диск не трогаем). # ' + MARKER + "\n"
    '        """\n'
    "        return {\n"
    '            "кто_я":        self.p.get("Official_Name"),\n'
    '            "заряд":        round(self.charge, 3),\n'
    '            "ядро":         self.p.get("Core_Phrase", ""),\n'
    '            "история":      self.p.get("Hidden_History", ""),\n'
    '            "чувство":      self.p.get("Sensory_Response", ""),\n'
    '            "якоря":        self.p.get("Anchor_Points", ""),\n'
    '            "скрытый_вкус": self.p.get("Hidden_Taste", ""),\n'
    '            "тянет_к":      self.p.get("Pull_Vector", ""),\n'
    '            "дом":          self.p.get("домашний_промпт", ""),\n'
    '            "натура":       self.p.get("DNA_Static", {}),\n'
    "        }\n"
    "\n"
    "    def dopisat_vyvod(self, vyvod: str, limit: int = 10) -> dict:\n"
    '        """Дописывает ВЫВОД из сделки в Anchor_Points — нога Опыта\n'
    "        (Чертёж §5.2/4.6.4). Опыт живёт рядом с Родом, рукой самого\n"
    "        жителя (в паспорт пишет только его движок). Лимит якорей — limit\n"
    "        (Чертёж: 7-10); переполнение — старейшее в archive, не в\n"
    "        забвение. Дубликат вывода строку не плодит. Возвращает что стало.\n"
    '        # ' + MARKER + "\n"
    '        """\n'
    "        vyvod = (vyvod or \"\").strip()\n"
    "        if not vyvod:\n"
    '            return {"дописано": False, "причина": "пустой вывод"}\n'
    '        raw = self.p.get("Anchor_Points", "") or ""\n'
    '        lines = [ln for ln in raw.split("\\n") if ln.strip()]\n'
    "        if vyvod in lines:\n"
    '            return {"дописано": False, "причина": "уже среди якорей",\n'
    '                    "всего": len(lines)}\n'
    "        lines.append(vyvod)\n"
    "        ushlo = []\n"
    "        if len(lines) > limit:\n"
    "            ushlo = lines[:len(lines) - limit]\n"
    "            lines = lines[len(lines) - limit:]\n"
    "            # старейшие якоря не в забвение — в архив жителя\n"
    "            try:\n"
    '                (self.dom / "archive").mkdir(parents=True, exist_ok=True)\n'
    '                ap = self.dom / "archive" / "archive.jsonl"\n'
    '                with open(ap, "a", encoding="utf-8") as f:\n'
    "                    for old in ushlo:\n"
    "                        f.write(json.dumps({\n"
    '                            "ts": datetime.now(timezone.utc)\n'
    '                                  .isoformat(timespec="seconds"),\n'
    '                            "слой": "archive",\n'
    '                            "факт": old,\n'
    '                            "причина": "якорь вытеснен (лимит опыта)",\n'
    "                        }, ensure_ascii=False) + \"\\n\")\n"
    "            except Exception:\n"
    "                pass   # архив не должен ронять запись опыта\n"
    '        self.p["Anchor_Points"] = "\\n".join(lines)\n'
    "        self.passport_path.write_text(\n"
    "            json.dumps(self.p, ensure_ascii=False, indent=2),\n"
    '            encoding="utf-8")\n'
    '        return {"дописано": True, "всего": len(lines), "вытеснено": len(ushlo)}\n'
    "\n"
    + ANCHOR
)


def main() -> int:
    if not TARGET.exists():
        print(f"✗ не нашёл {TARGET} — запусти из КОРНЯ репы "
              f"(там, где папка «жители»).")
        return 1

    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"✓ уже пропатчено ({MARKER}) — ничего не делаю.")
        return 0

    if ANCHOR not in src:
        print("✗ не нашёл метод vspomnit — точку врезки. Файл правился "
              "вручную? Сверь dvizhok.py: методы вставляются ПЕРЕД vspomnit.")
        return 2

    # imports нужны методам: json / datetime / timezone — проверим, что есть
    need = ("import json", "from datetime import datetime, timezone")
    missing = [n for n in need if n not in src]
    if missing:
        print("✗ в dvizhok.py не хватает импортов, на которые опираются "
              f"методы: {missing}. Ожидались в шапке файла. Проверь.")
        return 3

    bak = TARGET.with_suffix(TARGET.suffix + ".bak")
    if not bak.exists():
        bak.write_text(src, encoding="utf-8")
        print(f"• бэкап: {bak}")
    else:
        print(f"• бэкап уже был: {bak} (не перезаписываю)")

    patched = src.replace(ANCHOR, METHODS, 1)
    TARGET.write_text(patched, encoding="utf-8")
    print(f"✓ {TARGET}: добавлены nakryt_stol_chisto() и dopisat_vyvod().")
    print(f"  Маркер идемпотентности: {MARKER}")
    print("  Проверка (только чтение, Илью не трогает) — см. шапку патча.")
    return 0


if __name__ == "__main__":
    if isinstance(sys.stdout, __import__("io").TextIOWrapper):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    sys.exit(main())
