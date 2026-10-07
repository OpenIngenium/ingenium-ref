"""
Validate every step's custom_script.xml against docs/custom_script_schema.rnc.

The schema is written in RELAX NG *compact* syntax, which lxml cannot read
directly, so it is converted to the XML syntax with rnc2rng first.
"""
import glob
import os

import pytest

from lxml import etree
import rnc2rng

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCHEMA_PATH = os.path.join(REPO_ROOT, 'docs', 'custom_script_schema.rnc')

CUSTOM_SCRIPT_XMLS = sorted(
    glob.glob(os.path.join(REPO_ROOT, 'steps', '*', '*', 'custom_script.xml'))
)

# Deliberately malformed fixtures used by ing_lib's ProjConfigCreateUpdateCS tests.
# They are schema-valid but semantically invalid (duplicate input/output names,
# bad template or mouseover references), so they are checked separately.
INVALID_FIXTURE_XMLS = sorted(
    glob.glob(os.path.join(REPO_ROOT, 'steps', 'reference', 'reference_step', 'test_*.xml'))
)


@pytest.fixture(scope='module')
def relaxng():
    rng_source = rnc2rng.dumps(rnc2rng.load(SCHEMA_PATH))
    return etree.RelaxNG(etree.fromstring(rng_source.encode('utf-8')))


def relative(path):
    return os.path.relpath(path, REPO_ROOT)


def test_steps_were_discovered():
    assert CUSTOM_SCRIPT_XMLS, 'no steps/<adaptation>/<step>/custom_script.xml files found'


@pytest.mark.parametrize('xml_path', CUSTOM_SCRIPT_XMLS, ids=relative)
def test_custom_script_matches_schema(relaxng, xml_path):
    document = etree.parse(xml_path)
    assert relaxng.validate(document), (
        f'{relative(xml_path)} failed schema validation:\n'
        + '\n'.join(str(entry) for entry in relaxng.error_log)
    )


@pytest.mark.parametrize('xml_path', INVALID_FIXTURE_XMLS, ids=relative)
def test_semantic_fixtures_are_still_schema_valid(relaxng, xml_path):
    """
    These fixtures exercise semantic checks downstream of the schema; if one
    ever stops parsing or stops matching the schema, the fixture is no longer
    testing what it claims to.
    """
    document = etree.parse(xml_path)
    assert relaxng.validate(document), (
        f'{relative(xml_path)} is no longer schema-valid:\n'
        + '\n'.join(str(entry) for entry in relaxng.error_log)
    )


@pytest.mark.parametrize('xml_path', CUSTOM_SCRIPT_XMLS + INVALID_FIXTURE_XMLS, ids=relative)
def test_xml_model_points_at_the_schema(xml_path):
    """Keep the editor-facing <?xml-model?> hint in sync with the real schema path."""
    document = etree.parse(xml_path)
    hints = [
        node for node in document.getroot().itersiblings(tag=etree.ProcessingInstruction, preceding=True)
        if node.target == 'xml-model'
    ]
    assert hints, f'{relative(xml_path)} has no <?xml-model?> processing instruction'

    href = hints[0].get('href')
    resolved = os.path.normpath(
        os.path.join(os.path.dirname(xml_path), href.removeprefix('file:'))
    )
    assert resolved == SCHEMA_PATH, f'{relative(xml_path)} points at {href}'
