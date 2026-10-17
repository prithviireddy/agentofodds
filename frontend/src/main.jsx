import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import "../style.css";
import PaperLedger from "./PaperLedger.jsx";
import {
  Button,
  DataTable,
  Field,
  Metrics,
  Notice,
  SectionHeading,
  Timestamp,
  percent,
} from "./ui.jsx";

const readable = (value) => value.replaceAll("_", " ").replaceAll(":", " · "); 
const api = async (path, body) => {
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
  const value = await response.json();
  if (!response.ok) throw new Error(value.reason || value.status);
  return value;
};
const fields = [
  ["capital", "Capital (USD)"],
  ["min_asset_weight", "Minimum asset weight · fraction"],
  ["max_asset_weight", "Maximum asset weight · fraction"],
  ["min_cash_weight", "Minimum cash weight · fraction"],
  ["max_cash_weight", "Maximum cash weight · fraction"],
  ["max_evidence_age_days", "Maximum evidence age · days"],
  ["max_price_age_days", "Maximum price age · days"],
  ["min_return_observations", "Minimum return observations"],
  ["max_sample_volatility", "Maximum sample volatility · fraction"],
  ["min_candidates", "Minimum candidates"],
];

function App() {
  const [settings, setSettings] = useState();
  const [values, setValues] = useState({});
  const [run, setRun] = useState();
  const [runs, setRuns] = useState([]);
  const [selected, setSelected] = useState("");
  const [busy, setBusy] = useState(false);
  const paused = useRef(false);
  const active = useRef(false);
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const [opening, setOpening] = useState(false);
  const [formDirty, setFormDirty] = useState(false);
  useEffect(() => {
    if (!formDirty) return;
    const warn = (event) => {
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [formDirty]);
  useEffect(() => {
    if (error) document.getElementById("workspace-error")?.focus();
  }, [error]);
  const refresh = async () => setRuns(await api("/api/runs"));
  useEffect(() => {
    (async () => {
      try {
        const s = await api("/api/settings");
        setSettings(s);
        await refresh();
        const id = localStorage.getItem("agent-of-odds-run");
        if (id) setRun(await api("/api/runs/" + id));
      } catch (e) {
        setError(e.message);
      }
    })();
  }, []);
  const update = (key, value) => {
    setFormDirty(true);
    setValues((v) => ({ ...v, [key]: value }));
    setFieldErrors((previous) => ({ ...previous, [key]: "" }));
  };
  const payload = () => ({
    ...values,
    symbols: settings.companies
      .filter((c) => values.symbols?.includes(c.symbol))
      .map((c) => c.symbol),
    excluded_symbols: (values.excluded_symbols || "")
      .split(",")
      .map((x) => x.trim())
      .filter(Boolean),
    fundamental_assessments: (values.fundamental_assessments || "")
      .split(",")
      .map((x) => x.trim())
      .filter(Boolean),
    news_assessments: (values.news_assessments || "")
      .split(",")
      .map((x) => x.trim())
      .filter(Boolean),
    ...Object.fromEntries(
      [
        "max_evidence_age_days",
        "max_price_age_days",
        "min_return_observations",
        "max_sample_volatility",
        "min_candidates",
      ].map((k) => [k, Number(values[k])]),
    ),
  });
  const load = () => {
    setFormDirty(false);
    setFieldErrors({});
    setValues({
      ...settings.demo,
      excluded_symbols: settings.demo.excluded_symbols.join(", "),
      fundamental_assessments: settings.demo.fundamental_assessments.join(", "),
      news_assessments: settings.demo.news_assessments.join(", "),
    });
  };
  const render = (state) => {
    setRun(state);
    localStorage.setItem("agent-of-odds-run", state.run_id);
  };
  const advance = async (retry = false, initial = run) => {
    if (!initial || active.current) return;
    active.current = true;
    setBusy(true);
    paused.current = false;
    setError("");
    try {
      let state = initial;
      do {
        state = await api(`/api/runs/${state.run_id}/advance`, { retry });
        retry = false;
        render(state);
        await new Promise((resolve) => setTimeout(resolve, 60));
      } while (state.can_continue && !paused.current);
    } catch (e) {
      setError(e.message);
    } finally {
      active.current = false;
      setBusy(false);
      refresh().catch((e) => setError(e.message));
    }
  };
  const start = async (e) => {
    e.preventDefault();
    if (active.current) return;
    active.current = true;
    setBusy(true);
    setError("");
    try {
      const created = await api("/api/runs", payload());
      setFormDirty(false);
      const state = await api("/api/runs/" + created.run_id);
      render(state);
      active.current = false;
      await advance(false, state);
    } catch (e) {
      active.current = false;
      setError(e.message);
      setBusy(false);
    }
  };
  const download = () => {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(
      new Blob([JSON.stringify(run, null, 2)], { type: "application/json" }),
    );
    a.download = `agent-of-odds-${run.run_id}.json`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  };
  if (!settings)
    return (
      <main id="main-content" className="loading-workspace" aria-busy={!error}>
        {error ? (
          <>
            <Notice error id="workspace-error" title="Workspace unavailable">
              {error}. Reload to try the local connection again.
            </Notice>
            <Button onClick={() => window.location.reload()}>
              Reload workspace
            </Button>
          </>
        ) : (
          <>
            <p className="eyebrow">Agent of Odds</p>
            <h1>Opening your workspace.</h1>
            <p role="status">Loading local fixture workspace…</p>
          </>
        )}
      </main>
    );
  return (
    <>
      <a className="skip-link" href="#main-content">
        Skip to workspace
      </a>
      <header className="global-header">
        <div className="header-inner">
          <a className="brand" href="/">
            <span aria-hidden="true">◈</span> <span>AGENT OF ODDS</span>
          </a>
          <span className="mode-label">Local fixture mode</span>
        </div>
      </header>
      <nav className="workspace-nav" aria-label="Workspace sections">
        <div className="nav-inner">
          <span>Research workspace</span>
          <div>
            <a href="#configure">Configure</a>
            <a href="#review">Run & review</a>
            <a href="#saved-runs">Saved runs</a>
          </div>
        </div>
      </nav>
      <main id="main-content" tabIndex={-1}>
        <section className="intro">
          <div>
            <p className="eyebrow">Research with a record</p>
            <h1>
              Evidence first.
              <br />
              Allocation follows.
            </h1>
            <p className="sub">
              Explore a constrained research-to-portfolio workflow, with every
              finding and decision open to inspection.
            </p>
          </div>
          <aside className="fixture-note">
            <strong>A synthetic development sandbox</strong>
            <p>
              Prices, news, model findings and review decisions are invented
              fixtures. No external services or trades are used.
            </p>
            <div className="cutoff">
              <span>Fixed fixture cutoff</span>
              <Timestamp value={settings.as_of} />
            </div>
          </aside>
        </section>
        <div className="workspace-surface">
          <div className="workspace">
            <aside
              id="configure"
              className="panel controls"
              aria-labelledby="configure-title"
            >
              <h2 id="configure-title">Configure</h2>
              <p className="context-label">USD · Long-only</p>
              <p className="muted">
                Load editable demo values to begin. They are test inputs, not
                recommended investment settings.
              </p>
              <Button
                id="demo"
                type="button"
                className="secondary"
                onClick={load}
                disabled={busy || opening}
              >
                Load demo policy
              </Button>
              <form
                onSubmit={start}
                onInvalidCapture={(event) => {
                  const input = event.target;
                  const disclosure = input.closest("details");
                  if (disclosure) disclosure.open = true;
                  setFieldErrors((previous) => ({
                    ...previous,
                    [input.name]: input.validationMessage,
                  }));
                }}
              >
                <fieldset className="universe">
                  <legend>
                    Research universe · {settings.companies.length} fixture
                    companies
                  </legend>
                  <div className="company-options">
                    {settings.companies.map((c) => (
                      <label className="company-option" key={c.symbol}>
                        <input
                          name="symbols"
                          value={c.symbol}
                          type="checkbox"
                          checked={values.symbols?.includes(c.symbol) || false}
                          onChange={(e) =>
                            update(
                              "symbols",
                              e.target.checked
                                ? [...(values.symbols || []), c.symbol]
                                : (values.symbols || []).filter(
                                    (s) => s !== c.symbol,
                                  ),
                            )
                          }
                        />
                        <span translate="no">{c.symbol}</span>
                      </label>
                    ))}
                  </div>
                </fieldset>
                <div className="policy-fields">
                  {fields.slice(0, 5).map(([key, label]) => (
                    <Field
                      name={key}
                      label={label}
                      key={key}
                      error={fieldErrors[key]}
                    >
                      <input
                        required
                        type="number"
                        inputMode="decimal"
                        step="any"
                        min="0"
                        max={key === "capital" ? undefined : 1}
                        value={values[key] ?? ""}
                        onChange={(e) => update(key, e.target.value)}
                      />
                    </Field>
                  ))}
                </div>
                <Field name="review_frequency" label="Policy review schedule">
                  <select
                    value={values.review_frequency || "manual"}
                    onChange={(e) => update("review_frequency", e.target.value)}
                  >
                    <option>manual</option>
                    <option>monthly</option>
                  </select>
                </Field>
                <details>
                  <summary>Selection rules & freshness</summary>
                  <Field
                    name="excluded_symbols"
                    label="Excluded symbols · comma-separated"
                  >
                    <input
                      spellCheck={false}
                      value={values.excluded_symbols || ""}
                      onChange={(e) =>
                        update("excluded_symbols", e.target.value)
                      }
                    />
                  </Field>
                  <Field
                    name="fundamental_assessments"
                    label="Fundamental assessment allowlist"
                    error={fieldErrors.fundamental_assessments}
                  >
                    <input
                      required
                      value={values.fundamental_assessments || ""}
                      onChange={(e) =>
                        update("fundamental_assessments", e.target.value)
                      }
                    />
                  </Field>
                  <Field
                    name="news_assessments"
                    label="News assessment allowlist"
                    error={fieldErrors.news_assessments}
                  >
                    <input
                      required
                      value={values.news_assessments || ""}
                      onChange={(e) =>
                        update("news_assessments", e.target.value)
                      }
                    />
                  </Field>
                  {fields.slice(5).map(([key, label]) => (
                    <Field
                      name={key}
                      label={label}
                      key={key}
                      error={fieldErrors[key]}
                    >
                      <input
                        required
                        type="number"
                        inputMode={
                          key === "max_sample_volatility"
                            ? "decimal"
                            : "numeric"
                        }
                        step={key === "max_sample_volatility" ? "any" : "1"}
                        min="0"
                        value={values[key] ?? ""}
                        onChange={(e) => update(key, e.target.value)}
                      />
                    </Field>
                  ))}
                  <p className="muted">
                    Volatility is a fraction per observed interval, not
                    annualised.
                  </p>
                </details>
                <Field name="scenario" label="Fixture scenario">
                  <select
                    name="scenario"
                    value={values.scenario || "normal"}
                    onChange={(e) => update("scenario", e.target.value)}
                  >
                    <option value="normal">Complete workflow</option>
                    <option value="missing_evidence">Missing evidence</option>
                    <option value="quota">Quota interruption</option>
                    <option value="review_rejected">Rejected review</option>
                  </select>
                </Field>
                <details>
                  <summary>Execution limits</summary>
                  <p className="muted">
                    Sequential execution · {settings.budget.max_model_calls}{" "}
                    model calls · {settings.budget.max_reserved_output_tokens}{" "}
                    reserved output tokens ·{" "}
                    {settings.budget.max_retrieval_queries} retrieval queries ·{" "}
                    {settings.budget.max_retries_per_step} explicit retry per
                    stage · {settings.budget.max_review_rounds} critic round ·{" "}
                    {settings.budget.max_critic_prompt_characters} critic
                    characters maximum. All generation is scripted locally.
                  </p>
                </details>
                <Button
                  id="start"
                  type="submit"
                  disabled={busy || opening}
                  busy={busy}
                >
                  Run fixture research
                </Button>
                <p className="form-hint" role="status">
                  {busy
                    ? "Saving each stage. You can pause from Run & review."
                    : "New settings apply only to a new run."}
                </p>
              </form>
              <div id="saved-runs" className="saved">
                <h3>Saved runs</h3>
                <Field name="saved_run" label="Saved local run">
                  <select
                    value={selected}
                    onChange={(e) => setSelected(e.target.value)}
                  >
                    <option value="">Choose a run</option>
                    {runs.map((r) => (
                      <option key={r.run_id} value={r.run_id}>
                        {r.run_id.slice(0, 8)} · {r.status}
                      </option>
                    ))}
                  </select>
                </Field>
                {runs.length === 0 && (
                  <p className="muted">
                    No saved runs yet. Your first run will be recorded here.
                  </p>
                )}
                <Button
                  className="secondary"
                  busy={opening}
                  onClick={async () => {
                    if (!selected) return;
                    setOpening(true);
                    try {
                      render(await api("/api/runs/" + selected));
                    } catch (e) {
                      setError(e.message);
                    } finally {
                      setOpening(false);
                    }
                  }}
                  disabled={busy || opening || !selected}
                >
                  Open saved run
                </Button>
              </div>
            </aside>
            <Results
              run={run}
              error={error}
              busy={busy}
              pause={() => {
                paused.current = true;
              }}
              advance={advance}
              download={download}
            />
          </div>
        </div>
      </main>
      <footer className="site-footer">
        <div className="footer-inner">
          <span>AGENT OF ODDS</span>
          <span>Local evidence. Explicit constraints. No real trades.</span>
        </div>
      </footer>
    </>
  );
}

function Results({ run, error, busy, pause, advance, download }) {
  if (!run)
    return (
      <section id="review" className="results" aria-label="Run results">
        {error && (
          <Notice
            error
            id="workspace-error"
            title="Unable to complete the request"
          >
            {error}. Check your settings or retry the local request.
          </Notice>
        )}
        <article className="panel empty-workspace">
          <SectionHeading title="Run & review" />
          <div className="empty-intro">
            <h3>Your research starts here.</h3>
            <p className="empty">
              Your first run will appear here. A proposal is shown only after
              the workflow and reviews succeed.
            </p>
          </div>
          <ol className="workflow-outline">
            <li>
              <strong>Set your policy</strong>
              <p>
                Choose the companies and explicit constraints for this fixture
                run.
              </p>
            </li>
            <li>
              <strong>Inspect the research</strong>
              <p>Review findings, cited passages and the independent checks.</p>
            </li>
            <li>
              <strong>Approve paper tracking</strong>
              <p>
                A successful proposal can open a synthetic portfolio for saved
                price replay.
              </p>
            </li>
          </ol>
          <p className="muted">
            Nothing runs until you select Run fixture research.
          </p>
        </article>
      </section>
    );
  const u = run.usage || {};
  return (
    <section id="review" className="results" aria-label="Run results">
      {error && (
        <Notice
          error
          id="workspace-error"
          title="Unable to complete the request"
        >
          {error}. Check your settings or retry the local request.
        </Notice>
      )}
      <article className="panel run-overview" aria-busy={busy}>
        <SectionHeading title="Run & review">
          <span
            id="status"
            className={`tag ${run.status === "success" ? "tag-success" : ""}`}
            role="status"
          >
            {readable(run.status).toUpperCase()}
          </span>
        </SectionHeading>
        <p className="run-meta">
          Run {run.run_id.slice(0, 8)} · {run.progress.completed}/
          {run.progress.total} stages saved. {run.reason}
        </p>
        <progress
          aria-label="Completed workflow stages"
          max={run.progress.total || 1}
          value={run.progress.completed}
        />
        <div className="actions">
          {busy && run.can_continue && (
            <Button className="secondary" onClick={pause}>
              Pause after this stage
            </Button>
          )}
          {!busy && run.can_continue && (
            <Button onClick={() => advance()}>Continue saved run</Button>
          )}
          {!busy && run.can_retry && (
            <Button onClick={() => advance(true)}>Retry failed stage</Button>
          )}
          <Button className="secondary" onClick={download}>
            Download report JSON
          </Button>
        </div>
        <Metrics
          items={[
            [u.model_calls_reserved || 0, "Fixture model calls reserved"],
            [
              u.calls_with_unknown_total_usage || 0,
              "Calls with unknown token usage",
            ],
            [u.output_tokens_reserved || 0, "Output tokens reserved"],
          ]}
        />
        <p className="muted">
          Reported tokens (known fields only):{" "}
          {u.reported_token_totals?.totalTokenCount ?? 0}. Cost: unknown. No
          external service is called.
        </p>
        <details>
          <summary>Stage history</summary>
          <DataTable
            caption="Saved workflow stage history"
            numeric={[1]}
            headers={["Stage", "Attempt", "Outcome"]}
            rows={run.history.map((h) => [h.step, h.attempt, h.status])}
          />
        </details>
      </article>
      <article id="allocation" className="panel">
        <SectionHeading title="Reviewed proposal" />
        {run.status === "success" && run.allocation ? (
          <>
            <p className="muted">
              Reviewed synthetic allocation · paper approval is recorded below.
            </p>
            <DataTable
              caption="Reviewed synthetic allocation"
              numeric={[1]}
              headers={["Asset", "Weight"]}
              rows={[
                ...Object.entries(run.allocation.weights).map(([s, w]) => [
                  s,
                  percent(w),
                ]),
                ["Cash", percent(run.allocation.cash_weight)],
              ]}
            />
          </>
        ) : (
          <p className="empty">
            No reviewed proposal. Allocation remains hidden until the complete
            workflow succeeds.
          </p>
        )}
        <div className="review-checks">
          <p className="muted">
            Numerical review: {run.review?.status || "pending"} ·{" "}
            {run.review?.objective_limitation || run.review?.reason || ""}
          </p>
          <p className="muted">
            Evidence review: {run.critic?.review?.verdict || "pending"} ·{" "}
            {run.critic?.review?.rationale || ""}
          </p>
        </div>
      </article>
      <article className="panel">
        <SectionHeading title="Selection & evidence" />
        {run.selection && (
          <DataTable
            caption="Company eligibility decisions and reasons"
            headers={["Company", "Decision", "Reason"]}
            rows={run.selection.decisions.map((d) => [
              d.symbol,
              d.eligible ? "Eligible" : "Excluded",
              d.reasons.map(readable).join("; "),
            ])}
          />
        )}
        {!run.selection && (
          <p className="empty">
            Selection will appear after the research stages complete.
          </p>
        )}
        {run.selection && (
          <p className="muted">{run.selection.limitations.join(" ")}</p>
        )}
        <div id="reports">
          <Reports reports={run.reports} />
        </div>
      </article>
      {run.status === "success" && <PaperLedger key={run.run_id} run={run} />}
      <article className="panel">
        <SectionHeading title="Run settings & limitations" />
        {run.limitations.map((x) => (
          <p className="muted" key={x}>
            {x}
          </p>
        ))}
        <details>
          <summary>Saved policy & numerical provenance</summary>
          <pre>
            {JSON.stringify(
              {
                as_of: run.as_of,
                policy: run.policy,
                budget: run.budget,
                quantitative: run.quantitative,
                fingerprint: run.fingerprint,
              },
              null,
              2,
            )}
          </pre>
        </details>
      </article>
    </section>
  );
}
function Reports({ reports }) {
  if (!Object.keys(reports || {}).length)
    return (
      <p className="empty">
        Cited reports will appear here as research is saved.
      </p>
    );
  return (
    <>
      {Object.entries(reports || {}).map(([key, report]) => {
        const hits = Object.fromEntries(
          report.evidence.map((h) => [h.chunk_id, h]),
        );
        return (
          <details className="company" key={key}>
            <summary>
              <span translate="no">{key.replace(":", " / ")}</span>
              <span className="report-status">{readable(report.status)}</span>
            </summary>
            {report.findings.map((f, i) => (
              <div className="finding" key={i}>
                <small>{f.assessment.toUpperCase()}</small>
                <p>{f.claim}</p>
                {f.interpretation && (
                  <p className="muted">Interpretation: {f.interpretation}</p>
                )}
                {f.citation_chunk_ids.map(
                  (id) =>
                    hits[id] && (
                      <details key={id}>
                        <summary>
                          Cited passage ·{" "}
                          <Timestamp value={hits[id].published_at} />
                        </summary>
                        <blockquote>{hits[id].text}</blockquote>
                        <pre>
                          Source: {hits[id].source_id}
                          {"\n"}Chunk: {id}
                          {"\n"}Version: {hits[id].source_sha256}
                        </pre>
                      </details>
                    ),
                )}
              </div>
            ))}
            <p className="muted">{report.limitations.join(" ")}</p>
          </details>
        );
      })}
    </>
  );
}
createRoot(document.getElementById("root")).render(<App />);
