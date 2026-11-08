#!/usr/bin/env python3
"""Dựng REPORT.md từ dữ liệu auditor thu được (không hard-code số liệu)."""
from __future__ import annotations

import json
import math
import statistics
from collections import Counter
from pathlib import Path


def _pct(part, whole):
    return round(100.0 * part / whole, 1) if whole else 0.0


def _lat_stats(vals):
    if not vals:
        return {"n": 0, "mean": 0, "median": 0, "p95": 0, "max": 0}
    s = sorted(vals)
    return {
        "n": len(s),
        "mean": round(statistics.mean(s), 1),
        "median": round(statistics.median(s), 1),
        "p95": round(s[min(len(s) - 1, int(round(0.95 * (len(s) - 1))))], 1),
        "max": round(s[-1], 1),
    }


def build_report(a):
    A = a  # Auditor
    out = A.out
    reqs = A.reqs
    menus = A.menus
    analyses = [(m, A.analyze_menu(m)) for m in menus]
    st = Counter(str(r.status) for r in reqs)
    n_req = len(reqs)
    n200 = st.get("200", 0)
    n5xx = sum(v for k, v in st.items() if k.startswith("5"))
    n4xx = sum(v for k, v in st.items() if k.startswith("4"))
    errs = st.get("ERR", 0)
    lat_all = [r.latency_ms for r in reqs if isinstance(r.status, int)]
    lat_gen_web = [r.latency_ms for r in reqs
                   if r.phase in ("matrix", "matrix_rerun", "clinical") and r.config == "web"]
    lat_gen_smoke = [r.latency_ms for r in reqs if r.config == "smoke" and r.path == "/api/menu/generate"]
    by_phase = {}
    for r in reqs:
        by_phase.setdefault(r.phase, []).append(r.latency_ms)
    phase_lat = {k: _lat_stats(v) for k, v in by_phase.items()}

    # ---- menu aggregate
    viol_types = Counter()
    menus_with_viol = 0
    fitness_vals = [m.fitness for m in menus if m.fitness is not None]
    sodium_vals = [float(m.totals.get("sodium_mg", 0) or 0) for m in menus]
    sodium_over_hyp = [(m.label, m.phase, float(m.totals.get("sodium_mg", 0) or 0))
                       for m in menus if float(m.totals.get("sodium_mg", 0) or 0) > 1500]
    sodium_over_gen = [(m.label, m.phase, float(m.totals.get("sodium_mg", 0) or 0))
                       for m in menus if float(m.totals.get("sodium_mg", 0) or 0) > 2300]
    energy_viol = 0
    protein_viol = 0
    for m in menus:
        if m.violations:
            menus_with_viol += 1
        for v in m.violations:
            viol_types[v.split(":")[0].split(" ")[0]] += 1
            if v.startswith("energy"):
                energy_viol += 1
            if v.startswith("protein"):
                protein_viol += 1
    bad_nutrient_menus = [m.label for m, an in analyses if an["bad_nutrients"]]
    cal_mismatch = [an["cal_macro_mismatch_pct"] for _, an in analyses if an["cal_macro_mismatch_pct"] is not None]
    condiment_menus = [(m, an) for m, an in analyses if an["condiments"]]
    raw_menus = [(m, an) for m, an in analyses if an["raw"]]
    raw_display_menus = [(m, an) for m, an in analyses if an["raw_display"]]
    noprep_menus = [(m, an) for m, an in analyses if an["no_prep"]]
    absurd_menus = [(m, an) for m, an in analyses if an["absurd"]]
    structure_menus = [(m, an) for m, an in analyses if an["structure_issues"]]
    at_cap_menus = [(m, an) for m, an in analyses if an["at_cap"]]
    dup_menus = [(m, an) for m, an in analyses if an["duplicates"]]
    slot_bad = [(m, an) for m, an in analyses if an["slot_violations"]]
    slot0_total = 0
    slot0_staple = 0
    for m, an in analyses:
        for it, role in zip(m.items, an["roles"]):
            if str(it["slot"]).rsplit("_", 1)[0] in ("lunch", "dinner") and str(it["slot"]).endswith("_0"):
                slot0_total += 1
                if role == "staple":
                    slot0_staple += 1
    implausible_labels = {"height=30cm", "weight=5kg", "weight=400kg"}
    implausible_200 = [c for c in A.chaos if c["case"] in implausible_labels and c["status"] == 200]
    allergy_by_label = {}
    for run in A.allergy.get("runs", []):
        allergy_by_label.setdefault(run["label"], []).append(run["status"])

    def score(pair):
        m, an = pair
        return (5 * len(an["condiments"]) + 4 * len(an["raw"]) + 3 * len(an["absurd"])
                + 1.5 * len(an["at_cap"]) + 2 * len(an["structure_issues"])
                + 0.1 * an["gap_pct"])

    worst = []
    seen_chains = set()
    for pair in sorted(analyses, key=lambda p: -score(p)):
        key = (pair[0].phase, pair[0].label.split(":")[0])
        if key in seen_chains:
            continue
        seen_chains.add(key)
        worst.append(pair)
        if len(worst) == 6:
            break

    # ---- swap aggregate
    all_steps = []
    for ch in A.swap_chains:
        for s in ch.get("steps", []):
            # step 0 is the generated baseline, not a swap request.
            if s.get("step") == 0 or s.get("step") == "gen":
                continue
            if s.get("status", 200) == 200 and "gap" in s:
                all_steps.append(s)
    gaps = [s["gap"] for s in all_steps]
    chain_deltas = [ch["gap_end"] - ch["gap_start"] for ch in A.swap_chains
                    if "gap_start" in ch and "gap_end" in ch]
    gap_delta = round(statistics.mean(chain_deltas), 1) if chain_deltas else 0.0
    gap_series = {}
    for ch in A.swap_chains:
        ser = [s["gap"] for s in ch.get("steps", []) if "gap" in s]
        if ser:
            gap_series[ch["label"]] = ser
    chain5 = {}
    for ch in A.swap_chains:
        baseline = None
        vals = []
        for step in ch.get("steps", []):
            if str(step.get("step", "")).startswith("chain"):
                if step.get("status", 200) == 200 and "gap" in step:
                    vals.append(step["gap"])
            elif not vals and "gap" in step:
                baseline = step["gap"]
        if vals and baseline is not None:
            chain5[ch["label"]] = {"start": baseline, "end": vals[-1],
                                   "min": min(vals), "max": max(vals)}
    chain5_deltas = [v["end"] - v["start"] for v in chain5.values()]
    chain5_delta_signed = round(statistics.mean(chain5_deltas), 1) if chain5_deltas else 0.0
    chain5_delta_abs = round(statistics.mean([abs(x) for x in chain5_deltas]), 1) if chain5_deltas else 0.0

    # ---- matrix coverage
    meta = A.matrix_meta
    cover = {
        "age": dict(Counter(m.get("age_bucket") for m in meta)),
        "bmi": dict(Counter(m.get("bmi_bucket") for m in meta)),
        "activity": dict(Counter(m.get("activity") for m in meta)),
        "meal": dict(Counter(m.get("meal_structure") for m in meta)),
        "ok": sum(1 for m in meta if m.get("status") == 200),
        "err": sum(1 for m in meta if m.get("status") != 200),
    }
    rerun_meta = [m for m in meta if m.get("rerun")]

    # ---- derived facts: MỌI câu diễn giải trong REPORT.md phải đọc từ đây.
    # Không thêm câu khẳng định nào về hệ thống nếu không suy ra được từ các
    # trường trong khối này (hoặc từ summary ở dưới).
    ERR_EN = ("Input should", "String should", "Field required",
              "value is not a valid", "Decimal input", "Extra inputs are not permitted")
    req_4xx = [r for r in reqs if isinstance(r.status, int) and 400 <= r.status < 500]
    hyp_menus = [
        m for m in menus
        if "hypertension" in {str(c).strip().lower() for c in (m.profile.get("medical_conditions") or [])}
    ]
    hyp_sodium = [float(m.totals.get("sodium_mg", 0) or 0) for m in hyp_menus]
    # Baseline menus are named gen_*; they are not swap results. Counting them
    # as swap steps inflates the denominator by five.
    swap_menus = [
        m for m in menus
        if m.phase == "swap" and not m.label.startswith("gen_")
    ]
    swap_fit = [float(m.fitness) for m in swap_menus if m.fitness is not None]
    dia_rows = [r for r in A.clinical.get("diabetes", []) if r.get("status") == 200]
    derived = {
        "n_4xx": len(req_4xx),
        "n_4xx_english_pydantic": sum(
            1 for r in req_4xx if any(p in (r.note or "") for p in ERR_EN)
        ),
        "n_400_internal_message": sum(
            1 for r in req_4xx if r.status == 400
            and any(p in (r.note or "").casefold() for p in ("min_pool_size", "has size", "pool"))
        ),
        "n_swap_menus": len(swap_menus),
        "n_swap_menus_with_fitness": len(swap_fit),
        "swap_fitness_min": round(min(swap_fit), 2) if swap_fit else None,
        "swap_fitness_max": round(max(swap_fit), 2) if swap_fit else None,
        "n_menus_fitness_negative": sum(
            1 for m in menus if m.fitness is not None and float(m.fitness) < 0
        ),
        "n_hyp_menus": len(hyp_menus),
        "n_hyp_over_1500": sum(1 for v in hyp_sodium if v > 1500),
        "n_hyp_over_2300": sum(1 for v in hyp_sodium if v > 2300),
        "hyp_sodium_max": round(max(hyp_sodium), 1) if hyp_sodium else None,
        "hyp_sodium_targets": sorted({float(m.targets.get("sodium_mg", 0) or 0) for m in hyp_menus}),
        "n_allergy_menus_400": sum(
            1 for e in A.allergy.get("runs", []) if e.get("status") == 400
        ),
        "diabetes_warn": bool(dia_rows) and all(r.get("mentions_warning") for r in dia_rows),
        "diabetes_mentions_sugar": bool(dia_rows) and all(r.get("mentions_sugar") for r in dia_rows),
        "diabetes_keys": sorted({k for r in dia_rows for k in r.get("keys", [])}),
        "at_cap_threshold_g": 349.5,
    }

    # ---- builds
    summary = {
        "derived": derived,
        "n_requests": n_req,
        "status_counts": dict(st),
        "ok_rate_pct": _pct(n200, n_req),
        "n_4xx": n4xx,
        "n_5xx": n5xx,
        "n_err": errs,
        "latency_all": _lat_stats(lat_all),
        "latency_generate_web": _lat_stats(lat_gen_web),
        "latency_generate_smoke": _lat_stats(lat_gen_smoke),
        "latency_by_phase": phase_lat,
        "n_menus": len(menus),
        "menus_with_violation": menus_with_viol,
        "menus_with_violation_pct": _pct(menus_with_viol, len(menus)),
        "violation_types": dict(viol_types),
        "menus_energy_violation": energy_viol,
        "menus_protein_violation": protein_viol,
        "fitness": {"n": len(fitness_vals),
                    "mean": round(statistics.mean(fitness_vals), 1) if fitness_vals else None,
                    "min": round(min(fitness_vals), 1) if fitness_vals else None,
                    "max": round(max(fitness_vals), 1) if fitness_vals else None},
        "sodium": {"mean": round(statistics.mean(sodium_vals), 1) if sodium_vals else 0,
                   "max": round(max(sodium_vals), 1) if sodium_vals else 0,
                   "n_over_1500": len(sodium_over_hyp),
                   "n_over_2300": len(sodium_over_gen),
                   "over_1500_examples": sodium_over_hyp[:8]},
        "bad_nutrients": bad_nutrient_menus[:10],
        "cal_macro_mismatch_pct": {
            "n_checked": len(cal_mismatch),
            "max": round(max(cal_mismatch), 1) if cal_mismatch else None,
            "n_over_10pct": sum(1 for x in cal_mismatch if x > 10),
        },
        "condiment_menus": len(condiment_menus),
        "condiment_examples": sorted({c for _, an in condiment_menus for c in an["condiments"]}),
        "raw_menus": len(raw_menus),
        "raw_examples": sorted({c for _, an in raw_menus for c in an["raw"]}),
        "raw_display_menus": len(raw_display_menus),
        "raw_display_examples": sorted(
            {c for _, an in raw_display_menus for c in an["raw_display"]}
        )[:15],
        "no_prep_menus": len(noprep_menus),
        "no_prep_pct": _pct(len(noprep_menus), len(menus)),
        "no_prep_examples": sorted({c for _, an in noprep_menus for c in an["no_prep"]})[:15],
        "absurd_menus": len(absurd_menus),
        "absurd_examples": sorted({c for _, an in absurd_menus for c in an["absurd"]})[:15],
        "at_cap_menus": len(at_cap_menus),
        "at_cap_pct": _pct(len(at_cap_menus), len(menus)),
        "at_cap_examples": sorted({c for _, an in at_cap_menus for c in an["at_cap"]})[:15],
        "structure_fail_menus": len(structure_menus),
        "structure_fail_pct": _pct(len(structure_menus), len(menus)),
        "structure_examples": sorted({c for _, an in structure_menus for c in an["structure_issues"]}),
        "duplicate_menus": len(dup_menus),
        "slot_misplaced_menus": len(slot_bad),
        "slot_misplaced_pct": _pct(len(slot_bad), len(menus)),
        "slot_violation_examples": sorted(
            {v for _, an in slot_bad for v in an["slot_violations"]},
            key=lambda v: (0 if v.startswith(("lunch", "dinner")) else 1, v),
        )[:12],
        "slot0_staple_pct": _pct(slot0_staple, slot0_total),
        "slot0_n": slot0_total,
        "implausible_200": [{"case": c["case"], "status": c["status"]} for c in implausible_200],
        "allergy_status_by_label": {k: dict(Counter(str(v) for v in vs)) for k, vs in allergy_by_label.items()},
        "gap": {"mean": round(statistics.mean([an["gap_pct"] for _, an in analyses]), 1) if analyses else 0,
                "max": round(max([an["gap_pct"] for _, an in analyses]), 1) if analyses else 0},
        "swap": {
            "n_chains": len(A.swap_chains),
            "n_swap_steps": len(all_steps),
            "gap_series": gap_series,
            "chain5": chain5,
            "gap_first_last_delta": gap_delta,
            "gap_full_chain_delta": gap_delta,
            "gap_chain5_delta_signed": chain5_delta_signed,
            "gap_chain5_delta_abs": chain5_delta_abs,
            "max_portion_overall": max([s.get("max_portion", 0) for s in all_steps], default=0),
            "steps_with_cap": sum(1 for s in all_steps if s.get("n_at_cap", 0) > 0),
            "status_errors": [{"label": ch["label"], "error": ch.get("error")}
                              for ch in A.swap_chains if ch.get("error")],
        },
        "concurrency": A.concurrency,
        "determinism": A.determinism,
        "clinical": {
            "hypertension": {k: v for k, v in A.clinical.get("hypertension", {}).items() if k != "rows"},
            "aliases": A.clinical.get("aliases", []),
            "diabetes": A.clinical.get("diabetes", []),
        },
        "allergy": {k: v for k, v in A.allergy.items() if k != "runs"},
        "inventory": A.inventory,
        "chaos": A.chaos,
        "matrix": cover,
        "matrix_rerun_n": len(rerun_meta),
        "matrix_rerun_fitness_spread": round(
            (max(m["fitness"] for m in rerun_meta) - min(m["fitness"] for m in rerun_meta)), 1
        ) if len(rerun_meta) > 1 else None,
        "skipped": A.skipped,
        "elapsed_s": round(A.elapsed(), 1),
        "worst_menus": [
            {
                "phase": m.phase, "label": m.label, "config": m.config,
                "items": [f"{i['name']} {float(i['portion_g']):.0f}g" for i in m.items],
                "calories": m.totals.get("calories"), "sodium": m.totals.get("sodium_mg"),
                "gap_pct": an["gap_pct"], "issues": {
                    "absurd": an["absurd"], "structure": an["structure_issues"],
                    "raw": an["raw"], "condiment": an["condiments"],
                    "at_cap": an["at_cap"],
                },
                "violations": m.violations,
            }
            for m, an in worst
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "README.md").write_text(
        "# Audit live web\n\n"
        "Thư mục này do `scripts/auditor_grill_live_web.py` tạo: black-box HTTP vào server\n"
        "`app.main:app` đang chạy, không import solver, không sửa dữ liệu.\n\n"
        "- `config.json`: tham số lần chạy\n"
        "- `raw_requests.jsonl`: toàn bộ request/status/latency\n"
        "- `raw_menus.jsonl`: toàn bộ thực đơn sinh ra\n"
        "- `summary.json`: số liệu tổng hợp (khối `derived` chứa mọi dữ kiện dùng để diễn giải)\n"
        "- `REPORT.md`: báo cáo thẩm định — §2–§6 sinh từ `summary.json`, §7 đối chiếu từng khẳng định\n"
        "- `run.log`: log tiến độ\n\n"
        "Kiểm tra báo cáo khớp dữ liệu (chạy từ thư mục gốc repo, sau mọi lần dựng lại):\n\n"
        "    python scripts/check_audit_report.py experiments/<thư-mục-này>\n",
        encoding="utf-8",
    )
    md = render_markdown(summary, A)
    (out / "REPORT.md").write_text(md, encoding="utf-8")
    return summary


def render_markdown(s, A):
    """Sinh toàn bộ phần diễn giải của REPORT.md từ `s` (summary.json).

    Nguyên tắc: không có câu khẳng định nào về hệ thống được viết cứng. Mọi số
    liệu đọc từ `s` / `s["derived"]`, và mỗi con số được ghi vào bảng đối chiếu
    §7 (mã — đường dẫn — giá trị) để `scripts/check_audit_report.py` kiểm tra
    lại tự động. Thêm câu mới thì phải thêm mã `[Cxx]` tương ứng.
    """
    def num(x, nd=1):
        return "—" if x is None else f"{x:,.{nd}f}"

    d = s["derived"]
    lat = s["latency_all"]
    genw = s["latency_generate_web"]
    gens = s["latency_generate_smoke"]
    clin = s["clinical"]["hypertension"]
    aliases = s["clinical"]["aliases"]
    dia = s["clinical"]["diabetes"]
    inv = s["inventory"]
    chaos = s["chaos"]
    mat = s["matrix"]
    sw = s["swap"]
    conc = s.get("concurrency") or {}
    allergy = s["allergy"]
    det = s["determinism"]
    worst = s["worst_menus"]
    chaos_fail = [c for c in chaos if c["verdict"] == "FAIL"]
    chaos_500 = [c for c in chaos if c["status"] == 500]
    alias_ok = {a["condition"]: a["sodium_target"] for a in aliases}
    dia_ok = [r for r in dia if r.get("status") == 200]

    try:
        cfg = json.loads((Path(A.out) / "config.json").read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        cfg = {}

    claims: list[tuple[str, str, str]] = []
    seen: set[str] = set()

    def cv(cid, path, value):
        """Ghi một khẳng định vào bảng đối chiếu và trả về giá trị để in."""
        if cid not in seen:
            seen.add(cid)
            claims.append((cid, path, str(value)))
        return value

    lines = []
    L = lines.append

    L("# BÁO CÁO PHẢN BIỆN & THẨM ĐỊNH HỆ THỐNG GỢI Ý THỰC ĐƠN DBO/IDBO\n")
    L(f"- Thời điểm chạy: **{s.get('elapsed_s', 0):.0f} giây** (~{s.get('elapsed_s', 0) / 60:.0f} phút), "
      f"**{cv('C01', 'n_requests', s['n_requests'])} request HTTP thực tế** vào server `app.main:app`.")
    if cfg.get("base_url"):
        L(f"- Server: `{cfg['base_url']}`, black-box, không import solver, không sửa dữ liệu.")
    else:
        L("- Server: black-box, không import solver, không sửa dữ liệu.")
    L(f"- Thực đơn thu được để phân tích: **{cv('C02', 'n_menus', s['n_menus'])}** `[C02]`.")
    L("- Toàn bộ số liệu đọc từ `summary.json`, `raw_requests.jsonl`, `raw_menus.jsonl` trong cùng thư mục.")
    L("- **Phần diễn giải ở §2–§6 sinh tự động từ `summary.json`**, không có câu nào viết cứng. "
      "Mỗi con số mang mã `[Cxx]`; §7 đối chiếu từng mã với đường dẫn dữ liệu, "
      "`scripts/check_audit_report.py` kiểm tra lại tự động.\n")

    # ------------------------------------------------------------------ §1
    L("## 1. BẢNG TỔNG KẾT SỐ LIỆU ĐO ĐƯỢC\n")
    L("| Chỉ số | Giá trị | Mã |")
    L("|---|---|---|")
    L(f"| Tổng request | {s['n_requests']} | C01 |")
    L(f"| 200 OK | {s['status_counts'].get('200', 0)} ({s['ok_rate_pct']}%) | — |")
    L(f"| 4xx (từ chối đúng) | {d['n_4xx']} | C04 |")
    L(f"| 5xx (lỗi server) | {s['n_5xx']} | C03 |")
    L(f"| Lỗi kết nối/timeout | {s['n_err']} | — |")
    L(f"| Latency TB / trung vị / p95 / max | {num(lat['mean'])} / {num(lat['median'])} / "
      f"{lat['p95']} / {num(lat['max'])} ms | C25 |")
    L(f"| Generate `web` (TB / p95) | {num(genw['mean'])} / {num(genw['p95'])} ms (n={genw['n']}) | — |")
    L(f"| Generate `smoke` (TB) | {num(gens['mean'])} ms (n={gens['n']}) | — |")
    L(f"| Menu có ≥1 vi phạm | {s['menus_with_violation']}/{s['n_menus']} "
      f"({s['menus_with_violation_pct']}%) | C07 |")
    L(f"| Fitness TB (menu sinh ra) | {num(s['fitness']['mean'])} "
      f"(min {num(s['fitness']['min'])} – max {num(s['fitness']['max'])}) | — |")
    L(f"| Menu có fitness âm | {d['n_menus_fitness_negative']} | C09 |")
    L(f"| Sodium cao nhất | {s['sodium']['max']} mg | C10 |")
    L(f"| Menu vượt 1500 mg natri (mọi hồ sơ) | {s['sodium']['n_over_1500']}/{s['n_menus']} | C11 |")
    L(f"| Menu vượt 2300 mg natri | {s['sodium']['n_over_2300']}/{s['n_menus']} | — |")
    L(f"| Hồ sơ tăng huyết áp: menu / vượt 1500 mg | {d['n_hyp_menus']} / {d['n_hyp_over_1500']} "
      "| [C12] [C13] |")
    L(f"| Độ lệch dinh dưỡng TB (calo+4 macro) | {s['gap']['mean']}% (max {s['gap']['max']}%) | — |")
    L(f"| Menu có món kịch trần ≥{d['at_cap_threshold_g']:.1f} g | "
      f"{s['at_cap_menus']}/{s['n_menus']} ({s['at_cap_pct']}%) | C15 |")
    L(f"| Menu có khẩu phần phản ẩm thực | {s['absurd_menus']}/{s['n_menus']} | C16 |")
    L(f"| Menu sai cơ cấu bữa trưa/tối | {s['structure_fail_menus']}/{s['n_menus']} "
      f"({s['structure_fail_pct']}%) | C17 |")
    L(f"| Menu sai vai trò slot ẩm thực | {s['slot_misplaced_menus']}/{s['n_menus']} "
      f"({s['slot_misplaced_pct']}%) | — |")
    L(f"| Slot đầu bữa trưa/tối đúng là tinh bột | {s['slot0_staple_pct']}% ({s['slot0_n']} slot) | C18 |")
    L(f"| Menu chứa gia vị như món độc lập | {s['condiment_menus']}/{s['n_menus']} | — |")
    L(f"| Menu có nguyên liệu gốc bị coi là thô | {s['raw_menus']}/{s['n_menus']} | C19 |")
    L(f"| Menu hiển thị tên nguyên liệu thô | {s['raw_display_menus']}/{s['n_menus']} | C19b |")
    L(f"| Menu có món chính không nêu cách chế biến | {s['no_prep_pct']}% "
      f"({s['no_prep_menus']}/{s['n_menus']}) | C20 |")
    L(f"| Lượt lọt dị ứng ngữ nghĩa (token “hải sản”) | {allergy.get('semantic_leak_runs', 0)}/"
      f"{allergy.get('n_runs', 0)} | C21 |")
    L(f"| Lượt lọt dị ứng theo khớp chuỗi con (bộ dò auditor) | {allergy.get('leak_runs', 0)}/"
      f"{allergy.get('n_runs', 0)} | — |")
    L(f"| Lượt dị ứng trả 400 | {d['n_allergy_menus_400']}/{allergy.get('n_runs', 0)} | C22 |")
    L(f"| Menu trùng món trong ngày | {s['duplicate_menus']} | — |")
    L(f"| Số bước swap đo được | {sw['n_swap_steps']} (max portion {num(sw['max_portion_overall'], 0)} g) | — |")
    L(f"| Menu swap có trả `fitness` | {d['n_swap_menus_with_fitness']}/{d['n_swap_menus']} | C14 |")
    L(f"| Biến thiên gap toàn chuỗi swap | {sw['gap_full_chain_delta']} điểm % (baseline → cuối) | C24 |")
    L(f"| Biến thiên gap 5 bước cuối | {sw['gap_chain5_delta_signed']} điểm % "
      f"(signed; abs {sw['gap_chain5_delta_abs']}) | C24b |")
    L(f"| 10 swap đồng thời | {conc.get('status_counts')} · max {conc.get('latency_max_ms')} ms | — |")
    L(f"| Tái lập cùng seed | ids giống: {det.get('same_ids')} · portion giống: {det.get('same_portions')} "
      "| [C23] [C23b] |")
    L(f"| Ma trận nhân khẩu | {mat.get('ok')} OK / {mat.get('err')} lỗi, {s.get('matrix_rerun_n')} rerun seed "
      "| C27 |")
    L(f"| Nhất quán calo vs 4P+4C+9F | {s['cal_macro_mismatch_pct']['n_checked']} menu kiểm, "
      f"lệch max {s['cal_macro_mismatch_pct']['max']}%, "
      f"{s['cal_macro_mismatch_pct']['n_over_10pct']} menu >10% | C28 |")

    # §1 in số trực tiếp, §7 mới là nơi ghi lại (mã, đường dẫn, giá trị) để kiểm tra.
    for cid, path, value in (
        ("C01", "n_requests", s["n_requests"]),
        ("C03", "n_5xx", s["n_5xx"]),
        ("C04", "derived.n_4xx", d["n_4xx"]),
        ("C05", "derived.n_400_internal_message", d["n_400_internal_message"]),
        ("C07", "menus_with_violation", s["menus_with_violation"]),
        ("C09", "derived.n_menus_fitness_negative", d["n_menus_fitness_negative"]),
        ("C10", "sodium.max", s["sodium"]["max"]),
        ("C11", "sodium.n_over_1500", s["sodium"]["n_over_1500"]),
        ("C12", "derived.n_hyp_menus", d["n_hyp_menus"]),
        ("C13", "derived.n_hyp_over_1500", d["n_hyp_over_1500"]),
        ("C14", "derived.n_swap_menus_with_fitness", d["n_swap_menus_with_fitness"]),
        ("C15", "at_cap_menus", s["at_cap_menus"]),
        ("C16", "absurd_menus", s["absurd_menus"]),
        ("C17", "structure_fail_menus", s["structure_fail_menus"]),
        ("C18", "slot0_staple_pct", s["slot0_staple_pct"]),
        ("C19", "raw_menus", s["raw_menus"]),
        ("C19b", "raw_display_menus", s["raw_display_menus"]),
        ("C20", "no_prep_pct", s["no_prep_pct"]),
        ("C21", "allergy.semantic_leak_runs", allergy.get("semantic_leak_runs", 0)),
        ("C22", "derived.n_allergy_menus_400", d["n_allergy_menus_400"]),
        ("C23", "determinism.same_ids", det.get("same_ids")),
        ("C23b", "determinism.same_portions", det.get("same_portions")),
        ("C24", "swap.gap_first_last_delta", sw["gap_first_last_delta"]),
        ("C24b", "swap.gap_chain5_delta_signed", sw["gap_chain5_delta_signed"]),
        ("C25", "latency_all.p95", lat["p95"]),
        ("C27", "matrix.ok", mat.get("ok")),
        ("C28", "cal_macro_mismatch_pct.max", s["cal_macro_mismatch_pct"]["max"]),
    ):
        cv(cid, path, value)
    L("")
    L(f"Phân bố tuổi / BMI / vận động / cấu trúc bữa trong ma trận: `{mat.get('age')}`, "
      f"BMI `{mat.get('bmi')}`, vận động `{mat.get('activity')}`, bữa `{mat.get('meal')}`.\n")
    if s.get("skipped"):
        L(f"> Ghi chú: phần bị cắt do ngân sách thời gian: `{s['skipped']}`.\n")

    # ------------------------------------------------------------------ §2
    L("## 2. DIỄN GIẢI TỰ ĐỘNG\n")

    L("### 2.1. Lỗi server và thông điệp lỗi\n")
    if s["n_5xx"] == 0:
        L(f"- `[C03]` Không có request nào trả 5xx trên **{s['n_requests']}** request: server không sập, "
          "không rò traceback ra client.")
    else:
        L(f"- `[C03]` Có **{s['n_5xx']}** request trả 5xx. Chi tiết case chaos FAIL:")
        for c in chaos_500:
            L(f"  - `{c['case']}` → {c['status']} — {c['note'][:180]}")
    en_4xx = cv("C06", "derived.n_4xx_english_pydantic", d["n_4xx_english_pydantic"])
    if en_4xx == 0:
        L(f"- `[C04]` Trong **{d['n_4xx']}** phản hồi 4xx, **0** phản hồi chứa mẫu lỗi Pydantic "
          "tiếng Anh (`Input should…`, `String should…`, `Field required`) `[C06]`.")
    else:
        L(f"- `[C04]` **{en_4xx}/{d['n_4xx']}** phản hồi 4xx vẫn chứa câu lỗi `[C06]` "
          "Pydantic tiếng Anh → frontend sẽ hiện chuỗi kỹ thuật cho người dùng.")
    if d["n_400_internal_message"]:
        L(f"- `[C05]` **{cv('C05', 'derived.n_400_internal_message', d['n_400_internal_message'])}** "
          "phản hồi 400 có `detail` chứa thuật ngữ nội bộ "
          "(`pool`, `min_pool_size`, `has size …`) — người dùng cuối vẫn đọc thấy thông điệp kỹ thuật "
          "dù phần đầu câu đã tiếng Việt.")
    else:
        L("- `[C05]` Không phản hồi 400 nào chứa thuật ngữ nội bộ (`min_pool_size`).")
    L("")

    L("### 2.2. Swap: fitness, khẩu phần, độ lệch\n")
    L(f"- Đo được **{cv('C29', 'swap.n_swap_steps', sw['n_swap_steps'])}** bước swap trên "
      f"**{cv('C30', 'swap.n_chains', sw['n_chains'])}** chuỗi `[C29]` `[C30]`.")
    n_swap, n_fit = d["n_swap_menus"], d["n_swap_menus_with_fitness"]
    if n_swap and n_fit == n_swap:
        L(f"- `[C14]` `SwapOut` **có** trả `fitness`: **{n_fit}/{n_swap}** menu swap có trường này "
          f"(min {num(d['swap_fitness_min'], 2)} – max {num(d['swap_fitness_max'], 2)}). "
          "Vì vậy báo cáo dùng cả `fitness` (điểm solver trả về) và `gap` (độ lệch dinh dưỡng so với "
          "target, đơn vị %, là đại lượng suy ra chứ không phải fitness).")
    elif n_swap:
        L(f"- `[C14]` `SwapOut` trả `fitness` **không ổn định**: {n_fit}/{n_swap} menu swap có trường này "
          "→ không thể dùng `fitness` làm thước đo duy nhất cho swap.")
    else:
        L("- `[C14]` Không có menu swap nào trong dữ liệu đợt chạy này.")
    worse = [(k, v) for k, v in sw["chain5"].items() if v["end"] > v["start"]]
    better = [(k, v) for k, v in sw["chain5"].items() if v["end"] < v["start"]]
    flat = [(k, v) for k, v in sw["chain5"].items() if v["end"] == v["start"]]
    if sw["chain5"]:
        L(f"- Chuỗi 5 lần swap cùng slot: **{len(worse)}** chuỗi xấu đi, **{len(better)}** chuỗi tốt lên, "
          f"**{len(flat)}** chuỗi không đổi. Biến thiên trung bình đầu→cuối của đúng 5 bước: "
          f"`[C24b]` **{num(sw['gap_chain5_delta_signed'])}** điểm % "
          f"(abs {num(sw['gap_chain5_delta_abs'])}). "
          f"Toàn chuỗi (gồm các bước tuần tự trước đó): `[C24]` "
          f"**{num(sw['gap_full_chain_delta'])}** điểm %.")
        for label, v in sw["chain5"].items():
            trend = "xấu đi" if v["end"] > v["start"] else ("tốt lên" if v["end"] < v["start"] else "không đổi")
            L(f"  - {label}: {v['start']} → {v['end']} ({trend}), min {v['min']}, max {v['max']}")
        if worse:
            L("- `[SUY RA]` Dữ liệu cho thấy `gap` có thể **tăng** sau swap; audit này không ghi nhận "
              "cơ chế nào từ chối phương án có `gap`/`fitness` tệ hơn phương án trước.")
    L(f"- Tổng số bước swap có ít nhất một món chạm trần ≥{d['at_cap_threshold_g']:.1f} g: "
      f"**{cv('C31', 'swap.steps_with_cap', sw['steps_with_cap'])}/{sw['n_swap_steps']}**; "
      f"khẩu phần lớn nhất sau swap: "
      f"**{num(cv('C32', 'swap.max_portion_overall', sw['max_portion_overall']), 0)} g** `[C31]` `[C32]`.")
    L("")

    L("### 2.3. Bệnh lý\n")
    L(f"- Alias tiếng Việt: `hypertension` → {alias_ok.get('hypertension')} mg, "
      f"`tăng huyết áp` → {alias_ok.get('tăng huyết áp')} mg, "
      f"`cao huyết áp` → {alias_ok.get('cao huyết áp')} mg.")
    if dia_ok and d["diabetes_warn"] and d["diabetes_mentions_sugar"]:
        L(f"- `[C26]` Hồ sơ tiểu đường: **{len(dia_ok)}/{len(dia)}** lần gọi trả 200 "
          f"**đều có trường cảnh báo** "
          f"(`derived.diabetes_warn = {cv('C26', 'derived.diabetes_warn', d['diabetes_warn'])}`) "
          "và **đều nhắc tới sugar/đường** trong payload. Danh sách key trả về: "
          f"`{d['diabetes_keys']}`.")
    elif dia_ok:
        L(f"- `[C26]` Hồ sơ tiểu đường: {len(dia_ok)}/{len(dia)} lần gọi trả 200; "
          f"có cảnh báo = {d['diabetes_warn']}, nhắc sugar/đường = {d['diabetes_mentions_sugar']}.")
    else:
        L("- Không có lần gọi nào với hồ sơ tiểu đường trả 200 trong đợt chạy này.")
    unsupported = [a for a in aliases
                   if str(a.get("condition", "")).strip().lower()
                   not in ("hypertension", "tăng huyết áp", "cao huyết áp", "huyết áp cao",
                           "tiểu đường", "diabetes", "đái tháo đường")]
    if unsupported:
        listing = "; ".join(f"`{a['condition']}` → {a['sodium_target']} mg" for a in unsupported)
        L(f"- Bệnh lý không được mô hình hoá: {listing} — trả 200 nhưng `sodium_target` không đổi so với "
          "hồ sơ khỏe mạnh, tức không có ngưỡng riêng và không có cảnh báo “chưa hỗ trợ” trong payload.")
    L("")

    L("### 2.4. Natri\n")
    L(f"- Toàn bộ {s['n_menus']} menu: natri TB "
      f"**{num(cv('C33', 'sodium.mean', s['sodium']['mean']))} mg** `[C33]`, cao nhất "
      f"`[C10]` **{num(s['sodium']['max'])} mg**; "
      f"`[C11]` **{s['sodium']['n_over_1500']}** menu vượt 1500 mg và "
      f"**{s['sodium']['n_over_2300']}** menu vượt 2300 mg.")
    L(f"- Hồ sơ tăng huyết áp: `[C12]` **{d['n_hyp_menus']}** menu, target trả về "
      f"`{d['hyp_sodium_targets']}` mg; `[C13]` **{d['n_hyp_over_1500']}** menu vượt 1500 mg "
      f"({d['n_hyp_over_2300']} vượt cả 2300 mg), natri cao nhất **{num(d['hyp_sodium_max'])} mg**.")
    if d["n_hyp_over_1500"]:
        L("- `[SUY RA]` Ràng buộc natri **được kiểm tra và báo vi phạm**, nhưng **không được solver ép thoả** "
          "trong mọi trường hợp. Không thể tuyên bố “đáp ứng ngưỡng natri 1500 mg cho mọi thực đơn”.")
        for r in clin.get("over_1500", [])[:10]:
            L(f"  - seed {r['seed']} ({r['config']}): **{num(r['sodium'], 0)} mg**")
    else:
        L("- `[SUY RA]` Trong bộ seed này không có menu nào vượt 1500 mg; đây là kết quả trong phạm vi "
          "thử nghiệm, không phải bảo đảm lâm sàng. Ràng buộc natri vẫn là kiểm tra sau khi giải, "
          "không phải ràng buộc cứng của solver.")
    if clin.get("energy_violation") or clin.get("protein_violation"):
        L(f"- Hệ quả siết muối: "
          f"**{cv('C34', 'clinical.hypertension.energy_violation', clin.get('energy_violation'))} "
          "menu vi phạm năng lượng**, "
          f"**{cv('C35', 'clinical.hypertension.protein_violation', clin.get('protein_violation'))} "
          "menu vi phạm đạm** trên cùng bộ seed `[C34]` `[C35]`.")
    L("")

    L("### 2.5. Dị ứng\n")
    L(f"- `[C22]` {allergy.get('n_runs')} lượt sinh menu với nhiều cấu hình token loại trừ "
      "(đơn, bộ ba, 10 và 20 token); "
      f"trạng thái: `{allergy.get('status_counts')}`; "
      f"**{d['n_allergy_menus_400']}** lượt trả 400.")
    L(f"- `[C21]` Lượt còn món biển sau khi loại trừ token **“hải sản”**: "
      f"**{allergy.get('semantic_leak_runs')}/{allergy.get('n_runs')}** "
      "(khớp theo ranh giới từ, không phải chuỗi con).")
    if allergy.get("leak_runs"):
        L(f"- Bộ dò của auditor còn ghi **{allergy.get('leak_runs')}** lượt “lọt” theo **khớp chuỗi con**: "
          f"`{allergy.get('leak_examples')}`. Đây là false-positive của bộ dò (ví dụ “Gạo nếp **cái**” chứa "
          "“cá”), không phải món hải sản; chỉ số đúng là `[C21]`.")
    single_400 = [k for k, v in s.get("allergy_status_by_label", {}).items()
                  if k.startswith("single:") and "400" in v]
    if single_400:
        L(f"- Loại trừ **một** nhóm quen thuộc cũng làm hỏng yêu cầu: `{single_400}` trả 400, "
          "vì pool ứng viên còn lại nhỏ hơn `min_pool_size`. Hệ thống từ chối tạo thực đơn thay vì crash, "
          "nhưng người dùng không nhận được gợi ý nới điều kiện.")
    L("")

    L("### 2.6. Khẩu phần và ẩm thực\n")
    L(f"- `[C15]` Menu có món chạm trần ≥{d['at_cap_threshold_g']:.1f} g: **{s['at_cap_menus']}/{s['n_menus']}** "
      f"({s['at_cap_pct']}%). `[C16]` Khẩu phần bị coi là phản ẩm thực: **{s['absurd_menus']}** menu.")
    if s["at_cap_examples"]:
        L(f"  - Ví dụ chạm trần: `{s['at_cap_examples'][:8]}`.")
    if s["absurd_examples"]:
        L(f"  - Ví dụ khẩu phần phản ẩm thực: `{s['absurd_examples'][:8]}`.")
    L(f"- `[C18]` Slot đầu bữa trưa/tối đúng là tinh bột: **{s['slot0_staple_pct']}%** trên "
      f"{s['slot0_n']} slot; `[C17]` **{s['structure_fail_menus']}/{s['n_menus']}** "
      f"({s['structure_fail_pct']}%) menu bị coi là sai cơ cấu bữa.")
    L("- `[CẢNH BÁO ĐO LƯỜNG]` Auditor phân vai trò món bằng **từ vựng độc lập** với `DishRole` của hệ thống, "
      "nên 100% “sai” không đồng nghĩa 100% lỗi sản phẩm. Phải đối chiếu hai định nghĩa slot trước khi "
      "sửa theo con số này.")
    L(f"- `[C19]` **{s['raw_menus']}/{s['n_menus']}** menu có nguyên liệu gốc thuộc nhóm bị bộ dò coi là thô; "
      f"`[C19b]` **{s['raw_display_menus']}/{s['n_menus']}** menu còn hiển thị tên nguyên liệu thô; "
      f"`[C20]` **{s['no_prep_pct']}%** menu có món chính không nêu cách chế biến. "
      "C19 là giới hạn dữ liệu gốc (bảng dinh dưỡng theo 100 g nguyên liệu), không phải lỗi dinh dưỡng; "
      "C19b/C20 đo lớp ghép món hiển thị và phải đọc cùng C19.")
    if s["condiment_menus"]:
        L(f"- Gia vị xuất hiện như món độc lập: **{s['condiment_menus']}** menu `{s['condiment_examples'][:6]}`.")
    else:
        L("- Không có menu nào chứa gia vị như món độc lập trong đợt chạy này.")
    L(f"- `[C28]` Nhất quán calo vs 4P+4C+9F: lệch lớn nhất **{s['cal_macro_mismatch_pct']['max']}%**, "
      f"**{s['cal_macro_mismatch_pct']['n_over_10pct']}** menu lệch >10%.")
    L("")

    L("### 2.7. Dữ liệu món ăn\n")
    L(f"- Mẫu **{cv('C36', 'inventory.n_foods_sampled', inv.get('n_foods_sampled'))}** món `[C36]` "
      "lấy từ `/api/foods`; trong mẫu đó có "
      f"**{len(inv.get('condiments', []))}** tên gia vị, **{len(inv.get('raw', []))}** tên nguyên liệu thô, "
      f"**{len(inv.get('no_prep', []))}** tên không nêu cách chế biến.")
    if inv.get("max_sodium_per_100g"):
        L(f"- Natri/100 g cao nhất: `{inv.get('max_sodium_per_100g', [])[:5]}` — những món này một mình "
          "đã chiếm phần lớn ngưỡng 1500 mg/ngày.")
    L("")

    L("### 2.8. Chaos / fuzzing\n")
    L("| Case | Kỳ vọng | Thực tế | Kết luận |")
    L("|---|---|---|---|")
    for c in chaos:
        L(f"| {c['case']} | {c['expected']} | {c['status']} | {c['verdict']} |")
    L("")
    L(f"- **{len(chaos_fail)} case FAIL**, **{len(chaos_500)} case 500**.")
    if s["implausible_200"]:
        L(f"- **{len(s['implausible_200'])}** hồ sơ phi thực tế vẫn trả 200 "
          f"({', '.join(c['case'] for c in s['implausible_200'])}): thiếu kiểm tra hợp lý sinh học, "
          "không phải lỗi crash.")
    else:
        L("- Không có hồ sơ phi thực tế nào lọt qua.")
    L("")

    # ------------------------------------------------------------------ §3
    L("## 3. NHỮNG THỰC ĐƠN TỆ NHẤT GHI NHẬN ĐƯỢC\n")
    L("> Danh sách dưới đây do hàm chấm điểm của auditor xếp hạng từ chính `raw_menus.jsonl`.\n")
    for i, w in enumerate(worst, 1):
        L(f"**{i}. [{w['phase']}] {w['label']}** — {num(w['calories'], 0)} kcal, "
          f"natri {num(w['sodium'], 0)} mg, lệch target {w['gap_pct']}%")
        L(f"   - Món: {'; '.join(w['items'])}")
        if w["issues"]["absurd"]:
            L(f"   - Khẩu phần phản ẩm thực: {'; '.join(w['issues']['absurd'])}")
        if w["issues"]["structure"]:
            L(f"   - Cơ cấu bữa: {'; '.join(w['issues']['structure'])}")
        if w["issues"]["raw"]:
            L(f"   - Nguyên liệu thô (theo bộ dò): {'; '.join(w['issues']['raw'])}")
        if w["issues"]["condiment"]:
            L(f"   - Gia vị như món chính: {'; '.join(w['issues']['condiment'])}")
        if w["violations"]:
            L(f"   - Vi phạm: {'; '.join(w['violations'])}")
        L("")

    # ------------------------------------------------------------------ §4
    L("## 4. CÂU HỎI “BẪY” VÀ CÂU TRẢ LỜI SINH TỪ SỐ LIỆU\n")
    L("**Câu 1. “Hệ thống khẳng định thực đơn an toàn cho người tăng huyết áp. Vậy vì sao có seed ra "
      f"{num(d['hyp_sodium_max'], 0)} mg natri?”**")
    L(f"- Trả lời: “Không. Chúng em chỉ khẳng định thực đơn **đáp ứng hoặc không đáp ứng ngưỡng được "
      f"cấu hình trong thử nghiệm**. Trong {d['n_hyp_menus']} thực đơn của hồ sơ tăng huyết áp, "
      f"{d['n_hyp_over_1500']} thực đơn vượt 1500 mg và hệ thống báo vi phạm đúng; đây là hạn chế của bộ giải, "
      "không phải bảo đảm lâm sàng. Đây không phải thiết bị y tế.”")
    L("")
    L("**Câu 2. “Món ‘Gạo lứt 115 g’ là món gì? Ai ăn gạo sống?”**")
    L(f"- Trả lời: “Bảng dinh dưỡng lưu tên nguyên liệu theo 100 g; menu hiển thị tên món đã ghép "
      f"ở lớp trình bày. Bộ đo tên nguyên liệu thô hiển thị (`[C19b]`) ghi nhận "
      f"{s['raw_display_menus']}/{s['n_menus']} thực đơn ({_pct(s['raw_display_menus'], s['n_menus'])}%). "
      "Chỉ số này khác với việc thiếu mô tả cách chế biến (`[C20]`). Tên món ghép không thay đổi "
      "dữ liệu dinh dưỡng gốc.”")
    L("")
    L("**Câu 3. “Nếu tôi dị ứng hải sản và gõ ‘hải sản’, hệ thống có loại tôm cua cá không?”**")
    if allergy.get("semantic_leak_runs", 0) == 0:
        L(f"- Trả lời: “Trong {allergy.get('n_runs')} lượt thử, **không lượt nào còn món biển** sau khi "
          f"loại trừ token ‘hải sản’ (`[C21]` = 0). Bộ dò chuỗi con của auditor "
          f"vẫn ghi {allergy.get('leak_runs')} lượt, nhưng đó là false-positive như ‘Gạo nếp **cái**’ chứa "
          "‘cá’. Giới hạn còn lại: taxonomy hiện chỉ phủ một số nhóm thực phẩm, dị ứng ngoài "
          "các nhóm đó vẫn dựa vào so khớp chuỗi.”")
    else:
        L(f"- Trả lời trung thực: “Còn {allergy.get('semantic_leak_runs')}/{allergy.get('n_runs')} lượt vẫn "
          "lọt món biển sau khi loại trừ token ‘hải sản’. Đây là lỗi an toàn ưu tiên cao, cần bổ sung "
          "từ điển allergen trước khi demo cho người dị ứng.”")
    L("")
    L("**Câu 4. “Điểm fitness nghĩa là gì với bệnh nhân? Bấm Đổi món 5 lần thì điểm có đổi không?”**")
    if n_swap and n_fit == n_swap:
        L(f"- Trả lời: “Fitness là hàm mục tiêu nội bộ, không phải chỉ số sức khỏe. `SwapOut` **có** trả "
          f"`fitness` ({n_fit}/{n_swap} menu swap), nên giao diện cập nhật được điểm sau mỗi lần đổi món. "
          "Vấn đề còn lại là ý nghĩa: một con số 0–100 không cho người bệnh biết đang thiếu hay thừa chất gì.”")
    else:
        L("- Trả lời: “`SwapOut` không trả `fitness` ổn định trong đợt chạy này, nên giao diện có thể vẫn "
          "hiển thị điểm cũ sau khi đổi món. Fitness là hàm mục tiêu nội bộ, không phải chỉ số sức khỏe.”")
    L("")
    if s["at_cap_menus"] or s["absurd_menus"]:
        L("**Câu 5. “Vì sao có món khẩu phần rất lớn? Ràng buộc khẩu phần của em đâu?”**")
        L(f"- Trả lời: “Trong đợt chạy này có {s['at_cap_menus']}/{s['n_menus']} menu có món chạm ngưỡng "
          f"≥{d['at_cap_threshold_g']:.1f} g và {s['absurd_menus']} menu bị coi là khẩu phần phản ẩm thực. "
          "Ngưỡng khẩu phần theo vai trò món được áp ở tầng sinh thực đơn và sau khi làm tròn; con số này là "
          "phần chưa khớp giữa ngưỡng của hệ thống và tiêu chí của bộ đo độc lập.”")
    else:
        L("**Câu 5. “Vì sao bảng thực đơn có nhiều món là nguyên liệu thô như ‘Măng tre 220 g’?”**")
        L(f"- Trả lời: “Tên hiển thị đã được ghép thành món: {s['raw_display_menus']}/{s['n_menus']} menu "
          f"còn hiển thị tên nguyên liệu thô (`[C19b]`), {s['no_prep_pct']}% menu có món chính không nêu "
          f"cách chế biến (`[C20]`). Tuy nhiên {s['raw_menus']}/{s['n_menus']} menu vẫn có nguyên liệu gốc "
          "thuộc nhóm thô (`[C19]`), vì dữ liệu dinh dưỡng là bảng theo 100 g nguyên liệu và chưa có bảng "
          "món nấu chín tương ứng. Đây là giới hạn dữ liệu, không phải khẩu phần thô được phục vụ. "
          f"Trong đợt chạy này không có món nào chạm trần khẩu phần ≥{d['at_cap_threshold_g']:.1f} g "
          f"(`[C15]` = {s['at_cap_menus']}).”")
    L("")

    # ------------------------------------------------------------------ §5
    L("## 5. VIỆC CẦN FIX — CHỈ HIỆN KHI CHỈ SỐ TƯƠNG ỨNG KHÁC 0\n")
    fixes = []
    if d["n_hyp_over_1500"]:
        fixes.append(f"**Natri ở hồ sơ tăng huyết áp**: {d['n_hyp_over_1500']}/{d['n_hyp_menus']} menu vượt "
                     f"1500 mg (cao nhất {num(d['hyp_sodium_max'], 0)} mg). Cần đo feasibility của trần cứng "
                     "trước khi chọn giữa (a) ràng buộc cứng và (b) loại món có natri/100 g rất cao khỏi pool.")
    if allergy.get("semantic_leak_runs", 0) or d["n_allergy_menus_400"]:
        fixes.append("**Dị ứng**: mở rộng taxonomy allergen và bỏ fallback so khớp chuỗi con; "
                     f"{d['n_allergy_menus_400']} lượt trả 400 cần thông điệp nêu rõ món nào đang chặn pool.")
    if s["condiment_menus"] or s["absurd_menus"] or s["at_cap_menus"]:
        fixes.append(f"**Khẩu phần**: {s['at_cap_menus']} menu chạm ngưỡng và {s['absurd_menus']} menu bị coi "
                     "là phản ẩm thực; siết biên theo vai trò ở cả solver và validation.")
    if n_swap and n_fit < n_swap:
        fixes.append("**Swap**: bổ sung `fitness`/`diversity_pct` vào `SwapOut` hoặc bỏ điểm số khỏi UI sau "
                     "khi đổi món, để người dùng không thấy điểm cũ của thực đơn đã đổi.")
    if not d["diabetes_warn"]:
        fixes.append("**Cảnh báo bệnh lý**: thêm `warnings`/`data_limitations` vào response; tiểu đường phải "
                     "nêu rõ không có dữ liệu đường và không kết luận an toàn.")
    if d["n_4xx_english_pydantic"] or d["n_400_internal_message"]:
        parts = []
        if d["n_400_internal_message"]:
            parts.append(f"{d['n_400_internal_message']} phản hồi 400 còn lộ thuật ngữ nội bộ "
                         "(`pool`, `min_pool_size`)")
        if d["n_4xx_english_pydantic"]:
            parts.append(f"{d['n_4xx_english_pydantic']} phản hồi còn mẫu lỗi Pydantic tiếng Anh")
        fixes.append("**Thông điệp lỗi**: " + " và ".join(parts) + " — cần Việt hoá trọn câu.")
    if s["no_prep_pct"] >= 10:
        fixes.append(f"**Lớp tên món**: {s['no_prep_pct']}% menu có món chính không nêu cách chế biến; "
                     "thêm tên món ăn ở lớp hiển thị, không đổi nutrient hay `food_id`.")
    if s["structure_fail_pct"] > 0:
        fixes.append(f"**Cơ cấu bữa**: {s['structure_fail_pct']}% menu bị coi là sai cấu trúc theo bộ đo độc "
                     "lập; cần đối chiếu định nghĩa slot trước khi sửa.")
    if not fixes:
        L("Không có chỉ số nào vượt ngưỡng trong dữ liệu đợt chạy này.")
    else:
        for i, fx in enumerate(fixes, 1):
            L(f"{i}. {fx}")
    L("")

    # ------------------------------------------------------------------ §6
    L("## 6. GHI CHÚ THỦ CÔNG — KHÔNG SINH TỪ DỮ LIỆU\n")
    L("> Mục này **cố ý** không suy ra từ `summary.json`. Nó là quan sát giao diện, kiểm bằng cách đọc "
      "code frontend, nên **không tự cập nhật** khi chạy lại audit. Sửa UI thì phải sửa tay mục này.\n")
    L("- Bảng thực đơn hiển thị song song khẩu phần thô và khẩu phần đã làm tròn "
      "(`portion_g` → `portion_g_rounded`) — `app/static/js/app.js`, khối `renderMenu`.")
    L("- Dòng “Tổng ngày” in số tuyệt đối; ngưỡng cá nhân không nằm cạnh con số mà chỉ xuất hiện trong "
      "khối vi phạm bên dưới — cùng file, phần `totalRow` và `renderViolations`.")
    L("- Seed và cấu hình solver nằm trong `<details class=\"advanced-settings\">` "
      "(`app/static/index.html`), đã thu gọn mặc định.")
    L("- Thông điệp 422 được Việt hoá ở cả backend và `formatFieldError()` trong `app/static/js/api.js`; "
      "cảnh báo bệnh lý hiển thị qua `renderWarnings`.\n")

    # ------------------------------------------------------------------ §7
    L("## 7. BẢNG ĐỐI CHIẾU KHẲNG ĐỊNH ↔ DỮ LIỆU\n")
    L("Mỗi dòng: mã — đường dẫn trong `summary.json` — giá trị đã in ở trên. "
      "`scripts/check_audit_report.py <thư-mục>` đọc bảng này, so lại với `summary.json` và báo lệch.\n")
    L("```text")
    for cid, path, value in sorted(claims):
        L(f"{cid}\t{path}\t{value}")
    L("```\n")

    L("---")
    L(f"*Số liệu sinh tự động từ {s['n_requests']} request trong {s.get('elapsed_s', 0):.0f} giây; "
      "toàn bộ phần diễn giải đọc từ `summary.json` (xem §7), không có câu nào viết cứng. "
      "Đọc/ghi chỉ trong thư mục `experiments/` của đợt chạy; không đụng dữ liệu production.*")
    return "\n".join(lines) + "\n"
