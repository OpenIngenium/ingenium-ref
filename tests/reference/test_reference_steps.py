"""
Smoke tests for the reference adaptation steps.

Both reference steps are `if __name__ == '__main__':` scripts rather than
importable modules, so they are exercised here the same way Ingenium runs them:
as a subprocess given an input file path and an output file path. Each step is
run in a scratch directory so the artifacts it emits can be asserted on without
touching the checked-in examples.
"""
import json
import os
import subprocess
import sys
import shutil

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REFERENCE_STEPS_DIR = os.path.join(REPO_ROOT, 'steps', 'reference')

STEP_NAMES = ['basic_reference_step', 'reference_step']

# Artifacts reference_step.py writes alongside output.json; basic_reference_step.py
# deliberately writes none ("the basic version").
REFERENCE_STEP_ARTIFACTS = [
    'sample_file.txt',
    'sample_file_2.txt',
    'sample_graph.png',
    'sample_graph2.png',
    'series.json',
]


def run_step(step_name, tmp_path):
    """Run a reference step in tmp_path and return its parsed output_dict."""
    step_dir = os.path.join(REFERENCE_STEPS_DIR, step_name)
    script = os.path.join(step_dir, f'{step_name}.py')

    input_path = tmp_path / 'input.json'
    output_path = tmp_path / 'output.json'
    shutil.copyfile(os.path.join(step_dir, 'input.json'), input_path)

    env = dict(os.environ)
    env['MPLBACKEND'] = 'Agg'  # headless: no display available in CI

    result = subprocess.run(
        [sys.executable, script, str(input_path), str(output_path)],
        cwd=str(tmp_path), env=env, capture_output=True, text=True,
    )
    assert result.returncode == 0, (
        f'{step_name} exited {result.returncode}\n'
        f'--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}'
    )
    assert output_path.exists(), f'{step_name} did not write an output file'
    return json.loads(output_path.read_text())


@pytest.fixture(scope='module', params=STEP_NAMES)
def step_run(request, tmp_path_factory):
    """Run each reference step once and share the result across assertions."""
    step_name = request.param
    tmp_path = tmp_path_factory.mktemp(step_name)
    return step_name, tmp_path, run_step(step_name, tmp_path)


def test_step_reports_pass(step_run):
    _, _, output_dict = step_run
    assert output_dict['custom_script_status'] == 'PASS'


def test_every_entry_is_verified(step_run):
    step_name, _, output_dict = step_run
    entries = output_dict['entries']
    assert entries, f'{step_name} produced no entries'
    for i, entry in enumerate(entries):
        assert entry['verification_status'] == 'PASS', f'entry {i} did not pass'
        assert entry['entry_outputs']['entry_output_1'] == str(i)
        assert entry['entry_outputs']['entry_output_2'] == str(10 * i)


def test_output_summary_is_populated(step_run):
    _, _, output_dict = step_run
    assert output_dict['output_summary'].strip()


def test_query_range_is_derived_from_inputs(step_run):
    _, _, output_dict = step_run
    outputs = output_dict['outputs']
    for key in ('start_time_date_time', 'query_start', 'query_end'):
        assert outputs[key], f'{key} was not populated'
    assert outputs['query_start'] < outputs['start_time_date_time'] < outputs['query_end']


def test_declared_artifacts_are_written(step_run):
    step_name, tmp_path, output_dict = step_run
    if step_name != 'reference_step':
        pytest.skip('basic_reference_step intentionally emits no artifacts')

    for artifact in REFERENCE_STEP_ARTIFACTS:
        assert (tmp_path / artifact).stat().st_size > 0, f'{artifact} missing or empty'

    # The outputs block must point at the files that were actually written.
    for key in ('file_output_1', 'file_output_2', 'image_output_1', 'image_output_2'):
        assert (tmp_path / output_dict['outputs'][key]).exists()


def test_series_file_is_well_formed(step_run):
    step_name, tmp_path, _ = step_run
    if step_name != 'reference_step':
        pytest.skip('basic_reference_step writes no series data')

    series = json.loads((tmp_path / 'series.json').read_text())
    assert set(series) == {'series_output_1', 'series_output_2'}
    for series_output in series.values():
        assert series_output['timetype']
        assert series_output['series']
        for entry in series_output['series']:
            assert entry['series_type'] in ('HORIZONTAL', 'VERTICAL')
            assert entry['data']
