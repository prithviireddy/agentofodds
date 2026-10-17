"""Bounded, separate synthetic prices for manual paper valuation."""
import hashlib
import json
from pathlib import Path

from backend.app.domain.paper import PaperError


class ValuationFixture:
    def __init__(self, path):
        self.path = Path(path)

    def load(self):
        raw = self.path.read_bytes()
        if len(raw) > 100_000:
            raise PaperError('failed_validation', 'Valuation fixture exceeds size bound')
        payload = json.loads(raw)
        if payload['schema_version'] != 1 or not 1 <= len(payload['frames']) <= 30:
            raise PaperError('failed_validation', 'Unsupported valuation fixture')
        dates = [f['valuation_at'] for f in payload['frames']]
        if len(set(dates)) != len(dates):
            raise PaperError('failed_validation', 'Duplicate fixture dates')
        return payload, hashlib.sha256(raw).hexdigest()

    def dates(self):
        return [f['valuation_at'] for f in self.load()[0]['frames']]

    def prices(self, at, symbols):
        payload, checksum = self.load()
        frame = next((f for f in payload['frames'] if f['valuation_at'] == at), None)
        if frame is None:
            raise PaperError('missing_prices', 'No fixture for the requested valuation date')
        return {'valuation_at': at, 'max_price_age_days': payload['max_price_age_days'],
                'currency': payload['currency'], 'adjustment': payload['adjustment'],
                'corporate_actions': frame['corporate_actions'],
                'prices': [row for row in frame['prices'] if row['symbol'] in symbols],
                'source_sha256': checksum, 'label': payload['label']}
