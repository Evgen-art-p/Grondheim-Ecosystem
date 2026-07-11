# -*- coding: utf-8 -*-
"""
patch_dvizhok_yakorya_yadro_v1.py
────────────────────────────────────────────────────────────────────
ДВЕ МИНЫ, ПОЙМАННЫЕ ЖИВОЙ ПРОВЕРКОЙ НА ДИСКЕ ШЕФА (12.07).
Обе — под ногой Опыта. Обе взорвались бы в эталоне Авана.

МИНА 1 — ЯКОРЯ СЛИПЛИСЬ В ОДНУ СТРОКУ.
  В passport.json Ильи Anchor_Points записаны формой рождения с
  ЛИТЕРАЛЬНЫМ разделителем — два символа «\\» и «n», а НЕ перевод
  строки. На экране это видно как:
      Я вхожу на open...\\nЯ терплю просадку молча.\\nЯ выхожу...
  Последствие: dopisat_vyvod (патч B) режет по настоящему "\\n",
  не находит его — и считает, что у Ильи ОДИН якорь вместо пяти.
  → лимит 7-10 не сработает никогда;
  → весь торговый опыт остаётся слипшимся комом, выводы клеятся сбоку.

  ЛЕЧЕНИЕ: разделитель распознаём ОБА (литеральный и настоящий), а
  пишем обратно ТЕМ ЖЕ, каким паспорт написан (не ломаем вид для
  других читателей — кабинет, ui_zhitel, форма рождения). Паспорт
  жителя этот патч НЕ переписывает: правится только код движка.

МИНА 2 — ЯДРО ПУСТОЕ.
  nakryt_stol_chisto (и старый vydoh_stol!) читают Core_Phrase из
  ПАСПОРТА — а там его нет и не будет: по Чертежу §1.5 ядро живёт в
  РОЛИ (маске), не в Роде. Чертёж сам держит это в хвостах:
  «Core_Phrase: читается движком — не заполняется ничем». Диск
  подтвердил: у Ильи в маске «В рынке или в ауте.», в паспорте пусто,
  на стол приезжает "".

  ЛЕЧЕНИЕ: ядро — из маски «работа» дома жителя (она лежит рядом с
  паспортом, движок дотянется, чужую кухню не трогаем). Паспорт —
  фоллбэк, если однажды ядро появится и там.

ЧТО ПРАВИТ: только жители/dvizhok.py, только два метода патча B
  (nakryt_stol_chisto, dopisat_vyvod) + добавляет два помощника.
  Живую торговлю не трогает. Паспорта не мутирует.

Идемпотентно. .bak рядом. Из КОРНЯ репы:
    python patch_dvizhok_yakorya_yadro_v1.py
    python proverka_mostika.py      # ждём: ядро НЕ пусто, якорей 5
"""
from __future__ import annotations
import io
import sys
from pathlib import Path

MARKER = "DVIZHOK_YAKORYA_YADRO_V1"
TARGET = Path("жители") / "dvizhok.py"
NEED = "DVIZHOK_STOL_CHISTO_VYVOD_V1"   # патч B должен стоять

# ── помощники + новое ядро: врезаем ПЕРЕД nakryt_stol_chisto ─────────
ANCHOR_A = "    def nakryt_stol_chisto(self) -> dict:"

HELPERS = '''    # ── ЯКОРЯ: разделитель бывает ДВУХ видов ────────────────────────
    # Форма рождения писала литеральные два символа «\\\\» + «n», а не
    # перевод строки (проверено на паспорте Ильи 12.07). Читаем ОБА,
    # пишем ТЕМ ЖЕ, каким паспорт написан — иначе сломаем вид другим
    # читателям (кабинет, ui_zhitel). # {M}
    _YAKOR_LIT = "\\\\n"      # литерал: обратный слэш + n

    def _yakorya_razdelitel(self, raw: str) -> str:
        """Каким разделителем ЖИВЁТ этот паспорт. Литерал — если он есть."""
        if self._YAKOR_LIT in (raw or ""):
            return self._YAKOR_LIT
        return "\\n"

    def _yakorya_spisok(self, raw: str) -> list:
        """Якоря списком. Режет и по литералу, и по настоящему переводу."""
        s = (raw or "").replace(self._YAKOR_LIT, "\\n")
        return [ln.strip() for ln in s.split("\\n") if ln.strip()]

    def yadro(self) -> str:
        """ЯДРО живёт в РОЛИ (маске), не в Роде (Чертёж §1.5) — паспорт
        его не носит и носить не должен. Маска лежит в доме жителя,
        движок дотянется сам. Паспорт — фоллбэк. # {M}"""
        try:
            mp = self.dom / "маски" / "работа" / "mask.json"
            if mp.exists():
                m = json.loads(mp.read_text(encoding="utf-8"))
                cp = (m.get("Core_Phrase") or "").strip()
                if cp:
                    return cp
        except Exception:
            pass
        return self.p.get("Core_Phrase", "") or ""

'''.replace("{M}", MARKER) + ANCHOR_A

# ── правка ядра в чистом столе ──────────────────────────────────────
OLD_YADRO = '            "ядро":         self.p.get("Core_Phrase", ""),\n'
NEW_YADRO = '            "ядро":         self.yadro(),   # ' + MARKER + ": ядро из маски (Роль), не из Рода\n"

# ── правка резки/склейки якорей в дописчике ─────────────────────────
OLD_SPLIT = (
    '        raw = self.p.get("Anchor_Points", "") or ""\n'
    '        lines = [ln for ln in raw.split("\\n") if ln.strip()]\n'
)
NEW_SPLIT = (
    '        raw = self.p.get("Anchor_Points", "") or ""\n'
    "        sep = self._yakorya_razdelitel(raw)   # " + MARKER + "\n"
    "        lines = self._yakorya_spisok(raw)\n"
)

OLD_JOIN = '        self.p["Anchor_Points"] = "\\n".join(lines)\n'
NEW_JOIN = '        self.p["Anchor_Points"] = sep.join(lines)   # ' + MARKER + ": пишем ТЕМ ЖЕ разделителем\n"


def main() -> int:
    if isinstance(sys.stdout, io.TextIOWrapper):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    if not TARGET.exists():
        print(f"✗ не нашёл {TARGET} — запусти из КОРНЯ репы.")
        return 1

    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"✓ уже пропатчено ({MARKER}) — ничего не делаю.")
        return 0

    if NEED not in src:
        print(f"✗ сначала нужен патч B ({NEED}) — "
              "он кладёт методы, которые этот патч чинит.")
        return 2

    for old, what in ((ANCHOR_A, "метод nakryt_stol_chisto"),
                      (OLD_YADRO, "строка «ядро» в чистом столе"),
                      (OLD_SPLIT, "резка якорей в dopisat_vyvod"),
                      (OLD_JOIN, "склейка якорей в dopisat_vyvod")):
        if old not in src:
            print(f"✗ не нашёл: {what}. Файл правился вручную? Сверь глазами.")
            return 3

    bak = TARGET.with_suffix(".py.bak2")
    if not bak.exists():
        bak.write_text(src, encoding="utf-8")
        print(f"• бэкап: {bak}")

    src = src.replace(ANCHOR_A, HELPERS, 1)
    src = src.replace(OLD_YADRO, NEW_YADRO, 1)
    src = src.replace(OLD_SPLIT, NEW_SPLIT, 1)
    src = src.replace(OLD_JOIN, NEW_JOIN, 1)
    TARGET.write_text(src, encoding="utf-8")

    print(f"✓ {TARGET}:")
    print("   • якоря режутся и по литеральному \\n, и по настоящему;")
    print("     пишутся обратно ТЕМ ЖЕ разделителем (паспорт не ломаем);")
    print("   • ядро берётся из МАСКИ (Роль, Чертёж §1.5), не из паспорта.")
    print(f"   Маркер: {MARKER}")
    print("\nПроверка:  python proverka_mostika.py")
    print("Ждём: «ядро : В рынке или в ауте.» и ПЯТЬ отдельных якорей.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
