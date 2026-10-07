"""
Shared pytest fixtures for the COSMOS adaptation step tests.
"""
import sys
import os

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COSMOS_STEPS_DIR = os.path.join(REPO_ROOT, 'steps', 'cosmos')

# Required so `import send_command` / `import run_script` / `import halt_all_scripts` /
# `import query_telem` work in their respective test modules
for _step_name in ('send_command', 'run_script', 'halt_all_scripts', 'query_telem'):
    _step_dir = os.path.join(COSMOS_STEPS_DIR, _step_name)
    if _step_dir not in sys.path:
        sys.path.insert(0, _step_dir)

COSMOS_ENV_VARS = [
    'COSMOS_URL',
    'COSMOS_SCOPE',
    'COSMOS_USERNAME',
    'COSMOS_PASSWORD',
    'COSMOS_VERIFY_SSL',
    'COSMOS_AUTH_MODE',
]


@pytest.fixture(autouse=True)
def clean_cosmos_env(monkeypatch):
    """Ensure COSMOS_* environment variables never leak between tests."""
    for var in COSMOS_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    yield
