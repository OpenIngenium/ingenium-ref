# reference

[![Tests](https://github.com/OpenIngenium/reference/actions/workflows/tests.yml/badge.svg)](https://github.com/OpenIngenium/reference/actions/workflows/tests.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

This repository holds reference information and reference steps for various ground data system adaptations.

Steps live here rather than alongside the libraries they depend on, so that the
[`ing_lib`](https://github.com/OpenIngenium/ingenium-lib) and
[`ing_lib_cosmos`](https://github.com/OpenIngenium/ingenium-lib-cosmos) packages stay focused on library code.

## Structure

-   `steps/`: Ingenium custom scripts, grouped by ground data system adaptation. Each adaptation directory
    carries a `requirements.txt` describing what its steps need at runtime.
    -   `reference/`: Adaptation-independent example steps built on `ing_lib`.
        -   `basic_reference_step/`: Minimal template — reads inputs, populates entry outputs, reports status.
        -   `reference_step/`: Full template — additionally emits files, images, and series data.
    -   `cosmos/`: Steps for [OpenC3 COSMOS](https://openc3.com/), built on `ing_lib_cosmos`.
        -   `send_command/`: Send commands via the COSMOS JSON-RPC API.
        -   `run_script/`: Start a COSMOS script and optionally wait for completion.
        -   `halt_all_scripts/`: Halt every running COSMOS script.
        -   `query_telem/`: Query and verify COSMOS telemetry.
-   `tests/`: Pytest suite, mirroring the adaptation layout.
    -   `cosmos/`: Unit tests for the COSMOS steps (the COSMOS API is mocked; no live server needed).
    -   `reference/`: Smoke tests that run the reference steps end to end as subprocesses.
    -   `schema/`: Validates every `custom_script.xml` against `docs/custom_script_schema.rnc`.
-   `docs/`: Reference schemas and definitions.
    -   `custom_script_schema.rnc`: RELAX NG Compact schema for custom script XML.
-   `requirements-dev.txt`: Everything needed to run the full test suite.

Each step directory contains:

| File | Purpose |
| --- | --- |
| `<step_name>.py` | The custom script itself |
| `custom_script.xml` | Step definition (inputs, outputs, layout), validated against the schema |
| `input.json` | Example input, in the form Ingenium passes to the script |
| `output.json` | Example output, in the form Ingenium reads back |
| `requirements.txt` | Step-specific runtime dependencies, where any exist |

## Installation

Install only the adaptation you need:

```bash
pip install -r steps/cosmos/requirements.txt
# or
pip install -r steps/reference/requirements.txt
```

Both pull `ing_lib` (and, for COSMOS, `ing_lib_cosmos`) straight from GitHub at a pinned tag.
Python 3.10 or higher is required.

## Running a step

Ingenium invokes a custom script with an input file path and an output file path:

```bash
python steps/reference/basic_reference_step/basic_reference_step.py input.json output.json
```

The COSMOS steps additionally read their connection settings from the environment
(`COSMOS_URL`, `COSMOS_SCOPE`, `COSMOS_USERNAME`, `COSMOS_PASSWORD`, `COSMOS_VERIFY_SSL`, `COSMOS_AUTH_MODE`).

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

pytest tests/ -ra          # full suite
pytest tests/cosmos -ra    # one adaptation
ruff check steps tests     # lint
```

CI runs the suite against Python 3.10 through 3.14.
