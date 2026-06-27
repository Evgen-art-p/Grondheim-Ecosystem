# patch_ubrat_mertvuyu_generaciyu.py
# UBRAT_MERTVUYU_GENERACIYU_V1 · убрать мёртвый вызов generate_agent_files
# ─────────────────────────────────────────────────────────────
# В save_object был блок "if False and obj.get('Object_Type_Class')=='agent'"
# — никогда не выполняется (if False), мёртвый код с вызовом
# generate_agent_files(...). Шеф попросил убрать.
#
# Саму функцию generate_agent_files и DNA_DYNAMIC_DEFAULTS НЕ трогаем —
# это архитектурное решение на будущее, не хвост для уборки сейчас.
#
# Убирает только сам блок-вызов внутри save_object, заменяя на простое
# clear_form() + уведомление об успехе.
#
# Идемпотентно. Бэкап в .bak_mertvaya_generaciya.
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import ast, shutil, sys
from pathlib import Path

MARKER = "UBRAT_MERTVUYU_GENERACIYU_V1"
TARGET = Path(__file__).resolve().parent / "ui_registry.py"


def main():
    if not TARGET.exists():
        print(f"✗ не нашёл {TARGET} — положи патч в корень репо рядом с ui_registry.py")
        sys.exit(1)
    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"✓ {MARKER} уже на месте — пропускаю")
        return

    old_block = '''                    # ── Генерация файлов студии для агентов ──
                    generated = []
                    # PATCH_DVA_FILA: папки-слои отключены — это СЛЕДУЮЩИЙ шаг.
                    # Сейчас рождаем только паспорт (куча + кусочек). Памяти нет.
                    if False and obj.get("Object_Type_Class") == "agent":
                        try:
                            dna_static = obj.get("DNA_Static", {})
                            dna_dynamic = dict(DNA_DYNAMIC_DEFAULTS)
                            generated = generate_agent_files(
                                obj=obj,
                                dna_static=dna_static,
                                core_phrase=obj.get("Core_Phrase", ""),
                                anchor_points=obj.get("Anchor_Points", ""),
                                home_story=obj.get("Home_Story", ""),
                                pull_vector=obj.get("Pull_Vector", ""),
                                hidden_taste=obj.get("Hidden_Taste", ""),
                                trigger_keywords=obj.get("Trigger_Keywords", ""),
                                workshop=obj.get("Workshop_ID", ""),
                                agent_role=obj.get("Turbo_Role", ""),
                                balance_gnd=obj.get("Balance_GND", 0),
                                balance_tepl=obj.get("Balance_Tepl", 0),
                            )
                            if generated:
                                ui.notify(f"✓ Файлы агента созданы: {len(generated)} файлов", type="positive", timeout=6000)
                        except Exception as e:
                            ui.notify(f"⚠ Ошибка генерации файлов: {e}", type="warning")

                    clear_form()
                    msg = "Объект сохранён ✓"
                    if generated:
                        msg += f" · {len(generated)} файлов → studio/modules/"
                    ui.notify(msg, type="positive")'''

    new_block = '''                    # ── Генерация файлов студии для агентов: УБРАНО — UBRAT_MERTVUYU_GENERACIYU_V1 (был мёртвый код, if False) ──

                    clear_form()
                    ui.notify("Объект сохранён ✓", type="positive")'''

    if old_block not in src:
        print("✗ не нашёл мёртвый блок generate_agent_files в save_object — стоп")
        sys.exit(1)
    src = src.replace(old_block, new_block, 1)

    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"✗ синтаксис: {e}")
        sys.exit(1)

    if not TARGET.with_suffix(".py.bak_mertvaya_generaciya").exists():
        shutil.copy2(TARGET, TARGET.with_suffix(".py.bak_mertvaya_generaciya"))
    TARGET.write_text(src, encoding="utf-8")
    print(f"✓ {MARKER}: мёртвый вызов generate_agent_files убран из save_object")


if __name__ == "__main__":
    main()
