"""Offline controlled ablation: freeze decisions before reading evaluation-only prices."""
from dataclasses import asdict, replace
from decimal import Decimal
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile
from time import perf_counter

from backend.app.adapters.comparison_fixture import CombinedFixtureModel
from backend.app.application.demo import DemoService, FixtureModel, ROOT, plain
from backend.app.application.paper import digest
from backend.app.application.selection import select_candidates
from backend.app.contracts.market_data import timestamp
from backend.app.domain.optimizer import solve_minimum_variance, VERSION as SOLVER_VERSION
from backend.app.domain.paper import PaperError, opening_plan
from backend.app.domain.statistics import calculate_price_statistics
from backend.app.domain.valuation import value_portfolio
from backend.app.evaluation.basic import equal_weight_portfolio
from backend.app.research.combined import run_combined_research, PROMPT_VERSION as COMBINED_VERSION
from backend.app.research.fundamental import PROMPT_VERSION as FUNDAMENTAL_VERSION
from backend.app.research.news import PROMPT_VERSION as NEWS_VERSION
from backend.app.research.quantitative import run_quantitative_research
from backend.app.workflows.review import critic_prompt, review_allocation, validate_critique, SCHEMA, PROMPT_VERSION as CRITIC_VERSION
from backend.app.workflows.runner import run_workflow

VARIANTS = ('equal_weight', 'numerical_only', 'combined_researcher', 'separate_researchers')


def validate_plan(plan):
    if (plan['schema_version'] != 1 or tuple(plan['variants']) != VARIANTS or
            plan['profiles'] != ['five', 'twenty'] or plan['tuning'] != 'none' or
            plan['slippage'] != 'zero' or plan['dividends'] != 'unsupported_reject' or plan['taxes'] != 'excluded'):
        raise ValueError('Unsupported comparison specification')
    times = [timestamp(plan[k]) for k in ('decision_cutoff', 'execution_at', 'development_valuation_at', 'holdout_valuation_at')]
    if not all(a < b for a, b in zip(times, times[1:])) or times[0].date() >= times[1].date():
        raise ValueError('Decision, fill, development and holdout dates must be strictly ordered')
    fee = Decimal(plan['transaction_cost_bps'])
    if not fee.is_finite() or not 0 <= fee <= 10000 or type(plan['max_price_age_days']) is not int or not 0 <= plan['max_price_age_days'] <= 30:
        raise ValueError('Invalid experiment fees/freshness')


def usage(events, queries):
    return {'scripted_calls': len(events), 'reserved_output_tokens': sum(e['output_token_cap'] for e in events),
            'retrieval_queries': queries, 'calls_with_unknown_usage': len(events),
            'actual_tokens': None if events else 0, 'inference_cost_usd': None if events else '0',
            'external_calls': 0, 'additional_provider_spend_usd': '0', 'concurrency': 1, 'events': events}


def selected_allocation(inputs, candidates):
    policy = replace(inputs['investment'], symbols=tuple(candidates))
    prices = replace(inputs['prices'], requested_symbols=tuple(candidates),
                     bars=tuple(b for b in inputs['prices'].bars if b.symbol in candidates), missing_symbols=(), status='success')
    stats = calculate_price_statistics(prices)
    portfolio = solve_minimum_variance(policy, stats.covariance)
    review = review_allocation(policy, portfolio, stats.covariance)
    return policy, portfolio, review


def prepare_decisions(profile):
    """This function has no development/holdout price argument or access path."""
    with tempfile.TemporaryDirectory() as directory:
        service = DemoService(directory, fixture_set=profile)
        values = service.settings()['demo']
        inputs = service.inputs(values)
        policy = inputs['investment']
        decisions = {}
        start = perf_counter()
        baseline = equal_weight_portfolio(policy)
        decisions['equal_weight'] = {'status': baseline.status, 'portfolio': plain(baseline),
            'candidates': list(policy.symbols), 'usage': usage([], 0), 'seconds': perf_counter() - start}
        start = perf_counter()
        _, numerical, review = selected_allocation(inputs, policy.symbols)
        decisions['numerical_only'] = {'status': review['status'], 'portfolio': plain(numerical),
            'candidates': list(policy.symbols), 'review': review, 'usage': usage([], 0), 'seconds': perf_counter() - start}
        start = perf_counter()
        model = CombinedFixtureModel()
        retrieval_queries = 0
        fundamental, news = {}, {}
        try:
            quantitative = run_quantitative_research(inputs['prices'], max_age_days=inputs['selection_policy'].max_price_age_days)
            for symbol in policy.symbols:
                retrieval_queries += 2 * len(inputs['requests'][symbol].queries)
                fundamental[symbol], news[symbol] = run_combined_research(inputs['index'], inputs['requests'][symbol], inputs['news_start'], model)
            selection = select_candidates(policy, inputs['selection_policy'], fundamental, news, quantitative)
            item = {'status': selection.status, 'candidates': list(selection.candidates), 'selection': plain(selection),
                    'reports': plain({**{'fundamental:'+s: r for s,r in fundamental.items()}, **{'news:'+s: r for s,r in news.items()}})}
            if selection.status == 'success':
                _, portfolio, review = selected_allocation(inputs, selection.candidates)
                reports = {role+':'+s: source[s] for s in selection.candidates for role, source in (('fundamental', fundamental), ('news', news))}
                prompt = critic_prompt(reports, max_characters=service.budget.max_critic_prompt_characters)
                output, metadata = FixtureModel('critic:0', 'normal', False, '').generate_json(prompt, SCHEMA, 768, 0)
                critique = validate_critique(output, reports)
                model.events.append({'model': metadata['model'], 'output_token_cap': 768, 'usage': {},
                                     'prompt_characters': len(prompt), 'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest()})
                item.update(portfolio=plain(portfolio), review=review, critic=critique,
                            status='success' if review['status'] == 'success' and critique['verdict'] == 'approved' else 'review_rejected')
        except (ValueError, TypeError, KeyError) as exc:
            item = {'status': 'failed_validation', 'reason': str(exc), 'candidates': []}
        item.update(usage=usage(model.events, retrieval_queries), seconds=perf_counter() - start)
        decisions['combined_researcher'] = item
        start = perf_counter()
        state = run_workflow('comparison', **inputs)
        reports = {k:v for k,v in state.get('results', {}).items() if k.startswith(('fundamental:', 'news:'))}
        selection = state.get('results', {}).get('selection')
        decisions['separate_researchers'] = {'status': state['status'], 'candidates': list(selection.candidates) if selection else [],
            'portfolio': plain(state.get('results', {}).get('allocation')), 'selection': plain(selection), 'reports': plain(reports),
            'review': plain(state.get('results', {}).get('review')), 'critic': plain(state.get('results', {}).get('critic:0')),
            'workflow_fingerprint': state.get('fingerprint'), 'usage': usage(state.get('model_events', []), state.get('retrieval_queries', 0)),
            'seconds': perf_counter() - start}
        return {'profile': profile, 'policy': plain(policy), 'selection_policy': plain(inputs['selection_policy']),
                'decision_fixture_sha256': service.fixture_hash, 'solver_version': SOLVER_VERSION,
                'prompt_versions': {'combined': COMBINED_VERSION, 'critic': CRITIC_VERSION,
                                    'fundamental': FUNDAMENTAL_VERSION, 'news': NEWS_VERSION},
                'execution_limits': {'separate': asdict(service.budget),
                    'combined': {'research_calls': len(policy.symbols), 'critic_calls': 1, 'research_prompt_characters': 16000,
                                 'research_output_tokens_per_call': 1536, 'critic_output_tokens': 768,
                                 'critic_prompt_characters': service.budget.max_critic_prompt_characters},
                    'automatic_retries': 0, 'concurrency': 1}, 'variants': decisions}


def evaluate_decisions(decisions, plan, fills, development, holdout):
    """Only this phase sees future prices; it cannot modify any research or allocation."""
    from backend.app.domain.optimizer import PortfolioResult
    from backend.app.domain.policy import InvestmentPolicy
    validate_plan(plan)
    if timestamp(decisions['policy']['as_of']) != timestamp(plan['decision_cutoff']):
        raise ValueError('Decision cutoff differs from experiment specification')
    if timestamp(fills['execution_at']) != timestamp(plan['execution_at']):
        raise ValueError('Fill timing differs from experiment specification')
    results = {}
    for name in VARIANTS:
        decision = decisions['variants'][name]
        if decision['status'] != 'success':
            results[name] = {'status': decision['status'], 'evaluations': {}}
            continue
        try:
            raw = decisions['policy']
            policy = InvestmentPolicy(**{**raw, 'as_of': timestamp(raw['as_of']), 'symbols': tuple(decision['candidates']),
                **{key: Decimal(raw[key]) for key in ('capital', 'min_asset_weight', 'max_asset_weight', 'min_cash_weight', 'max_cash_weight')}})
            stored = decision['portfolio']
            portfolio = PortfolioResult(**{**stored, 'weights': {s:Decimal(w) for s,w in stored['weights'].items()}, 'cash_weight': Decimal(stored['cash_weight'])})
            execution = timestamp(plan['execution_at'])
            quotes = {s: {'price': fills['prices'][s], 'at': execution.isoformat(), 'source_id': 'fixture:comparison-fill:'+s}
                      for s in policy.symbols if s in fills['prices']}
            book = opening_plan(policy, portfolio, execution_at=execution, quotes=quotes,
                                fee_bps=plan['transaction_cost_bps'], corporate_actions=fills['corporate_actions'])
            evaluated = {}
            for split, source in (('development', development), ('holdout', holdout)):
                expected = plan[split + '_valuation_at']
                if source['schema_version'] != 1 or len({f['valuation_at'] for f in source['frames']}) != len(source['frames']):
                    raise ValueError('Invalid evaluation frames')
                frame = next((f for f in source['frames'] if f['valuation_at'] == expected), None)
                if frame is None:
                    raise PaperError('missing_prices', 'Missing declared evaluation frame: ' + split)
                prices = {**frame, 'prices': [row for row in frame['prices'] if row['symbol'] in book['balances']['holdings']],
                          'currency': source['currency'], 'adjustment': source['adjustment'],
                          'max_price_age_days': plan['max_price_age_days']}
                evaluated[split] = value_portfolio(book, prices)
            results[name] = {'status': 'success', 'opening_book': book, 'evaluations': evaluated}
        except (PaperError, ValueError, TypeError, KeyError) as exc:
            results[name] = {'status': getattr(exc, 'status', 'failed_validation'), 'reason': str(exc), 'evaluations': {}}
    return results


def decision_identity(decisions):
    stable = {**decisions, 'variants': {name: {k:v for k,v in item.items() if k != 'seconds'}
                                      for name, item in decisions['variants'].items()}}
    return digest(stable)


def run_comparison():
    def read(name):
        raw = (ROOT / 'fixtures' / name).read_bytes()
        return json.loads(raw), {'text': raw.decode('utf-8'), 'sha256': hashlib.sha256(raw).hexdigest()}
    plan, plan_source = read('comparison_plan.json')
    validate_plan(plan)
    # Freeze every decision before loading either evaluation split. No parameter search or tuning.
    decisions = [prepare_decisions(profile) for profile in plan['profiles']]
    decision_hashes = [decision_identity(d) for d in decisions]
    holdout, holdout_source = read('comparison_holdout.json')
    archive = {'comparison_plan.json': plan_source, 'comparison_holdout.json': holdout_source}
    runs = []
    for frozen, decision_hash in zip(decisions, decision_hashes):
        suffix = '_20' if frozen['profile'] == 'twenty' else ''
        _, research_source = read('workflow_demo' + suffix + '.json')
        if research_source['sha256'] != frozen['decision_fixture_sha256']:
            raise ValueError('Research fixture changed after decisions were frozen')
        fills, fill_source = read('paper_fills' + suffix + '.json')
        development, dev_source = read('paper_valuations' + suffix + '.json')
        archive.update({f'workflow_demo{suffix}.json': research_source,
                        f'paper_fills{suffix}.json': fill_source, f'paper_valuations{suffix}.json': dev_source})
        results = evaluate_decisions(frozen, plan, fills, development, holdout)
        if decision_identity(frozen) != decision_hash:
            raise ValueError('Evaluation mutated frozen decisions')
        runs.append({'decisions_sha256': decision_hash, 'decisions': frozen, 'results': results})
    return {'schema_version': 1, 'implementation_version': 'comparison-v1',
            'recorded_at': datetime.now(timezone.utc).isoformat(),
            'mode': 'synthetic_controlled_ablation', 'plan': plan, 'plan_sha256': digest(plan),
            'source_archive': archive, 'runs': runs, 'limitations': [
                'Scripted fixtures establish mechanics and schema/citation checks, not factual accuracy or an investment advantage.',
                'Holdout is synthetic and withheld from decision code, not independently sourced market evidence. No statistical significance claim.',
                'Combined means one researcher call per company plus the same shared critic; separate uses two role calls plus that critic.',
                'Local timings include different orchestration/checkpoint overhead and are not a fair model latency benchmark.',
                'No annualised return, Sharpe ratio or ranking is inferred from these short fixture windows.',
                'No external calls, real approvals, ledger writes, trades or provider spend. Model token usage/cost are unknown.']}


def replay_comparison(result):
    """Verify and recalculate only from the self-contained archive; never run models."""
    if result['schema_version'] != 1 or result['mode'] != 'synthetic_controlled_ablation' or digest(result['plan']) != result['plan_sha256']:
        raise ValueError('Invalid experiment identity')
    archive = {}
    for name, source in result['source_archive'].items():
        if hashlib.sha256(source['text'].encode()).hexdigest() != source['sha256']:
            raise ValueError('Archived source hash mismatch')
        archive[name] = json.loads(source['text'])
    if archive['comparison_plan.json'] != result['plan']:
        raise ValueError('Archived plan mismatch')
    if [run['decisions']['profile'] for run in result['runs']] != result['plan']['profiles']:
        raise ValueError('Missing or duplicate experiment profile')
    for run in result['runs']:
        decisions = run['decisions']
        if decision_identity(decisions) != run['decisions_sha256']:
            raise ValueError('Archived decisions were changed')
        suffix = '_20' if decisions['profile'] == 'twenty' else ''
        if result['source_archive'][f'workflow_demo{suffix}.json']['sha256'] != decisions['decision_fixture_sha256']:
            raise ValueError('Archived research identity mismatch')
        evaluated = evaluate_decisions(decisions, result['plan'], archive[f'paper_fills{suffix}.json'],
                                       archive[f'paper_valuations{suffix}.json'], archive['comparison_holdout.json'])
        if evaluated != run['results']:
            raise ValueError('Archived evaluation does not reconcile')
    return result
