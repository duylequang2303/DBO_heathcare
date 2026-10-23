import json
from pathlib import Path

import pytest

from scripts import experiment_week11_budget as runner


def test_hash_order_independent():
    assert runner.canonical_hash({'a': 1, 'b': 2}) == runner.canonical_hash({'b': 2, 'a': 1})


def test_atomic_json(tmp_path):
    path = tmp_path / 'nested' / 'x.json'
    runner.atomic_json(path, {'seed': 8001})
    assert json.loads(path.read_text()) == {'seed': 8001}
    assert not path.with_name('x.json.tmp').exists()


def test_resume_and_lock(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(runner, 'git_commit', lambda: 'test-commit')
    def fake_execute(algo, seed, cfg, commit, cfg_hash):
        calls.append((algo, seed))
        return {'algorithm': algo, 'seed': seed, 'config_hash': cfg_hash,
                'git_commit': commit, 'function_evaluations': 50,
                'best_fitness': 1.0, 'runtime_seconds': 0.1}
    monkeypatch.setattr(runner, 'execute', fake_execute)
    args = ['--smoke', '--max-evaluations', '150', '--output-dir', str(tmp_path / 'runs')]
    assert runner.run(args) == 0
    assert len(calls) == 4
    assert runner.run(args + ['--resume']) == 0
    assert len(calls) == 4
    with pytest.raises(SystemExit):
        runner.run(args + ['--resume', '--max-evaluations', '160'])


def test_independent_seeds_guard(tmp_path):
    with pytest.raises(SystemExit):
        runner.run(['--seeds', '8003', '--max-evaluations', '150', '--output-dir', str(tmp_path)])
