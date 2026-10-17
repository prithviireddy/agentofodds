import React, { useEffect, useState } from "react";
import "./paper.css";
import Monitoring from "./Monitoring.jsx";
import {
  Button,
  DataTable,
  Metrics,
  Notice,
  SectionHeading,
  Timestamp,
  money,
} from "./ui.jsx";

async function request(path, body) {
  const response = await fetch(
    path,
    body === undefined
      ? {}
      : {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        },
  );
  const result = await response.json();
  if (!response.ok)
    throw new Error(`${result.status}: ${result.reason || "Request failed"}`);
  return result;
}

export default function PaperLedger({ run }) {
  const [paper, setPaper] = useState(null);
  const [accepted, setAccepted] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const path = `/api/runs/${run.run_id}`;
  useEffect(() => {
    let alive = true;
    request(path + "/paper")
      .then((value) => {
        if (alive) setPaper(value);
      })
      .catch((e) => {
        if (alive) setError(e.message);
      });
    return () => {
      alive = false;
    };
  }, [path]);
  async function approve() {
    if (!accepted || busy || !paper) return;
    setBusy(true);
    setError("");
    try {
      setPaper(
        await request(path + "/approve-paper", {
          approved: true,
          proposal_id: paper.proposal_id,
        }),
      );
      setAccepted(false);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <article className="panel" data-testid="paper-ledger">
      <SectionHeading title="Paper portfolio">
        <span className="tag">Synthetic replay</span>
      </SectionHeading>
      {error && (
        <Notice error title="Paper approval unavailable">
          {error}. Reload to check whether approval was recorded before trying
          again.
        </Notice>
      )}
      {!paper && !error && (
        <p className="muted" role="status">
          Preparing the opening ledger preview…
        </p>
      )}
      {paper && (
        <>
          <p>
            {paper.status === "approved"
              ? "Paper portfolio approved and recorded."
              : "Review this opening portfolio before approving paper tracking."}
          </p>
          <p className="muted">
            Simulated fill:{" "}
            <Timestamp value={paper.binding.plan.execution_at} />. This is a
            historical fixture replay; approval is recorded at the current time.
          </p>
          <Metrics
            items={[
              [money(paper.summary.cash_usd), "Cash after fills"],
              [
                money(paper.summary.fees_usd),
                `Fees (${paper.binding.plan.fee_bps} bps)`,
              ],
              [
                money(paper.summary.equity_at_fill_usd),
                "Equity at synthetic fill",
              ],
            ]}
          />
          <DataTable
            caption="Opening paper portfolio holdings"
            headers={[
              "Asset",
              "Fractional shares",
              "Fill price",
              "Position cost",
            ]}
            numeric={[1, 2, 3]}
            rows={paper.summary.holdings.map((h) => [
              <span translate="no">{h.symbol}</span>,
              <span title={h.quantity_exact}>{h.quantity_display}</span>,
              money(h.price_usd),
              money(h.cost_usd),
            ])}
          />
          <p className="reconciliation">
            Funding: {money(paper.summary.capital_usd)}.{" "}
            {paper.summary.journal_entries} entries. Exact reconciliation
            difference: {paper.summary.reconciliation_difference} USD.
          </p>
          <div className="limitations">
            {paper.limitations.map((text) => (
              <p key={text} className="muted">
                {text}
              </p>
            ))}
          </div>
          {paper.status === "approved" ? (
            <div
              data-testid="paper-approved"
              className="approval-record"
              role="status"
            >
              <strong>Paper approval recorded</strong>
              <p>
                <Timestamp value={paper.approved_at} />
              </p>
            </div>
          ) : (
            <div className="approval-actions">
              <label className="approval-consent">
                <input
                  type="checkbox"
                  name="paper_consent"
                  checked={accepted}
                  onChange={(e) => setAccepted(e.target.checked)}
                />
                I approve this exact synthetic replay and its stated fill and
                fee conventions.
              </label>
              <Button
                disabled={!accepted || busy}
                busy={busy}
                onClick={approve}
              >
                Approve paper portfolio
              </Button>
              <p className="form-hint" role="status">
                {busy
                  ? "Recording this paper approval…"
                  : "Approval opens a local synthetic book. It places no real orders."}
              </p>
            </div>
          )}
          <details>
            <summary>Approval identity & exact journal</summary>
            <pre>
              {JSON.stringify(
                {
                  proposal_id: paper.proposal_id,
                  run_id: run.run_id,
                  approved_at: paper.approved_at,
                  workflow_fingerprint: paper.binding.workflow_fingerprint,
                  conventions: paper.binding.plan.conventions,
                  journal: paper.binding.plan.journal,
                },
                null,
                2,
              )}
            </pre>
          </details>
          {paper.status === "approved" && (
            <Monitoring key={run.run_id} runId={run.run_id} />
          )}
        </>
      )}
    </article>
  );
}
