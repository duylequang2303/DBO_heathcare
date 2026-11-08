#!/usr/bin/env python3
"""Đối chiếu từng khẳng định trong REPORT.md với summary.json.

Cách dùng:
    venv/bin/python scripts/check_audit_report.py experiments/audit_live_web_post_fix

Kiểm tra 3 thứ:
1. Mỗi dòng trong bảng §7 (mã — đường dẫn — giá trị) phải khớp `summary.json`.
2. Mọi mã `[Cxx]` xuất hiện trong phần diễn giải phải có dòng tương ứng ở §7
   (không có khẳng định nào "mồ côi").
3. Không còn câu khẳng định cũ đã sai (blacklist văn bản hard-code cũ).

Exit code: 0 = PASS, 1 = có lỗi, 2 = tài liệu không do generator mới sinh.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Những câu khẳng định của bản báo cáo cũ đã sai với code hiện tại.
# Nếu chúng xuất hiện lại trong REPORT.md thì generator đang hard-code.
STALE_PHRASES = [
    "không trả `fitness`, `diversity_pct`, `runtime_s`",
    "Frontend giữ lại fitness cũ",
    "25–350 g",
    "so khớp chuỗi con trên tên món",
    "không tránh được lỗi trình bày",
    "`SwapOut` hiện không trả",
    "Solver dùng biên kỹ thuật",
    "không** chứa bất kỳ trường cảnh báo",
]


def _norm(x) -> str:
    s = str(x).strip().strip("`").replace(",", "")
    return s.lower() if s.lower() in ("true", "false") else s


def _resolve(summary: dict, path: str):
    cur = summary
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise KeyError(path)
        cur = cur[part]
    return cur


def _values_equal(reported: str, actual) -> bool:
    a, b = _norm(reported), _norm(actual)
    if a == b:
        return True
    try:
        return abs(float(a) - float(b)) <= 0.05
    except ValueError:
        return False


def check(exp_dir: Path) -> int:
    summary = json.loads((exp_dir / "summary.json").read_text(encoding="utf-8"))
    report = (exp_dir / "REPORT.md").read_text(encoding="utf-8")

    block = re.search(r"## 7\..*?```text\n(.*?)```", report, re.S)
    if not block:
        print(f"[SKIP] {exp_dir.name}: REPORT.md không có bảng §7 → báo cáo historical "
              "(không sinh bằng build_audit_report.py hiện tại). Không ghi đè.")
        return 2

    rows = [ln for ln in block.group(1).strip().splitlines() if ln.strip()]
    errors: list[str] = []
    checked = 0

    for line in rows:
        parts = line.split("\t")
        if len(parts) != 3:
            errors.append(f"dòng §7 sai định dạng: {line!r}")
            continue
        cid, path, reported = parts
        checked += 1
        try:
            actual = _resolve(summary, path)
        except KeyError:
            errors.append(f"{cid}: đường dẫn `{path}` không tồn tại trong summary.json")
            continue
        if not _values_equal(reported, actual):
            errors.append(f"{cid}: báo cáo ghi {reported!r} nhưng summary.json[{path}] = {actual!r}")

    # §1: con số hiển thị phải trùng giá trị đã ghi ở §7 (bắt drift khi sửa tay §1).
    sec1 = re.search(r"## 1\..*?(?=\n## 2\.)", report, re.S)
    if sec1:
        claim_values = {ln.split("\t")[0]: ln.split("\t")[2]
                        for ln in rows if "\t" in ln}
        for line in sec1.group(0).splitlines():
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 3:
                continue
            codes = re.findall(r".?C\d+b?.?", cells[-1])
            codes = [c.strip("[]|") for c in codes]
            codes = [c for c in codes if re.fullmatch(r"C\d+b?", c)]
            if not codes:
                continue
            shown = [_norm(x) for x in re.findall(r"-?\d[\d,]*\.?\d*", cells[1])]
            for cid in codes:
                if cid not in claim_values:
                    errors.append(f"{cid}: xuất hiện ở §1 nhưng không có dòng §7")
                    continue
                expected = _norm(claim_values[cid])
                if expected in ("true", "false"):
                    ok = expected in cells[1].lower()
                else:
                    ok = any(_values_equal(expected, x) for x in shown)
                if not ok:
                    errors.append(f"{cid}: §1 in khác §7 "
                                  f"(ô §1 = {cells[1]!r}, §7 = {claim_values[cid]!r})")

    # khẳng định mồ côi: [Cxx] trong phần diễn giải nhưng không có dòng §7.
    # Chấp nhận cả dạng `[C01]` trong câu và dạng cột riêng `| C01 |` ở bảng §1.
    body = report[:block.start()] + report[block.end():]
    cited = {m for m in re.findall(r"(?<![A-Za-z0-9])(C\d+b?)(?![0-9])", body)}
    listed = {ln.split("\t")[0] for ln in rows if "\t" in ln}
    for cid in sorted(cited - listed):
        errors.append(f"{cid}: được trích trong báo cáo nhưng thiếu dòng đối chiếu ở §7")
    for cid in sorted(listed - cited):
        errors.append(f"{cid}: có dòng §7 nhưng không được trích ở phần diễn giải")

    for phrase in STALE_PHRASES:
        if phrase in report:
            errors.append(f"còn câu khẳng định cũ (đã sai với code hiện tại): {phrase!r}")

    if errors:
        print(f"[FAIL] {exp_dir.name}: {len(errors)} lỗi")
        for e in errors:
            print("  -", e)
        return 1
    print(f"[PASS] {exp_dir.name}: {checked} khẳng định khớp summary.json, "
          f"{len(cited)} mã được đối chiếu, 0 câu cũ.")
    return 0


if __name__ == "__main__":
    target = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    sys.exit(check(target))
