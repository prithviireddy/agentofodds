"""Run the fixed offline M5.2 comparison and export reviewable JSON/Markdown."""
import argparse
import json
from pathlib import Path

from backend.app.evaluation.comparison import run_comparison, replay_comparison


def markdown(result):
    plan = result['plan']
    comparable = all(all(item['status'] == 'success' for item in run['results'].values()) for run in result['runs'])
    full_universe = comparable and all(
        all(item['candidates'] == run['decisions']['policy']['symbols'] for item in run['decisions']['variants'].values())
        for run in result['runs'])
    same_weights = comparable and all(
        all(run['decisions']['variants'][name]['portfolio']['weights'] == run['decisions']['variants']['numerical_only']['portfolio']['weights']
            for name in ('combined_researcher', 'separate_researchers')) for run in result['runs'])
    lines = ['# M5.2 synthetic comparison', '',
             'Fixture mechanics only. These results do not establish agent quality or investment performance.', '',
             f"Plan identity: `{result['plan_sha256']}`. No tuning; all decisions frozen before loading evaluation prices.", '',
             f"Common execution: {plan['execution_at']}; {plan['transaction_cost_bps']} bps opening cost, zero slippage, no dividends/taxes/liquidation cost.",
             f"Development valuation: {plan['development_valuation_at']}. Synthetic holdout valuation: {plan['holdout_valuation_at']}. Returns below include opening fees.", '',
             '| Universe | Variant | Candidates | Calls | Output tokens reserved | Development return | Holdout return | Status |',
             '| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |']
    for run in result['runs']:
        decisions = run['decisions']
        for name, decision in decisions['variants'].items():
            evaluated = run['results'][name]
            def percentage(split):
                value = evaluated['evaluations'].get(split)
                return value['summary']['return_percent'] + '%' if value else 'unavailable'
            lines.append(f"| {decisions['profile']} | {name} | {len(decision['candidates'])} | "
                         f"{decision['usage']['scripted_calls']} | {decision['usage']['reserved_output_tokens']} | "
                         f"{percentage('development')} | {percentage('holdout')} | {evaluated['status']} |")
    lines += ['', ('Every variant retains the full universe. ' if full_universe else 'See candidate sets and failure outcomes in the archive. ')
              + ('Research allocations match numerical-only allocation; no incremental selection benefit is established. ' if same_weights else '')
              + 'No winner is inferred.', '',
              'The combined and separate researchers use the same selection policy, optimiser and one shared critic. '
              'Combined is one researcher call per company, not a system without a critic. Equal-weight and numerical-only baselines do not use research selection.', '',
              'Agent variants retain unknown actual token usage/inference cost. Reserved tokens are limits, not measured consumption. '
              'External calls and additional provider spend are zero. Local timings in JSON include unequal orchestration/checkpoint overhead.', '',
              'JSON archives the plan, source files/hashes, report evidence, selection decisions, numerical allocations, exact opening books, '
              'valuations, call traces and deterministic decision identities.', '']
    lines.extend('- ' + text for text in result['limitations'])
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='JSON evidence path; Markdown is written beside it')
    parser.add_argument('--replay', type=Path, help='Verify an existing archive without constructing research or calling models')
    args = parser.parse_args()
    if args.output.suffix != '.json':
        parser.error('--output must end in .json')
    result = replay_comparison(json.loads(args.replay.read_text(encoding='utf-8'))) if args.replay else run_comparison()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    args.output.with_suffix('.md').write_text(markdown(result), encoding='utf-8')
    for run in result['runs']:
        print(run['decisions']['profile'], {name: item['status'] for name,item in run['results'].items()})
    return 0 if all(item['status'] == 'success' for run in result['runs'] for item in run['results'].values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
