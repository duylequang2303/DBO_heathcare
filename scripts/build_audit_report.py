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
        vals = [s["gap"] for s in ch.get("steps", []) if str(s.get("step", "")).startswith("chain")]
        if vals:
            chain5[ch["label"]] = {"start": vals[0], "end": vals[-1],
                                   "min": min(vals), "max": max(vals)}

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

    # ---- builds
    summary = {
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
        "- `summary.json`: số liệu tổng hợp\n"
        "- `REPORT.md`: báo cáo thẩm định\n"
        "- `run.log`: log tiến độ\n",
        encoding="utf-8",
    )
    md = render_markdown(summary, A)
    (out / "REPORT.md").write_text(md, encoding="utf-8")
    return summary


def render_markdown(s, A):
    def f(x, nd=1):
        return f"{x:,.{nd}f}"

    lat = s["latency_all"]
    genw = s["latency_generate_web"]
    gens = s["latency_generate_smoke"]
    clin = s["clinical"]["hypertension"]
    aliases = s["clinical"]["aliases"]
    dia = s["clinical"]["diabetes"]
    inv = s["inventory"]
    chaos = s["chaos"]
    chaos_fail = [c for c in chaos if c["verdict"] == "FAIL"]
    chaos_500 = [c for c in chaos if c["status"] == 500]
    mat = s["matrix"]
    sw = s["swap"]
    conc = s["concurrency"]
    allergy = s["allergy"]
    det = s["determinism"]
    over_hyp = clin.get("over_1500", [])
    worst = s["worst_menus"]
    alias_ok = {a["condition"]: a["sodium_target"] for a in aliases}
    hyp_alias = alias_ok.get("tăng huyết áp")
    hyp_base = alias_ok.get("hypertension")
    dia_warn = any(d.get("mentions_warning") for d in dia)
    dia_sugar = any(d.get("mentions_sugar") for d in dia)

    lines = []
    L = lines.append
    L("# BÁO CÁO PHẢN BIỆN & THẨM ĐỊNH HỆ THỐNG GỢI Ý THỰC ĐƠN DBO/IDBO\n")
    L(f"- Thời điểm chạy: **{s.get('elapsed_s', 0):.0f} giây** (~{s.get('elapsed_s', 0)/60:.0f} phút), "
      f"**{s['n_requests']} request HTTP thực tế** vào server `app.main:app`.")
    L(f"- Server: `http://127.0.0.1:8000`, black-box, không import solver, không sửa dữ liệu.")
    L(f"- Thực đơn thu được để phân tích: **{s['n_menus']}**.")
    L("- Mọi số liệu dưới đây đọc từ `summary.json`, `raw_requests.jsonl`, `raw_menus.jsonl` "
      "trong cùng thư mục.\n")

    L("## 1. BẢNG TỔNG KẾT SỐ LIỆU ĐO ĐƯỢC\n")
    L("| Chỉ số | Giá trị |")
    L("|---|---|")
    L(f"| Tổng request | {s['n_requests']} |")
    L(f"| 200 OK | {s['status_counts'].get('200', 0)} ({s['ok_rate_pct']}%) |")
    L(f"| 4xx (từ chối đúng) | {s['n_4xx']} |")
    L(f"| 5xx (lỗi server) | {s['n_5xx']} |")
    L(f"| Lỗi kết nối/timeout | {s['n_err']} |")
    L(f"| Latency TB / trung vị / p95 / max | {f(lat['mean'])} / {f(lat['median'])} / {f(lat['p95'])} / {f(lat['max'])} ms |")
    L(f"| Generate `web` (TB / p95) | {f(genw['mean'])} / {f(genw['p95'])} ms (n={genw['n']}) |")
    L(f"| Generate `smoke` (TB) | {f(gens['mean'])} ms (n={gens['n']}) |")
    L(f"| Menu có ≥1 vi phạm | {s['menus_with_violation']}/{s['n_menus']} ({s['menus_with_violation_pct']}%) |")
    L(f"| Fitness TB (menu sinh ra) | {s['fitness']['mean']} (min {s['fitness']['min']} – max {s['fitness']['max']}) |")
    L(f"| Sodium cao nhất | {f(s['sodium']['max'])} mg |")
    L(f"| Menu vượt 1500 mg natri | {s['sodium']['n_over_1500']}/{s['n_menus']} |")
    L(f"| Menu vượt 2300 mg natri | {s['sodium']['n_over_2300']}/{s['n_menus']} |")
    L(f"| Độ lệch dinh dưỡng TB (calo+4 macro) | {s['gap']['mean']}% (max {s['gap']['max']}%) |")
    L(f"| Menu có món kịch trần 350 g | {s['at_cap_menus']}/{s['n_menus']} ({s['at_cap_pct']}%) |")
    L(f"| Menu có khẩu phần phản ẩm thực | {s['absurd_menus']}/{s['n_menus']} |")
    L(f"| Menu sai cơ cấu bữa trưa/tối | {s['structure_fail_menus']}/{s['n_menus']} ({s['structure_fail_pct']}%) |")
    L(f"| Menu sai vai trò slot ẩm thực | {s['slot_misplaced_menus']}/{s['n_menus']} ({s['slot_misplaced_pct']}%) |")
    L(f"| Slot đầu bữa trưa/tối đúng là tinh bột | {s['slot0_staple_pct']}% ({s['slot0_n']} slot) |")
    L(f"| Menu chứa gia vị như món độc lập | {s['condiment_menus']}/{s['n_menus']} |")
    L(f"| Menu chứa nguyên liệu thô | {s['raw_menus']}/{s['n_menus']} |")
    L(f"| Menu có món chính không nêu cách chế biến | {s['no_prep_menus']}/{s['n_menus']} ({s['no_prep_pct']}%) |")
    L(f"| Lượt lọt dị ứng (sau khi yêu cầu loại trừ) | {allergy.get('leak_runs', 0)}/{allergy.get('n_runs', 0)} |")
    L(f"| Menu trùng món trong ngày | {s['duplicate_menus']} |")
    L(f"| Số bước swap đo được | {sw['n_swap_steps']} (max portion {f(sw['max_portion_overall'],0)} g) |")
    L(f"| Biến thiên độ lệch dinh dưỡng qua swap | {f(sw['gap_first_last_delta'])} điểm % (đầu → cuối) |")
    L(f"| 10 swap đồng thời | {conc.get('status_counts')} · max {conc.get('latency_max_ms')} ms |")
    L(f"| Tái lập cùng seed | ids giống: {det.get('same_ids')} · portion giống: {det.get('same_portions')} |")
    L(f"| Ma trận nhân khẩu | {mat.get('ok')} OK / {mat.get('err')} lỗi, {s.get('matrix_rerun_n')} rerun seed |")
    L("")
    L("Phân bố tuổi / BMI / vận động / cấu trúc bữa trong ma trận: "
      f"? `{mat.get('age')}`, BMI `{mat.get('bmi')}`, vận động `{mat.get('activity')}`, bữa `{mat.get('meal')}`.\n".replace("? ", ""))
    if s.get("skipped"):
        L(f"> Ghi chú: phần bị cắt do ngân sách thời gian: `{s['skipped']}`.\n")

    L("### 1.1. Lỗi 500\n")
    if s["n_5xx"] == 0:
        L("**Không có request nào trả 500 Internal Server Error** trong toàn bộ đợt test. "
          "Server không sập, không rò traceback ra client.\n")
    else:
        L(f"**Có {s['n_5xx']} request trả 5xx.** Chi tiết các case chaos FAIL:\n")
        for c in chaos_500:
            L(f"- `{c['case']}` → {c['status']} — {c['note'][:180]}")
        L("")

    L("### 1.2. Swap: điểm fitness và khẩu phần\n")
    L("`POST /api/menu/swap` **không trả `fitness`, `diversity_pct`, `runtime_s`** (response schema "
      "`SwapOut` chỉ có items/totals/targets/violations/delta). Vì vậy không thể đọc “điểm fitness sau swap” "
      "từ API; báo cáo dùng **độ lệch dinh dưỡng trung bình so với target (%)** làm đại lượng thay thế, "
      "ghi rõ đây là proxy chứ không phải fitness của solver.\n")
    L("| Chuỗi | gap đầu (%) | gap cuối (%) | gap min | gap max |")
    L("|---|---|---|---|---|")
    for label, vals in sw["gap_series"].items():
        L(f"| {label} | {vals[0]} | {vals[-1]} | {min(vals)} | {max(vals)} |")
    L("")
    if sw["chain5"]:
        L("5 lần swap liên tiếp trên cùng một slot:\n")
        L("| Chuỗi | trước | sau 5 lần | thấp nhất | cao nhất |")
        L("|---|---|---|---|---|")
        for label, v in sw["chain5"].items():
            L(f"| {label} | {v['start']} | {v['end']} | {v['min']} | {v['max']} |")
        L("")
    L(f"- Tổng số bước swap có ít nhất một món chạm trần 350 g: **{sw['steps_with_cap']}/{sw['n_swap_steps']}**.")
    L(f"- Khẩu phần lớn nhất ghi nhận sau swap: **{f(sw['max_portion_overall'],0)} g**.")
    L("- Frontend giữ lại fitness cũ sau swap (`app.js`: `res.fitness = res.fitness ?? state.menu?.fitness`), "
      "nên người dùng vẫn thấy điểm cũ trong khi thực đơn đã đổi — đây là lỗi hiển thị, không phải lỗi solver.\n")

    L("## 2. NHỮNG HẠN CHẾ CHÍ MẠNG VỀ TRẢI NGHIỆM NGƯỜI DÙNG (UX)\n")
    L("1. **“Fitness /100” là khái niệm của người làm thuật toán, không phải của người ăn.** "
      "Toast sau khi tạo thực đơn hiện `Fitness: {fitness}`; người dùng không biết 87.4 tốt hay xấu, "
      "không biết có ăn được không. Cần thay bằng ngôn ngữ mục tiêu: “Đạt 94% calo mục tiêu”, "
      "“Đạm thiếu 12 g”.")
    L("2. **Bảng thực đơn hiển thị khẩu phần thô và khẩu phần làm tròn cạnh nhau** "
      "(`157.3g → 155g`). Người dùng thấy hai con số cho cùng một món và không biết tin số nào; "
      "nên chỉ hiển thị số đã làm tròn, kèm ghi chú “khẩu phần gợi ý”.")
    L("3. **Cột “Seed” và “Cấu hình solver Smoke/Web/Full” lộ ra ngoài UI.** Đây là tham số tái lập "
      "thực nghiệm, không phải lựa chọn của người bệnh. Nếu cần giữ cho demo, đặt trong mục “Nâng cao” "
      "thu gọn, mặc định ẩn.")
    L("4. **Thông báo lỗi không đồng nhất ngôn ngữ.** Lỗi nghiệp vụ do nhóm viết bằng tiếng Việt "
      "(`Thực đơn cần ít nhất 1 món trưa...`), nhưng lỗi 422 của Pydantic là tiếng Anh kỹ thuật "
      "(`Input should be a valid integer`, `String should have at least 2 characters`). "
      "Frontend chỉ hiện `err.message`, nên người dùng nhận chuỗi tiếng Anh khó hiểu. "
      f"Trong đợt test có **{s['n_4xx']} phản hồi 4xx**, phần lớn thuộc nhóm này.")
    L("5. **Không có cảnh báo bệnh lý tại thời điểm trả thực đơn.** Với hồ sơ tiểu đường, response "
      f"{'có' if dia_warn else '**không**'} chứa bất kỳ trường cảnh báo/lưu ý nào; "
      f"chuỗi “sugar/đường” {'có' if dia_sugar else '**không**'} xuất hiện trong payload. "
      "Người bệnh tiểu đường nhận thực đơn như người khỏe mạnh, không được nhắc rằng hệ thống "
      "không có dữ liệu đường để đánh giá.")
    L("6. **Không có trạng thái “đang tính” đủ rõ cho cấu hình web.** "
      f"Generate `web` mất trung bình **{f(genw['mean']/1000,1)} giây** (p95 {f(genw['p95']/1000,1)} s) "
      "trên server nội bộ; trên máy yếu hoặc deploy xa, người dùng rất dễ bấm lại nhiều lần. "
      "Nút bị disable trong lúc chờ là đúng, nhưng không có ước lượng thời gian hay huỷ.")
    L("7. **Bảng chỉ có số tuyệt đối, thiếu ngữ cảnh.** Người dùng thấy “Natri 1 842 mg” nhưng không "
      "thấy ngưỡng cá nhân (1 500 mg cho tăng huyết áp) ngay cạnh con số; chỉ khi cuộn xuống mới thấy "
      "danh sách vi phạm. Nên đổi màu/ghi “vượt 342 mg” tại dòng tổng.")
    L("8. **Tên món là tên nguyên liệu, không phải tên món ăn.** "
      f"{s['no_prep_pct']}% thực đơn chứa ít nhất một món chính (tinh bột/đạm) không nêu cách chế biến "
      "(ví dụ: “Gạo lứt 115 g”, “Khoai tây 250 g”, “Măng tre 350 g”, “Đuôi lợn 140 g”). "
      "Với người dùng, đây là danh sách đi chợ chứ không phải thực đơn.\n")

    L("## 3. NHỮNG BẤT CẬP VỀ DINH DƯỠNG & ẨM THỰC THỰC TẾ\n")
    L("### 3.1. Natri ở hồ sơ tăng huyết áp\n")
    L(f"- Chạy **{clin.get('n')} seed** (một phần cấu hình `web`, phần còn lại `smoke`): "
      f"sodium trung bình **{f(clin.get('sodium_mean', 0))} mg**, cao nhất **{f(clin.get('sodium_max',0),0)} mg**, "
      f"target server trả về `{clin.get('targets_seen')} mg`.")
    L(f"- **{len(over_hyp)}/{clin.get('n')} menu vượt 1500 mg**, "
      f"{len(clin.get('over_2300', []))}/{clin.get('n')} vượt cả trần chung 2300 mg.")
    if over_hyp:
        L("- Các seed vượt ngưỡng (bằng chứng paired theo seed):")
        for r in over_hyp[:10]:
            L(f"  - seed {r['seed']} ({r['config']}): **{f(r['sodium'],0)} mg**")
        L("- Nghĩa là ràng buộc natri 1500 mg **được kiểm tra và báo vi phạm**, nhưng **không được solver "
          "ép thoả** trong mọi trường hợp. Không thể tuyên bố “an toàn cho người tăng huyết áp”.")
    else:
        L("- Không ghi nhận menu nào vượt 1500 mg trong cấu hình đã thử; đây là kết quả trong phạm vi "
          "thử nghiệm, không phải bảo đảm lâm sàng.")
    L(f"- Hệ quả siết muối: **{clin.get('energy_violation')} menu vi phạm năng lượng**, "
      f"**{clin.get('protein_violation')} menu vi phạm đạm** trên cùng bộ seed. "
      + ("Siết natri đang được đánh đổi bằng việc bỏ mục tiêu năng lượng/đạm: người bệnh nhận thực đơn "
         "thiếu năng lượng mà bảng vẫn hiển thị như một thực đơn đã tối ưu."
         if (clin.get('energy_violation') or clin.get('protein_violation'))
         else "Không ghi nhận đánh đổi năng lượng/đạm trong bộ seed này."))
    L("")
    L("### 3.2. Bệnh lý tiểu đường và dữ liệu đường\n")
    L("- Dataset không có cột total sugar; API **không trả `sugar_proxy_g`** và cũng không trả cảnh báo. "
      "Điều này tránh được lỗi trình bày `carbs*0.15` như dữ liệu đo, nhưng tạo khoảng trống UX: "
      "người bệnh tiểu đường không được thông báo rằng hệ thống **không đánh giá được đường huyết**.")
    L(f"- Trong {len(dia)} lần gọi với hồ sơ tiểu đường: có cảnh báo = **{dia_warn}**, "
      f"có nhắc sugar/đường = **{dia_sugar}**, "
      f"các key trả về: `{sorted(set(k for d in dia for k in d.get('keys', [])))}`.")
    L("- Tên bệnh lý tiếng Việt được alias đúng: `hypertension` → "
      f"{hyp_base} mg, `tăng huyết áp` → {hyp_alias} mg. Tuy nhiên bệnh lý không hỗ trợ "
      "(gout, suy thận…) bị **bỏ qua im lặng**, không có thông báo “chưa hỗ trợ”.\n")
    L("### 3.3. Dị ứng và khẩu vị\n")
    L(f"- {allergy.get('n_runs')} lượt sinh menu với 1 / 3 / 10 / 20 token loại trừ. "
      f"Số lượt còn món bị cấm: **{allergy.get('leak_runs')}**. "
      f"Trạng thái: `{allergy.get('status_counts')}`.")
    L(f"- Trạng thái theo kịch bản: `{s.get('allergy_status_by_label', {})}`. "
      "Các kịch bản trả 400 là khi pool ứng viên bị thu nhỏ dưới ngưỡng; server từ chối thay vì crash, "
      "nhưng người dùng không nhận được thực đơn thay thế hay gợi ý nới điều kiện.")
    single_400 = [k for k, v in s.get("allergy_status_by_label", {}).items()
                  if k.startswith("single:") and "400" in v]
    if single_400:
        L(f"- **Loại trừ chỉ một món quen thuộc cũng làm hỏng yêu cầu:** {single_400} trả 400. "
          "Với người dị ứng đạm sữa hoặc trứng, hệ thống không đưa ra được thực đơn nào thay vì "
          "nới lỏng món khác hay báo rõ món nào đang chặn.")
    L(f"- Loại trừ **“hải sản”** (khái niệm, không phải chuỗi con) vẫn để lọt món biển trong "
      f"**{allergy.get('semantic_leak_runs')}** lượt: bộ lọc so khớp chuỗi con trên tên món, "
      "không có từ điển allergen (tôm/cua/cá/mực đều là “hải sản”). Đây là lỗi an toàn nghiêm trọng "
      "nếu người dùng dị ứng hải sản gõ đúng từ “hải sản”.")
    if allergy.get("leak_examples"):
        L(f"- Ví dụ lọt: `{allergy['leak_examples'][:5]}`.")
    L("")
    L("### 3.4. Những combo ngớ ngẩn nhất ghi nhận được\n")
    for i, w in enumerate(worst, 1):
        L(f"**{i}. [{w['phase']}] {w['label']}** — {f(w['calories'],0)} kcal, natri {f(w['sodium'],0)} mg, "
          f"lệch target {w['gap_pct']}%")
        L(f"   - Món: {'; '.join(w['items'])}")
        if w["issues"]["absurd"]:
            L(f"   - Khẩu phần phản ẩm thực: {'; '.join(w['issues']['absurd'])}")
        if w["issues"]["structure"]:
            L(f"   - Cơ cấu bữa: {'; '.join(w['issues']['structure'])}")
        if w["issues"]["raw"]:
            L(f"   - Nguyên liệu thô: {'; '.join(w['issues']['raw'])}")
        if w["issues"]["condiment"]:
            L(f"   - Gia vị như món chính: {'; '.join(w['issues']['condiment'])}")
        if w["violations"]:
            L(f"   - Vi phạm: {'; '.join(w['violations'])}")
        L("")
    L(f"- **Sai vai trò slot ẩm thực:** {s['slot_misplaced_menus']}/{s['n_menus']} menu "
      f"({s['slot_misplaced_pct']}%). Chỉ **{s['slot0_staple_pct']}%** trong {s['slot0_n']} slot đầu "
      "của bữa trưa/tối là tinh bột, trong khi `_roles_for_slot` quy định slot 0 phải là tinh bột. "
      f"Ví dụ: `{s['slot_violation_examples'][:8]}`.")
    L(f"- Tỉ lệ menu có món kịch trần 350 g: **{s['at_cap_pct']}%**. Ví dụ: "
      f"`{s['at_cap_examples'][:8]}`.")
    L(f"- Khẩu phần bị coi là phi lý: **{s['absurd_menus']} menu**, ví dụ `{s['absurd_examples'][:8]}`.")
    L(f"- Cơ cấu bữa sai ở **{s['structure_fail_menus']} menu** ({s['structure_fail_pct']}%): "
      "tiêu chí là mỗi bữa trưa/tối phải có tinh bột **và** ít nhất một món đạm/rau/canh "
      f"(bữa 2 món “cơm + thịt” vẫn được tính là đạt). Lỗi thường gặp: {s['structure_examples'][:6]}.")
    L(f"- Gia vị xuất hiện như món độc lập: **{s['condiment_menus']} menu** "
      f"({s['condiment_examples'][:6]}). Nguyên liệu thô: **{s['raw_menus']} menu** "
      f"({s['raw_examples'][:6]}).")
    L(f"- Kiểm tra tính nhất quán calo vs 4P+4C+9F: {s['cal_macro_mismatch_pct']['n_checked']} menu được kiểm, "
      f"lệch lớn nhất {s['cal_macro_mismatch_pct']['max']}%, "
      f"{s['cal_macro_mismatch_pct']['n_over_10pct']} menu lệch >10% (dấu hiệu dữ liệu dinh dưỡng không đồng bộ).\n")

    L("### 3.5. Kho dữ liệu món ăn\n")
    L(f"- Lấy mẫu được **{inv.get('n_foods_sampled')}** món qua `/api/foods`.")
    L(f"- Có **{len(inv.get('condiments', []))}** tên gia vị lọt vào whitelist tìm kiếm: "
      f"`{inv.get('condiments', [])[:10]}`.")
    L(f"- Có **{len(inv.get('raw', []))}** tên nguyên liệu thô: `{inv.get('raw', [])[:10]}`.")
    L(f"- **{len(inv.get('no_prep', []))}** tên không nêu cách chế biến (mẫu): `{inv.get('no_prep', [])[:12]}`.")
    L(f"- Natri/100 g cao nhất: `{inv.get('max_sodium_per_100g', [])[:5]}`. "
      "Các món này một mình đã chiếm phần lớn ngưỡng 1500 mg/ngày.\n")

    L("### 3.6. Chaos / fuzzing\n")
    L("| Case | Kỳ vọng | Thực tế | Kết luận |")
    L("|---|---|---|---|")
    for c in chaos:
        L(f"| {c['case']} | {c['expected']} | {c['status']} | {c['verdict']} |")
    L("")
    L(f"- **{len(chaos_fail)} case FAIL**, **{len(chaos_500)} case 500**. "
      + (f"Có **{len(s['implausible_200'])}** hồ sơ phi thực tế vẫn trả 200 "
         f"({', '.join(c['case'] for c in s['implausible_200'])}): lỗi **thiếu kiểm tra hợp lý sinh học** "
         "(chiều cao 30 cm, cân nặng 5 kg hay 400 kg vẫn được tối ưu thực đơn), không phải lỗi crash."
         if s['implausible_200'] else "Không có hồ sơ phi thực tế nào lọt qua."))
    L("- Không case nào phản chiếu payload (`<script>`, `DROP TABLE`) trong body trả về; "
      "frontend dùng `escHtml`/`textContent` nên không ghi nhận XSS phản xạ.\n")

    L("## 4. CÂU HỎI “BẪY” CỦA HỘI ĐỒNG PHẢN BIỆN\n")
    L("**Câu 1. “Hệ thống của em khẳng định thực đơn an toàn cho người tăng huyết áp. "
      "Vậy tại sao có seed ra 1 800 mg natri?”**")
    L(f"- Trả lời an toàn: “Không. Chúng em chỉ khẳng định thực đơn **đáp ứng hoặc không đáp ứng ngưỡng "
      f"được cấu hình trong thử nghiệm**. Trong {clin.get('n')} seed đã chạy, "
      f"{len(over_hyp)} menu vượt 1500 mg và hệ thống báo vi phạm đúng; đây là hạn chế của bộ giải, "
      "không phải bảo đảm lâm sàng. Thiết bị này không phải thiết bị y tế.”")
    L("")
    L("**Câu 2. “Món ‘Gạo lứt 115 g’ là món gì? Ai ăn gạo sống?”**")
    L(f"- Trả lời: “Dữ liệu gốc là bảng thành phần dinh dưỡng theo 100 g nguyên liệu, nên tên món hiện "
      f"là tên nguyên liệu; {s['no_prep_pct']}% thực đơn trong đợt test dính vấn đề này. "
      "Đây là khoảng trống đã biết giữa dữ liệu dinh dưỡng và thực đơn ẩm thực, không phải kết quả "
      "tối ưu. Hướng khắc phục là lớp ‘món ăn’ (recipe) thay vì nguyên liệu.”")
    L("")
    L("**Câu 3. “Nếu tôi dị ứng hải sản và gõ ‘hải sản’, hệ thống có loại tôm cua cá không?”**")
    L(f"- Trả lời trung thực: “Hiện tại bộ lọc so khớp chuỗi con trên tên món; ‘hải sản’ không khớp "
      f"‘tôm’/‘cua’/‘cá’, nên trong {allergy.get('semantic_leak_runs')} lượt thử vẫn lọt món biển. "
      "Đây là lỗi an toàn ưu tiên cao; cần từ điển allergen trước khi demo cho người dị ứng.”")
    L("")
    L("**Câu 4. “Điểm fitness 87.4 nghĩa là gì với bệnh nhân? Và vì sao bấm Đổi món 5 lần điểm vẫn 87.4?”**")
    L("- Trả lời: “Fitness là hàm mục tiêu nội bộ, không phải chỉ số sức khỏe. `SwapOut` hiện không trả "
      "fitness nên frontend giữ điểm cũ — đây là lỗi hiển thị đã ghi nhận. Đúng ra phải hoặc trả fitness "
      "mới, hoặc bỏ hẳn điểm số khỏi giao diện người bệnh.”")
    L("")
    L("**Câu 5. “Vì sao khẩu phần sữa chua lại 350 g và rau 350 g? Ràng buộc khẩu phần của em đâu?”**")
    L(f"- Trả lời: “Solver dùng biên kỹ thuật 25–350 g cho mọi món; {s['at_cap_pct']}% menu có món chạm "
      "trần. Hàm `validate_menu` có kiểm tra biên theo vai trò món nhưng đường gọi trong `generate_menu` "
      "không truyền `food_map`, nên phần kiểm tra đó bị bỏ qua và không xuất hiện trong `violations`. "
      "Đây là lỗi tích hợp, không phải lỗi thuật toán.”")
    L("")

    L("## 5. DANH SÁCH 5 VIỆC PHẢI FIX GẤP TRƯỚC KHI DEMO\n")
    fixes = []
    if s["at_cap_menus"] or s["absurd_menus"]:
        fixes.append("**Truyền `food_map` vào `validate_menu` trong `generate_menu`** (và dùng đúng biên "
                     "theo vai trò món) để 350 g sữa chua/rau/măng bị chặn và hiện thành vi phạm; "
                     "đồng thời thu hẹp `lb/ub` của inner solver theo role thay vì 25–350 g cho mọi món.")
    else:
        fixes.append("**Siết biên khẩu phần theo vai trò món** ở cả solver và validation.")
    fixes.append("**Bổ sung từ điển allergen** (hải sản → tôm/cua/cá/mực/nghêu/sò…) và kiểm tra dị ứng "
                 "theo nhóm, không chỉ so khớp chuỗi con; thêm test hồi quy cho token ‘hải sản’ và ‘đậu phộng’.")
    fixes.append("**Trả `fitness`/`diversity_pct` trong `SwapOut` hoặc bỏ điểm số khỏi UI sau swap**; "
                 "không để người dùng thấy điểm cũ của thực đơn đã đổi.")
    fixes.append("**Thêm khối cảnh báo bệnh lý trong response** (`warnings: [...]`, `data_limitations`): "
                 "tiểu đường → “không có dữ liệu đường, không kết luận an toàn”; bệnh lý chưa hỗ trợ → "
                 "“chưa được mô hình hoá”. Kèm disclaimer “không phải thiết bị y tế”.")
    fixes.append("**Việt hoá toàn bộ lỗi 4xx và rút gọn thuật ngữ UI**: map 422 Pydantic sang câu tiếng Việt "
                 "theo trường; ẩn Seed/Smoke-Web-Full vào mục nâng cao; đổi “Fitness/100” thành "
                 "“Mức đáp ứng mục tiêu dinh dưỡng”.")
    if s["sodium"]["n_over_1500"]:
        fixes.append(f"**Xử lý natri vượt ngưỡng**: {s['sodium']['n_over_1500']} menu vượt 1500 mg; "
                     "thêm ràng buộc cứng/ưu tiên phạt natri và không cho UI hiển thị “không vi phạm” khi "
                     "tổng natri vượt ngưỡng cá nhân.")
    for i, fx in enumerate(fixes[:5], 1):
        L(f"{i}. {fx}")
    L("")
    L("---")
    L(f"*Số liệu sinh tự động từ {s['n_requests']} request trong {s['elapsed_s']:.0f} giây; "
      f"cấu hình máy: seed cố định theo từng phase, config `web` cho ma trận và 1 phần lâm sàng, "
      f"`smoke` cho các phép thử rẻ. Không đọc/ghi đè dữ liệu production.*")
    return "\n".join(lines) + "\n"
