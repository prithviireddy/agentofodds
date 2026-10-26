"""Distributable inventory, integrity, exclusions and path confinement."""
from pathlib import Path
import hashlib
import json
import tempfile
import unittest
import zipfile

from backend.app.demo_bundle import DOCUMENTATION_FILES, FIXED_FILES, LEGACY_DOCUMENTATION_FILES, MANIFEST, build_bundle, verify_bundle, permitted


class DemoBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in (*FIXED_FILES, *DOCUMENTATION_FILES):
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
                     'frontend/dist/index.html', 'backend/app/private.csv', 'evidence/live_cache.json',
                     'docs/private-notes.md', 'docs/platform/unreviewed.md', *LEGACY_DOCUMENTATION_FILES):
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
            self.assertTrue(set(DOCUMENTATION_FILES) <= set(archive.namelist()))

    def rewrite_inventory(self, files):
        manifest = json.loads(files[MANIFEST])
        manifest['files'] = [{'path': name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
                             for name, raw in sorted(files.items()) if name != MANIFEST]
        files[MANIFEST] = (json.dumps(manifest, indent=2) + '\n').encode()
        with zipfile.ZipFile(self.zip_path, 'w') as archive:
            for name, raw in files.items():
                archive.writestr(name, raw)
        return manifest

    def test_original_and_consolidated_schema_v1_bundles_still_verify(self):
        for with_platform_docs in (False, True):
            with self.subTest(with_platform_docs=with_platform_docs):
                build_bundle(self.root, self.zip_path)
                removed = {'docs/handoff.md', 'docs/tasks.md', 'docs/changes.md'} if with_platform_docs else set(DOCUMENTATION_FILES)
                with zipfile.ZipFile(self.zip_path) as archive:
                    files = {name: archive.read(name) for name in archive.namelist() if name not in removed}
                files.update({name: b'Legacy documentation fixture' for name in LEGACY_DOCUMENTATION_FILES})
                manifest = self.rewrite_inventory(files)
                self.assertEqual(verify_bundle(self.zip_path), manifest)

    def test_incomplete_document_layouts_are_refused_even_with_valid_hashes(self):
        for kind in ('current', 'legacy', 'mixed'):
            with self.subTest(kind=kind):
                build_bundle(self.root, self.zip_path)
                with zipfile.ZipFile(self.zip_path) as archive:
                    files = {name: archive.read(name) for name in archive.namelist()}
                if kind == 'legacy':
                    files = {name: raw for name, raw in files.items() if name not in DOCUMENTATION_FILES}
                    files.update({name: b'Legacy documentation fixture' for name in LEGACY_DOCUMENTATION_FILES[:-1]})
                else:
                    del files['docs/handoff.md']
                    if kind == 'mixed':
                        files['handoff.md'] = b'Legacy handoff fixture'
                self.rewrite_inventory(files)
                with self.assertRaisesRegex(ValueError, 'documentation layout is incomplete'):
                    verify_bundle(self.zip_path)

    def test_new_build_requires_platform_documents(self):
        (self.root / 'docs/platform/README.md').unlink()
        with self.assertRaisesRegex(ValueError, 'Missing.*docs/platform/README.md'):
            build_bundle(self.root, self.zip_path)

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
                     'backend/app/.private/x.py', 'data/ui_runs/receipt.py', '.env.example',
                     'docs/private-notes.md', 'docs/platform/unreviewed.md', 'docs/../.env'):
            self.assertFalse(permitted(name), name)
        self.assertTrue(permitted('backend/app/domain/paper.py'))
        self.assertTrue(permitted('backend/app/adapters/data/fixture.py'))
        self.assertTrue(permitted('frontend/src/main.jsx'))
        self.assertTrue(permitted('docs/platform/README.md'))


if __name__ == '__main__':
    unittest.main()
