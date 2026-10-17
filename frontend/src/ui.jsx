import React from "react";

// Small presentation primitives. Domain values and API payloads remain untouched.
export function Button({ children, busy = false, className = "", ...props }) {
  return (
    <button
      type="button"
      className={className}
      aria-busy={busy || undefined}
      {...props}
    >
      {busy && <span className="spinner" aria-hidden="true" />}
      {children}
    </button>
  );
}

export function SectionHeading({ title, children, level = 2 }) {
  const Heading = `h${level}`;
  return (
    <div className="section-head">
      <Heading>{title}</Heading>
      {children}
    </div>
  );
}

export function Notice({ children, title, error = false, id }) {
  return (
    <div
      id={id}
      className={`notice-message${error ? " error" : ""}`}
      role={error ? "alert" : "status"}
      tabIndex={error ? -1 : undefined}
    >
      {title && <strong>{title}</strong>}
      <div>{children}</div>
    </div>
  );
}

export function Metrics({ items }) {
  return (
    <dl className="metrics">
      {items.map(([value, label]) => (
        <div className="metric" key={label}>
          <dt>{label}</dt>
          <dd>
            {typeof value === "number"
              ? new Intl.NumberFormat("en-US").format(value)
              : value}
          </dd>
        </div>
      ))}
    </dl>
  );
}

export function DataTable({ headers, rows, caption, numeric = [] }) {
  if (!rows.length) return <p className="empty">No entries recorded yet.</p>;
  return (
    <div
      className="table-scroll"
      role="region"
      aria-label={caption}
      tabIndex={0}
    >
      <table>
        <caption className="sr-only">{caption}</caption>
        <thead>
          <tr>
            {headers.map((h, i) => (
              <th
                scope="col"
                key={h}
                className={numeric.includes(i) ? "numeric" : undefined}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {row.map((value, j) => (
                <td
                  key={j}
                  className={numeric.includes(j) ? "numeric" : undefined}
                >
                  {value}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Field({ label, name, error, children }) {
  return (
    <div className="field">
      <label htmlFor={`field-${name}`}>{label}</label>
      {React.cloneElement(children, {
        id: `field-${name}`,
        name,
        autoComplete: "off",
        "aria-invalid": error ? true : undefined,
        "aria-describedby": error ? `error-${name}` : undefined,
      })}
      {error && (
        <p id={`error-${name}`} className="field-error">
          {error}
        </p>
      )}
    </div>
  );
}

export function dateLabel(value) {
  if (!value) return "Not recorded by this older run";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
    timeZoneName: "short",
  }).format(date);
}

export function Timestamp({ value }) {
  if (!value) return <span>{dateLabel(value)}</span>;
  return (
    <time dateTime={value} title={value}>
      {dateLabel(value)}
    </time>
  );
}

export const money = (value) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(value));

export const percent = (fraction) =>
  new Intl.NumberFormat("en-US", {
    style: "percent",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(fraction));
