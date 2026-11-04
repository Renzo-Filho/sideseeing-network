"""Rules the package layout enforces (docs/ARCHITECTURE.md, section 7)."""
import ast
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1] / 'walk2net'


def imported_modules(path):
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            yield from (alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module
            yield from (f'{node.module}.{alias.name}' for alias in node.names)


def test_construction_never_imports_the_evaluation():
    """The reference must not leak into the graph (research plan decision 2, AGENTS.md rule 12)."""
    offenders = {str(path.relative_to(PACKAGE)): name
                 for path in (PACKAGE / 'stages').rglob('*.py')
                 for name in imported_modules(path) if name.startswith('walk2net.evaluate')}
    assert not offenders, offenders
