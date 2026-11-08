"""Regression checks using saved HTTP audit evidence and the actual analyzer."""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from auditor_grill_live_web import Auditor, MenuRec
from rebuild_audit_report import rebuild


def test_raw_display_does_not_require_exact_ingredient_name():
    a = Auditor.__new__(Auditor)
    m = MenuRec('test', 'test', 'smoke', 1, {}, [
        {'name': 'Gạo lứt', 'display_name': display, 'ingredient_name': 'Gạo lứt',
         'slot': 'breakfast_0', 'portion_g': 100}
        for display in ['Gạo lứt nguyên hạt', 'Cơm gạo lứt nấu chín']
    ], {}, {}, [], None, None, 0)
    assert a.analyze_menu(m)['raw_display'] == ['Gạo lứt nguyên hạt']


def test_rebuilt_report_counts_pool_errors_and_all_five_swaps(tmp_path):
    source = Path(__file__).resolve().parents[1] / 'experiments/audit_after_c4c6_clean'
    for name in ['raw_requests.jsonl', 'raw_menus.jsonl', 'summary.json']:
        shutil.copy(source / name, tmp_path / name)
    s = rebuild(tmp_path)
    assert s['derived']['n_400_internal_message'] == 14
    # Independently derive the pre-chain baseline and final result from raw menus.
    menus = [json.loads(line) for line in (source / 'raw_menus.jsonl').read_text().splitlines()]
    for label, chain in s['swap']['chain5'].items():
        records = [m for m in menus if m['phase'] == 'swap' and m['label'].startswith(label + ':')]
        before = next(i for i, m in enumerate(records) if ':chain5:' in m['label']) - 1
        assert chain['start'] == round(Auditor.gap_pct(records[before]['totals'], records[before]['targets']), 1)
    assert s['swap']['gap_chain5_delta_signed'] == 5.2
    assert s['swap']['gap_chain5_delta_abs'] == 6.8
    report = (tmp_path / 'REPORT.md').read_text()
    assert '14 phản hồi 400 còn lộ' in report
    assert '6/133 thực đơn (4.5%)' in report
