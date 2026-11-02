#!/usr/bin/env python3
"""A/B impact check: bounds vai trò món cho tầng inner (Tuần 11).

Mục đích: đo ảnh hưởng của việc thay khoảng vô hướng [25, 350] bằng
``ROLE_PORTION_BOUNDS`` trong generate + swap, trên N seed cố định.

Với mỗi seed, kiểm tra thực đơn SAU làm tròn 5g:
  - mọi khẩu phần nằm trong bounds vai trò của món đó;
  - validator (food_map=...) không báo "portion ... out of range";
  - không có nutrient âm / NaN / vô hạn.

Chạy:
    venv/bin/python scripts/check_role_bounds_impact.py --seeds 30 \\
        --config smoke --out experiments/week11_role_bounds
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.api.schemas import GenerateIn, ProfileIn  # noqa: E402
from app.api.services import (  # noqa: E402
    PRESET_PROFILES,
    generate_menu,
    get_food_map,
)
from src.models.dish_category import (  # noqa: E402
    classify_dish_role,
    get_role_portion_bounds,
)


def _role_high(food_id: str, food_map: dict) -> tuple[float, float]:
    row = food_map[food_id]
    role = classify_dish_role(
        str(row.get("food_name", "")),
        str(row.get("category", "")),
        str(row.get("source", "")),
    )
    return get_role_portion_bounds(role)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--config", default="smoke", choices=["smoke", "web", "full"])
    parser.add_argument("--preset", default="p1", choices=sorted(PRESET_PROFILES))
    parser.add_argument("--out", default="experiments/week11_role_bounds")
    args = parser.parse_args()

    food_map = get_food_map()
    out_dir = ROOT / args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    for i in range(args.seeds):
        seed = 8000 + i
        req = GenerateIn(
            profile=ProfileIn(**PRESET_PROFILES[args.preset]),
            seed=seed,
            config=args.config,
        )
        menu = generate_menu(req)

        out_of_bounds = 0
        max_over = 0.0
        for item in menu.items:
            low, high = _role_high(item.food_id, food_map)
            p = item.portion_g_rounded
            if not (low <= p <= high):
                out_of_bounds += 1
                max_over = max(max_over, max(low - p, p - high))

        out_of_range_msgs = [v for v in menu.violations if "out of range" in v]
        bad_totals = [
            key
            for key, value in menu.totals.items()
            if not math.isfinite(value) or value < 0
        ]

        rows.append(
            {
                "seed": seed,
                "n_items": len(menu.items),
                "fitness": menu.fitness,
                "n_out_of_bounds": out_of_bounds,
                "max_overshoot_g": round(max_over, 2),
                "n_violations": len(menu.violations),
                "n_out_of_range_msgs": len(out_of_range_msgs),
                "bad_totals": ";".join(bad_totals),
                "max_portion_g": max(item.portion_g_rounded for item in menu.items),
            }
        )

    summary = {
        "config": args.config,
        "preset": args.preset,
        "n_seeds": args.seeds,
        "seeds": [row["seed"] for row in rows],
        "n_menu_items_checked": sum(row["n_items"] for row in rows),
        "n_out_of_bounds": sum(row["n_out_of_bounds"] for row in rows),
        "n_out_of_range_violations": sum(row["n_out_of_range_msgs"] for row in rows),
        "max_overshoot_g": max(row["max_overshoot_g"] for row in rows),
        "n_bad_totals": sum(1 for row in rows if row["bad_totals"]),
        "mean_fitness": round(sum(row["fitness"] for row in rows) / len(rows), 2),
    }

    with (out_dir / "summary.json").open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)

    with (out_dir / "runs.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["n_out_of_bounds"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
