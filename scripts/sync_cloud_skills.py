"""Copy newly available Odoo skills; preserve differing installed content."""
import argparse
from pathlib import Path
import shutil


def contents(root):
    files = {}
    for path in root.rglob('*'):
        if path.is_symlink():
            raise ValueError(f'Skill symlinks require manual review: {path}')
        if path.is_file():
            files[path.relative_to(root)] = path.read_bytes()
    return files


def sync(source, targets):
    skills = sorted(path.parent for path in source.glob('*/SKILL.md'))
    if not skills:
        raise ValueError(f'No skills found in configured source: {source}')
    pending = []
    # Validate all destinations before copying anything.
    for skill in skills:
        expected = contents(skill)
        for target in targets:
            dest = target / skill.name
            if dest.is_symlink():
                raise ValueError(f'Existing destination is a symlink: {dest}')
            if dest.exists():
                if contents(dest) != expected:
                    raise ValueError(f'Existing skill differs; preserve and review it: {dest}')
            else:
                pending.append((skill, dest))
    for skill, dest in pending:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(skill, dest)
    return len(skills), len(pending)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--target', type=Path, action='append', required=True)
    args = parser.parse_args()
    count, added = sync(args.source, args.target)
    print(f'Verified {count} source skills; added {added} skill directories')
