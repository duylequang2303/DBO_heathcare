"""Week 11 two-tier shared-budget DBO/IDBO smoke benchmark.

Requires explicit evaluation budget; does not silently select a scientific budget.
Saves one JSON record per completed run atomically and supports --resume.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.experiment_dbo_idbo_ablation import get_profile_p1
from src.algorithms.menu_objective import decode_result
from src.algorithms.two_tier_solver import TwoTierConfig, two_tier_optimize
from src.models.constraints import validate_menu
from src.utils.data_loader import build_food_map, load_food_db
from src.utils.nutrition import daily_all_targets

FIELDS = [
    'algorithm', 'seed', 'outer_diversity_threshold', 'inner_diversity_threshold',
    'best_fitness', 'final_fitness', 'runtime_seconds', 'function_evaluations',
    'outer_evals', 'inner_evals_total', 'outer_min_diversity',
    'outer_mean_diversity', 'outer_max_stagnation', 'outer_collapse_events',
    'outer_perturbations', 'outer_restarts', 'inner_perturbations_total',
    'inner_restarts_total', 'final_inner_perturbations', 'final_inner_restarts',
    'final_inner_fitness', 'final_inner_runtime_s', 'inner_runtime_total_s',
    'inner_diversity_min_observed', 'inner_diversity_mean_observed',
    'number_of_violations', 'git_commit', 'config_hash', 'max_evaluations',
    'budget_remaining', 'budget_exceeded',
]


def canonical_hash(config: dict) -> str:
    return hashlib.sha256(json.dumps(config, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp')
    with temp.open('w', encoding='utf-8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)


def git_commit() -> str:
    try:
        return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, stderr=subprocess.DEVNULL, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return 'UNKNOWN_NO_GIT'


def execute(algo: str, seed: int, cfg: dict, commit: str, config_hash: str) -> dict:
    food_map = build_food_map(load_food_db())
    profile = get_profile_p1()
    targets = daily_all_targets(profile)
    kwargs = dict(cfg)
    kwargs.pop('evaluation_seeds', None)
    kwargs.pop('profile', None)
    kwargs.pop('experiment_version', None)
    kwargs.pop('algorithms', None)
    kwargs['outer_algo'] = algo
    kwargs['inner_algo'] = algo
    kwargs['seed'] = seed
    model_cfg = TwoTierConfig(**kwargs)
    start = time.perf_counter()
    result = two_tier_optimize(profile, food_map, targets, model_cfg)
    runtime = time.perf_counter() - start
    menu = decode_result(result.best_food_ids, result.best_portions_g, food_map, profile.meal_counts)
    violations = validate_menu(menu, profile, targets)
    evaluations = int(result.function_evaluations)
    budget = int(cfg['max_evaluations'])
    if evaluations > budget:
        raise RuntimeError(f'BUDGET EXCEEDED: {evaluations} > {budget} ({algo}, seed={seed})')
    diversity = result.inner_diversity_history
    return {
        'algorithm': algo, 'seed': seed,
        'outer_diversity_threshold': model_cfg.outer_diversity_threshold,
        'inner_diversity_threshold': model_cfg.inner_diversity_threshold,
        'best_fitness': float(result.best_fitness),
        'final_fitness': float(result.history[-1]) if result.history else float(result.best_fitness),
        'runtime_seconds': runtime,
        'function_evaluations': evaluations,
        'outer_evals': result.outer_evals,
        'inner_evals_total': result.inner_evals_total,
        'outer_min_diversity': result.outer_min_diversity,
        'outer_mean_diversity': result.outer_mean_diversity,
        'outer_max_stagnation': result.outer_max_stagnation,
        'outer_collapse_events': result.outer_collapse_events,
        'outer_perturbations': result.outer_perturbations,
        'outer_restarts': result.outer_restarts,
        'inner_perturbations_total': result.inner_perturbations_total,
        'inner_restarts_total': result.inner_restarts_total,
        'final_inner_perturbations': result.final_inner_perturbations,
        'final_inner_restarts': result.final_inner_restarts,
        'final_inner_fitness': result.final_inner_fitness,
        'final_inner_runtime_s': result.final_inner_runtime_s,
        'inner_runtime_total_s': result.inner_runtime_total_s,
        'inner_diversity_min_observed': min(diversity) if diversity else None,
        'inner_diversity_mean_observed': sum(diversity) / len(diversity) if diversity else None,
        'number_of_violations': len(violations),
        'git_commit': commit, 'config_hash': config_hash,
        'max_evaluations': budget, 'budget_remaining': budget - evaluations,
        'budget_exceeded': False,
    }


def export_csv(out: Path, cfg_hash: str, commit: str) -> None:
    records = []
    for file in sorted((out / 'runs').glob('*.json')):
        record = json.loads(file.read_text(encoding='utf-8'))
        if record.get('config_hash') != cfg_hash or record.get('git_commit') != commit:
            raise RuntimeError(f'Run metadata mismatch: {file}')
        records.append(record)
    temp = out / 'paired_runs.csv.tmp'
    with temp.open('w', newline='', encoding='utf-8-sig') as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(records)
    os.replace(temp, out / 'paired_runs.csv')


def run(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Week 11 shared-budget paired DBO/IDBO smoke benchmark')
    parser.add_argument('--smoke', action='store_true', help='Run calibration seeds 8001 and 8002')
    parser.add_argument('--seeds', type=int, nargs='+', help='Explicit seeds; independent seeds require --allow-independent')
    parser.add_argument('--allow-independent', action='store_true', help='Confirm all Week 11 full-benchmark gates were reviewed')
    parser.add_argument('--max-evaluations', type=int, required=True, help='Shared maximum objective evaluations for BOTH algorithms; no default')
    parser.add_argument('--outer-n-agents', type=int, default=10)
    parser.add_argument('--inner-n-agents', type=int, default=10)
    parser.add_argument('--outer-max-iter', type=int, default=25)
    parser.add_argument('--inner-max-iter', type=int, default=25)
    parser.add_argument('--inner-diversity-threshold', type=float, default=None, help='Only set if calibrated; default None')
    parser.add_argument('--output-dir', type=Path, default=Path('results/week11_budget_smoke'))
    parser.add_argument('--resume', action='store_true', help='Continue incomplete runs with identical locked config')
    args = parser.parse_args(argv)
    if args.smoke and args.seeds:
        parser.error('Use either --smoke or --seeds, not both')
    seeds = [8001, 8002] if args.smoke else args.seeds
    if not seeds:
        parser.error('Specify --smoke or --seeds')
    if len(set(seeds)) != len(seeds):
        parser.error('Duplicate seeds are not allowed')
    if any(s not in (8001, 8002) for s in seeds) and not args.allow_independent:
        parser.error('Independent evaluation requires --allow-independent after checking all eight gates in the Week 11 plan')
    if args.max_evaluations <= 0:
        parser.error('--max-evaluations must be positive')
    if args.inner_diversity_threshold is not None and not 0 <= args.inner_diversity_threshold <= 1:
        parser.error('inner diversity threshold must be in [0, 1]')
    cfg = {
        'experiment_version': 1, 'profile': 'P1', 'algorithms': ['dbo', 'idbo'],
        'evaluation_seeds': seeds, 'max_evaluations': args.max_evaluations,
        'outer_n_agents': args.outer_n_agents, 'inner_n_agents': args.inner_n_agents,
        'outer_max_iter': args.outer_max_iter, 'inner_max_iter': args.inner_max_iter,
        'outer_diversity_threshold': 0.28,
        'inner_diversity_threshold': args.inner_diversity_threshold,
        'stagnation_window': 25,
    }
    minimum = args.outer_n_agents * (args.inner_n_agents + 1) + args.inner_n_agents
    if args.max_evaluations < minimum:
        parser.error(f'--max-evaluations must be >= {minimum} for this population configuration')
    out = args.output_dir.resolve()
    lock_path = out / 'config_locked.json'
    hash_value = canonical_hash(cfg)
    commit = git_commit()
    lock = {'config': cfg, 'config_hash': hash_value, 'git_commit': commit}
    if lock_path.exists():
        existing = json.loads(lock_path.read_text(encoding='utf-8'))
        if existing != lock:
            parser.error('Existing config_locked.json differs (configuration or Git commit). Use a NEW --output-dir')
        if not args.resume:
            parser.error('Output already locked. Use --resume to continue, or a NEW --output-dir')
    else:
        if args.resume and out.exists() and any(out.iterdir()):
            parser.error('Cannot resume existing output without config_locked.json')
        if out.exists() and any(out.iterdir()):
            parser.error('Output directory is not empty; choose a new directory')
        atomic_json(lock_path, lock)
    if commit == 'UNKNOWN_NO_GIT':
        print('[WARNING] No Git commit detected. Results are traceable by config_hash but cannot satisfy the Git-commit gate.')
    print(f'[CONFIG] hash={hash_value} | commit={commit} | budget={args.max_evaluations}')
    for seed in seeds:
        for algo in ('dbo', 'idbo'):
            path = out / 'runs' / f'{seed}_{algo}.json'
            if path.exists():
                record = json.loads(path.read_text(encoding='utf-8'))
                if record.get('config_hash') != hash_value or record.get('git_commit') != commit:
                    raise RuntimeError(f'Invalid resume metadata in {path}')
                print(f'[SKIP] {algo.upper()} seed={seed}: already saved')
                continue
            print(f'[RUN] {algo.upper()} seed={seed}', flush=True)
            record = execute(algo, seed, cfg, commit, hash_value)
            atomic_json(path, record)
            export_csv(out, hash_value, commit)
            print(f"[SAVED] {path.name}: fitness={record['best_fitness']:.4f}, evals={record['function_evaluations']}/{args.max_evaluations}, time={record['runtime_seconds']:.1f}s", flush=True)
    export_csv(out, hash_value, commit)
    print(f'[DONE] {out / "paired_runs.csv"}')
    print('[NOTE] A hard shared budget is an upper bound; actual DBO/IDBO evaluation counts may differ. Compare observed counts.')
    return 0


if __name__ == '__main__':
    raise SystemExit(run())
