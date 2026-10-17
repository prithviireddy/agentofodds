import React, { useEffect, useState } from "react";
import {
  Button,
  DataTable,
  Field,
  Metrics,
  Notice,
  SectionHeading,
  Timestamp,
  money,
  dateLabel,
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

export default function Monitoring({ runId }) {
  const [data, setData] = useState(null);
  const [date, setDate] = useState("");
  const [selected, setSelected] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const path = `/api/runs/${runId}/valuations`;
  useEffect(() => {
    let alive = true;
    request(path)
      .then((value) => {
        if (!alive) return;
        setData(value);
        setDate(value.available_dates[0] || "");
        setSelected(value.history.at(-1)?.inputs.valuation_at || "");
      })
      .catch((e) => {
        if (alive) setError(e.message);
      });
    return () => {
      alive = false;
    };
  }, [path]);
  async function update() {
    setBusy(true);
    setError("");
    try {
      const snapshot = await request(path, { valuation_at: date });
      setData(await request(path));
      setSelected(snapshot.inputs.valuation_at);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  const snapshot = data?.history.find(
    (s) => s.inputs.valuation_at === selected,
  );
  return (
    <section data-testid="monitoring">
      <SectionHeading title="Historical price replay" level={3} />
      <p className="context-label">Synthetic replay · No fresh research</p>
      {error && (
        <Notice error title="Valuation unavailable">
          {error}. Check the selected fixture date or reload the saved history.
        </Notice>
      )}
      {!data && !error && <p role="status">Loading saved valuations…</p>}
      {data && (
        <>
          <dl className="timeline">
            {[
              ["Original research cutoff", data.research_as_of],
              ["Run created", data.run_created_at],
              ["Historical fill", data.fill_at],
              ["Approval recorded", data.approved_at],
            ].map(([label, value]) => (
              <div key={label}>
                <dt>{label}</dt>
                <dd>
                  <Timestamp value={value} />
                </dd>
              </div>
            ))}
          </dl>
          <div className="limitations">
            {data.limitations.map((text) => (
              <p className="muted" key={text}>
                {text}
              </p>
            ))}
          </div>
          {data.price_error && (
            <Notice error title="Fixture prices unavailable">
              {data.price_error}
            </Notice>
          )}
          <div className="valuation-controls">
            <Field name="valuation_date" label="Fixture valuation date">
              <select
                aria-label="Fixture valuation date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                disabled={busy || !data.available_dates.length}
              >
                {data.available_dates.map((value) => (
                  <option key={value} value={value}>
                    {dateLabel(value)}
                  </option>
                ))}
              </select>
            </Field>
            <Button disabled={busy || !date} busy={busy} onClick={update}>
              Update prices only
            </Button>
          </div>
          <p className="muted" role="status">
            {busy
              ? "Saving the numerical valuation…"
              : `${data.history.length} saved valuations. Updating a saved date replays its original prices.`}
          </p>
          {!data.history.length && (
            <p className="empty">
              No saved valuations yet. Choose a fixture date to start price-only
              tracking.
            </p>
          )}
          {data.history.length > 0 && (
            <Field name="replay_date" label="Replay saved valuation">
              <select
                aria-label="Replay saved valuation"
                value={selected}
                onChange={(e) => setSelected(e.target.value)}
              >
                {data.history.map((s) => (
                  <option
                    key={s.inputs.valuation_at}
                    value={s.inputs.valuation_at}
                  >
                    {dateLabel(s.inputs.valuation_at)}
                  </option>
                ))}
              </select>
            </Field>
          )}
          {snapshot && (
            <div data-testid="valuation-result">
              <h4>
                Valuation as of{" "}
                <Timestamp value={snapshot.inputs.valuation_at} />
              </h4>
              <p className="muted">
                Recorded at <Timestamp value={snapshot.recorded_at} />.{" "}
                {snapshot.inputs.label}
              </p>
              <Metrics
                items={[
                  [
                    money(snapshot.result.summary.equity_usd),
                    "Equity at replay date",
                  ],
                  [money(snapshot.result.summary.pnl_usd), "P/L since funding"],
                  [
                    snapshot.result.summary.return_percent + "%",
                    "Return since funding",
                  ],
                ]}
              />
              <p>Unchanged cash: {money(snapshot.result.summary.cash_usd)}</p>
              <DataTable
                caption="Saved valuation market values"
                headers={["Asset", "Market value (USD)"]}
                numeric={[1]}
                rows={Object.entries(snapshot.result.summary.positions).map(
                  ([s, v]) => [<span translate="no">{s}</span>, money(v)],
                )}
              />
              <details>
                <summary>Archived prices & exact valuation</summary>
                <pre>{JSON.stringify(snapshot, null, 2)}</pre>
              </details>
            </div>
          )}
        </>
      )}
    </section>
  );
}
