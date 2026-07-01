# dvizhok.py — личный движок жителя. Лежит в доме жителя.
# ─────────────────────────────────────────────────────────────
# СУТЬ: орган дыхания. Не мозг (решает житель), не город (свой у каждого).
#   ВХОД (факт: контекст, сила, свежесть)
#     → через РУЧКИ жителя (DNA_Static из паспорта)
#     → ВДОХ: насколько вход тронул = f(сила, свежесть, ручки)
#     → сдвиг состояния (charge ±, к балансу)
#     → открывает глубину памяти по |charge|
#   Решение и выход — НЕ здесь (следующие камни). Движок только дышит.
#
# Прежде она — житель (ядро). Из ядра вдох. Ручки — её натура.
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import json
from pathlib import Path
from datetime import datetime, timezone

# контекст входа → в какой слой осядет (Закон Слоёв)
KONTEKST_SLOI = {
    "факт":     "sensory",    # сухой факт дня — свежее
    "работа":  "sensory",     # дело — свежее (потом архивируется)
    "общение": "resonance",   # с кем общалась — связи
    "учёба":   "archive",     # узнала — осело глубоко
    "дом":     "sensory",     # личное, свежее
}

# знак входа: что тянет вверх (+), что вниз (−)
# но РЕШАЕТ не это — это лишь куда качнуло маятник
def _znak(tonus: str) -> float:
    return {"плюс": 1.0, "минус": -1.0, "ровно": 0.0}.get(tonus, 0.0)


# OSTYVANIE_ZARYADA_V1: заряд тает к нулю с каждым вдохом, не застывает.
# Не по реальному времени — на фиксированный процент за вдох (иначе без
# диалога обида не пройдёт сама за неделю тишины). Упрямство держит
# заряд дольше: упрямый таёт медленнее.
OSTYVANIE_BAZA = 0.10   # базовый процент остывания за один вдох (10%)


class Dvizhok:
    """Личный движок одного жителя. Дышит его паспортом."""

    def __init__(self, dom: Path):
        self.dom = Path(dom)
        self.passport_path = self.dom / "passport.json"
        self.p = json.loads(self.passport_path.read_text(encoding="utf-8"))
        # РУЧКИ — из натуры жителя
        dna = self.p.get("DNA_Static", {})
        self.empathy    = dna.get("Empathy", 0.5)
        self.stubborn   = dna.get("Stubbornness", 0.5)
        self.resonance  = dna.get("Resonance_Frequency", 0.5)
        # СОСТОЯНИЕ — заряд. Если в паспорте нет — рождаем в покое (0.0).
        self.charge = self.p.get("_charge", 0.0)

    def vdoh(self, kontekst: str, sila: float, svezhest: float, tonus: str = "ровно") -> dict:
        """Вдох: входящий факт проходит через ядро.
        сила 0..1, свежесть 0..1 (1=только что, 0=давно).
        Возвращает что стало — но НЕ решает за жителя."""
        # OSTYVANIE_ZARYADA_V1: маятник сначала чуть качнулся обратно к
        # покою САМ (до нового толчка) — упрямый тает медленнее.
        _ostyv_koef = OSTYVANIE_BAZA * (1.0 - 0.7 * self.stubborn)
        self.charge *= (1.0 - _ostyv_koef)

        # насколько тронуло = сила × свежесть × резонанс ядра.
        # эмпатия усиливает удар (чужое чувствуется как своё).
        trogaet = sila * svezhest * (0.5 + self.resonance) * (0.5 + self.empathy)
        trogaet = min(1.0, trogaet)

        # сдвиг заряда: вдох даёт ЧАСТЬ, не всё разом — маятник копится,
        # не прыгает в край. Упрямство держит уже набранное (медленнее тает,
        # но и новый вход сдвигает осторожнее — натура устойчивая).
        VDOH_COEF = 0.35           # один вдох двигает максимум на треть
        sdvig = _znak(tonus) * trogaet * VDOH_COEF
        self.charge = max(-1.0, min(1.0, self.charge + sdvig))

        # глубина открытой памяти по |заряду| (стресс-шлюз)
        c = abs(self.charge)
        if c < 0.25:
            sloi = ["core"]
        elif c < 0.55:
            sloi = ["core", "sensory"]
        elif c < 0.8:
            sloi = ["core", "sensory", "resonance"]
        else:
            sloi = ["core", "sensory", "resonance", "archive"]

        # куда осело событие (по контексту)
        osel_v = KONTEKST_SLOI.get(kontekst, "sensory")

        return {
            "тронуло":     round(trogaet, 3),
            "заряд":       round(self.charge, 3),
            "открыто":     sloi,
            "осело_в":     osel_v,
        }

    def _zapisat_sobytie(self, sloy: str, fakt: str, vdoh_result: dict):
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
                    f.write(json.dumps(zapis, ensure_ascii=False) + "\n")
            elif sloy == "archive":
                # archive.jsonl — JSONL, дозапись строкой
                p = self.dom / "archive" / "archive.jsonl"
                with open(p, "a", encoding="utf-8") as f:
                    f.write(json.dumps(zapis, ensure_ascii=False) + "\n")
        except Exception:
            pass  # память не должна ронять дыхание — пропускаем тихо

    def vydoh_stol(self, fakt: str, vdoh_result: dict) -> dict:
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
        }

    def sохранить(self):
        """Заряд оседает в паспорт (состояние помнится между вдохами)."""
        self.p["_charge"] = round(self.charge, 4)
        self.p["_charge_ts"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.passport_path.write_text(
            json.dumps(self.p, ensure_ascii=False, indent=2), encoding="utf-8")