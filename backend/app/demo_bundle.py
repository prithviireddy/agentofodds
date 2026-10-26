"""Allowlisted local demo ZIP, file manifest and archive integrity verification."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

from backend.app.application.demo import ROOT

FIXED_FILES = (
    'README.md', 'AGENTS.md',
    'pyproject.toml', 'uv.lock', '.python-version', '.gitignore',
    'frontend/package.json', 'frontend/package-lock.json', 'frontend/index.html', 'frontend/style.css',
    'frontend/vite.config.js', 'frontend/smoke.cjs', 'frontend/DESIGN.md', 'frontend/design-audit.cjs',
    'config/universe.toml', 'config/research.toml', 'config/model.toml', 'config/evidence_samples.toml',
    'fixtures/prices.json', 'fixtures/workflow_demo.json', 'fixtures/workflow_demo_20.json',
    'fixtures/paper_fills.json', 'fixtures/paper_fills_20.json', 'fixtures/paper_valuations.json',
    'fixtures/paper_valuations_20.json', 'fixtures/comparison_plan.json', 'fixtures/comparison_holdout.json',
    'evidence/m5_1_fixture_audit.json', 'evidence/m5_2_comparison.json', 'evidence/m5_2_comparison.md',
    'evidence/m5_3_verification.json', 'evidence/m5_3_refresh_verification.json',
    'demo/README.md', 'demo/walkthrough.md', 'demo/presenter_notes.md', 'demo/report.md',
)
# Schema-v1 archives retain the same inventory/hash format. Verification accepts
# either complete documentation layout; new builds include only the current one.
LEGACY_DOCUMENTATION_FILES = ('documentation.md', 'architecture.md', 'tasks.md', 'changes.md', 'handoff.md')
DOCUMENTATION_FILES = (
    'docs/README.md', 'docs/handoff.md', 'docs/tasks.md', 'docs/changes.md',
    'docs/platform/README.md', 'docs/platform/01-product-and-scope.md',
    'docs/platform/02-architecture.md', 'docs/platform/03-data-and-persistence.md',
    'docs/platform/04-research-and-workflow.md', 'docs/platform/05-allocation-and-simulation.md',
    'docs/platform/06-interface.md', 'docs/platform/07-security-and-budget.md',
    'docs/platform/08-evaluation-and-evidence.md',
    'docs/adrs/README.md', 'docs/adrs/TEMPLATE.md',
    'docs/feats/README.md', 'docs/feats/TEMPLATE.md', 'docs/feats/FEAT-0001-documentation-foundation.md',
    'docs/runbooks/README.md', 'docs/runbooks/local-demo.md', 'docs/runbooks/verification.md',
    'docs/deferred/README.md', 'docs/reviews/LEDGER.md', 'docs/history/README.md',
    'docs/history/2026-10-24/readme.md', 'docs/history/2026-10-24/contributor-instructions.md',
    'docs/history/2026-10-24/requirements.md', 'docs/history/2026-10-24/architecture.md',
    'docs/history/2026-10-24/tasks.md', 'docs/history/2026-10-24/handoff.md',
    'docs/history/2026-10-24/changes.md', 'docs/history/2026-10-24/demo-guide.md',
)
MANIFEST = 'BUNDLE_MANIFEST.json'
MAX_BYTES = 20_000_000


def permitted(name):
    path = PurePosixPath(name)
    if '\\' in name or path.is_absolute() or '..' in path.parts or not name or ':' in name:
        return False
    if name in FIXED_FILES or name in DOCUMENTATION_FILES or name in LEGACY_DOCUMENTATION_FILES:
        return True
    if any(part.startswith('.') or part in ('__pycache__', 'node_modules', 'dist') for part in path.parts):
        return False
    return ((path.parts[:2] in (('backend', 'app'), ('backend', 'tests')) and path.suffix == '.py') or
            (path.parts[:2] == ('frontend', 'src') and path.suffix in ('.jsx', '.js', '.css')))


def source_files(root):
    root = Path(root).resolve()
    names = set(FIXED_FILES) | set(DOCUMENTATION_FILES)
    for base, suffixes in (('backend/app', ('.py',)), ('backend/tests', ('.py',)), ('frontend/src', ('.jsx', '.js', '.css'))):
        names.update(p.relative_to(root).as_posix() for p in (root / base).rglob('*') if p.is_file() and p.suffix in suffixes)
    result = {}
    for name in sorted(names):
        if not permitted(name):
            continue
        path = root / name
        if not path.is_file() or not path.resolve().is_relative_to(root):
            raise ValueError('Missing or out-of-workspace bundle source: ' + name)
        if any(p.is_symlink() for p in (path, *path.parents) if p != root and p.is_relative_to(root)):
            raise ValueError('Symlinks are not permitted in bundle sources: ' + name)
        result[name] = path.read_bytes()
    if sum(map(len, result.values())) > MAX_BYTES:
        raise ValueError('Demo sources exceed the archive size bound')
    return result


def build_bundle(root, output, manifest_path=None):
    files = source_files(root)
    output = Path(output).resolve()
    sources = {(Path(root) / name).resolve() for name in files}
    if output in sources or (manifest_path and Path(manifest_path).resolve() in sources):
        raise ValueError('Bundle output must not overwrite an included source')
    manifest = {'schema_version': 1, 'purpose': 'local_synthetic_college_demo',
                'excluded': ['credentials/env files', 'live caches/restricted datasets', 'existing runtime books',
                             '.git', '.venv', 'node_modules', 'compiled frontend', 'screenshots'],
                'files': [{'path': name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()} for name, raw in files.items()]}
    payloads = {**files, MANIFEST: (json.dumps(manifest, indent=2) + '\n').encode()}
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in sorted(payloads.items()):
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, raw)
    verify_bundle(output)
    if manifest_path:
        manifest_path = Path(manifest_path)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return manifest


def verify_bundle(path):
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        if (len(names) != len(set(names)) or MANIFEST not in names or len(names) > 300 or
                sum(entry.file_size for entry in entries) > MAX_BYTES):
            raise ValueError('Invalid or oversized demo archive inventory')
        if any(name != MANIFEST and not permitted(name) for name in names):
            raise ValueError('Archive contains a file outside the demo allowlist')
        if any(entry.is_dir() or (entry.external_attr >> 16) & 0o170000 == 0o120000 for entry in entries):
            raise ValueError('Directories/symlinks are not valid bundle entries')
        manifest = json.loads(archive.read(MANIFEST))
        if manifest['schema_version'] != 1 or manifest['purpose'] != 'local_synthetic_college_demo':
            raise ValueError('Unsupported demo manifest')
        records = manifest['files']
        if len({row['path'] for row in records}) != len(records) or set(names) != {MANIFEST, *(row['path'] for row in records)}:
            raise ValueError('Manifest does not match archive inventory')
        if not set(FIXED_FILES) <= set(names):
            raise ValueError('Required demo source/evidence is missing')
        if not (set(LEGACY_DOCUMENTATION_FILES) <= set(names) or set(DOCUMENTATION_FILES) <= set(names)):
            raise ValueError('Required demo documentation layout is incomplete')
        for row in records:
            raw = archive.read(row['path'])
            if len(raw) != row['bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
                raise ValueError('Bundle checksum mismatch: ' + row['path'])
        return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--output', type=Path)
    group.add_argument('--verify', type=Path)
    parser.add_argument('--manifest', type=Path)
    args = parser.parse_args()
    result = verify_bundle(args.verify) if args.verify else build_bundle(ROOT, args.output, args.manifest)
    print(f"Verified demo bundle: {len(result['files'])} files; credentials/runtime data excluded by allowlist.")


if __name__ == '__main__':
    main()
