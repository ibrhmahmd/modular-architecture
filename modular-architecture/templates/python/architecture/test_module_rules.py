"""Import-graph contracts. A module fails only once it is in ENFORCED_MODULES.

Add a module to ENFORCED_MODULES when its migration finishes (or on creation,
for a new module). Modules in the set must have zero violations.
"""

import pytest

from tests.architecture.conftest import MODULES, MODULES_PACKAGE, RULE_KEYS, RULE_TITLES

ENFORCED_MODULES: set[str] = set()


def _assert_clean(rule: str, module: str, violations: dict) -> None:
    offences = violations[rule][module]
    if module in ENFORCED_MODULES and offences:
        rendered = "\n".join(f"  - {o}" for o in offences)
        raise AssertionError(f"{RULE_TITLES[rule]} violations in enforced module '{module}':\n{rendered}")


@pytest.mark.parametrize("module", MODULES)
def test_module_order(module, violations):
    _assert_clean("module_order", module, violations)


@pytest.mark.parametrize("module", MODULES)
def test_facade_only(module, violations):
    _assert_clean("facade_only", module, violations)


@pytest.mark.parametrize("module", MODULES)
def test_in_module_layers(module, violations):
    _assert_clean("layers", module, violations)


@pytest.mark.parametrize("module", MODULES)
def test_no_session_factory(module, violations):
    _assert_clean("session_factory", module, violations)


def test_module_list(import_graph):
    """The packages under the modules package must equal MODULES exactly."""
    prefix = MODULES_PACKAGE + "."
    found = {name[len(prefix):] for name in import_graph.find_children(MODULES_PACKAGE)}
    assert found == set(MODULES), "modules changed on disk; update MODULES (and its order) in conftest.py"


def test_enforced_modules_exist():
    assert ENFORCED_MODULES <= set(MODULES), f"unknown modules: {ENFORCED_MODULES - set(MODULES)}"


def test_every_rule_reports_every_module(violations):
    for key in RULE_KEYS:
        for module in MODULES:
            assert isinstance(violations[key][module], list)
