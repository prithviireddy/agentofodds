"""Distributable inventory, integrity, exclusions and path confinement."""
from pathlib import Path
import tempfile
import unittest
import zipfile

from backend.app.demo_bundle import FIXED_FILES, MANIFEST, build_bundle, verify_bundle, permitted


class DemoBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in FIXED_FILES:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('permitted fixture content')
        for name in ('backend/app/example.py', 'backend/app/adapters/data/fixture.py', 'frontend/src/App.jsx'):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('source fixture')
        self.zip_path = self.root / 'data/demo.zip'

    def test_bundle_excludes_runtime_env_dependencies_and_is_repeatable(self):
        for name in ('.env', '.env.example', 'data/ui_runs/receipt.json', 'frontend/node_modules/index.js',
                     'frontend/dist/index.html', 'backend/app/private.csv', 'evidence/live_cache.json'):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('DO NOT PACKAGE')
        manifest = build_bundle(self.root, self.zip_path)
        original = self.zip_path.read_bytes()
        self.assertEqual(verify_bundle(self.zip_path), manifest)
        build_bundle(self.root, self.zip_path)
        self.assertEqual(self.zip_path.read_bytes(), original)
        with zipfile.ZipFile(self.zip_path) as archive:
            self.assertFalse(any(b'DO NOT PACKAGE' in archive.read(name) for name in archive.namelist()))
            self.assertIn('backend/app/example.py', archive.namelist())
            self.assertIn('backend/app/adapters/data/fixture.py', archive.namelist())

    def test_corrupt_payload_or_unlisted_secret_is_refused(self):
        for kind in ('corrupt', 'secret', 'traversal'):
            build_bundle(self.root, self.zip_path)
            with zipfile.ZipFile(self.zip_path) as archive:
                files = {name: archive.read(name) for name in archive.namelist()}
            if kind == 'corrupt':
                files['README.md'] += b'changed'
            elif kind == 'secret':
                files['.env'] = b'secret fixture'
            else:
                files['../outside.txt'] = b'outside'
            with zipfile.ZipFile(self.zip_path, 'w') as archive:
                for name, raw in files.items():
                    archive.writestr(name, raw)
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                verify_bundle(self.zip_path)

    def test_missing_required_file_and_source_overwrite_refused(self):
        (self.root / 'uv.lock').unlink()
        with self.assertRaises(ValueError):
            build_bundle(self.root, self.zip_path)
        (self.root / 'uv.lock').write_text('lock fixture')
        with self.assertRaises(ValueError):
            build_bundle(self.root, self.root / 'README.md')
        self.assertEqual((self.root / 'README.md').read_text(), 'permitted fixture content')

    def test_path_policy(self):
        for name in ('../README.md', '/README.md', 'C:/README.md', 'backend\\app\\x.py',
                     'backend/app/.private/x.py', 'data/ui_runs/receipt.py', '.env.example'):
            self.assertFalse(permitted(name), name)
        self.assertTrue(permitted('backend/app/domain/paper.py'))
        self.assertTrue(permitted('backend/app/adapters/data/fixture.py'))
        self.assertTrue(permitted('frontend/src/main.jsx'))


if __name__ == '__main__':
    unittest.main()
