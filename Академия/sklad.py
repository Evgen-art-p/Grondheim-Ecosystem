# -*- coding: utf-8 -*-
# SKLAD_AKADEMII_V1
"""
СКЛАД АКАДЕМИИ — карточки и ключи.

СЛОВА ШЕФА (15.09)
    «Мне важно, чтобы житель прочёл инфу в Академии, мог это
    использовать когда требуется, где требуется, и это не мешало
    всем остальным.»
    «Академия — только я подписываю.»

ЧТО ЭТО ТАКОЕ
    Единица склада — не файл, а КАРТОЧКА. Одна карточка — одна мысль.
    Страница с рисунком и подписью под ним — карточка (резать её не
    надо: у Вильямса объяснение и рисунок стоят на одной странице
    нарочно). Глава — не карточка, это стопка карточек.

КЛЮЧ — ДВЕ ПОЛОВИНЫ (решение Шефа 09.09, тот же закон, что у метки)
    ОБЩАЯ половина — одна на всех, живёт ЗДЕСЬ, на складе:
        откуда · когда · от кого · подпись Шефа
        Ничьих мнений в ней нет, только происхождение.
    ЛИЧНАЯ половина — своя у каждого, живёт В ДОМЕ ЖИТЕЛЯ:
        ярлыки его словами · важность его глазами · прочитано ·
        поправки учителя по этой карточке
        Уезжает вместе с человеком при переезде.

    Карточка на складе ОДНА, личных половин у неё сколько угодно.
    Одна и та же страница у реставратора икон и у трейдера подписана
    по-разному — это не беспорядок, это то, ради чего всё делается.

ПОЧЕМУ ЭТО ВООБЩЕ СТРОИТСЯ
    Раньше в память ученика ложился только его ПЕРЕСКАЗ материала.
    Вернуться к оригиналу он не мог: посмотрел раз, пересказал — и
    живёшь с пересказом. Теперь рядом с выводом лежит КЛЮЧ, и житель
    достаёт оригинал своей рукой — и за партой, и на Бирже за столом.

ЗАКОНЫ ЭТОГО ФАЙЛА
    · ПОДПИСЫВАЕТ ТОЛЬКО ШЕФ. Машина за него не сочиняет. Не сказал
      подписи — карточка честно лежит без неё и ищется по источнику.
      Библиотекаря здесь нет намеренно: не строим то, чем не будут
      пользоваться.
    · МАТЕРИАЛ КОПИРУЕТСЯ НА СКЛАД, а не запоминается ссылкой. Иначе
      убрал исходник — карточка мертва.
    · СКЛАД НЕ РАСХОДУЕТСЯ. Нина прочитала — для Синди осталась
      непрочитанной.
    · САМОДОСТАТОЧЕН (Закон Двух Стандартов): ничего не импортирует
      из Академии и Биржи, только стандартная библиотека. Его зовут —
      он не зовёт.
    · ХРАНИМ ИМЯ ИСТОЧНИКА, А НЕ ОЦЕНКУ. Сколько весит подпись —
      решает тот, кто достаёт.

`шесть·проверено·до·корня`
"""
from __future__ import annotations

import json
import hashlib
import shutil
import re
from datetime import datetime, timezone
from pathlib import Path

# ── ГДЕ ЧТО ЛЕЖИТ ──────────────────────────────────────────
_HERE = Path(__file__).resolve().parent          # Академия/
_REPO = _HERE.parent                             # корень репо
_SKLAD = _REPO / "GRONDHEIM_CITY" / "Академия" / "склад"
_MATERIALY = _SKLAD / "материалы"
_KARTOCHKI = _SKLAD / "карточки.json"

# личная половина ключа — в доме жителя, рядом с его памятью
_LICHNOE_IMYA = "ключи_склада.json"

KARTINKA_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
TEKST_EXT = {".txt", ".md", ".rtf"}


# ═══════════════════════════════════════════════════════════
# ДИСК — читаем честно, пустое отдаём пустым
# ═══════════════════════════════════════════════════════════

def _chitat_json(p: Path, pusto):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return pusto


def _pisat_json(p: Path, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                 encoding="utf-8")


def _dvor():
    """Склад заводит свой двор сам — не падаем на пустом городе."""
    _MATERIALY.mkdir(parents=True, exist_ok=True)
    if not _KARTOCHKI.exists():
        _pisat_json(_KARTOCHKI, {"карточки": {}})


def _seychas() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ═══════════════════════════════════════════════════════════
# КЛЮЧ
# ═══════════════════════════════════════════════════════════

def _chistoe(s: str) -> str:
    """Кусок ключа: буквы, цифры, подчёркивание. Читаемый, не хеш."""
    s = (s or "").strip().lower()
    s = re.sub(r"[^\wа-яё]+", "_", s, flags=re.IGNORECASE)
    return s.strip("_")[:40]


def sdelat_klyuch(istochnik: str, chast: str = "", nomer: str = "") -> str:
    """Читаемый ключ из происхождения: «вильямс/гл07/стр11».

    Ключ — это адрес, а не имя файла. По нему на карточку ссылаются
    из памяти жителя, из урока, с Биржи.
    """
    kuski = [_chistoe(x) for x in (istochnik, chast, nomer) if (x or "").strip()]
    kuski = [k for k in kuski if k]
    return "/".join(kuski) if kuski else "без_имени"


def _svobodnyy_klyuch(klyuch: str, vse: dict) -> str:
    """Ключ занят — дописываем номер. Молча не затираем чужое."""
    if klyuch not in vse:
        return klyuch
    n = 2
    while f"{klyuch}_{n}" in vse:
        n += 1
    return f"{klyuch}_{n}"


def _imya_na_diske(klyuch: str, suffix: str) -> str:
    """Имя файла материала — ASCII, из ключа.

    Нарочно не кириллицей: терминал Шефа (PowerShell) кириллические
    пути режет, и первая буква теряется. Настоящее имя исходника
    живёт в карточке, а на диске лежит спокойный ASCII.
    """
    h = hashlib.sha1(klyuch.encode("utf-8")).hexdigest()[:12]
    return f"{h}{suffix.lower()}"


# ═══════════════════════════════════════════════════════════
# ОБЩАЯ ПОЛОВИНА — склад
# ═══════════════════════════════════════════════════════════

def vse_kartochki() -> dict:
    _dvor()
    return (_chitat_json(_KARTOCHKI, {"карточки": {}}) or {}).get("карточки", {})


def kartochka(klyuch: str) -> dict:
    """Одна карточка по ключу. Нет такой — пустой словарь, не падаем."""
    return vse_kartochki().get(klyuch, {})


def skolko() -> int:
    return len(vse_kartochki())


def polozhit(put_faila=None, tekst: str = "", otkuda: str = "",
             podpis: str = "", tema: str = "", klyuch: str = "",
             podpisal: str = "Шеф", chast: str = "", nomer: str = "") -> str:
    """Положить карточку на склад. Возвращает ключ.

    put_faila — картинка или текстовый файл (можно вместе с tekst,
                если на странице рисунок и объяснение рядом);
    tekst     — текст карточки, если он не файлом;
    otkuda    — ПРОИСХОЖДЕНИЕ словами: «книга «Торговый Хаос», Билл
                Вильямс, глава 7, страница 11». Не имя файла;
    podpis    — что тут нарисовано/написано. Ставит ТОЛЬКО Шеф;
    tema      — одним словом: трейдинг, психология…;
    klyuch    — можно задать свой; пусто — соберётся из источника.

    Материал КОПИРУЕТСЯ на склад. Исходник можно потом убрать.
    """
    _dvor()
    vse = vse_kartochki()

    fp = Path(put_faila) if put_faila else None
    if fp is not None and not fp.is_file():
        raise FileNotFoundError(f"нет такого файла: {fp}")

    if not klyuch:
        osnova = otkuda or (fp.stem if fp else "карточка")
        klyuch = sdelat_klyuch(osnova, chast, nomer or (fp.stem if fp else ""))
    klyuch = _svobodnyy_klyuch(klyuch, vse)

    zapis = {
        "ключ": klyuch,
        "откуда": (otkuda or "").strip(),
        "подпись": (podpis or "").strip(),
        "подписал": (podpisal or "").strip() if (podpis or "").strip() else "",
        "тема": (tema or "").strip(),
        "когда": _seychas(),
        "вид": "",
        "файл": "",
        "имя_исходника": "",
        "текст": (tekst or "").strip(),
    }

    if fp is not None:
        suffix = fp.suffix.lower()
        imya = _imya_na_diske(klyuch, suffix)
        shutil.copy2(fp, _MATERIALY / imya)
        zapis["файл"] = imya
        zapis["имя_исходника"] = fp.name
        if suffix in KARTINKA_EXT:
            zapis["вид"] = "оба" if zapis["текст"] else "изображение"
        elif suffix in TEKST_EXT:
            if not zapis["текст"]:
                try:
                    zapis["текст"] = fp.read_text(
                        encoding="utf-8", errors="replace").strip()
                except Exception:
                    pass
            zapis["вид"] = "текст"
        else:
            zapis["вид"] = "файл"
    else:
        zapis["вид"] = "текст" if zapis["текст"] else "пусто"

    vse[klyuch] = zapis
    _pisat_json(_KARTOCHKI, {"карточки": vse})
    return klyuch


def polozhit_pachku(papka, otkuda: str = "", podpis: str = "",
                    tema: str = "", istochnik: str = "",
                    chast: str = "") -> list:
    """Пачка страниц разом: источник один, номера — из имён файлов.

    Так кладётся глава книги: подпись одна на всю пачку, а ключи
    получаются сами — «вильямс/гл07/gl07_str11_1» и так далее.
    Возвращает список ключей в порядке укладки.
    """
    p = Path(papka)
    if not p.is_dir():
        raise NotADirectoryError(f"нет такой папки: {p}")
    klyuchi = []
    for f in sorted(p.iterdir()):
        if not f.is_file():
            continue
        if f.suffix.lower() not in (KARTINKA_EXT | TEKST_EXT):
            continue
        klyuchi.append(polozhit(
            put_faila=f, otkuda=otkuda, podpis=podpis, tema=tema,
            klyuch=sdelat_klyuch(istochnik or otkuda, chast, f.stem)))
    return klyuchi


def dostat(klyuch: str):
    """(карточка, путь к материалу или None, текст).

    Это и есть «посмотреть». Платный взгляд модели — дело того, кто
    зовёт: склад просто отдаёт, что у него есть.
    """
    k = kartochka(klyuch)
    if not k:
        return {}, None, ""
    put = (_MATERIALY / k["файл"]) if k.get("файл") else None
    if put is not None and not put.exists():
        put = None
    return k, put, k.get("текст", "")


def perepodpisat(klyuch: str, podpis: str, podpisal: str = "Шеф") -> bool:
    """Переписать общую подпись. Кто и когда — записывается заново."""
    _dvor()
    vse = vse_kartochki()
    if klyuch not in vse:
        return False
    vse[klyuch]["подпись"] = (podpis or "").strip()
    vse[klyuch]["подписал"] = podpisal
    vse[klyuch]["подписано_когда"] = _seychas()
    _pisat_json(_KARTOCHKI, {"карточки": vse})
    return True


# ═══════════════════════════════════════════════════════════
# ЛИЧНАЯ ПОЛОВИНА — дом жителя
# ═══════════════════════════════════════════════════════════

def _lichnoe_put(dom) -> Path:
    return Path(dom) / _LICHNOE_IMYA


def moi_klyuchi(dom) -> dict:
    """Вся личная половина жителя: {ключ: {ярлыки, важность, ...}}"""
    return _chitat_json(_lichnoe_put(dom), {}) or {}


def moy_klyuch(dom, klyuch: str) -> dict:
    return moi_klyuchi(dom).get(klyuch, {})


def pomenit(dom, klyuch: str, yarlyki=None, vazhnost: str = "") -> dict:
    """Житель вешает СВОИ ярлыки и ставит СВОЮ важность.

    Важность ставит только сам житель — «это его жизнь, пусть
    отвечает» (слово Шефа 09.09). Общую подпись это не трогает
    никогда: склад не должен начать врать всем остальным чужими
    глазами.
    """
    lich = moi_klyuchi(dom)
    zap = lich.get(klyuch, {"ярлыки": [], "важность": "", "прочитано": "",
                            "поправки": []})
    for y in (yarlyki or []):
        y = (y or "").strip().lower()
        if y and y not in zap["ярлыки"]:
            zap["ярлыки"].append(y)
    if vazhnost:
        zap["важность"] = vazhnost.strip()
    lich[klyuch] = zap
    _pisat_json(_lichnoe_put(dom), lich)
    return zap


def otmetit_prochitannym(dom, klyuch: str) -> None:
    """Склад не расходуется: отметка личная, у каждого своя."""
    lich = moi_klyuchi(dom)
    zap = lich.get(klyuch, {"ярлыки": [], "важность": "", "прочитано": "",
                            "поправки": []})
    zap["прочитано"] = _seychas()
    lich[klyuch] = zap
    _pisat_json(_lichnoe_put(dom), lich)


def popravka(dom, klyuch: str, tekst: str, ot_kogo: str = "Шеф") -> None:
    """Поправка учителя ложится К КАРТОЧКЕ, а не в общий котёл.

    Ради этого всё и затевалось: через месяц житель достаёт карточку
    и достаёт вместе с ней то, что Шеф ему про неё сказал. Не пересказ
    урока — сам урок, привязанный к материалу.
    """
    lich = moi_klyuchi(dom)
    zap = lich.get(klyuch, {"ярлыки": [], "важность": "", "прочитано": "",
                            "поправки": []})
    zap.setdefault("поправки", []).append(
        {"текст": (tekst or "").strip(), "от_кого": ot_kogo,
         "когда": _seychas()})
    lich[klyuch] = zap
    _pisat_json(_lichnoe_put(dom), lich)


def prochitannoe(dom) -> list:
    """Ключи, которые этот житель уже читал."""
    return [k for k, v in moi_klyuchi(dom).items() if v.get("прочитано")]


# ═══════════════════════════════════════════════════════════
# ПОИСК — три входа
# ═══════════════════════════════════════════════════════════

def _slova(zapros: str) -> list:
    return [w for w in re.split(r"[^\wа-яё]+", (zapros or "").lower())
            if len(w) > 2]


def nayti(o_chyom: str = "", tema: str = "", istochnik: str = "",
          dom=None, skolko_nado: int = 5, tolko_neprochitannoe: bool = False
          ) -> list:
    """[(ключ, карточка, очки)] — по словам, по теме, по источнику.

    Вес взят из закона меток (09.09): совпадение по ЯРЛЫКУ жителя
    весит как пять слов. Один ярлык достаёт широко, два сужают, три
    бьют в точку.

    dom — если передан, в поиске участвует личная половина этого
    жителя: его ярлыки и его важность. Не передан — ищем только по
    общей половине, одинаково для всех.
    """
    lich = moi_klyuchi(dom) if dom else {}
    slova = _slova(o_chyom)
    tema = (tema or "").strip().lower()
    istochnik = (istochnik or "").strip().lower()

    ocenki = []
    for klyuch, k in vse_kartochki().items():
        moyo = lich.get(klyuch, {})

        if tolko_neprochitannoe and moyo.get("прочитано"):
            continue
        if tema and tema not in (k.get("тема", "") or "").lower():
            continue
        if istochnik and istochnik not in (
                f"{k.get('откуда','')} {klyuch}").lower():
            continue

        if not slova:
            ocenki.append((0, klyuch, k))
            continue

        seno_obshee = " ".join([
            k.get("подпись", ""), k.get("откуда", ""), k.get("тема", ""),
            klyuch, k.get("имя_исходника", ""), k.get("текст", "")[:2000],
        ]).lower()
        ochki = sum(1 for w in slova if w in seno_obshee)
        # подпись Шефа весит больше, чем случайное совпадение в тексте
        podpis = (k.get("подпись", "") or "").lower()
        ochki += sum(2 for w in slova if w in podpis)
        # ярлык жителя весит как пять слов — закон меток
        for y in (moyo.get("ярлыки") or []):
            if any(w in y for w in slova):
                ochki += 5
        if moyo.get("важность") in ("высокая", "высокий", "важно"):
            ochki += 2
        if ochki:
            ocenki.append((ochki, klyuch, k))

    ocenki.sort(key=lambda x: (-x[0], x[1]))
    return [(kl, k, o) for o, kl, k in ocenki[:max(1, skolko_nado)]]


def po_istochniku(istochnik: str) -> list:
    """Стопка по порядку: «покажи главу 7 Вильямса»."""
    naydeno = nayti(istochnik=istochnik, skolko_nado=10_000)
    return sorted(naydeno, key=lambda x: x[0])


def chto_est() -> str:
    """Что вообще на складе — по темам и источникам, словами."""
    vse = vse_kartochki()
    if not vse:
        return "склад пуст — ни одной карточки"
    po_teme, bez_podpisi = {}, 0
    for k in vse.values():
        t = k.get("тема") or "без темы"
        po_teme[t] = po_teme.get(t, 0) + 1
        if not k.get("подпись"):
            bez_podpisi += 1
    stroki = [f"карточек всего: {len(vse)}"]
    stroki += [f"  · {t} — {n}" for t, n in sorted(po_teme.items())]
    if bez_podpisi:
        stroki.append(f"  ⚠ без подписи Шефа: {bez_podpisi} "
                      f"(ищутся только по источнику)")
    return "\n".join(stroki)


def dlya_promta(dom, klyuchi=None, skolko_nado: int = 6) -> str:
    """Кусок в промпт: что житель про эти карточки уже знает.

    Ни одного материала сюда не кладём — только ключи, ярлыки и
    поправки. Сам материал достаётся рукой, и за него платят.
    """
    lich = moi_klyuchi(dom)
    if not lich:
        return ""
    klyuchi = klyuchi or list(lich.keys())
    stroki = []
    for kl in klyuchi[:skolko_nado]:
        zap = lich.get(kl) or {}
        k = kartochka(kl)
        if not k:
            continue
        hvost = ""
        if zap.get("ярлыки"):
            hvost += " · мои ярлыки: " + ", ".join(zap["ярлыки"])
        if zap.get("поправки"):
            hvost += " · поправок: " + str(len(zap["поправки"]))
        stroki.append(f"  [{kl}] {k.get('подпись') or k.get('откуда') or ''}"
                      f"{hvost}")
    if not stroki:
        return ""
    return ("\n=== ЧТО Я УЖЕ РАЗБИРАЛ (достать могу рукой по ключу) ===\n"
            + "\n".join(stroki) + "\n")


# SKLAD_AKADEMII_V1 - marker
