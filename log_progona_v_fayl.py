# -*- coding: utf-8 -*-
# log_progona_v_fayl.py — весь вывод прогона дублируется в лог.txt
# рядом с отчёт.md и местами.jsonl — без фильтров, ничего не теряется
# в терминале.
#
# Кладётся в КОРЕНЬ репозитория (рядом с папкой Биржа/). Запуск из
# PowerShell, из корня:
#   python log_progona_v_fayl.py
#
# Найдено 15.09 (Шеф): отчёт прогона показывает только решения
# трейдера, а весь код-уровневый след — переезды заявок, отмены,
# подтяжки стопа, ошибки зрения и рук — печатается только в
# терминал и после прогона недостижимо. На длинном прогоне (сотни
# баров) это тысячи строк, среди которых бывает самое важное
# (см. сессию про "переезд заявки" — без лога это не найти).
#
# Правка: в progon_po_istorii весь sys.stdout на время прогона
# дублируется в файл GRONDHEIM_CITY/.../прогоны/<время>/лог.txt —
# и в терминал по-прежнему тоже пишет, просто теперь ещё и в файл.
# Восстановление stdout стоит ПЕРВОЙ строкой в существующем finally —
# он выполняется, даже если прогон упал с необработанной ошибкой,
# значит терминал не онемеет навсегда даже при сбое.
#
# Ничего не удаляет. Кладёт рядом копию ui_torg.py.bak_log_progona.
# Запускать можно сколько угодно раз.

import shutil
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent
FAYL = KOREN / "Биржа" / "ui_torg.py"

# ── 1. класс-дублировщик, у самого верха файла ──────────────────────

BYLO_1 = (
    "from nicegui import ui, app, events\n"
    "\n"
    "_HERE = Path(__file__).resolve().parent          # Биржа/\n"
)

STALO_1 = (
    "from nicegui import ui, app, events\n"
    "\n\n"
    "class _TeeVyvod:\n"
    "    \"\"\"LOG_PROGONA_SYROY_V1: пишет разом в консоль и в файл.\n"
    "\n"
    "    Ничего не решает и не фильтрует — сырое дублирование вывода,\n"
    "    чтобы после прогона было что почитать, кроме памяти терминала.\n"
    "    \"\"\"\n"
    "\n"
    "    def __init__(self, *potoki):\n"
    "        self.potoki = potoki\n"
    "\n"
    "    def write(self, dannye):\n"
    "        for p in self.potoki:\n"
    "            try:\n"
    "                p.write(dannye)\n"
    "            except Exception:\n"
    "                pass\n"
    "\n"
    "    def flush(self):\n"
    "        for p in self.potoki:\n"
    "            try:\n"
    "                p.flush()\n"
    "            except Exception:\n"
    "                pass\n"
    "\n\n"
    "_HERE = Path(__file__).resolve().parent          # Биржа/\n"
)

# ── 2. запуск дублирования — сразу после того, как папка прогона известна ──

BYLO_2 = (
    "        except Exception as _e:\n"
    "            _otchyot = None\n"
    "            print(f\"[ОТЧЁТ] не завёлся ({_e}) — прогон пойдёт без записи\")\n"
    "        state[\"tester_running\"] = True\n"
)

STALO_2 = (
    "        except Exception as _e:\n"
    "            _otchyot = None\n"
    "            print(f\"[ОТЧЁТ] не завёлся ({_e}) — прогон пойдёт без записи\")\n"
    "        # LOG_PROGONA_SYROY_V1: дублируем весь вывод в лог.txt рядом\n"
    "        # с отчётом — без фильтров, чтобы после прогона не бегать по\n"
    "        # терминалу за тем, что там мелькнуло и пропало.\n"
    "        _original_stdout = sys.stdout\n"
    "        _log_fayl_progona = None\n"
    "        if _otchyot is not None:\n"
    "            try:\n"
    "                _log_fayl_progona = open(_otchyot.papka / \"лог.txt\", \"a\",\n"
    "                                          encoding=\"utf-8\")\n"
    "                sys.stdout = _TeeVyvod(_original_stdout, _log_fayl_progona)\n"
    "            except Exception as _e_log:\n"
    "                print(f\"[ЛОГ] файл прогона не завёлся ({_e_log}) — иду \"\n"
    "                      f\"без него\")\n"
    "        state[\"tester_running\"] = True\n"
)

# ── 3. восстановление — первой строкой существующего finally ───────────

BYLO_3 = (
    "        finally:\n"
    "            state[\"tester_running\"] = False\n"
    "            state[\"stop_requested\"] = False\n"
    "            try:\n"
    "                istoriya.postavit(_bylo_moment)\n"
    "            except Exception:\n"
    "                pass\n"
)

STALO_3 = (
    "        finally:\n"
    "            # LOG_PROGONA_SYROY_V1: возвращаем stdout ПЕРВЫМ делом —\n"
    "            # finally срабатывает даже при необработанном исключении,\n"
    "            # терминал не должен онеметь навсегда из-за сбоя прогона.\n"
    "            sys.stdout = _original_stdout\n"
    "            if _log_fayl_progona:\n"
    "                try:\n"
    "                    _log_fayl_progona.close()\n"
    "                except Exception:\n"
    "                    pass\n"
    "            state[\"tester_running\"] = False\n"
    "            state[\"stop_requested\"] = False\n"
    "            try:\n"
    "                istoriya.postavit(_bylo_moment)\n"
    "            except Exception:\n"
    "                pass\n"
)


def _pravka(tekst, bylo, stalo, opisanie):
    if stalo in tekst:
        print(f"· уже сделано — {opisanie}")
        return tekst, False
    if bylo not in tekst:
        print(f"✗ не нашёл место — {opisanie}. Скажи Брату, поправим по месту")
        return tekst, False
    print(f"✓ {opisanie}")
    return tekst.replace(bylo, stalo, 1), True


def main() -> int:
    if not FAYL.exists():
        print(f"✗ нет файла {FAYL} — запускать из корня репозитория")
        return 1

    tekst = FAYL.read_text(encoding="utf-8")
    ishodnyy = tekst
    sdelano = 0

    tekst, ok = _pravka(tekst, BYLO_1, STALO_1, "класс _TeeVyvod")
    sdelano += ok
    tekst, ok = _pravka(tekst, BYLO_2, STALO_2, "запуск дублирования")
    sdelano += ok
    tekst, ok = _pravka(tekst, BYLO_3, STALO_3, "восстановление stdout")
    sdelano += ok

    if tekst != ishodnyy:
        kopiya = FAYL.with_suffix(FAYL.suffix + ".bak_log_progona")
        if not kopiya.exists():
            shutil.copy2(FAYL, kopiya)
            print(f"  (копия старого: {kopiya.name})")
        FAYL.write_text(tekst, encoding="utf-8")

    print()
    print(f"ИТОГ: правок {sdelano} из 3")
    if sdelano:
        print("Перезапусти Кабинет (main.py) — правка кода не подхватится "
              "на лету.")
    return 0 if sdelano == 3 or (sdelano == 0 and "лог.txt" in tekst) else 1


if __name__ == "__main__":
    sys.exit(main())
