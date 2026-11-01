#!/usr/bin/env python3
"""Auditor live web cho DBO/IDBO menu API (black-box, không import solver).

Chạy: venv/bin/python scripts/auditor_grill_live_web.py \
        --base-url http://127.0.0.1:8000 --profiles 100 --min-seconds 900 --max-seconds 1740

Ghi kết quả vào experiments/audit_live_web_<timestamp>/ (config, raw jsonl, summary, REPORT.md).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import math
import re
import statistics
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------- từ vựng độc lập
def _words(*items: str) -> re.Pattern:
    """Khớp theo từ nguyên vẹn (tránh 'cá' lọt vào 'củ cái')."""
    return re.compile(r"\b(?:" + "|".join(items) + r")\b", re.IGNORECASE)


CONDIMENT_RE = re.compile(
    r"nước mắm|mắm tôm|mắm cá|\bmuối\b|bột ngọt|mì chính|hạt nêm|dầu ăn|dầu thực vật|"
    r"dầu đậu nành|tương ớt|tương cà|nước tương|\bgiấm\b|\bđường\b|bột năng|bột mì|"
    r"hạt tiêu|ớt bột|sa tế|gia vị|nước cốt dừa|dầu mè|mỡ nước",
    re.IGNORECASE,
)
RAW_RE = re.compile(
    r"\bgạo\b|\bgạo lứt\b|\bnếp\b|\bđậu xanh\b|\bđậu tương\b|\bđậu nành\b|\bđậu đen\b|"
    r"\bđậu hà lan\b|\bkhoai tây\b|\bmăng tre\b|\bmăng tươi\b|\bcủ sắn\b|\bkhoai mì\b|"
    r"\bbột\b|\bmen\b",
    re.IGNORECASE,
)
PREP_RE = _words(
    "xào", "luộc", "hấp", "chiên", "rán", "kho", "nướng", "canh", "súp", "cháo", "cơm",
    "bún", "phở", "bánh mì", "sữa chua", "sinh tố", "nộm", "gỏi", "chả", "giò", "xúc xích",
    "rim", "om", "hầm", "trộn", "cuốn", "quay", "ram", "sốt", "rang", "nấu", "chín",
)
READY_RE = _words(
    "chuối", "táo", "cam", "bưởi", "xoài", "nho", "ổi", "dứa", "hồng", "đu đủ", "lê",
    "lựu", "mít", "mơ", "na", "nhãn", "quít", "sầu riêng", "vải", "khế", "thanh long",
    "dưa hấu", "mận", "chôm chôm", "măng cụt", "kiwi", "sữa", "trứng", "hạt", "đậu phụ",
    "lạc", "bơ",
)
DAIRY_RE = _words("sữa", "sữa chua", "phô mai", "yogurt", "sữa tươi", "sữa đậu", "sữa bò", "sữa dê")
SOUP_RE = _words("canh", "súp", "cháo", "broth")
STAPLE_RE = _words(
    "cơm", "gạo", "bún", "phở", "mì", "miến", "bánh mì", "khoai", "ngô", "kê", "yến mạch",
    "nếp", "bắp", "bánh cuốn", "bánh ướt", "bánh phở",
)
PROTEIN_RE = _words(
    "thịt", "bò", "heo", "lợn", "gà", "vịt", "cá", "tôm", "cua", "mực", "tép", "nghêu",
    "sò", "hến", "trứng", "đậu phụ", "chả", "giò", "sườn", "chim", "bồ câu", "thỏ", "ếch",
    "lươn", "đuôi", "chân giò", "gan", "tim", "lòng", "ba chỉ", "nạc", "xúc xích", "dăm bông",
    "óc",
)
VEG_RE = _words(
    "rau", "cải", "muống", "ngót", "dền", "mồng tơi", "xà lách", "dưa leo", "cà chua",
    "cà pháo", "bí", "bầu", "mướp", "súp lơ", "bông cải", "nấm", "măng", "su hào", "cà rốt",
    "giá", "su su", "đậu cô ve", "ngồng", "hành", "tỏi", "cà tím", "củ", "mướp đắng", "khổ qua",
)
FRUIT_RE = _words(
    "quả", "trái", "chuối", "táo", "cam", "bưởi", "xoài", "nho", "ổi", "dứa", "hồng",
    "đu đủ", "lê", "lựu", "mít", "mơ", "na", "nhãn", "quít", "sầu riêng", "vải", "khế",
    "hạt", "sữa", "dưa hấu", "thanh long", "mận", "chôm chôm", "măng cụt", "kiwi", "bơ",
)
SEAFOOD_RE = _words("tôm", "cua", "cá", "mực", "tép", "nghêu", "sò", "hến", "ghẹ", "hải sản")
# Món có dạng món ăn rõ ràng → luôn là tinh bột, kể cả khi tên chứa từ khoá khác.
STICKY_STAPLE_RE = _words("cơm", "bún", "phở", "bánh mì", "miến", "mì", "xôi", "cháo", "bánh phở")
# Từ đầu của tên rau/củ/quả: ưu tiên hơn tinh bột để tránh 'Bí ngô' bị nhận là 'ngô'.
VEG_HEAD_RE = _words("bí", "bầu", "mướp", "rau", "cải", "cà", "su", "măng", "nấm", "củ",
                    "bắp cải", "dưa leo", "đậu cô ve", "hành", "tỏi", "ngồng", "giá")

SODIUM_HYP = 1500.0
SODIUM_GEN = 2300.0

AGES = [("18-25", 22), ("26-45", 35), ("46-65", 55), (">65", 72)]
BMIS = [("underweight", 17.0), ("normal", 21.5), ("overweight", 27.0), ("obese1", 32.0), ("obese2", 37.0)]
ACTS = ["SEDENTARY", "LIGHT", "MODERATE", "ACTIVE", "VERY_ACTIVE"]
MEALS = [
    ("3meals", {"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 0}),
    ("4meals", {"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 1}),
    ("big", {"breakfast": 3, "lunch": 3, "dinner": 3, "snack": 2}),
    ("light", {"breakfast": 1, "lunch": 2, "dinner": 2, "snack": 0}),
]


def bmi_class(bmi: float) -> str:
    if bmi < 18.5:
        return "underweight"
    if bmi < 25:
        return "normal"
    if bmi < 30:
        return "overweight"
    if bmi < 35:
        return "obese1"
    return "obese2"


def p95(values: list[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    return s[min(len(s) - 1, int(round(0.95 * (len(s) - 1))))]


@dataclass
class Req:
    phase: str
    label: str
    method: str
    path: str
    status: int | str
    latency_ms: float
    config: str | None = None
    note: str = ""


@dataclass
class MenuRec:
    phase: str
    label: str
    config: str
    seed: int
    profile: dict
    items: list
    totals: dict
    targets: dict
    violations: list
    fitness: float | None
    diversity: float | None
    latency_ms: float


class Auditor:
    def __init__(self, base_url: str, out: Path, min_seconds: int, max_seconds: int):
        self.base_url = base_url
        self.out = out
        self.out.mkdir(parents=True, exist_ok=True)
        self.min_seconds = min_seconds
        self.max_seconds = max_seconds
        self.t0 = time.perf_counter()
        self.client = httpx.Client(base_url=base_url, timeout=httpx.Timeout(180.0, connect=10.0))
        self.reqs: list[Req] = []
        self.menus: list[MenuRec] = []
        self.swap_chains: list[dict] = []
        self.concurrency: dict = {}
        self.determinism: dict = {}
        self.chaos: list[dict] = []
        self.clinical: dict = {}
        self.allergy: dict = {}
        self.inventory: dict = {}
        self.matrix_meta: list[dict] = []
        self.skipped: dict[str, int] = {}
        self.log_path = self.out / "run.log"

    # ------------------------------------------------------------- utils
    def elapsed(self) -> float:
        return time.perf_counter() - self.t0

    def remaining(self) -> float:
        return self.max_seconds - self.elapsed()

    def log(self, msg: str) -> None:
        line = f"[{self.elapsed():7.1f}s] {msg}"
        print(line, flush=True)
        with self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")

    def request(self, phase, label, method, path, payload=None, config=None, raw=None,
                params=None) -> dict:
        t = time.perf_counter()
        status: int | str = "ERR"
        note = ""
        data = None
        try:
            headers = {"content-type": "application/json"}
            if raw is not None:
                content = raw
            else:
                content = json.dumps(payload).encode() if payload is not None else None
            resp = self.client.request(method, path, content=content, headers=headers, params=params)
            status = resp.status_code
            try:
                data = resp.json()
            except Exception:
                data = resp.text[:300]
            if resp.status_code >= 400:
                note = json.dumps(data, ensure_ascii=False)[:300] if not isinstance(data, str) else data[:300]
        except Exception as exc:  # noqa: BLE001
            note = f"{type(exc).__name__}: {exc}"[:300]
        latency = (time.perf_counter() - t) * 1000
        rec = Req(phase, label, method, path, status, round(latency, 1), config, note)
        self.reqs.append(rec)
        if status == 500:
            self.log(f"!! 500 tại {phase}/{label}: {note[:160]}")
        return {"status": status, "data": data, "latency_ms": latency, "note": note}

    def post(self, phase, label, path, payload, config=None):
        return self.request(phase, label, "POST", path, payload, config)

    def get(self, phase, label, path, params=None):
        return self.request(phase, label, "GET", path, None, None, params=params)

    def add_menu(self, phase, label, res, profile, config, seed):
        if res["status"] != 200 or not isinstance(res["data"], dict):
            return
        d = res["data"]
        items = [
            {
                "food_id": i.get("food_id"),
                "name": i.get("name"),
                "slot": i.get("slot"),
                "meal_type": i.get("meal_type"),
                "portion_g": i.get("portion_g"),
                "macros": i.get("macros"),
            }
            for i in d.get("items", [])
        ]
        self.menus.append(
            MenuRec(phase, label, config, seed, profile, items, d.get("totals", {}),
                    d.get("targets", {}), d.get("violations", []), d.get("fitness"),
                    d.get("diversity_pct"), round(res["latency_ms"], 1))
        )

    # ------------------------------------------------------------- menu analysis
    @staticmethod
    def role_of(name: str) -> str:
        n = name or ""
        if CONDIMENT_RE.search(n):
            return "condiment"
        if DAIRY_RE.search(n):
            return "dairy"
        if SOUP_RE.search(n):
            return "soup"
        if STICKY_STAPLE_RE.search(n):
            return "staple"
        if VEG_HEAD_RE.search(n):
            return "veg"
        if STAPLE_RE.search(n):
            return "staple"
        if PROTEIN_RE.search(n):
            return "protein"
        if VEG_RE.search(n):
            return "veg"
        if FRUIT_RE.search(n):
            return "fruit"
        return "unknown"

    def analyze_menu(self, m: MenuRec) -> dict:
        names = [it["name"] or "" for it in m.items]
        portions = [float(it["portion_g"] or 0) for it in m.items]
        roles = [self.role_of(n) for n in names]
        by_meal: dict[str, list] = {}
        for it, r in zip(m.items, roles):
            by_meal.setdefault(str(it["slot"]).rsplit("_", 1)[0], []).append((it, r))
        structure_issues = []
        slot_violations = []
        for meal, pairs in by_meal.items():
            rs = [r for _, r in pairs]
            if meal in ("lunch", "dinner"):
                # Bữa 2 món: tinh bột + (đạm hoặc rau/canh) là hợp lý.
                if "staple" not in rs:
                    structure_issues.append(f"{meal}: thiếu tinh bột")
                elif not any(r in ("protein", "veg", "soup") for r in rs):
                    structure_issues.append(f"{meal}: chỉ có tinh bột")
            if meal == "breakfast" and "staple" not in rs:
                structure_issues.append("breakfast: thiếu tinh bột")
            for idx, (it, r) in enumerate(pairs):
                if meal in ("lunch", "dinner"):
                    if idx == 0 and r != "staple":
                        slot_violations.append(f"{meal}_0 = {r} ('{it['name']}') thay vì tinh bột")
                    elif idx > 0 and r not in ("protein", "veg", "soup"):
                        slot_violations.append(f"{meal}_{idx} = {r} ('{it['name']}')")
                elif meal == "breakfast":
                    if idx == 0 and r != "staple":
                        slot_violations.append(f"breakfast_0 = {r} ('{it['name']}') thay vì tinh bột")
                    elif idx > 0 and r not in ("protein", "fruit", "dairy", "veg"):
                        slot_violations.append(f"breakfast_{idx} = {r} ('{it['name']}')")
                elif meal == "snack" and r not in ("fruit", "dairy", "veg"):
                    slot_violations.append(f"snack_{idx} = {r} ('{it['name']}')")
        absurd = []
        for it, r in zip(m.items, roles):
            p = float(it["portion_g"] or 0)
            if r == "condiment" and p > 30:
                absurd.append(f"{it['name']} {p:.0f}g (gia vị)")
            elif r == "staple" and p > 400:
                absurd.append(f"{it['name']} {p:.0f}g (tinh bột)")
            elif r in ("fruit", "dairy") and p > 400:
                absurd.append(f"{it['name']} {p:.0f}g (trái cây/sữa)")
            elif r == "protein" and p > 250:
                absurd.append(f"{it['name']} {p:.0f}g (đạm)")
            elif r == "veg" and p > 300:
                absurd.append(f"{it['name']} {p:.0f}g (rau)")
            if p > 350.5:
                absurd.append(f"{it['name']} {p:.0f}g > trần 350g")
        bad_nutrients = []
        for k, v in (m.totals or {}).items():
            try:
                fv = float(v)
            except (TypeError, ValueError):
                bad_nutrients.append(f"{k} không phải số")
                continue
            if math.isnan(fv) or math.isinf(fv):
                bad_nutrients.append(f"{k} NaN/inf")
            elif fv < 0:
                bad_nutrients.append(f"{k} âm ({fv})")
        cal_check = None
        try:
            calc = 4 * float(m.totals.get("protein_g", 0)) + 4 * float(m.totals.get("carbs_g", 0)) + 9 * float(m.totals.get("fat_g", 0))
            if calc > 0:
                cal_check = abs(float(m.totals.get("calories", 0)) - calc) / calc * 100
        except (TypeError, ValueError):
            pass
        gap = self.gap_pct(m.totals, m.targets)
        dup = len(names) - len(set(names))
        return {
            "condiments": [n for n in names if CONDIMENT_RE.search(n)],
            "raw": [n for n in names if RAW_RE.search(n) and not PREP_RE.search(n)
                    and not DAIRY_RE.search(n) and not n.lower().startswith("giá")],
            "no_prep": [n for n, r in zip(names, roles) if r in ("staple", "protein", "unknown")
                        and not PREP_RE.search(n) and not READY_RE.search(n)],
            "at_cap": [f"{n} {p:.0f}g" for n, p in zip(names, portions) if p >= 349.5],
            "at_floor": [f"{n} {p:.0f}g" for n, p in zip(names, portions) if p <= 25.5],
            "absurd": absurd,
            "structure_issues": structure_issues,
            "slot_violations": slot_violations,
            "bad_nutrients": bad_nutrients,
            "cal_macro_mismatch_pct": None if cal_check is None else round(cal_check, 1),
            "gap_pct": round(gap, 1),
            "duplicates": dup,
            "max_portion": round(max(portions), 1) if portions else 0,
            "min_portion": round(min(portions), 1) if portions else 0,
            "roles": roles,
        }

    @staticmethod
    def gap_pct(totals: dict, targets: dict) -> float:
        vals = []
        for k in ("calories", "protein_g", "carbs_g", "fat_g", "fiber_g"):
            t = float(targets.get(k, 0) or 0)
            if t > 0:
                vals.append(abs(float(totals.get(k, 0) or 0) - t) / t)
        return 100 * sum(vals) / len(vals) if vals else 0.0

    # ------------------------------------------------------------- bootstrap
    def phase_bootstrap(self):
        self.log("PHASE 0 bootstrap: /, /api/health, /api/foods, /api/profiles")
        self.request("bootstrap", "root", "GET", "/")
        self.get("bootstrap", "health", "/api/health")
        self.get("bootstrap", "profiles", "/api/profiles")
        r = self.get("bootstrap", "foods_all", "/api/foods", {"q": "", "limit": 100})
        seen: dict[str, dict] = {}
        if r["status"] == 200 and isinstance(r["data"], list):
            for f in r["data"]:
                seen[f["food_id"]] = f
        for q in ["cơm", "rau", "canh", "thịt", "cá", "gà", "bò", "sữa", "chuối", "gạo", "khoai",
                  "đậu", "măng", "tôm", "trứng", "bánh", "mắm", "dầu", "muối"]:
            rr = self.get("bootstrap", f"foods_{q}", "/api/foods", {"q": q, "limit": 100})
            if rr["status"] == 200 and isinstance(rr["data"], list):
                for f in rr["data"]:
                    seen[f["food_id"]] = f
        names = [f["food_name"] for f in seen.values()]
        self.inventory = {
            "n_foods_sampled": len(seen),
            "condiments": sorted({n for n in names if CONDIMENT_RE.search(n)}),
            "raw": sorted({n for n in names if RAW_RE.search(n)}),
            "no_prep": sorted({n for n in names if not PREP_RE.search(n) and not READY_RE.search(n)}),
            "max_sodium_per_100g": sorted(
                [(f["food_name"], f["sodium_mg"]) for f in seen.values()],
                key=lambda x: -float(x[1] or 0),
            )[:10],
        }
        self.log(
            f"  inventory: {len(seen)} món, gia vị={len(self.inventory['condiments'])}, "
            f"nguyên liệu thô={len(self.inventory['raw'])}, tên không nêu cách chế biến={len(self.inventory['no_prep'])}"
        )

    # ------------------------------------------------------------- clinical
    def base_profile(self, **over):
        p = {
            "name": "Audit",
            "age": 35,
            "gender": "male",
            "height_cm": 168.0,
            "weight_kg": 65.0,
            "activity_level": "MODERATE",
            "goal": "MAINTAIN",
            "meal_counts": {"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 1},
            "medical_conditions": [],
            "allergies": [],
            "dislikes": [],
        }
        p.update(over)
        return p

    def phase_clinical(self, hyp_web: int):
        self.log(f"PHASE 1 lâm sàng: 30 seed tăng huyết áp ({hyp_web} web / {30 - hyp_web} smoke)")
        hyp = self.base_profile(age=55, height_cm=168.0, weight_kg=75.0,
                                activity_level="SEDENTARY", medical_conditions=["hypertension"])
        rows = []
        for i in range(30):
            if self.remaining() < 300:
                self.skipped["clinical_hypertension"] = self.skipped.get("clinical_hypertension", 0) + 30 - i
                break
            cfg = "web" if i < hyp_web else "smoke"
            seed = 100 + i
            res = self.post("clinical", f"hyp_seed{seed}", "/api/menu/generate",
                            {"profile": hyp, "seed": seed, "config": cfg}, cfg)
            if res["status"] == 200:
                self.add_menu("clinical", f"hyp_seed{seed}", res, hyp, cfg, seed)
                d = res["data"]
                rows.append({
                    "seed": seed, "config": cfg,
                    "sodium": float(d["totals"].get("sodium_mg", 0)),
                    "target_sodium": float(d["targets"].get("sodium_mg", 0)),
                    "violations": d.get("violations", []),
                    "energy": float(d["totals"].get("calories", 0)),
                })
            if (i + 1) % 5 == 0:
                self.log(f"  hyp {i + 1}/30 — sodium max tới giờ: "
                         f"{max([r['sodium'] for r in rows], default=0):.0f} mg")
        over_hyp = [r for r in rows if r["sodium"] > SODIUM_HYP]
        over_general = [r for r in rows if r["sodium"] > SODIUM_GEN]
        energy_viol = [r for r in rows if any(v.startswith("energy") for v in r["violations"])]
        protein_viol = [r for r in rows if any(v.startswith("protein") for v in r["violations"])]
        self.clinical["hypertension"] = {
            "n": len(rows), "rows": rows,
            "sodium_max": max([r["sodium"] for r in rows], default=0),
            "sodium_mean": round(statistics.mean([r["sodium"] for r in rows]), 1) if rows else 0,
            "over_1500": [{"seed": r["seed"], "config": r["config"], "sodium": r["sodium"]} for r in over_hyp],
            "over_2300": [{"seed": r["seed"], "config": r["config"], "sodium": r["sodium"]} for r in over_general],
            "energy_violation": len(energy_viol),
            "protein_violation": len(protein_viol),
            "targets_seen": sorted({r["target_sodium"] for r in rows}),
        }
        self.log(f"  sodium max={self.clinical['hypertension']['sodium_max']:.0f} mg, "
                 f"vượt 1500={len(over_hyp)}/{len(rows)}, vượt 2300={len(over_general)}")

        # alias + bệnh lý chưa hỗ trợ
        alias_rows = []
        for cond in ["hypertension", "tăng huyết áp", "cao huyết áp", "huyết áp cao", "HYPERTENSION",
                     "tiểu đường", "diabetes", "đái tháo đường", "gout", "suy thận"]:
            res = self.post("clinical", f"targets_{cond}", "/api/targets",
                            self.base_profile(medical_conditions=[cond]))
            sodium = None
            if res["status"] == 200:
                sodium = res["data"].get("targets", {}).get("sodium_mg")
            alias_rows.append({"condition": cond, "status": res["status"], "sodium_target": sodium})
        self.clinical["aliases"] = alias_rows

        dia = self.base_profile(age=45, gender="female", height_cm=158.0, weight_kg=62.0,
                                activity_level="LIGHT", goal="LOSE_WEIGHT",
                                medical_conditions=["diabetes"])
        dia_rows = []
        for seed in (7, 8, 9):
            res = self.post("clinical", f"diabetes_seed{seed}", "/api/menu/generate",
                            {"profile": dia, "seed": seed, "config": "smoke"}, "smoke")
            entry = {"seed": seed, "status": res["status"]}
            if res["status"] == 200:
                self.add_menu("clinical", f"diabetes_seed{seed}", res, dia, "smoke", seed)
                d = res["data"]
                flat_keys = json.dumps(d, ensure_ascii=False)
                entry.update({
                    "violations": d.get("violations", []),
                    "keys": sorted(d.keys()),
                    "mentions_sugar": "sugar" in flat_keys.lower() or "đường" in flat_keys.lower(),
                    "mentions_warning": any(w in flat_keys.lower() for w in ("warning", "cảnh báo", "note", "lưu ý")),
                    "carbs": d["totals"].get("carbs_g"),
                })
            dia_rows.append(entry)
        self.clinical["diabetes"] = dia_rows
        self.log(f"  tiểu đường: {len(dia_rows)} truy vấn, có cảnh báo="
                 f"{any(r.get('mentions_warning') for r in dia_rows)}")

    # ------------------------------------------------------------- allergies
    def phase_allergies(self):
        self.log("PHASE 2 dị ứng / khẩu vị")
        singles = ["tôm", "cua", "cá", "bò", "heo", "gà", "trứng", "sữa", "đậu phộng", "hải sản"]
        triples = [["tôm", "cua", "cá"], ["bò", "heo", "gà"], ["trứng", "sữa", "đậu phộng"]]
        ten = singles
        heavy = ["tôm", "cua", "cá", "bò", "heo", "gà", "trứng", "sữa", "đậu", "mực", "tép",
                 "nghêu", "sò", "hến", "lươn", "ếch", "vịt", "dê", "thịt", "chả"]
        results = []

        def run(label, tokens, cfg="smoke", reps=1):
            for rep in range(reps):
                if self.remaining() < 300:
                    self.skipped["allergy"] = self.skipped.get("allergy", 0) + 1
                    return
                prof = self.base_profile(allergies=tokens)
                seed = 300 + len(results) * 7 + rep
                res = self.post("allergy", label, "/api/menu/generate",
                                {"profile": prof, "seed": seed, "config": cfg}, cfg)
                entry = {"label": label, "tokens": tokens, "status": res["status"],
                         "config": cfg, "leaks": [], "seafood_leak": False, "note": res["note"][:200]}
                if res["status"] == 200:
                    self.add_menu("allergy", label, res, prof, cfg, seed)
                    names = [i["name"] for i in res["data"]["items"]]
                    for tok in tokens:
                        entry["leaks"] += [n for n in names if tok.lower() in n.lower()]
                    entry["seafood_leak"] = any(SEAFOOD_RE.search(n) for n in names)
                    entry["names"] = names
                results.append(entry)

        for tok in singles:
            run(f"single:{tok}", [tok], "web" if tok in ("tôm", "hải sản") else "smoke", reps=2)
        for grp in triples:
            run("triple:" + "+".join(grp), grp, "smoke", reps=2)
        run("ten-tokens", ten, "smoke", reps=2)
        run("ten-tokens-web", ten, "web", reps=1)
        run("twenty-tokens", heavy, "smoke", reps=1)

        leaks = [e for e in results if e["leaks"]]
        semantic = [e for e in results if "hải sản" in e["tokens"] and e["seafood_leak"]]
        self.allergy = {
            "n_runs": len(results),
            "runs": results,
            "leak_runs": len(leaks),
            "leak_examples": [{"label": e["label"], "leaks": e["leaks"][:5]} for e in leaks[:10]],
            "semantic_leak_runs": len(semantic),
            "status_counts": {str(s): sum(1 for e in results if e["status"] == s)
                              for s in sorted({e["status"] for e in results}, key=str)},
        }
        self.log(f"  {len(results)} lượt, lọt dị ứng={len(leaks)}, lọt 'hải sản'={len(semantic)}")

    # ------------------------------------------------------------- swap
    def phase_swap(self):
        self.log("PHASE 3 swap chain + concurrency")
        scenarios = [
            (self.base_profile(name="SwapA"), 11, "web"),
            (self.base_profile(name="SwapB", age=52, gender="female", height_cm=158, weight_kg=70,
                               activity_level="LIGHT", goal="LOSE_WEIGHT"), 12, "smoke"),
            (self.base_profile(name="SwapC", age=24, height_cm=178, weight_kg=85,
                               activity_level="ACTIVE", goal="GAIN_WEIGHT",
                               meal_counts={"breakfast": 3, "lunch": 3, "dinner": 3, "snack": 2}), 13, "smoke"),
            (self.base_profile(name="SwapD", age=68, activity_level="SEDENTARY",
                               medical_conditions=["hypertension"]), 14, "smoke"),
            (self.base_profile(name="SwapE", age=30, gender="female", meal_counts={"breakfast": 1, "lunch": 2,
                                                                                  "dinner": 2, "snack": 0}), 15, "smoke"),
        ]
        chains = []
        for prof, seed, cfg in scenarios:
            gen = self.post("swap", f"gen_{prof['name']}", "/api/menu/generate",
                            {"profile": prof, "seed": seed, "config": cfg}, cfg)
            if gen["status"] != 200:
                chains.append({"label": prof["name"], "error": gen["status"], "note": gen["note"][:200]})
                continue
            menu = gen["data"]
            self.add_menu("swap", f"gen_{prof['name']}", gen, prof, cfg, seed)
            base_gap = self.gap_pct(menu["totals"], menu["targets"])
            steps = [{"step": 0, "slot": "gen", "gap": round(base_gap, 1),
                      "calories": menu["totals"].get("calories"),
                      "violations": len(menu.get("violations", [])),
                      "max_portion": round(max(float(i["portion_g"]) for i in menu["items"]), 1),
                      "n_at_cap": sum(1 for i in menu["items"] if float(i["portion_g"]) >= 349.5)}]
            # đổi lần lượt từng slot
            order = [i["slot"] for i in menu["items"]]
            for slot in order:
                body = {
                    "profile": prof,
                    "food_ids": [i["food_id"] for i in menu["items"]],
                    "slot": slot,
                    "seed": seed + len(steps),
                    "old_portions_g": [i["portion_g"] for i in menu["items"]],
                }
                res = self.post("swap", f"{prof['name']}:seq:{slot}", "/api/menu/swap", body)
                if res["status"] != 200:
                    steps.append({"step": len(steps), "slot": slot, "status": res["status"],
                                  "error": res["note"][:150]})
                    continue
                menu = res["data"]
                self.add_menu("swap", f"{prof['name']}:seq:{slot}", res, prof, cfg, seed)
                steps.append({
                    "step": len(steps), "slot": slot, "status": 200,
                    "gap": round(self.gap_pct(menu["totals"], menu["targets"]), 1),
                    "calories": menu["totals"].get("calories"),
                    "violations": len(menu.get("violations", [])),
                    "max_portion": round(max(float(i["portion_g"]) for i in menu["items"]), 1),
                    "n_at_cap": sum(1 for i in menu["items"] if float(i["portion_g"]) >= 349.5),
                })
            # 5 lần liên tiếp cùng 1 slot
            slot = "lunch_1" if "lunch_1" in order else order[-1]
            for k in range(5):
                body = {
                    "profile": prof,
                    "food_ids": [i["food_id"] for i in menu["items"]],
                    "slot": slot,
                    "seed": seed + 500 + k,
                    "old_portions_g": [i["portion_g"] for i in menu["items"]],
                }
                res = self.post("swap", f"{prof['name']}:chain5:{k}", "/api/menu/swap", body)
                if res["status"] != 200:
                    steps.append({"step": f"chain{k}", "slot": slot, "status": res["status"],
                                  "error": res["note"][:150]})
                    continue
                menu = res["data"]
                self.add_menu("swap", f"{prof['name']}:chain5:{k}", res, prof, cfg, seed)
                steps.append({
                    "step": f"chain{k}", "slot": slot, "status": 200,
                    "gap": round(self.gap_pct(menu["totals"], menu["targets"]), 1),
                    "calories": menu["totals"].get("calories"),
                    "violations": len(menu.get("violations", [])),
                    "max_portion": round(max(float(i["portion_g"]) for i in menu["items"]), 1),
                    "n_at_cap": sum(1 for i in menu["items"] if float(i["portion_g"]) >= 349.5),
                })
            chains.append({"label": prof["name"], "steps": steps,
                           "gap_start": steps[0]["gap"],
                           "gap_end": [s for s in steps if s.get("status") == 200][-1].get("gap")})
            self.log(f"  chain {prof['name']}: gap {steps[0]['gap']:.1f}% -> "
                     f"{chains[-1]['gap_end']:.1f}%, max portion "
                     f"{max([s.get('max_portion', 0) for s in steps]):.0f}g")
        self.swap_chains = chains
        self._phase_concurrency()

    def _phase_concurrency(self):
        prof = self.base_profile(name="Race")
        gen = self.post("swap", "race_gen", "/api/menu/generate",
                        {"profile": prof, "seed": 77, "config": "smoke"}, "smoke")
        if gen["status"] != 200:
            self.concurrency = {"error": gen["status"]}
            return
        menu = gen["data"]
        base = {
            "profile": prof,
            "food_ids": [i["food_id"] for i in menu["items"]],
            "slot": "lunch_1",
            "old_portions_g": [i["portion_g"] for i in menu["items"]],
        }

        async def fire():
            async with httpx.AsyncClient(base_url=self.base_url, timeout=httpx.Timeout(120.0)) as ac:
                async def one(k):
                    body = dict(base, seed=1000 + k)
                    t = time.perf_counter()
                    try:
                        r = await ac.post("/api/menu/swap", json=body)
                        return k, r.status_code, (time.perf_counter() - t) * 1000, r.text[:200], r.json() if r.status_code == 200 else None
                    except Exception as exc:  # noqa: BLE001
                        return k, "ERR", (time.perf_counter() - t) * 1000, str(exc)[:200], None
                return await asyncio.gather(*[one(k) for k in range(10)])

        results = asyncio.run(fire())
        signatures = set()
        for k, status, lat, text, data in results:
            rec = Req("swap_concurrent", f"concurrent_{k}", "POST", "/api/menu/swap",
                      status, round(lat, 1), "smoke", text)
            self.reqs.append(rec)
            if data:
                signatures.add(tuple(i["food_id"] for i in data["items"]))
        self.concurrency = {
            "n": len(results),
            "status_counts": {str(s): sum(1 for _, st, _, _, _ in results if st == s)
                              for s in sorted({st for _, st, _, _, _ in results}, key=str)},
            "latency_max_ms": round(max(lat for _, _, lat, _, _ in results), 1),
            "latency_mean_ms": round(statistics.mean([lat for _, _, lat, _, _ in results]), 1),
            "distinct_results": len(signatures),
        }
        self.log(f"  concurrency 10 swap: {self.concurrency['status_counts']}, "
                 f"max {self.concurrency['latency_max_ms']} ms, {len(signatures)} kết quả khác nhau")

    # ------------------------------------------------------------- chaos
    def phase_chaos(self):
        self.log("PHASE 4 chaos / fuzzing nhập liệu")
        base = self.base_profile()
        gen = self.post("chaos", "chaos_gen", "/api/menu/generate",
                        {"profile": base, "seed": 42, "config": "smoke"}, "smoke")
        ids = [i["food_id"] for i in gen["data"]["items"]] if gen["status"] == 200 else ["VN_4002"] * 7
        portions = [i["portion_g"] for i in gen["data"]["items"]] if gen["status"] == 200 else [100.0] * 7

        def swap_body(**over):
            b = {"profile": base, "food_ids": ids, "slot": "lunch_0", "seed": 9, "old_portions_g": portions}
            b.update(over)
            return b

        cases = [
            ("age=0", "/api/menu/generate", {"profile": self.base_profile(age=0), "seed": 1, "config": "smoke"}, "4xx"),
            ("age=-10", "/api/menu/generate", {"profile": self.base_profile(age=-10), "seed": 1, "config": "smoke"}, "4xx"),
            ("age=200", "/api/menu/generate", {"profile": self.base_profile(age=200), "seed": 1, "config": "smoke"}, "4xx"),
            ("age='hai mươi tuổi'", "/api/menu/generate", {"profile": self.base_profile(age="hai mươi tuổi"), "seed": 1, "config": "smoke"}, "4xx"),
            ("height=30cm", "/api/menu/generate", {"profile": self.base_profile(height_cm=30), "seed": 1, "config": "smoke"}, "any"),
            ("height=300cm", "/api/menu/generate", {"profile": self.base_profile(height_cm=300), "seed": 1, "config": "smoke"}, "4xx"),
            ("weight=5kg", "/api/menu/generate", {"profile": self.base_profile(weight_kg=5), "seed": 1, "config": "smoke"}, "any"),
            ("weight=400kg", "/api/menu/generate", {"profile": self.base_profile(weight_kg=400), "seed": 1, "config": "smoke"}, "any"),
            ("meal_counts toàn 0", "/api/menu/generate", {"profile": self.base_profile(meal_counts={"breakfast": 0, "lunch": 0, "dinner": 0, "snack": 0}), "seed": 1, "config": "smoke"}, "4xx"),
            ("chỉ snack x3", "/api/menu/generate", {"profile": self.base_profile(meal_counts={"snack": 3}), "seed": 1, "config": "smoke"}, "4xx"),
            ("snack=10", "/api/menu/generate", {"profile": self.base_profile(meal_counts={"breakfast": 2, "lunch": 2, "dinner": 2, "snack": 10}), "seed": 1, "config": "smoke"}, "4xx"),
            ("breakfast=-1", "/api/menu/generate", {"profile": self.base_profile(meal_counts={"breakfast": -1, "lunch": 2, "dinner": 2}), "seed": 1, "config": "smoke"}, "4xx"),
            ("meal key 'brunch'", "/api/menu/generate", {"profile": self.base_profile(meal_counts={"breakfast": 2, "lunch": 2, "dinner": 2, "brunch": 1}), "seed": 1, "config": "smoke"}, "4xx"),
            ("allergy rỗng", "/api/menu/generate", {"profile": self.base_profile(allergies=[""]), "seed": 1, "config": "smoke"}, "4xx"),
            ("allergy '<script>'", "/api/menu/generate", {"profile": self.base_profile(allergies=["<script>alert(1)</script>"]), "seed": 1, "config": "smoke"}, "any"),
            ("allergy emoji", "/api/menu/generate", {"profile": self.base_profile(allergies=["🍤🍤"]), "seed": 1, "config": "smoke"}, "any"),
            ("allergy null byte", "/api/menu/generate", {"profile": self.base_profile(allergies=["\u0000abc"]), "seed": 1, "config": "smoke"}, "any"),
            ("allergy 10.000 ký tự", "/api/menu/generate", {"profile": self.base_profile(allergies=["x" * 10000]), "seed": 1, "config": "smoke"}, "any"),
            ("allergy 1000 token", "/api/menu/generate", {"profile": self.base_profile(allergies=[f"tok{i}" for i in range(1000)]), "seed": 1, "config": "smoke"}, "any"),
            ("name SQL injection", "/api/menu/generate", {"profile": self.base_profile(name="'; DROP TABLE foods;--"), "seed": 1, "config": "smoke"}, "any"),
            ("name 10.000 ký tự", "/api/menu/generate", {"profile": self.base_profile(name="ế" * 10000), "seed": 1, "config": "smoke"}, "any"),
            ("medical SQL", "/api/menu/generate", {"profile": self.base_profile(medical_conditions=["'; DROP TABLE foods;--"]), "seed": 1, "config": "smoke"}, "any"),
            ("extra field", "/api/menu/generate", {"profile": dict(self.base_profile(), is_admin=True), "seed": 1, "config": "smoke"}, "any"),
            ("thiếu profile", "/api/menu/generate", {"seed": 1, "config": "smoke"}, "4xx"),
            ("gender 'other'", "/api/menu/generate", {"profile": self.base_profile(gender="other"), "seed": 1, "config": "smoke"}, "4xx"),
            ("activity thường", "/api/menu/generate", {"profile": self.base_profile(activity_level="sedentary"), "seed": 1, "config": "smoke"}, "4xx"),
            ("seed=-1", "/api/menu/generate", {"profile": base, "seed": -1, "config": "smoke"}, "4xx"),
            ("config='turbo'", "/api/menu/generate", {"profile": base, "seed": 1, "config": "turbo"}, "4xx"),
            ("foods q SQL", "/api/foods", "Q:'; OR 1=1 --", "any"),
            ("foods q 10.000", "/api/foods", "Q:" + "a" * 10000, "any"),
            ("foods limit=0", "/api/foods", "Q:", "4xx", {"limit": 0}),
            ("foods limit=1000", "/api/foods", "Q:", "4xx", {"limit": 1000}),
            ("swap slot lạ", "/api/menu/swap", swap_body(slot="lunch_9"), "4xx"),
            ("swap thiếu food_ids", "/api/menu/swap", swap_body(food_ids=ids[:-1]), "4xx"),
            ("swap food_id lạ", "/api/menu/swap", swap_body(food_ids=["VN_9999"] * len(ids)), "4xx"),
            ("swap new_food lạ", "/api/menu/swap", swap_body(new_food_id="VN_9999"), "4xx"),
            ("swap old_portions lệch", "/api/menu/swap", swap_body(old_portions_g=portions[:-1]), "4xx"),
            ("swap old_portions=0", "/api/menu/swap", swap_body(old_portions_g=[0.0] * len(ids)), "4xx"),
            ("swap old_portions=1e9", "/api/menu/swap", swap_body(old_portions_g=[1e9] * len(ids)), "4xx"),
            ("swap food_ids rỗng", "/api/menu/swap", swap_body(food_ids=[]), "4xx"),
            ("swap trùng món trong bữa", "/api/menu/swap", swap_body(new_food_id=ids[3] if len(ids) > 3 else ids[1]), "4xx"),
            ("targets age=0", "/api/targets", self.base_profile(age=0), "4xx"),
        ]
        rows = []
        for case in cases:
            label, path, payload = case[0], case[1], case[2]
            expected = case[3]
            if path == "/api/foods":
                params = {"q": payload[2:], "limit": case[4]["limit"] if len(case) > 4 else 20}
                res = self.get("chaos", label, path, params)
            else:
                res = self.post("chaos", label, path, payload, "smoke")
            status = res["status"]
            if expected == "4xx":
                verdict = "PASS" if isinstance(status, int) and 400 <= status < 500 else "FAIL"
            elif expected == "any":
                verdict = "INFO" if status != 500 else "FAIL"
            else:
                verdict = "INFO"
            body = json.dumps(res["data"], ensure_ascii=False) if res["data"] is not None else ""
            rows.append({
                "case": label, "expected": expected, "status": status, "verdict": verdict,
                "note": res["note"][:200], "echoed_payload": ("<script>" in body or "DROP TABLE" in body or "text/html" in body),
                "latency_ms": round(res["latency_ms"], 1),
            })
        # JSON hỏng / content-type sai
        for label, raw in [("JSON hỏng", b'{"profile": '), ("content-type text/plain", b"hello")]:
            res = self.request("chaos", label, "POST", "/api/menu/generate", raw=raw)
            rows.append({"case": label, "expected": "4xx", "status": res["status"],
                         "verdict": "PASS" if isinstance(res["status"], int) and 400 <= res["status"] < 500 else "FAIL",
                         "note": res["note"][:200], "echoed_payload": False, "latency_ms": round(res["latency_ms"], 1)})

        self.chaos = rows
        bad = [r for r in rows if r["verdict"] == "FAIL"]
        self.log(f"  {len(rows)} case chaos, FAIL={len(bad)}, 500={sum(1 for r in rows if r['status'] == 500)}")

    # ------------------------------------------------------------- determinism
    def phase_determinism(self):
        self.log("PHASE 5 tái lập (cùng seed)")
        payload = {"profile": self.base_profile(name="Det"), "seed": 4242, "config": "smoke"}
        runs = []
        for k in range(3):
            res = self.post("determinism", f"run{k}", "/api/menu/generate", payload, "smoke")
            if res["status"] == 200:
                self.add_menu("determinism", f"run{k}", res, payload["profile"], "smoke", 4242)
                runs.append((tuple(i["food_id"] for i in res["data"]["items"]),
                             tuple(round(float(i["portion_g"]), 3) for i in res["data"]["items"])))
        self.determinism = {
            "n": len(runs),
            "same_ids": len({r[0] for r in runs}) == 1 if runs else None,
            "same_portions": len({r[1] for r in runs}) == 1 if runs else None,
        }
        self.log(f"  same ids={self.determinism['same_ids']}, same portions={self.determinism['same_portions']}")

    # ------------------------------------------------------------- matrix
    def matrix_profiles(self, n: int):
        out = []
        for k in range(n):
            age_b, age = AGES[k % 4]
            bmi_b, target_bmi = BMIS[(k // 4) % 5]
            act = ACTS[(k // 20) % 5]
            meal_b, meals = MEALS[(k // 5) % 4]
            height = 158 + (k * 3) % 18
            weight = round(target_bmi * (height / 100) ** 2, 1)
            weight = max(22.0, min(weight, 395.0))
            goal = "GAIN_WEIGHT" if target_bmi < 18.5 else ("MAINTAIN" if target_bmi < 25 else "LOSE_WEIGHT")
            p = self.base_profile(
                name=f"Audit-{k + 1:03d}", age=age, gender="female" if k % 2 else "male",
                height_cm=float(height), weight_kg=weight, activity_level=act, goal=goal,
                meal_counts=dict(meals),
            )
            out.append({"profile": p, "meta": {"age_bucket": age_b, "bmi_bucket": bmi_b,
                                               "bmi": round(weight / (height / 100) ** 2, 1),
                                               "activity": act, "meal_structure": meal_b}})
        return out

    def phase_matrix(self, n: int):
        self.log(f"PHASE 6 ma trận nhân khẩu {n} hồ sơ (config web)")
        done = 0
        for item in self.matrix_profiles(n):
            if self.remaining() < 120:
                self.skipped["matrix"] = self.skipped.get("matrix", 0) + n - done
                self.log("  hết ngân sách thời gian — dừng ma trận")
                break
            p = item["profile"]
            self.post("matrix_targets", p["name"], "/api/targets", p)
            res = self.post("matrix", p["name"], "/api/menu/generate",
                            {"profile": p, "seed": 2000 + done, "config": "web"}, "web")
            if res["status"] == 200:
                self.add_menu("matrix", p["name"], res, p, "web", 2000 + done)
                self.matrix_meta.append({**item["meta"], "name": p["name"], "status": 200,
                                         "fitness": res["data"].get("fitness"),
                                         "violations": len(res["data"].get("violations", []))})
            else:
                self.matrix_meta.append({**item["meta"], "name": p["name"], "status": res["status"],
                                         "note": res["note"][:160]})
            done += 1
            if done % 5 == 0:
                fit = [m["fitness"] for m in self.matrix_meta if m.get("fitness") is not None]
                self.log(f"  ma trận {done}/{n} — fitness TB {statistics.mean(fit):.1f}" if fit else
                         f"  ma trận {done}/{n}")
        # bổ sung độ nhạy seed nếu còn thời gian
        reruns = 0
        sample = self.matrix_profiles(min(n, 20))[::2]
        while self.elapsed() < self.min_seconds and self.remaining() > 120 and reruns < 40:
            item = sample[reruns % len(sample)]
            p = item["profile"]
            res = self.post("matrix_rerun", p["name"], "/api/menu/generate",
                            {"profile": p, "seed": 9000 + reruns, "config": "web"}, "web")
            if res["status"] == 200:
                self.add_menu("matrix_rerun", p["name"], res, p, "web", 9000 + reruns)
                self.matrix_meta.append({**item["meta"], "name": p["name"], "status": 200,
                                         "fitness": res["data"].get("fitness"),
                                         "violations": len(res["data"].get("violations", [])),
                                         "rerun": True})
            reruns += 1
            if reruns % 5 == 0:
                self.log(f"  rerun seed {reruns} (elapsed {self.elapsed():.0f}s)")
        self.log(f"  ma trận xong: {done} hồ sơ, {reruns} rerun seed")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8000")
    ap.add_argument("--profiles", type=int, default=100)
    ap.add_argument("--hypertension-web", type=int, default=15)
    ap.add_argument("--min-seconds", type=int, default=900)
    ap.add_argument("--max-seconds", type=int, default=1740)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    out = Path(args.out) if args.out else ROOT / "experiments" / f"audit_live_web_{stamp}"
    a = Auditor(args.base_url, out, args.min_seconds, args.max_seconds)
    a.log(f"Auditor start -> {out} (budget {args.max_seconds}s, min {args.min_seconds}s)")
    try:
        a.phase_bootstrap()
        a.phase_clinical(args.hypertension_web)
        a.phase_allergies()
        a.phase_swap()
        a.phase_chaos()
        a.phase_determinism()
        a.phase_matrix(args.profiles)
    finally:
        a.log(f"Hoàn tất thu thập: {len(a.reqs)} request, {len(a.menus)} menu, "
              f"elapsed {a.elapsed():.0f}s")
        from build_audit_report import build_report  # local module cùng thư mục
        summary = build_report(a)
        (out / "config.json").write_text(json.dumps({
            "base_url": args.base_url, "profiles": args.profiles,
            "hypertension_web": args.hypertension_web,
            "min_seconds": args.min_seconds, "max_seconds": args.max_seconds,
            "started": stamp, "elapsed_s": round(a.elapsed(), 1),
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        with (out / "raw_requests.jsonl").open("w", encoding="utf-8") as fh:
            for r in a.reqs:
                fh.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")
        with (out / "raw_menus.jsonl").open("w", encoding="utf-8") as fh:
            for m in a.menus:
                fh.write(json.dumps(asdict(m), ensure_ascii=False) + "\n")
        a.log(f"Đã ghi report + summary vào {out}")
    a.client.close()


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
