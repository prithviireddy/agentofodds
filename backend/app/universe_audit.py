"""Reproducible offline coverage/scaling proof; no live data or investment benchmark."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile
from time import perf_counter

from backend.app.application.demo import DemoService
from backend.app.domain.paper import PaperError


def audit(fixture_set):
    with tempfile.TemporaryDirectory() as directory:
        service = DemoService(directory, fixture_set=fixture_set)
        values = service.settings()['demo']
        start = perf_counter()
        run = service.create(values)
        run_id = run['run_id']
        state = service.get(run_id)
        stages = []
        for _ in range(2 * len(values['symbols']) + 5):
            if not state['can_continue']:
                break
            tick = perf_counter()
            state = service.advance(run_id)
            stages.append({'step': state['history'][-1]['step'], 'seconds': perf_counter() - tick})
        workflow_seconds = perf_counter() - start
        checkpoint = service.store.load(run_id)
        fill_raw = service.paper.fill_path.read_bytes()
        fills = json.loads(fill_raw)
        valuation_fixture, valuation_hash = service.monitoring.provider.load()
        coverage = []
        for company in service.fixture['companies']:
            symbol = company['symbol']
            roles = {role: state['reports'].get(role + ':' + symbol, {}) for role in ('fundamental', 'news')}
            coverage.append({'symbol': symbol, 'name': company['name'],
                'price_sessions': len(company['closes']),
                'research': {role: {'status': report.get('status', 'not_run'),
                                   'evidence_count': len(report.get('evidence', []))} for role, report in roles.items()},
                'opening_fill': symbol in fills['prices'],
                'valuation_frames': sum(any(row['symbol'] == symbol for row in frame['prices']) for frame in valuation_fixture['frames']),
                'source_kind': 'synthetic_shared_passage', 'live_coverage': 'not_audited'})
        paper_status, valuation_count = 'not_attempted', 0
        if state['status'] == 'success':
            try:
                preview = service.paper.preview(run_id)
                service.paper.approve(run_id, preview['proposal_id'], True)  # Temporary automated fixture test only.
                for at in service.monitoring.provider.dates():
                    service.monitoring.update(run_id, at)
                paper_status, valuation_count = 'success', len(service.monitoring.history(run_id))
            except PaperError as exc:
                paper_status = exc.status
        return {'schema_version': 1, 'measured_at': datetime.now(timezone.utc).isoformat(),
                'fixture_set': fixture_set, 'mode': 'offline_synthetic_scaling_proof',
                'run_id': run_id, 'workflow_fingerprint': state['fingerprint'],
                'fixture_hashes': {'research': service.fixture_hash, 'fills': hashlib.sha256(fill_raw).hexdigest(), 'valuations': valuation_hash},
                'policy': values, 'budget': service.settings()['budget'], 'coverage': coverage,
                'workflow_status': state['status'], 'paper_status': paper_status, 'saved_valuations': valuation_count,
                'report_count': len(state['reports']), 'candidate_count': len((state.get('selection') or {}).get('candidates', [])),
                'workflow_seconds': workflow_seconds, 'total_seconds': perf_counter() - start,
                'stage_seconds': stages, 'usage': state['usage'],
                'max_prompt_characters': max((e['prompt_characters'] for e in checkpoint['model_events']), default=0),
                'critic_prompt_characters': [e['prompt_characters'] for e in checkpoint['model_events'] if e['step'].startswith('critic:')],
                'external_calls': 0, 'additional_provider_spend_usd': '0',
                'limitations': ['One local wall-clock sample including checkpoint I/O; not provider latency or a performance benchmark.',
                    'Scripted fixture model has no measured inference tokens or monetary inference cost; reserved output tokens are a cap.',
                    'One identical invented passage per company serves both roles; independent news and live coverage are not established.',
                    'Three sessions and repeated return patterns are a scaling fixture, not a statistically adequate covariance sample.',
                    'Illustrative company labels are not verified point-in-time universe membership. Temporary automated approvals are test fixtures.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = {'schema_version': 1, 'runs': [audit(profile) for profile in ('five', 'twenty')]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    for run in result['runs']:
        print(f"{run['fixture_set']}: workflow={run['workflow_status']}, paper={run['paper_status']}, "
              f"reports={run['report_count']}, calls={run['usage']['model_calls_reserved']}, "
              f"seconds={run['workflow_seconds']:.3f}, critic_chars={run['critic_prompt_characters']}")
    return 0 if all(r['workflow_status'] == r['paper_status'] == 'success' for r in result['runs']) else 1


if __name__ == '__main__':
    raise SystemExit(main())
