"""Week 11 Cuong P0 verification, independent from solver implementation.

Run from repository root:
    python scripts/verify_week11_cuong_p0.py --pool-only
    python scripts/verify_week11_cuong_p0.py --seeds 20

Writes auditable CSV/JSON under experiments/week11_cuong_p0/. Does not edit datasets.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import traceback
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.api.schemas import GenerateIn, ProfileIn
from app.api.services import PRESET_PROFILES, build_profile, generate_menu, get_food_map
from src.models.food_selector import build_meal_pools


def csv_write(path: Path, rows: list[dict], fieldnames: list[str], append: bool = False) -> None:
    mode = 'a' if append else 'w'
    with path.open(mode, newline='', encoding='utf-8-sig' if not append else 'utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        if not append or path.stat().st_size == 0:
            w.writeheader()
        w.writerows(rows)


def main() -> int:
    p = argparse.ArgumentParser(description='Verify Cuong Week11 whitelist and 20-seed x 3-profile demo.')
    p.add_argument('--seeds', type=int, default=20, help='Number of seeds per profile (default: 20)')
    p.add_argument('--seed-start', type=int, default=9001)
    p.add_argument('--config', choices=['smoke', 'web', 'full'], default='smoke')
    p.add_argument('--pool-only', action='store_true', help='Check whitelist and pools without optimizer runs')
    p.add_argument('--output', default='experiments/week11_cuong_p0')
    args = p.parse_args()
    if not 1 <= args.seeds <= 10000 or args.seed_start < 0 or args.seed_start + args.seeds - 1 > 2147483647:
        p.error('Require 1<=seeds<=10000, seed-start>=0, and last seed<=2147483647')

    out = ROOT / args.output
    out.mkdir(parents=True, exist_ok=True)
    foods = get_food_map()
    whitelist_rows = []
    for fid, item in sorted(foods.items()):
        name = str(item.get('food_name', ''))
        na = float(item.get('sodium_mg', 0))
        whitelist_rows.append(dict(food_id=fid, name=name, sodium_mg=na,
                                   vn_id=fid.startswith('VN_'), sodium_positive=na > 0,
                                   meal_type=str(item.get('meal_type', ''))))
    csv_write(out / 'whitelist_audit.csv', whitelist_rows,
              ['food_id', 'name', 'sodium_mg', 'vn_id', 'sodium_positive', 'meal_type'])
    whitelist_valid = 150 <= len(foods) <= 300 and all(r['vn_id'] and r['sodium_positive'] for r in whitelist_rows)
    pool_rows = []
    min_pool = None
    for key, profile_data in PRESET_PROFILES.items():
        profile = build_profile(ProfileIn(**profile_data))
        pools = build_meal_pools(foods, profile.meal_counts, profile)
        for slot, candidates in pools.items():
            size = len(candidates)
            min_pool = size if min_pool is None else min(min_pool, size)
            pool_rows.append({'profile':key, 'slot':slot, 'pool_size':size, 'pass_min20':size >= 20})
    csv_write(out / 'pool_audit.csv', pool_rows, ['profile', 'slot', 'pool_size', 'pass_min20'])
    pool_valid = bool(pool_rows) and all(r['pass_min20'] for r in pool_rows)
    print(f'[POOL] whitelist={len(foods)}; min_slot_pool={min_pool}; whitelist_valid={whitelist_valid}; pools_valid={pool_valid}', flush=True)

    run_rows = []
    chosen_rows = []
    if not args.pool_only:
        run_fields = ['profile','seed','status','elapsed_s','item_count','invalid_id_count',
                      'sodium_zero_or_missing_count','display_name_mismatch_count','fitness','violations','error']
        chosen_fields = ['profile','seed','slot','food_id','name','source_sodium_mg','portion_g',
                         'invalid_id','sodium_zero_or_missing','display_name_mismatch']
        csv_write(out / 'runs.csv', [], run_fields)
        csv_write(out / 'selected_foods.csv', [], chosen_fields)
        for key, profile_data in PRESET_PROFILES.items():
            for seed in range(args.seed_start, args.seed_start + args.seeds):
                print(f'[RUN] {key} seed={seed}', flush=True)
                started = time.perf_counter()
                status = 'pass'
                error = ''
                fitness = ''
                violations = ''
                item_count = 0
                bad_id_count = 0
                zero_na_count = 0
                wrong_display_count = 0
                chosen_start = len(chosen_rows)
                try:
                    req = GenerateIn(profile=ProfileIn(**profile_data), seed=seed, config=args.config)
                    result = generate_menu(req)
                    fitness = result.fitness
                    violations = json.dumps(result.violations, ensure_ascii=False)
                    item_count = len(result.items)
                    for item in result.items:
                        food = foods.get(item.food_id)
                        bad_id = food is None or not item.food_id.startswith('VN_')
                        zero_na = food is None or float(food.get('sodium_mg', 0)) <= 0
                        name_mismatch = food is None or item.name != str(food.get('food_name', ''))
                        bad_id_count += int(bad_id)
                        zero_na_count += int(zero_na)
                        wrong_display_count += int(name_mismatch)
                        chosen_rows.append(dict(profile=key, seed=seed, slot=item.slot,
                                                food_id=item.food_id, name=item.name,
                                                source_sodium_mg=food.get('sodium_mg', '') if food else '',
                                                portion_g=item.portion_g,
                                                invalid_id=bad_id, sodium_zero_or_missing=zero_na,
                                                display_name_mismatch=name_mismatch))
                    if bad_id_count or zero_na_count or wrong_display_count or item_count != sum(profile_data['meal_counts'].values()):
                        status = 'fail'
                except Exception as exc:
                    status = 'error'
                    error = f'{type(exc).__name__}: {exc}'
                    print(f'[ERROR] {key} seed={seed}: {error}', flush=True)
                    traceback.print_exc()
                run_rows.append(dict(profile=key, seed=seed, status=status,
                                     elapsed_s=round(time.perf_counter()-started, 3),
                                     item_count=item_count, invalid_id_count=bad_id_count,
                                     sodium_zero_or_missing_count=zero_na_count,
                                     display_name_mismatch_count=wrong_display_count,
                                     fitness=fitness, violations=violations, error=error))
                # Append only this run, not the entire history; restart produces fresh files.
                csv_write(out / 'runs.csv', [run_rows[-1]], run_fields, append=True)
                csv_write(out / 'selected_foods.csv', chosen_rows[chosen_start:], chosen_fields, append=True)
    status_counts = dict(Counter(row['status'] for row in run_rows))
    all_pass = whitelist_valid and pool_valid and (args.pool_only or (len(run_rows) == 3*args.seeds and status_counts.get('pass', 0) == len(run_rows)))
    summary = dict(whitelist_count=len(foods), whitelist_valid=whitelist_valid,
                   min_slot_pool=min_pool, pools_valid=pool_valid, profiles=list(PRESET_PROFILES),
                   seeds_per_profile=0 if args.pool_only else args.seeds,
                   expected_runs=0 if args.pool_only else 3*args.seeds,
                   actual_runs=len(run_rows), run_status=status_counts, config=args.config,
                   technical_checks_pass=all_pass,
                   disclaimer='Positive sodium and a technical pass do NOT imply clinical safety or a realistic meal. Manually review selected_foods.csv and violations.')
    (out / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    print('[SAVED]', out, flush=True)
    print(json.dumps(summary, indent=2, ensure_ascii=False), flush=True)
    return 0 if all_pass else 1


if __name__ == '__main__':
    raise SystemExit(main())
