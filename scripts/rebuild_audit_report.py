#!/usr/bin/env python3
"""Dựng lại summary.json + REPORT.md từ raw_requests/raw_menus + summary cũ.

Dùng khi cần sửa tiêu chí phân tích mà không phải gõ lại 400 request vào server:
    venv/bin/python scripts/rebuild_audit_report.py experiments/audit_live_web_YYYYMMDD_HHMM
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from auditor_grill_live_web import DAIRY_RE, Auditor, MenuRec, Req  # noqa: E402
from build_audit_report import build_report  # noqa: E402


def rebuild(out: Path) -> dict:
    old = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    a = Auditor.__new__(Auditor)
    a.out = out
    a.reqs = [Req(**json.loads(line)) for line in (out / "raw_requests.jsonl").read_text(encoding="utf-8").splitlines()]
    a.menus = [MenuRec(**json.loads(line)) for line in (out / "raw_menus.jsonl").read_text(encoding="utf-8").splitlines()]
    a.elapsed = lambda: old["elapsed_s"]
    a.skipped = old["skipped"]
    a.chaos = old["chaos"]
    a.concurrency = old["concurrency"]
    a.determinism = old["determinism"]
    a.inventory = {**old["inventory"]}
    # Cùng quy tắc với analyze_menu: bỏ đồ uống sữa và giá đỗ khỏi nhóm 'nguyên liệu thô'.
    a.inventory["raw"] = [n for n in old["inventory"].get("raw", [])
                          if not DAIRY_RE.search(n) and not n.lower().startswith("giá")]
    a.clinical = old["clinical"]
    runs = []
    for label, counts in old.get("allergy_status_by_label", {}).items():
        for status, n in counts.items():
            for _ in range(n):
                runs.append({"label": label, "status": int(status), "tokens": [], "leaks": [],
                             "seafood_leak": False})
    a.allergy = {**{k: v for k, v in old["allergy"].items()}, "runs": runs}

    # Dựng lại chuỗi swap từ chính raw menus (giá trị thật, không bịa).
    chains: dict[str, dict] = {}
    for m in a.menus:
        if m.phase != "swap":
            continue
        if m.label.startswith("gen_"):
            name = m.label[4:]
            chain = chains.setdefault(name, {"label": name, "steps": []})
            idx = 0
            step = "gen"
        elif ":" in m.label:
            name, tail = m.label.split(":", 1)
            chain = chains.setdefault(name, {"label": name, "steps": []})
            idx = len(chain["steps"])
            step = tail.split(":")[0] if tail.startswith("chain") else f"seq{idx}"
        else:
            continue
        portions = [float(i["portion_g"]) for i in m.items]
        chain["steps"].append({
            "step": step, "slot": m.label.rsplit(":", 1)[-1], "status": 200,
            "gap": round(Auditor.gap_pct(m.totals, m.targets), 1),
            "calories": m.totals.get("calories"),
            "violations": len(m.violations),
            "max_portion": round(max(portions), 1) if portions else 0,
            "n_at_cap": sum(1 for p in portions if p >= 349.5),
        })
    for chain in chains.values():
        gapped = [s for s in chain["steps"] if "gap" in s]
        if gapped:
            chain["gap_start"] = gapped[0]["gap"]
            chain["gap_end"] = gapped[-1]["gap"]
    a.swap_chains = list(chains.values())

    cover = old["matrix"]
    expanded = {}
    for key in ("age", "bmi", "activity", "meal"):
        expanded[key] = [k for k, n in cover[key].items() for _ in range(n)]
    n = len(expanded["age"])
    statuses = [200] * cover["ok"] + [400] * cover["err"]
    a.matrix_meta = [
        {
            "age_bucket": expanded["age"][i] if i < len(expanded["age"]) else None,
            "bmi_bucket": expanded["bmi"][i] if i < len(expanded["bmi"]) else None,
            "activity": expanded["activity"][i] if i < len(expanded["activity"]) else None,
            "meal_structure": expanded["meal"][i] if i < len(expanded["meal"]) else None,
            "name": f"rebuilt-{i}", "status": statuses[i] if i < len(statuses) else 200,
        }
        for i in range(n)
    ]
    return build_report(a)


if __name__ == "__main__":
    target = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    summary = rebuild(target)
    print(json.dumps({k: summary[k] for k in (
        "n_requests", "ok_rate_pct", "n_5xx", "n_menus", "structure_fail_menus",
        "structure_fail_pct", "slot_misplaced_menus", "slot0_staple_pct")}, ensure_ascii=False))
