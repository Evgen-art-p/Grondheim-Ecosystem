# -*- coding: utf-8 -*-
# kartinka_v_istorii_zhitelya.py — та же правка, что для Академии,
# теперь для обычных жителей: картинка ложится в state["чат"] в
# момент, когда её кладут в руду, а не только текстовым пересказом
# после «Прочитать».
#
# Кладётся в КОРЕНЬ репозитория (рядом с папкой жители/). Запуск из
# PowerShell, из корня:
#   python kartinka_v_istorii_zhitelya.py
#
# У жителей живой чат (`messages = [...]; for m in state["chat"]...`)
# уже устроен ПРАВИЛЬНО — он просто проигрывает историю, без своего
# «стола» сбоку, чинить там нечего. Дыра — в другом месте: сама
# картинка никогда не попадала в state["чат"], только текстовый
# пересказ после «Прочитать», а само чтение — изолированный вызов
# без единой строчки истории.
#
# Правка:
#   1. handle_upload — картинка при заходе в руду сразу ложится в
#      state["чат"] отдельным сообщением, молча.
#   2. do_chtenie (ветка картинки) — история чата теперь идёт впереди
#      вопроса; сама картинка не прикладывается второй раз — она уже
#      в истории с момента, когда легла в руду.
#
# Чтение книг (текст) не тронуто — та же логика, что и в Академии:
# усвоение в личную память кусками, не живой разговор.
#
# Ничего не удаляет. Кладёт рядом копию ui_zhitel.py.bak_kartinka_istoriya.
# Запускать можно сколько угодно раз.

import shutil
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent
FAYL = KOREN / "жители" / "ui_zhitel.py"

# ── 1. handle_upload: картинка сразу в историю ──────────────────────

BYLO_1 = (
    '    def handle_upload(e: events.UploadEventArguments):\n'
    '        # ZHITEL_CHTENIE_V1: приёмка — один в один труба Брата\n'
    '        # (handle_upload ui_brat.py). Файл падает в ДОМ жителя.\n'
    '        try:\n'
    '            if dom is None:\n'
    '                ui.notify("дом не найден — руду класть некуда", color="warning")\n'
    '                return\n'
    '            ruda_dir = dom / RUDA_PODPAPKA\n'
    '            ruda_dir.mkdir(parents=True, exist_ok=True)\n'
    '            (ruda_dir / e.name).write_bytes(e.content.read())\n'
    '            ui.notify(f"⛏ руда: {e.name}", color="positive")\n'
    '            update_files()\n'
    '        except Exception as ex:\n'
    '            ui.notify(f"⚠ {ex}", color="negative")\n'
)

STALO_1 = (
    '    def handle_upload(e: events.UploadEventArguments):\n'
    '        # ZHITEL_CHTENIE_V1: приёмка — один в один труба Брата\n'
    '        # (handle_upload ui_brat.py). Файл падает в ДОМ жителя.\n'
    '        try:\n'
    '            if dom is None:\n'
    '                ui.notify("дом не найден — руду класть некуда", color="warning")\n'
    '                return\n'
    '            ruda_dir = dom / RUDA_PODPAPKA\n'
    '            ruda_dir.mkdir(parents=True, exist_ok=True)\n'
    '            _dannye = e.content.read()\n'
    '            (ruda_dir / e.name).write_bytes(_dannye)\n'
    '            ui.notify(f"⛏ руда: {e.name}", color="positive")\n'
    '            # AKADEMIA_KARTINKA_V_ISTORII_V1 (перенесено 15.09, Шеф+\n'
    '            # София): картинка сразу ложится в историю чата, молча,\n'
    '            # там, где её положили — не собирается заново отдельным\n'
    '            # звонком, когда её наконец прочитают.\n'
    '            if Path(e.name).suffix.lower() in KARTINKA_EXT:\n'
    '                try:\n'
    '                    _mime_u = _KARTINKA_MIME.get(\n'
    '                        Path(e.name).suffix.lower(), "image/png")\n'
    '                    _url_u = (f"data:{_mime_u};base64,"\n'
    '                              f"{base64.b64encode(_dannye).decode(\'ascii\')}")\n'
    '                    state["chat"].append({"role": "user", "content": [\n'
    '                        {"type": "image_url", "image_url": {"url": _url_u}},\n'
    '                    ]})\n'
    '                except Exception as _ie:\n'
    '                    print(f"[РУДА] картинка не легла в историю ({_ie})")\n'
    '            update_files()\n'
    '        except Exception as ex:\n'
    '            ui.notify(f"⚠ {ex}", color="negative")\n'
)

# ── 2. do_chtenie: ветка картинки — с историей впереди ──────────────

BYLO_2 = (
    '                _mime = _KARTINKA_MIME.get(fp.suffix.lower(), "image/png")\n'
    '                _url = f"data:{_mime};base64,{base64.b64encode(_img_data).decode(\'ascii\')}"\n'
    '                messages = [\n'
    '                    {"role": "system", "content": dusha},\n'
    '                    {"role": "user", "content": [\n'
    '                        {"type": "text", "text": _prompt_chtenia_kartinka(\n'
    '                            fp.name, linza, lok_imya, professia)},\n'
    '                        {"type": "image_url", "image_url": {"url": _url}},\n'
    '                    ]},\n'
    '                ]\n'
)

STALO_2 = (
    '                # AKADEMIA_KARTINKA_V_ISTORII_V1: картинка уже лежит в\n'
    '                # state["chat"] с момента, когда она попала в руду —\n'
    '                # заново прикладывать её здесь не нужно, только история\n'
    '                # впереди и сам вопрос на чтение.\n'
    '                messages = [{"role": "system", "content": dusha}]\n'
    '                for _m in state.get("chat", [])[-20:]:\n'
    '                    _r = ("user" if _m.get("role") == "user"\n'
    '                          else "assistant")\n'
    '                    messages.append({"role": _r,\n'
    '                                     "content": _m.get("content", "")})\n'
    '                messages.append({"role": "user", "content":\n'
    '                                 _prompt_chtenia_kartinka(\n'
    '                                     fp.name, linza, lok_imya, professia)})\n'
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

    tekst, ok = _pravka(tekst, BYLO_1, STALO_1,
                         "картинка ложится в историю при заходе в руду")
    sdelano += ok
    tekst, ok = _pravka(tekst, BYLO_2, STALO_2,
                         "чтение картинки — с историей впереди")
    sdelano += ok

    if tekst != ishodnyy:
        kopiya = FAYL.with_suffix(FAYL.suffix + ".bak_kartinka_istoriya")
        if not kopiya.exists():
            shutil.copy2(FAYL, kopiya)
            print(f"  (копия старого: {kopiya.name})")
        FAYL.write_text(tekst, encoding="utf-8")

    print()
    print(f"ИТОГ: правок {sdelano} из 2")
    if sdelano:
        print("Перезапусти Кабинет (main.py) — правка кода не подхватится "
              "на лету.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
