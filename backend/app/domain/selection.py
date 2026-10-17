"""Explicit eligibility rules, independent of models and data providers."""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class SelectionPolicy:
    policy_id: str
    version: int
    excluded_symbols: tuple[str, ...]
    fundamental_assessments: tuple[str, ...]
    news_assessments: tuple[str, ...]
    max_evidence_age_days: int
    max_price_age_days: int
    min_return_observations: int
    max_sample_volatility: float
    min_candidates: int

    def validate(self, universe):
        if not self.policy_id.strip() or self.version != 1:
            raise ValueError("Invalid selection policy identity/version")
        if len(set(self.excluded_symbols)) != len(self.excluded_symbols) or not set(self.excluded_symbols) <= set(universe):
            raise ValueError("Exclusions must be unique universe members")
        for values in (self.fundamental_assessments, self.news_assessments):
            if not values or len(set(values)) != len(values) or not set(values) <= {"positive", "negative", "mixed", "neutral"}:
                raise ValueError("Assessment allowlists must be explicit, nonempty and valid")
        for value in (self.max_evidence_age_days, self.max_price_age_days):
            if type(value) is not int or value < 0:
                raise ValueError("Freshness limits must be nonnegative calendar days")
        if type(self.min_return_observations) is not int or self.min_return_observations < 2:
            raise ValueError("At least two return observations are required")
        if type(self.min_candidates) is not int or not 1 <= self.min_candidates <= len(universe):
            raise ValueError("Invalid minimum candidate count")
        if isinstance(self.max_sample_volatility, bool) or not math.isfinite(self.max_sample_volatility) or self.max_sample_volatility < 0:
            raise ValueError("Volatility ceiling must be finite and nonnegative")
        return self
