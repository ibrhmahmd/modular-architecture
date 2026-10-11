"""Architecture contracts: import-graph rules for a modular monolith.

Copy into tests/architecture/ and edit the CONFIG block. The import graph is
built once per session with grimp (`pip install grimp`). Each rule is computed
once; a summary table of violations per module and rule prints at the end of
every run. Rules only FAIL for modules listed in ENFORCED_MODULES
(test_module_rules.py); everything else is report-only.
"""

import ast
import os

import pytest
from grimp import build_graph

# ── CONFIG ──────────────────────────────────────────────────────────────────
# Top-level package to scan, and the package holding the modules.
ROOT_PACKAGE = "app"
MODULES_PACKAGE = "app.modules"

# Module order, TOP to BOTTOM: a module may import only modules BELOW it.
# A module added on disk but missing here fails test_module_list.
MODULES: list[str] = [
    # "reports",
    # "billing",
    # "people",
    # "identity",
]

# In-module layers (first matching path segment wins).
LAYERS = ("api", "services", "repositories", "schemas", "models")

# Name of the session factory that only entry points may call, and the paths
# (relative to the repo root) sanctioned to call it anyway.
SESSION_FACTORY = "get_session"
SESSION_FACTORY_ALLOW: tuple[str, ...] = (
    # "app/modules/notifications/adapters",
)

# Repo root, relative to this file (tests/architecture/conftest.py).
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
# ────────────────────────────────────────────────────────────────────────────

ORDER = {name: i for i, name in enumerate(MODULES)}  # lower index = higher
RULE_KEYS = ["module_order", "facade_only", "layers", "session_factory"]
RULE_TITLES = {
    "module_order": "module order",
    "facade_only": "facade only",
    "layers": "layers",
    "session_factory": SESSION_FACTORY,
}

_PREFIX = MODULES_PACKAGE + "."
_ROOT_DIR = os.path.join(PROJECT_ROOT, *ROOT_PACKAGE.split("."))


def _module_of(dotted: str) -> str | None:
    if not dotted.startswith(_PREFIX):
        return None
    return dotted[len(_PREFIX):].split(".", 1)[0]


def _relpath(dotted: str) -> str:
    path = dotted.replace(".", "/")
    if os.path.isdir(os.path.join(PROJECT_ROOT, path)):
        return path + "/__init__.py"
    return path + ".py"


def _is_models(imported: str, module: str) -> bool:
    prefix = f"{_PREFIX}{module}.models"
    return imported == prefix or imported.startswith(prefix + ".")


def _is_facade_or_models(imported: str, module: str) -> bool:
    return imported == f"{_PREFIX}{module}" or _is_models(imported, module)


def _layer_of(dotted: str, module: str) -> str | None:
    for segment in dotted[len(_PREFIX) + len(module):].split("."):
        if segment in LAYERS:
            return segment
    return None


def _forbidden_layer_move(importer: str, imported: str) -> bool:
    if importer == "services":
        return imported == "api"
    if importer == "repositories":
        return imported in ("services", "api")
    if importer in ("schemas", "models"):
        return imported in ("services", "repositories", "api")
    return False


def _edges(graph, importer: str, imported: str):
    """(file, line) pairs for one direct import; line is None when unknown."""
    details = graph.get_import_details(importer=importer, imported=imported)
    if not details:
        return [(_relpath(importer), None)]
    return [(_relpath(importer), d["line_number"]) for d in sorted(details, key=lambda d: d["line_number"])]


def _fmt(importer: str, imported: str, file: str, line: int | None) -> str:
    where = file if line is None else f"{file}:{line}"
    return f"{importer} -> {imported} ({where})"


def _compute(graph) -> dict[str, dict[str, list[str]]]:
    out = {key: {m: [] for m in MODULES} for key in RULE_KEYS}
    for importer in sorted(graph.modules):
        x = _module_of(importer)
        if x is None or x not in ORDER:
            continue
        for imported in sorted(graph.find_modules_directly_imported_by(importer)):
            y = _module_of(imported)
            if y is None or y not in ORDER:
                continue
            for file, line in _edges(graph, importer, imported):
                v = _fmt(importer, imported, file, line)
                if y != x:
                    if ORDER[y] < ORDER[x] and not _is_models(imported, y):
                        out["module_order"][x].append(v)
                    if not _is_facade_or_models(imported, y):
                        out["facade_only"][x].append(v)
                else:
                    a, b = _layer_of(importer, x), _layer_of(imported, x)
                    if a and b and _forbidden_layer_move(a, b):
                        out["layers"][x].append(v)
    for module, hits in _session_factory_calls().items():
        if module in out["session_factory"]:
            out["session_factory"][module] = hits
    return out


def _session_factory_calls() -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for root, dirs, files in os.walk(_ROOT_DIR):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for name in files:
            if not name.endswith(".py"):
                continue
            path = os.path.join(root, name)
            rel = os.path.relpath(path, PROJECT_ROOT)
            if any(rel == a or rel.startswith(a + os.sep) for a in SESSION_FACTORY_ALLOW):
                continue
            dotted = rel[:-3].replace(os.sep, ".").removesuffix(".__init__")
            module = _module_of(dotted)
            if module is None:
                continue
            try:
                tree = ast.parse(open(path, encoding="utf-8").read())
            except (SyntaxError, UnicodeDecodeError):
                continue
            for node in ast.walk(tree):
                line = _session_factory_line(node)
                if line is not None:
                    result.setdefault(module, []).append(f"{rel}:{line}")
    return result


def _session_factory_line(node) -> int | None:
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == SESSION_FACTORY:
        return node.lineno
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        for alias in node.names:
            if alias.name == SESSION_FACTORY or alias.name.endswith("." + SESSION_FACTORY):
                return node.lineno
    return None


RULE_RESULTS: dict[str, dict[str, list[str]]] = {}


@pytest.fixture(scope="session")
def import_graph():
    return build_graph(ROOT_PACKAGE, cache_dir=None)


@pytest.fixture(scope="session")
def violations(import_graph):
    if not RULE_RESULTS:
        RULE_RESULTS.update(_compute(import_graph))
    return RULE_RESULTS


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    if not RULE_RESULTS:
        return
    tw = terminalreporter
    widths = [max(14, len(RULE_TITLES[k]) + 2) for k in RULE_KEYS]
    header = f"{'module':<16}" + "".join(f"{RULE_TITLES[k]:>{w}}" for k, w in zip(RULE_KEYS, widths)) + f"{'total':>8}"
    tw.write_line("")
    tw.write_line("architecture contracts: violations per module (fails only for ENFORCED_MODULES)")
    tw.write_line(header)
    tw.write_line("-" * len(header))
    totals = [0] * len(RULE_KEYS)
    for module in MODULES:
        counts = [len(RULE_RESULTS[k][module]) for k in RULE_KEYS]
        totals = [t + c for t, c in zip(totals, counts)]
        tw.write_line(f"{module:<16}" + "".join(f"{c:>{w}}" for c, w in zip(counts, widths)) + f"{sum(counts):>8}")
    tw.write_line("-" * len(header))
    tw.write_line(f"{'total':<16}" + "".join(f"{t:>{w}}" for t, w in zip(totals, widths)) + f"{sum(totals):>8}")
