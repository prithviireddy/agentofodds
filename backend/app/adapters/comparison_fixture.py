"""Scripted combined-role model for offline ablation mechanics, never real inference."""
import hashlib
import json


class CombinedFixtureModel:
    model_id = 'fixture-combined-v1'

    def __init__(self):
        self.events = []

    def generate_json(self, prompt, schema, max_output_tokens, temperature):
        if len(self.events) >= 20 or len(prompt) > 16000 or max_output_tokens != 1536 or temperature != 0:
            raise ValueError('Combined fixture budget exceeded')
        data = json.loads(prompt.split('\n', 1)[1])
        output = {}
        for role in ('fundamental', 'news'):
            hits = data['evidence'][role]
            finding = {'claim': 'Synthetic company revenue changed during the quarter.', 'assessment': 'neutral',
                       'citation_chunk_ids': [hits[0]['chunk_id']]} if hits else None
            if finding and role == 'news':
                finding['interpretation'] = 'The cause is unknown; no investment implication is established.'
            output[role] = {'company': data['company'], 'status': 'success' if hits else 'insufficient_evidence',
                            'findings': [finding] if hits else [],
                            'limitations': ['Scripted synthetic finding, not actual company research.']}
        event = {'model': self.model_id, 'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
                 'prompt_characters': len(prompt), 'output_token_cap': max_output_tokens, 'usage': {},
                 'response_sha256': hashlib.sha256(json.dumps(output, sort_keys=True).encode()).hexdigest()}
        self.events.append(event)
        return output, event
