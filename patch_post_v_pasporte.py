# -*- coding: utf-8 -*-
# POST_V_PASPORTE_V1
"""
ПОСТ ПЕРЕЕЗЖАЕТ В ПАСПОРТ. Две правки, вторая важнее первой.

ПРАВКА 1 — ЗАПИСЬ ПАСПОРТА БОЛЬШЕ НЕ ЗАТИРАЕТ ЧУЖОЕ (dvizhok.py)
    Было: Dvizhok снимает копию паспорта при рождении и в
    sохранить() пишет ЭТУ КОПИЮ обратно целиком. Всё, что записал в
    паспорт кто-то другой, пока житель разговаривал, — молча
    пропадает. Это касается не только постов: любое поле в опасности.
    Стало: перед записью паспорт перечитывается с диска, и движок
    кладёт поверх только СВОИ поля (заряд и просев). Чужое остаётся.
    Без этой правки вторая не имеет смысла — пост будет исчезать.

ПРАВКА 2 — ПРАВДА О ПОСТЕ ЖИВЁТ В ПАСПОРТЕ (rezidenty.py)
    Было: связь лежала сбоку, в посты/{id}/хранитель.json. Житель не
    знал, что он на посту; работу ему подкладывали снаружи на время
    разговора. Отсюда «ректор не знает, что он ректор».
    Стало: в паспорте поле "Посты" — список того, что этот житель
    сейчас делает. Всё, что и так читает паспорт (душа, стол, память),
    видит работу само, без подкладывания.

    Чертёж §1.5.2б: роль живёт ВНУТРИ Рода, не рядом. Это не «навсегда»
    — сняли с поста, строка ушла, житель прежний.

ЧЕГО ПАТЧ НЕ ЛОМАЕТ
    Имена и подписи функций те же: posadit, snyat, kto_na_postu,
    lichnost_na_postu. Кто их зовёт (ректор, библиотекарь, кабинеты) —
    не трогаем ни строчкой.

СТАРЫЕ ФАЙЛЫ
    хранитель.json не удаляются. Первый вызов perenesti_posty()
    переносит их в паспорта и переименовывает в .перенесено — чтобы
    никто случайно не прочитал устаревшее. Перенос идёт сам при первом
    обращении, вручную звать не надо.

ЗАПУСК из корня репо:
    python patch_post_v_pasporte.py
"""
import ast
import py_compile
import shutil
import sys
from pathlib import Path

MARKER = "POST_V_PASPORTE_V1"

T_REZ = Path("ГОРОД") / "rezidenty.py"
B_REZ = Path("ГОРОД") / "rezidenty.py.bak_post_v_pasporte"
T_DVI = Path("жители") / "dvizhok.py"
B_DVI = Path("жители") / "dvizhok.py.bak_post_v_pasporte"

# ═══════════════════════════════════════════════════════════
# DVIZHOK — запись паспорта сливает, а не затирает
# ═══════════════════════════════════════════════════════════
D_OLD = '''    def sохранить(self):
        """Заряд оседает в паспорт (состояние помнится между вдохами)."""
        self.p["_charge"] = round(self.charge, 4)
        self.p["_charge_ts"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.passport_path.write_text(
            json.dumps(self.p, ensure_ascii=False, indent=2), encoding="utf-8")
'''

D_NEW = '''    # POST_V_PASPORTE_V1: свои поля движка — только эти. Всё остальное
    # в паспорте принадлежит кому-то другому и трогать его нельзя.
    _SVOI_POLYA = ("_charge", "_charge_ts", "_prosev_consumed")

    def sохранить(self):
        """Заряд оседает в паспорт (состояние помнится между вдохами).

        POST_V_PASPORTE_V1. Раньше здесь писалась КОПИЯ паспорта,
        снятая при рождении движка, — и всё, что записал в паспорт
        кто-то другой за время разговора, молча пропадало (пост,
        например). Теперь паспорт перечитывается с диска, и поверх
        ложатся только свои поля. Чужое остаётся чужим.
        """
        self.p["_charge"] = round(self.charge, 4)
        self.p["_charge_ts"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            svezhiy = json.loads(self.passport_path.read_text(encoding="utf-8"))
            if not isinstance(svezhiy, dict):
                svezhiy = dict(self.p)
        except Exception:
            svezhiy = dict(self.p)   # не прочитался — пишем как раньше, не теряем
        for k in self._SVOI_POLYA:
            if k in self.p:
                svezhiy[k] = self.p[k]
        self.p = svezhiy
        self.passport_path.write_text(
            json.dumps(svezhiy, ensure_ascii=False, indent=2), encoding="utf-8")
'''

# ═══════════════════════════════════════════════════════════
# REZIDENTY — связь переезжает в паспорт
# ═══════════════════════════════════════════════════════════
R_OLD = '''def posadit(post_id: str, imya_zhitelya: str, zid: str = "") -> tuple:
    """Сажает жителя на пост. Род НЕ проверяется — закон Шефа.
    Пост занят другим — честно сменяем, но возвращаем, кто был,
    чтобы вызывающий мог сказать это вслух (не тайком).

    Возвращает (успех: bool, сообщение: str).
    """
    d = POSTY_DIR / post_id
    if not (d / "пост.json").exists():
        return False, f"поста «{post_id}» нет — сначала заведи"
    byl = (_read_json(d / "хранитель.json", {}) or {}).get("житель", "")
    ok = _write_json(d / "хранитель.json", {
        "житель": imya_zhitelya,
        "id": zid,
        "с": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })
    if not ok:
        return False, "не записался на диск"
    if byl and byl != imya_zhitelya:
        return True, f"сменил(а) на посту: {byl}"
    return True, "на посту"


def snyat(post_id: str) -> tuple:
    """Освобождает пост. Пост остаётся, вакансия открыта."""
    f = POSTY_DIR / post_id / "хранитель.json"
    if not f.exists():
        return True, "пост и так свободен"
    try:
        f.unlink()
        return True, "пост освобождён"
    except Exception as e:
        return False, str(e)


def kto_na_postu(post_id: str) -> str:
    """Имя того, кто сейчас на посту. Пусто — вакансия."""
    return (_read_json(POSTY_DIR / post_id / "хранитель.json", {})
            or {}).get("житель", "") or ""
'''

R_NEW = '''# POST_V_PASPORTE_V1 — ПРАВДА О ПОСТЕ ЖИВЁТ В ПАСПОРТЕ ЖИТЕЛЯ
#
# Было: связь в посты/{id}/хранитель.json, сбоку от обоих. Житель не
# знал, что он на посту, — работу ему подкладывали снаружи на время
# разговора. Ректор не знал, что он ректор.
#
# Стало: в паспорте поле "Посты" — список того, что житель сейчас
# делает. Душа, стол и память читают паспорт и так, значит работу
# видят сами. Одна правда, одно место.
#
# Это НЕ «прикрутить личность к роли» (закон Шефа в шапке файла в
# силе). Пост в паспорте — состояние, а не порода: сняли с поста,
# строка ушла, житель прежний. Чертёж §1.5.2б: роль живёт внутри Рода.
POLE_POSTY = "Посты"


def _pasport_put(imya: str):
    """Путь к паспорту жителя. Нет жителя — None."""
    d = KOVCHEG / imya
    p = d / "passport.json"
    return p if p.exists() else None


def _posty_zhitelya(imya: str) -> list:
    p = _pasport_put(imya)
    if p is None:
        return []
    spisok = (_read_json(p, {}) or {}).get(POLE_POSTY, [])
    return spisok if isinstance(spisok, list) else []


def _zapisat_posty(imya: str, spisok: list) -> bool:
    """Кладёт список постов в паспорт, НЕ трогая остальное. Паспорт
    перечитывается прямо перед записью — рядом может работать движок."""
    p = _pasport_put(imya)
    if p is None:
        return False
    pasport = _read_json(p, None)
    if not isinstance(pasport, dict):
        return False
    if spisok:
        pasport[POLE_POSTY] = spisok
    else:
        pasport.pop(POLE_POSTY, None)   # пустой список не держим
    return _write_json(p, pasport)


def perenesti_posty() -> int:
    """Разовый переезд старых хранитель.json в паспорта. Зовётся сам
    при первом обращении к постам, вручную не нужен.

    Старый файл НЕ удаляем — переименовываем в .перенесено, чтобы
    никто случайно не прочитал устаревшую правду, но и не потерять.
    """
    if not POSTY_DIR.exists():
        return 0
    pereehalo = 0
    for d in sorted(POSTY_DIR.iterdir()):
        f = d / "хранитель.json"
        if not f.is_dir() and f.exists():
            imya = (_read_json(f, {}) or {}).get("житель", "")
            if imya and _pasport_put(imya) is not None:
                spisok = _posty_zhitelya(imya)
                if not any(x.get("пост") == d.name for x in spisok
                           if isinstance(x, dict)):
                    spisok.append({
                        "пост": d.name,
                        "с": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    })
                    _zapisat_posty(imya, spisok)
                    pereehalo += 1
            try:
                f.rename(d / "хранитель.json.перенесено")
            except Exception:
                pass
    return pereehalo


_perenos_sdelan = False


def _perenos_odin_raz():
    global _perenos_sdelan
    if not _perenos_sdelan:
        _perenos_sdelan = True
        try:
            perenesti_posty()
        except Exception:
            pass   # переезд не должен ронять город


def posadit(post_id: str, imya_zhitelya: str, zid: str = "") -> tuple:
    """Сажает жителя на пост. Род НЕ проверяется — закон Шефа.
    Пост занят другим — честно сменяем, но возвращаем, кто был,
    чтобы вызывающий мог сказать это вслух (не тайком).

    POST_V_PASPORTE_V1: пишем в паспорт. Заодно снимаем прежнего —
    иначе два паспорта заявят один пост, и никто не заметит.

    Возвращает (успех: bool, сообщение: str).
    """
    _perenos_odin_raz()
    d = POSTY_DIR / post_id
    if not (d / "пост.json").exists():
        return False, f"поста «{post_id}» нет — сначала заведи"
    if _pasport_put(imya_zhitelya) is None:
        return False, f"жителя «{imya_zhitelya}» нет в ковчеге"

    byl = kto_na_postu(post_id)
    if byl and byl != imya_zhitelya:
        # снимаем прежнего явно: одна правда, дублей не заводим
        _zapisat_posty(byl, [x for x in _posty_zhitelya(byl)
                             if not (isinstance(x, dict)
                                     and x.get("пост") == post_id)])

    spisok = [x for x in _posty_zhitelya(imya_zhitelya)
              if not (isinstance(x, dict) and x.get("пост") == post_id)]
    spisok.append({
        "пост": post_id,
        "id": zid,
        "с": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })
    if not _zapisat_posty(imya_zhitelya, spisok):
        return False, "не записался в паспорт"
    if byl and byl != imya_zhitelya:
        return True, f"сменил(а) на посту: {byl}"
    return True, "на посту"


def snyat(post_id: str) -> tuple:
    """Освобождает пост. Пост остаётся, вакансия открыта."""
    _perenos_odin_raz()
    imya = kto_na_postu(post_id)
    if not imya:
        return True, "пост и так свободен"
    ok = _zapisat_posty(imya, [x for x in _posty_zhitelya(imya)
                               if not (isinstance(x, dict)
                                       and x.get("пост") == post_id)])
    return (True, "пост освобождён") if ok else (False, "паспорт не записался")


def kto_na_postu(post_id: str) -> str:
    """Имя того, кто сейчас на посту. Пусто — вакансия.

    POST_V_PASPORTE_V1: смотрим паспорта. Ковчег маленький, обход
    дешёвый, зато правда одна и врать нечему.
    """
    _perenos_odin_raz()
    vse = kto_na_postu_vse(post_id)
    return vse[0] if vse else ""


def kto_na_postu_vse(post_id: str) -> list:
    """Все, кто заявил этот пост. В норме ноль или один. Двое —
    рассинхрон, и его лучше увидеть, чем спрятать: кабинет может
    показать это Шефу."""
    if not KOVCHEG.exists():
        return []
    out = []
    for d in sorted(KOVCHEG.iterdir()):
        if not d.is_dir():
            continue
        for x in _posty_zhitelya(d.name):
            if isinstance(x, dict) and x.get("пост") == post_id:
                out.append(d.name)
                break
    return out
'''

PRAVKI = [
    (T_DVI, B_DVI, [("запись паспорта сливает, а не затирает", D_OLD, D_NEW)]),
    (T_REZ, B_REZ, [("связь поста переезжает в паспорт", R_OLD, R_NEW)]),
]


def main() -> int:
    for target, _, _ in PRAVKI:
        if not target.exists():
            print(f"✗ не нашёл {target} — запускать из КОРНЯ репо")
            return 1

    if all(MARKER in t.read_text(encoding="utf-8") for t, _, _ in PRAVKI):
        print(f"✓ {MARKER} уже стоит — патч идемпотентен, ничего не делаю")
        return 0

    gotovo = []
    for target, bak, pravki in PRAVKI:
        src = target.read_text(encoding="utf-8")
        if MARKER in src:
            print(f"  · {target.name} — уже пропатчен, пропускаю")
            continue
        novyy = src
        for imya, old, new in pravki:
            n = novyy.count(old)
            if n != 1:
                print(f"✗ {target.name}, якорь «{imya}»: найден {n} раз "
                      f"(нужно 1). Файл изменился — НИЧЕГО не применено.")
                return 1
            novyy = novyy.replace(old, new, 1)
        try:
            ast.parse(novyy)
        except SyntaxError as e:
            print(f"✗ {target.name}: ast.parse упал: {e}. Ничего не записал.")
            return 1
        gotovo.append((target, bak, src, novyy))
        print(f"  · {target.name} — готов")

    for target, bak, src, novyy in gotovo:
        shutil.copy2(target, bak)
        target.write_text(novyy, encoding="utf-8")
        try:
            py_compile.compile(str(target), doraise=True)
        except py_compile.PyCompileError as e:
            shutil.copy2(bak, target)
            print(f"✗ {target.name}: py_compile упал: {e}. Откатил.")
            return 1
        print(f"✓ {target.name}: {len(src)} → {len(novyy)} символов, бэкап {bak.name}")

    print(f"\n✓ {MARKER} применён")
    print("  Старые хранитель.json переедут в паспорта при первом обращении")
    print("  и станут .перенесено — ничего не удаляется.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
