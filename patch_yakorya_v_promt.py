# patch_yakorya_v_promt.py
# YAKORYA_V_PROMT_V1 · якоря/резонанс/натура реально попадают в LLM
# ─────────────────────────────────────────────────────────────
# Баг (найден 28.06, на примере Локи): LLM отвечала "не в тему" — придумы-
# вала образ от себя (избу, топор), хотя в паспорте были явные якоря
# (розовое сияние, Творец Джем, клятва хранить искру). Причина: vydoh_stol
# отдавал только кто_я/факт/заряд/открыто/ядро — без единого слова про
# якоря, резонанс, натуру. Правая колонка кабинета (update_viewer) их
# ПОКАЗЫВАЕТ Шефу, но движок их никогда не передавал в LLM. Две системы
# читали один паспорт, но только одна доходила до самого ответа.
#
# Решение (Шеф, 28.06): да, всё это — давай в системный промпт.
#
# Делает в dvizhok.py:
#   1. vydoh_stol() добавляет в стол: история (Hidden_History), чувство
#      (Sensory_Response), якоря (Anchor_Points), скрытый_вкус (Hidden_Taste),
#      тянет_к (Pull_Vector), натура (DNA_Static) — те же поля и имена,
#      что показывает правая колонка кабинета (update_viewer в ui_zhitel.py).
#
# Идемпотентно. Бэкап в .bak_yakorya_v_promt.
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import ast, shutil, sys
from pathlib import Path

MARKER = "YAKORYA_V_PROMT_V1"
TARGET = Path(__file__).resolve().parent / "dvizhok.py"


def main():
    if not TARGET.exists():
        print(f"✗ не нашёл {TARGET} — положи патч в корень репо рядом с dvizhok.py")
        sys.exit(1)
    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"✓ {MARKER} уже на месте — пропускаю")
        return

    old_stol = '''    def vydoh_stol(self, fakt: str, vdoh_result: dict) -> dict:
        """Выдох: накрывает СТОЛ для решения жителя. НЕ решает сам.
        Стол = факт + кто она + что заряд открыл. Житель посмотрит и выберет."""
        self._zapisat_sobytie(vdoh_result.get("осело_в", "sensory"), fakt, vdoh_result)  # PAMYAT_SOBYTIY_V1
        return {
            "кто_я":    self.p.get("Official_Name"),
            "факт":     fakt,
            "заряд":    vdoh_result["заряд"],
            "открыто":  vdoh_result["открыто"],
            "ядро":     self.p.get("Core_Phrase", ""),
        }'''

    new_stol = '''    def vydoh_stol(self, fakt: str, vdoh_result: dict) -> dict:
        """Выдох: накрывает СТОЛ для решения жителя. НЕ решает сам.
        Стол = факт + кто она + что заряд открыл + личность (якоря/
        резонанс/натура — YAKORYA_V_PROMT_V1). Житель посмотрит и выберет."""
        self._zapisat_sobytie(vdoh_result.get("осело_в", "sensory"), fakt, vdoh_result)  # PAMYAT_SOBYTIY_V1
        return {
            "кто_я":          self.p.get("Official_Name"),
            "факт":           fakt,
            "заряд":          vdoh_result["заряд"],
            "открыто":        vdoh_result["открыто"],
            "ядро":           self.p.get("Core_Phrase", ""),
            # YAKORYA_V_PROMT_V1: те же поля, что правая колонка кабинета
            # показывает Шефу (update_viewer) — теперь и LLM их видит.
            "история":        self.p.get("Hidden_History", ""),
            "чувство":        self.p.get("Sensory_Response", ""),
            "якоря":          self.p.get("Anchor_Points", ""),
            "скрытый_вкус":   self.p.get("Hidden_Taste", ""),
            "тянет_к":        self.p.get("Pull_Vector", ""),
            "натура":         self.p.get("DNA_Static", {}),
        }'''

    if old_stol not in src:
        print("✗ не нашёл def vydoh_stol — стоп")
        sys.exit(1)
    src = src.replace(old_stol, new_stol, 1)

    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"✗ синтаксис: {e}")
        sys.exit(1)

    if not TARGET.with_suffix(".py.bak_yakorya_v_promt").exists():
        shutil.copy2(TARGET, TARGET.with_suffix(".py.bak_yakorya_v_promt"))
    TARGET.write_text(src, encoding="utf-8")
    print(f"✓ {MARKER}: стол несёт якоря/резонанс/натуру — то же, что видит Шеф")


if __name__ == "__main__":
    main()
