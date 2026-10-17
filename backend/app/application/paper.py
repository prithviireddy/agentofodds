"""Approval binding and atomic exactly-once opening books for reviewed fixture runs."""
from dataclasses import asdict, replace
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3

from backend.app.contracts.market_data import timestamp
from backend.app.domain.paper import PaperError, opening_plan, reconcile, display
from backend.app.workflows.checkpoint import canonical
from backend.app.workflows.review import review_allocation


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


class PaperService:
    def __init__(self, demo, fill_path):
        self.demo = demo
        self.fill_path = Path(fill_path)
        self.database = demo.directory / "paper_ledger.sqlite3"

    def preview(self, run_id):
        manifest = self.demo._manifest(run_id)
        state = self.demo.store.load(run_id)
        if not state or state["status"] != "success" or state.get("in_flight"):
            raise PaperError("not_reviewed", "Complete research and both reviews before paper approval")
        results = state["results"]
        critiques = [value for key, value in results.items() if key.startswith("critic:")]
        if (not critiques or critiques[-1]["review"]["verdict"] != "approved" or
                results["review"]["status"] != "success" or results["selection"].status != "success"):
            raise PaperError("not_reviewed", "A successful numerical and evidence review is required")
        inputs = self.demo.inputs(manifest["values"])
        if (asdict(inputs["investment"]) != state["configuration"]["investment"] or
                asdict(inputs["selection_policy"]) != state["configuration"]["selection"]):
            raise PaperError("proposal_changed", "Saved policy differs from the reviewed policy")
        policy = replace(inputs["investment"], symbols=results["selection"].candidates)
        allocation = results["allocation"]
        if review_allocation(policy, allocation, results["allocation_statistics"].covariance)["status"] != "success":
            raise PaperError("not_reviewed", "Saved allocation no longer reconciles with its review")
        raw = self.fill_path.read_bytes()
        fill = json.loads(raw)
        if fill["schema_version"] != 1:
            raise PaperError("failed_validation", "Unsupported fill fixture")
        execution = timestamp(fill["execution_at"])
        quotes = {s: {"price": fill["prices"][s], "at": execution.isoformat(), "source_id": f"fixture:paper:{s}"}
                  for s in policy.symbols if s in fill["prices"]}
        plan = opening_plan(policy, allocation, execution_at=execution, quotes=quotes,
                            fee_bps=fill["fee_bps"], corporate_actions=fill["corporate_actions"])
        binding = {"version": 1, "run_id": run_id, "workflow_fingerprint": state["fingerprint"],
                   "run_created_at": manifest.get("created_at"), "research_as_of": policy.as_of.isoformat(),
                   "research_fixture_sha256": manifest["fixture_hash"], "policy": manifest["values"],
                   "selection_sha256": results["selection"].input_sha256,
                   "fill_fixture_sha256": hashlib.sha256(raw).hexdigest(),
                   "allocation": {"weights": {s: str(w) for s, w in allocation.weights.items()},
                                  "cash_weight": str(allocation.cash_weight)}, "plan": plan}
        return {"status": "preview", "proposal_id": digest(binding), "binding": binding,
                "summary": summary(plan), "limitations": [fill["label"],
                    "Approval time is recorded now; the fill date is a separate historical simulation time.",
                    "One opening portfolio per run; no rebalancing, dividends, splits, withdrawals or real orders.",
                    "Shares and USD are stored as exact fractions; displayed amounts are rounded only for readability."]}

    def get(self, run_id):
        self.demo.store.path(run_id)
        if not self.database.exists():
            return None
        with closing(sqlite3.connect(self.database)) as connection:
            if not connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='approvals'").fetchone():
                return None
            row = connection.execute("SELECT payload, sha256 FROM approvals WHERE run_id = ?", (run_id,)).fetchone()
        if row is None:
            return None
        receipt = json.loads(row[0])
        if digest(receipt) != row[1] or receipt["run_id"] != run_id:
            raise PaperError("failed_reconciliation", "Stored approval checksum or identity mismatch")
        balances = reconcile(receipt["binding"]["plan"]["journal"])
        if balances != receipt["binding"]["plan"]["balances"] or digest(receipt["binding"]) != receipt["proposal_id"]:
            raise PaperError("failed_reconciliation", "Stored ledger or approval binding does not reconcile")
        return receipt

    def approve(self, run_id, proposal_id, approved):
        if approved is not True or not isinstance(proposal_id, str):
            raise PaperError("approval_required", "Explicit approval of the preview is required")
        # Serialize against workflow mutation, and make receipt/journal one SQLite transaction.
        with self.demo.store.locked(run_id):
            existing = self.get(run_id)
            if existing:
                if existing["proposal_id"] != proposal_id:
                    raise PaperError("approval_conflict", "This run already has a different approved paper portfolio")
                return existing
            preview = self.preview(run_id)
            if proposal_id != preview["proposal_id"]:
                raise PaperError("proposal_changed", "Preview changed; inspect the updated proposal before approving")
            receipt = {"status": "approved", "run_id": run_id, "proposal_id": proposal_id,
                       "approved_at": datetime.now(timezone.utc).isoformat(),
                       "approval_method": "explicit_local_user_action", "binding": preview["binding"],
                       "summary": preview["summary"], "limitations": preview["limitations"]}
            self.database.parent.mkdir(parents=True, exist_ok=True)
            with closing(sqlite3.connect(self.database)) as connection, connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute("CREATE TABLE IF NOT EXISTS approvals (run_id TEXT PRIMARY KEY, proposal_id TEXT NOT NULL UNIQUE, payload TEXT NOT NULL, sha256 TEXT NOT NULL)")
                connection.execute("INSERT INTO approvals VALUES (?, ?, ?, ?)",
                                   (run_id, proposal_id, canonical(receipt), digest(receipt)))
            return receipt


def summary(plan):
    balances = plan["balances"]
    prices = {e["symbol"]: e["price"] for e in plan["journal"] if e["kind"] == "buy"}
    return {"capital_usd": display(balances["capital"]), "cash_usd": display(balances["cash"]),
            "fees_usd": display(balances["fees"]), "equity_at_fill_usd": display(balances["equity_at_fill"]),
            "reconciliation_difference": balances["difference"], "journal_entries": len(plan["journal"]),
            "holdings": [{"symbol": s, "quantity_display": display(h["quantity"], 8),
                          "quantity_exact": h["quantity"], "price_usd": display(prices[s]),
                          "cost_usd": display(h["cost"])} for s, h in balances["holdings"].items()]}
