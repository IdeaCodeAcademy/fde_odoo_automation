"""List installable custom addons and require discoverable Python test files."""
import ast
from pathlib import Path


def discover(root: Path) -> list[str]:
    modules = []
    for manifest in sorted(root.glob('*/__manifest__.py')):
        metadata = ast.literal_eval(manifest.read_text())
        if not metadata.get('installable', True):
            continue
        module = manifest.parent
        if not module.name.isidentifier():
            raise ValueError(f'Invalid module name: {module.name}')
        if not (module / '__init__.py').is_file():
            raise ValueError(f'{module.name}: missing __init__.py')
        tests = module / 'tests'
        files = sorted(tests.glob('test_*.py'))
        if not files or not (tests / '__init__.py').is_file():
            raise ValueError(f'{module.name}: add tests/test_*.py and tests/__init__.py')
        tree = ast.parse((tests / '__init__.py').read_text())
        imports = {
            alias.name for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.level == 1
            and node.module is None for alias in node.names
        }
        for test in files:
            if test.stem not in imports:
                raise ValueError(f'{module.name}: import {test.stem} in tests/__init__.py')
        modules.append(module.name)
    return modules


if __name__ == '__main__':
    print(','.join(discover(Path('addons'))))
