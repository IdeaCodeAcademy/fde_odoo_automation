from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.sync_cloud_skills import sync


class CloudSkillTests(unittest.TestCase):
    def test_new_skill_detected_on_next_setup_without_fixed_count(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, target = root / 'source', root / 'target'
            skill = source / 'first'
            skill.mkdir(parents=True)
            (skill / 'SKILL.md').write_text('first')
            self.assertEqual(sync(source, [target]), (1, 1))
            self.assertEqual(sync(source, [target]), (1, 0))
            second = source / 'second'
            second.mkdir()
            (second / 'SKILL.md').write_text('second')
            self.assertEqual(sync(source, [target]), (2, 1))
            self.assertEqual((target / 'second/SKILL.md').read_text(), 'second')

    def test_conflicting_installed_skill_is_preserved(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, target = root / 'source', root / 'target'
            for path in (source / 'skill', target / 'skill'):
                path.mkdir(parents=True)
            (source / 'skill/SKILL.md').write_text('upstream')
            local = target / 'skill/SKILL.md'
            local.write_text('local')
            with self.assertRaises(ValueError):
                sync(source, [target])
            self.assertEqual(local.read_text(), 'local')

    def test_missing_source_fails(self):
        with TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                sync(Path(tmp) / 'missing', [Path(tmp) / 'target'])
