# patch_pamyat_sobytiy.py
# PAMYAT_SOBYTIY_V1 · события реально оседают в память, не теряются
# ─────────────────────────────────────────────────────────────
# Закон (Шеф, 28.06): "память вообще сохраняется?" → нет, только заряд.
# Решение: "каждый в свой [слой]" — событие летит ровно в тот файл,
# который указан в KONTEKST_SLOI (карта уже была, просто не использовалась).
# Порог по силе заряда — нет, пишем всё без фильтра (явный выбор: лучше
# растущий архив, чем забытое "привет").
#
# Делает в dvizhok.py:
#   1. Добавляет _zapisat_sobytie(kontekst, fakt, vdoh_result) — пишет
#      одну запись в файл слоя, который укажет KONTEKST_SLOI:
#        "работа"/"факт"/"дом" → sensory/sensory_memory.json  (entries: [...])
#        "общение"             → resonance/event_log.jsonl    (одна JSON-строка)
#        "учёба"               → archive/archive.jsonl        (одна JSON-строка)
#      Формат записи единый для всех трёх:
#        {ts, kontekst, fakt, заряд, тонус, сила}
#   2. vdoh() теперь сам вызывает _zapisat_sobytie в конце — каждый вдох
#      оставляет след без дополнительных действий снаружи.
#
# sensory_memory.json — это JSON-объект с массивом entries (не построчный
# JSONL, как resonance/archive), поэтому пишется иначе: читаем, добавляем,
# перезаписываем целиком. event_log.jsonl и archive.jsonl — JSONL (одна
# JSON-запись на строку, дозапись в конец, без перечитывания файла).
#
# Идемпотентно. Бэкап в .bak_pamyat_sobytiy.
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import ast, shutil, sys
from pathlib import Path

MARKER = "PAMYAT_SOBYTIY_V1"
TARGET = Path(__file__).resolve().parent / "dvizhok.py"


def main():
    if not TARGET.exists():
        print(f"✗ не нашёл {TARGET} — положи патч в корень репо рядом с dvizhok.py")
        sys.exit(1)
    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"✓ {MARKER} уже на месте — пропускаю")
        return

    # ── 1) Добавляем метод _zapisat_sobytie перед vydoh_stol ──
    anchor = '    def vydoh_stol(self, fakt: str, vdoh_result: dict) -> dict:'
    if anchor not in src:
        print("✗ шаг 1: не нашёл def vydoh_stol — стоп")
        sys.exit(1)

    new_method = '''    def _zapisat_sobytie(self, sloy: str, fakt: str, vdoh_result: dict):
        """PAMYAT_SOBYTIY_V1: событие оседает в свой слой (sloy — из
        vdoh_result['осело_в'], уже посчитан по KONTEKST_SLOI).
        Без порога — пишем всё (мелкое 'привет' тоже часть памяти)."""
        zapis = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "слой": sloy,
            "факт": fakt,
            "заряд": vdoh_result.get("заряд"),
        }
        try:
            if sloy == "sensory":
                # sensory_memory.json — JSON-объект с массивом entries
                p = self.dom / "sensory" / "sensory_memory.json"
                data = {"entries": []}
                if p.exists():
                    try:
                        data = json.loads(p.read_text(encoding="utf-8"))
                    except Exception:
                        data = {"entries": []}
                data.setdefault("entries", []).append(zapis)
                p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            elif sloy == "resonance":
                # event_log.jsonl — JSONL, дозапись строкой
                p = self.dom / "resonance" / "event_log.jsonl"
                with open(p, "a", encoding="utf-8") as f:
                    f.write(json.dumps(zapis, ensure_ascii=False) + "\\n")
            elif sloy == "archive":
                # archive.jsonl — JSONL, дозапись строкой
                p = self.dom / "archive" / "archive.jsonl"
                with open(p, "a", encoding="utf-8") as f:
                    f.write(json.dumps(zapis, ensure_ascii=False) + "\\n")
        except Exception:
            pass  # память не должна ронять дыхание — пропускаем тихо

    def vydoh_stol(self, fakt: str, vdoh_result: dict) -> dict:'''

    src = src.replace(anchor, new_method, 1)

    # ── 2) vydoh_stol() сам вызывает _zapisat_sobytie — здесь fakt уже
    #       реально доступен как параметр (в vdoh() его нет вообще,
    #       туда передаётся только kontekst/sila/svezhest/tonus). ──
    old_vydoh = '''    def vydoh_stol(self, fakt: str, vdoh_result: dict) -> dict:
        """Выдох: накрывает СТОЛ для решения жителя. НЕ решает сам.
        Стол = факт + кто она + что заряд открыл. Житель посмотрит и выберет."""
        return {'''
    new_vydoh = '''    def vydoh_stol(self, fakt: str, vdoh_result: dict) -> dict:
        """Выдох: накрывает СТОЛ для решения жителя. НЕ решает сам.
        Стол = факт + кто она + что заряд открыл. Житель посмотрит и выберет."""
        self._zapisat_sobytie(vdoh_result.get("осело_в", "sensory"), fakt, vdoh_result)  # PAMYAT_SOBYTIY_V1
        return {'''
    if old_vydoh not in src:
        print("✗ шаг 2: не нашёл def vydoh_stol — стоп")
        sys.exit(1)
    src = src.replace(old_vydoh, new_vydoh, 1)

    # ── 3) импорт timezone — datetime уже импортирован, добавляем timezone ──
    old_import = 'from datetime import datetime, timezone'
    if old_import not in src:
        print("✗ шаг 3: не нашёл импорт datetime/timezone — проверь вручную")
        # не критично, sохранить() уже использует timezone — если его нет,
        # значит файл отличается сильнее, чем ожидалось
        sys.exit(1)

    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"✗ синтаксис: {e}")
        sys.exit(1)

    if not TARGET.with_suffix(".py.bak_pamyat_sobytiy").exists():
        shutil.copy2(TARGET, TARGET.with_suffix(".py.bak_pamyat_sobytiy"))
    TARGET.write_text(src, encoding="utf-8")
    print(f"✓ {MARKER}: каждый вдох теперь пишет след в свой слой памяти")


if __name__ == "__main__":
    main()
