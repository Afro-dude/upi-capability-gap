import React, { useEffect, useState, useRef } from "react";
import {
  Activity,
  ArrowUpRight,
  ArrowRight,
  LayoutDashboard,
  SlidersHorizontal,
  ChartScatter,
  Calculator,
  BookOpen,
  Bookmark,
  Download,
  Info,
  Check,
  ChevronRight,
  Globe,
  Database,
  Menu,
  X,
  Trash2,
  Search,
  RefreshCw,
} from "lucide-react";
import {
  gql,
  analysisQuery,
  savedQuery,
  download,
  pct,
  number,
  crore,
} from "./api.js";

const defaults = { state: "All", sector: "All", sex: "All", age: "All" };
const pages = [
  ["overview", "Overview", LayoutDashboard],
  ["explore", "Capability explorer", SlidersHorizontal],
  ["transactions", "NPCI transactions", ChartScatter],
  ["scenario", "What-if calculator", Calculator],
  ["methods", "Methods & sources", BookOpen],
  ["saved", "Saved comparisons", Bookmark],
];
function useRequest(query, variables) {
  const [state, setState] = useState({
    loading: true,
    data: null,
    error: null,
  });
  const key = JSON.stringify(variables);
  useEffect(() => {
    const controller = new AbortController();
    setState({ loading: true, data: null, error: null });
    gql(query, JSON.parse(key), controller.signal)
      .then((data) => setState({ loading: false, data, error: null }))
      .catch((e) => {
        if (e.name !== "AbortError")
          setState({ loading: false, data: null, error: e.message });
      });
    return () => controller.abort();
  }, [query, key]);
  return state;
}
function Loading() {
  return (
    <div className="loading" role="status">
      <Activity size={24} />
      <span>Loading the evidence…</span>
    </div>
  );
}
function ErrorBox({ message }) {
  return (
    <div className="error" role="alert">
      <Info size={19} />
      {message}
      <button onClick={() => location.reload()}>Retry</button>
    </div>
  );
}
function Notice({ children, warm = false }) {
  return (
    <div className={`notice ${warm ? "warm" : ""}`}>
      <Info size={17} />
      <div>{children}</div>
    </div>
  );
}
function Panel({ title, eyebrow, children, action, className = "" }) {
  return (
    <section className={`panel ${className}`}>
      <header className="panel-head">
        <div>
          {eyebrow && <p className="eyebrow">{eyebrow}</p>}
          <h2>{title}</h2>
        </div>
        {action}
      </header>
      {children}
    </section>
  );
}
function Metric({ label, value, unit, detail, accent = false }) {
  return (
    <article className={`metric ${accent ? "accent" : ""}`}>
      <p>{label}</p>
      <div className="metric-value">
        {value}
        <span>{unit}</span>
      </div>
      <div className="metric-detail">{detail}</div>
    </article>
  );
}
function Heading({ kicker, title, description, children }) {
  return (
    <div className="heading">
      <div>
        <p className="eyebrow">{kicker}</p>
        <h1>{title}</h1>
        <p className="lede">{description}</p>
      </div>
      {children}
    </div>
  );
}
function Bars({ items }) {
  return (
    <div className="bars">
      {items.map((item, i) => (
        <div className="bar-row" key={item.label}>
          <div className="bar-label">{item.label}</div>
          <div className="bar-track">
            <div
              className={`bar-fill ${i === items.length - 1 ? "emphasis" : ""}`}
              style={{
                width: `${Math.max(0, Math.min(100, item.share * 100))}%`,
              }}
            />
          </div>
          <strong>{pct(item.share)}</strong>
        </div>
      ))}
    </div>
  );
}
function Filters({ data, value, setValue, state = true }) {
  const fields = [
    ...(state
      ? [["state", "State / UT", data.states.map((s) => s.state)]]
      : []),
    ["sector", "Sector", ["Rural", "Urban"]],
    ["sex", "Sex", ["Female", "Male", "Transgender"]],
    ["age", "Age group", ["15-24", "25-34", "35-44", "45-59", "60+"]],
  ];
  return (
    <div className="filters">
      {fields.map(([key, label, options]) => (
        <label key={key}>
          {label}
          <select
            value={value[key]}
            onChange={(e) => setValue({ ...value, [key]: e.target.value })}
          >
            <option value="All">
              All{" "}
              {key === "state"
                ? "states & UTs"
                : key === "age"
                  ? "ages 15+"
                  : key === "sex"
                    ? "recorded categories"
                    : "sectors"}
            </option>
            {options.map((o) => (
              <option key={o}>{o}</option>
            ))}
          </select>
        </label>
      ))}
      <button className="reset" onClick={() => setValue(defaults)}>
        <RefreshCw size={15} /> Reset
      </button>
    </div>
  );
}

function Overview({ dataset, navigate }) {
  const d = dataset.payload,
    n = d.national[0],
    c = d.conditional[0];
  const labels = [
    "Can operate a phone or computer",
    "Access to a mobile phone · past 3 months",
    "Used a smartphone · past 3 months",
    "Able to use the internet",
    "Used the internet · past 3 months",
    "Able to transact online",
    "Able to transact via UPI",
  ];
  return (
    <>
      <Heading
        kicker="THE CAPABILITY PICTURE"
        title="India’s UPI capability gap"
        description="Digital payments are growing. Who has the capability to take part?"
      >
        <button className="primary" onClick={() => navigate("explore")}>
          Explore the data <ArrowUpRight size={17} />
        </button>
      </Heading>
      <div className="scope-line">
        <span>
          <Globe size={15} /> India · Persons aged 15+
        </span>
        <span>CMS-T survey · January–March 2025</span>
        <span className="pill">Weighted estimates</span>
      </div>
      <div className="metrics">
        <Metric
          accent
          label="Report being UPI-capable"
          value={pct(n.upi_capable_rate)}
          detail="Self-reported ability, not transaction activity"
        />
        <Metric
          label="Estimated not UPI-capable"
          value={crore(n.gap_pop)}
          unit="crore"
          detail="People aged 15+ in the survey population"
        />
        <Metric
          label="Online, but unable to bank online"
          value={crore(c.internet_users_not_online_capable)}
          unit="crore"
          detail="Among people who recently used the internet"
        />
      </div>
      <div className="grid-main">
        <Panel
          eyebrow="ACCESS, USE & CAPABILITY"
          title="Different measures of participation"
          action={<span className="tag">Share of persons 15+</span>}
        >
          <Bars
            items={d.indicators.map((r, i) => ({
              label: labels[i],
              share: r.pct_of_adults,
            }))}
          />
          <p className="footnote">
            These are separate indicators, not a sequential funnel. Capability
            does not require recent use.
          </p>
        </Panel>
        <Panel
          eyebrow="A CLOSER LOOK"
          title="Internet use isn’t the whole story"
          className="insight"
        >
          <div
            className="ring"
            style={{ "--p": `${c.conditional_rate * 100}%` }}
          >
            <div>
              <strong>{pct(c.conditional_rate)}</strong>
              <span>can bank online</span>
            </div>
          </div>
          <p>
            Among recent internet users, online-banking capability varies by sex
            and sector.
          </p>
          <div className="mini-groups">
            {d.groups
              .filter((g) => g.gender_name !== "Transgender")
              .map((g) => (
                <div key={g.sector_name + g.gender_name}>
                  <span>
                    {g.sector_name} · {g.gender_name}
                  </span>
                  <b>{pct(g.conditional_rate)}</b>
                </div>
              ))}
          </div>
          <p className="footnote">
            Rates use respondent intersections. Smaller third-category groups
            are not charted here, but remain in national totals.
          </p>
        </Panel>
      </div>
      <div className="bottom-grid">
        <div className="callout">
          <span className="icon-tile">
            <Calculator size={23} />
          </span>
          <div>
            <h3>Explore a possibility, not a prediction.</h3>
            <p>Apply your own assumption to the estimated capability gap.</p>
          </div>
          <button
            className="icon-button"
            aria-label="Open what-if calculator"
            onClick={() => navigate("scenario")}
          >
            <ArrowRight />
          </button>
        </div>
        <div className="source-note">
          <BookOpen size={19} />
          <div>
            <strong>Evidence with its limits</strong>
            <p>
              Point estimates have no published confidence intervals here.{" "}
              <button
                className="text-button"
                onClick={() => navigate("methods")}
              >
                Read the methodology <ArrowUpRight size={13} />
              </button>
            </p>
          </div>
        </div>
      </div>
      <section className="panel barriers-panel">
        <h2>Why some households have no internet at home</h2>
        <p className="muted">
          Reported main reasons. These do not establish causes of UPI exclusion.
        </p>
        <Bars
          items={Object.entries(
            d.barriers.reduce(
              (a, r) => (
                (a[r.reason_no_internet_hh] =
                  (a[r.reason_no_internet_hh] || 0) + r.households),
                a
              ),
              {},
            ),
          )
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5)
            .map(([label, v]) => ({
              label,
              share: v / d.barriers.reduce((s, r) => s + r.households, 0),
            }))}
        />
        <p className="footnote">
          Top five reasons shown; shares use all households reporting a reason.
        </p>
      </section>
    </>
  );
}

function SaveForm({ version, filters, onClose, onSaved }) {
  const [title, setTitle] = useState("Capability comparison"),
    [note, setNote] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const ref = useRef();
  useEffect(() => {
    ref.current?.focus();
  }, []);
  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await gql(
        `mutation($version:ID!,$title:String!,$note:String!,$filters:Filters!){saveComparison(version:$version,title:$title,note:$note,filters:$filters){id}}`,
        { version, title, note, filters },
      );
      onSaved();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="save-sheet">
      <form onSubmit={submit}>
        <header>
          <h3>Save this comparison</h3>
          <button
            type="button"
            className="icon-button"
            onClick={onClose}
            aria-label="Close save form"
          >
            <X size={18} />
          </button>
        </header>
        <label>
          Title
          <input
            ref={ref}
            required
            maxLength={100}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </label>
        <label>
          Your note
          <textarea
            maxLength={2000}
            rows={3}
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="What would you like to remember?"
          />
        </label>
        <p className="footnote">
          Saved privately for this browser, with its filters and dataset
          version. Clearing browser cookies removes access.
        </p>
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        <button className="primary" disabled={busy}>
          {busy ? "Saving…" : "Save comparison"}
          <Bookmark size={16} />
        </button>
      </form>
    </div>
  );
}

function Explorer({ dataset, initial, navigate }) {
  const [filters, setFilters] = useState(initial?.filters || defaults),
    [save, setSave] = useState(false);
  const version = initial?.datasetId || dataset.id;
  const state = useRequest(analysisQuery, { version, filters });
  const a = state.data?.analysis;
  function exportCsv() {
    const rows = [
      [
        "State / UT",
        "Capability rate (fraction; blank below 30 respondents)",
        "Respondents",
        "Estimated excluded",
        "Statewide online-banking reference check",
        "Sector",
        "Sex",
        "Age group",
        "Dataset version",
      ],
      ...a.states.map((s) => [
        s.state,
        s.rate ?? "",
        s.sample,
        s.excluded,
        s.review,
        filters.sector,
        filters.sex,
        filters.age,
        version,
      ]),
    ];
    download(
      `upi-comparison-${version}.csv`,
      rows
        .map((r) =>
          r.map((v) => '"' + String(v).replaceAll('"', '""') + '"').join(","),
        )
        .join("\r\n"),
      "text/csv",
    );
  }
  return (
    <>
      <Heading
        kicker="SURVEY EXPLORER"
        title="Look closer at capability"
        description="Compare weighted estimates across populations. Rates are recalculated from their underlying totals."
      />
      <Filters data={dataset.payload} value={filters} setValue={setFilters} />
      {version !== dataset.id && (
        <Notice>
          You’re viewing the original dataset version saved with this
          comparison: {version}.
        </Notice>
      )}
      {filters.state === "Himachal Pradesh" && (
        <Notice warm>
          Himachal Pradesh has an unresolved 1.8 percentage-point difference in
          the official online-banking cross-check. Its survey estimates remain
          provisional.
        </Notice>
      )}
      {state.loading ? (
        <Loading />
      ) : state.error ? (
        <ErrorBox message={state.error} />
      ) : (
        <>
          <div className="metrics">
            <Metric
              accent
              label="UPI capability · selected population"
              value={pct(a.rate)}
              detail={
                a.suppressed
                  ? "Fewer than 30 respondents; rate withheld"
                  : "Weighted capable people / weighted population"
              }
            />
            <Metric
              label="Survey respondents"
              value={number(a.sample)}
              detail="Sample count, not a precision guarantee"
            />
            <Metric
              label="Estimated not UPI-capable"
              value={crore(a.excluded)}
              unit="crore"
              detail="Among the selected population"
            />
          </div>
          <div className="grid-main">
            <Panel title="Capability by age" eyebrow="SELECTED POPULATION">
              <div className="age-chart">
                {a.ages.map((r) => (
                  <div className="age-col" key={r.age}>
                    <b>{pct(r.rate)}</b>
                    <div className="age-well">
                      <div style={{ height: `${(r.rate || 0) * 100}%` }} />
                    </div>
                    <span>{r.age}</span>
                  </div>
                ))}
              </div>
              <p className="footnote">
                A blank rate means the group has fewer than 30 respondents or no
                matching records.
              </p>
            </Panel>
            <Panel title="Keep the context" eyebrow="HOW TO READ THIS">
              <p>
                Differences between point estimates do not establish
                statistically significant differences or their causes.
              </p>
              <div className="fact-line">
                <Check size={16} /> All recorded sex categories remain in
                totals.
              </div>
              <div className="fact-line">
                <Check size={16} /> State rows are alphabetical, not ranked.
              </div>
              <div className="fact-line">
                <Info size={16} /> Confidence intervals are unavailable.
              </div>
              <button className="primary full" onClick={() => setSave(true)}>
                <Bookmark size={16} /> Save comparison
              </button>
              {save && (
                <SaveForm
                  version={version}
                  filters={filters}
                  onClose={() => setSave(false)}
                  onSaved={() => navigate("saved")}
                />
              )}
            </Panel>
          </div>
          <Panel
            title="State and union territory comparison"
            action={
              <button className="secondary" onClick={exportCsv}>
                <Download size={15} /> CSV
              </button>
            }
          >
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>State / UT</th>
                    <th>UPI-capable</th>
                    <th>Respondents</th>
                    <th>Online-banking check</th>
                  </tr>
                </thead>
                <tbody>
                  {a.states.map((s) => (
                    <tr key={s.state}>
                      <td>{s.state}</td>
                      <td>
                        <span className="rate-cell">
                          <i style={{ width: `${(s.rate || 0) * 80}px` }} />
                          {pct(s.rate)}
                        </span>
                      </td>
                      <td>{number(s.sample)}</td>
                      <td>
                        <span
                          className={`status ${s.review.startsWith("Unresolved") ? "review" : ""}`}
                          title={s.review}
                        >
                          {s.review.startsWith("Unresolved")
                            ? "Review note"
                            : "Matched reference"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {!a.states.length && <p className="empty">No matching records.</p>}
            <p className="footnote">
              Source checks compare statewide online-banking estimates, not the
              demographic UPI rates shown here.
            </p>
          </Panel>
        </>
      )}
    </>
  );
}

function Transactions({ dataset }) {
  const d = dataset.payload,
    n = d.npci[0];
  const [hover, setHover] = useState(null),
    [search, setSearch] = useState("");
  const selected = d.transactions.find((s) => s.state === hover);
  const maxY =
    Math.ceil(Math.max(...d.transactions.map((r) => r.txn_per_adult)) / 20) *
    20;
  const rows = d.transactions
    .filter((r) => r.state.toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => a.state.localeCompare(b.state));
  return (
    <>
      <Heading
        kicker="A SEPARATE LENS"
        title="Transactions, with context"
        description="Recorded transaction activity and survey capability measure different things. This comparison is exploratory."
      />
      <Notice warm>
        <strong>
          {pct(n.unclassified_share_volume)} of national volume has no state
          classification.
        </strong>{" "}
        State-specific coverage is unknown. Complete-volume rankings cannot be
        inferred.
      </Notice>
      <div className="metrics">
        <Metric
          label="National transactions"
          value={(n.total_volume_mn / 1000).toFixed(2)}
          unit="billion"
          detail="Q1 2025 · includes unclassified volume"
        />
        <Metric
          accent
          label="Classified transactions"
          value={(n.classified_volume_mn / 1000).toFixed(2)}
          unit="billion"
          detail="Used for observed state comparisons"
        />
        <Metric
          label="Unclassified transactions"
          value={(n.unclassified_volume_mn / 1000).toFixed(2)}
          unit="billion"
          detail="Retained in national totals; not redistributed"
        />
      </div>
      <div className="grid-main">
        <Panel
          eyebrow="36 STATES & UNION TERRITORIES"
          title="Capability and classified activity"
        >
          <p className="chart-axis-note">
            Classified transactions per resident aged 15+
          </p>
          <svg
            className="scatter"
            viewBox="0 0 740 355"
            role="img"
            aria-label="Scatter plot of state UPI capability and classified transactions per resident aged 15 and over"
          >
            {[0, 20, 40, 60, 80, 100, 120]
              .filter((y) => y <= maxY)
              .map((y) => (
                <g key={y}>
                  <line
                    x1="50"
                    x2="715"
                    y1={300 - (y / maxY) * 265}
                    y2={300 - (y / maxY) * 265}
                    stroke="#e8eeeb"
                  />
                  <text x="37" y={305 - (y / maxY) * 265} textAnchor="end">
                    {y}
                  </text>
                </g>
              ))}
            {[0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8].map((x) => (
              <text
                key={x}
                x={50 + ((x - 0.15) / 0.7) * 665}
                y="328"
                textAnchor="middle"
              >
                {Math.round(x * 100)}%
              </text>
            ))}
            {d.transactions.map((r) => (
              <circle
                key={r.state}
                cx={50 + ((r.upi_capable_rate - 0.15) / 0.7) * 665}
                cy={300 - (r.txn_per_adult / maxY) * 265}
                r={hover === r.state ? 8 : 5.5}
                tabIndex="0"
                role="button"
                aria-label={`${r.state}: ${pct(r.upi_capable_rate)}, ${r.txn_per_adult.toFixed(1)} classified transactions per resident`}
                onFocus={() => setHover(r.state)}
                onMouseEnter={() => setHover(r.state)}
                onClick={() => setHover(r.state)}
                fill={r.state === "Himachal Pradesh" ? "#c98542" : "#208074"}
                opacity=".85"
              >
                <title>{r.state}</title>
              </circle>
            ))}
          </svg>
          <p className="x-axis-label">Survey UPI-capability rate</p>
          <div className="chart-selection" aria-live="polite">
            {selected ? (
              <>
                <strong>{selected.state}</strong>
                <span>
                  {pct(selected.upi_capable_rate)} capable ·{" "}
                  {selected.txn_per_adult.toFixed(1)} classified transactions
                  per resident 15+
                </span>
              </>
            ) : (
              <span>Hover or focus a point to inspect a state.</span>
            )}
          </div>
          <p className="footnote">
            All 36 observed points are shown. The amber point is Himachal
            Pradesh, under source review. No fitted line or behavioural
            diagnosis is asserted.
          </p>
        </Panel>
        <Panel title="Missing state attribution" eyebrow="BY MONTH">
          <Bars
            items={d.months.map((m) => ({
              label: m.month + " 2025",
              share: m.unclassified_share_volume,
            }))}
          />
          <div className="divider" />
          <h3>What this cannot tell us</h3>
          <p>
            Transaction location need not equal payer residence. These data
            cannot identify merchant acceptance or a programme’s effect.
          </p>
          <p className="footnote">
            Demographic survey filters do not apply to this page. There are no
            age- or sex-specific transaction estimates.
          </p>
        </Panel>
      </div>
      <Panel
        title="Observed state data"
        action={
          <label className="search">
            <Search size={15} />
            <input
              aria-label="Search transaction states"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Find a state"
            />
          </label>
        }
      >
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>State / UT</th>
                <th>Classified volume · million</th>
                <th>Transactions / resident 15+</th>
                <th>Coverage</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.state}>
                  <td>{r.state}</td>
                  <td>{r.volume_mn.toFixed(2)}</td>
                  <td>{r.txn_per_adult.toFixed(1)}</td>
                  <td>State-specific coverage unknown</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!rows.length && <p className="empty">No states match your search.</p>}
      </Panel>
    </>
  );
}

function Scenario({ dataset }) {
  const [filters, setFilters] = useState(defaults),
    [share, setShare] = useState(10);
  const state = useRequest(
    `query($version:ID!,$filters:Filters!,$share:Float!){scenario(version:$version,filters:$filters,share:$share){baseline share newlyCapable sample suppressed}}`,
    { version: dataset.id, filters, share: share / 100 },
  );
  const r = state.data?.scenario;
  return (
    <>
      <Heading
        kicker="ASSUMPTIONS, MADE EXPLICIT"
        title="What if capability increased?"
        description="Choose a population and an assumed share becoming UPI-capable. Explore the arithmetic, not a forecast."
      />
      <Filters
        data={dataset.payload}
        value={filters}
        setValue={setFilters}
        state={false}
      />
      <div className="scenario-grid">
        <Panel eyebrow="YOUR ASSUMPTION" title="Share becoming capable">
          <div className="assumption">
            <strong>
              {share}
              <span>%</span>
            </strong>
            <span>of the estimated excluded population</span>
          </div>
          <label className="sr-only" htmlFor="share">
            Assumed share becoming capable
          </label>
          <input
            id="share"
            className="range"
            type="range"
            min="0"
            max="100"
            step="1"
            value={share}
            onChange={(e) => setShare(Number(e.target.value))}
          />
          <div className="range-labels">
            <span>0%</span>
            <span>100%</span>
          </div>
          <div className="presets">
            {[0, 5, 10, 25, 50, 100].map((v) => (
              <button
                key={v}
                className={share === v ? "selected" : ""}
                onClick={() => setShare(v)}
              >
                {v}%
              </button>
            ))}
          </div>
          <Notice>
            No machine learning is used. Changing the assumption does not
            estimate how people would respond to an intervention.
          </Notice>
        </Panel>
        <section className="scenario-result" aria-live="polite">
          <p className="eyebrow">HYPOTHETICAL RESULT</p>
          {state.error ? (
            <ErrorBox message={state.error} />
          ) : state.loading ? (
            <Loading />
          ) : r.suppressed ? (
            <>
              <h2>Too few respondents</h2>
              <p>
                This selection has {number(r.sample)} respondents. A scenario is
                withheld below 30.
              </p>
            </>
          ) : (
            <>
              <p className="result-number">{number(r.newlyCapable)}</p>
              <h2>newly UPI-capable people</h2>
              <div className="scenario-equation">
                <div>
                  <strong>{number(r.baseline)}</strong>
                  <span>baseline excluded</span>
                </div>
                <span>×</span>
                <div>
                  <strong>{share}%</strong>
                  <span>assumed share</span>
                </div>
              </div>
              <p>
                Approximately <strong>{crore(r.newlyCapable)} crore</strong>{" "}
                people under this assumption.
              </p>
            </>
          )}
          <p className="result-note">
            Baseline sampling uncertainty remains unresolved. No additional
            transactions, programme returns or causal effects are predicted.
          </p>
        </section>
      </div>
      <Notice>
        Scenarios use national demographic groups. State scenarios are
        unavailable while source and uncertainty limitations remain unresolved.
      </Notice>
    </>
  );
}

function Methods({ dataset }) {
  const d = dataset.payload;
  return (
    <>
      <Heading
        kicker="TRANSPARENCY BY DESIGN"
        title="Understand the evidence"
        description="The definitions, checks and limitations that travel with every result."
      />
      <div className="method-grid">
        <Panel title="Survey capability" eyebrow="SOURCE 01">
          <h3>CMS-T · NSS 80th Round</h3>
          <p>
            January–March 2025. This analysis covers people aged 15+, using
            MLT/100 survey weights. UPI capability is a self-reported ability,
            identified by Q12 codes 1 or 3.
          </p>
          <p>
            State geography comes from the first two digits of NSS-Region. It is
            independent of the NPCI join.
          </p>
          <a
            className="source-link"
            href="https://microdata.gov.in/NADA/index.php/catalog/239/related-materials"
            target="_blank"
            rel="noreferrer"
          >
            Official survey materials <ArrowUpRight size={15} />
          </a>
        </Panel>
        <Panel title="Recorded transactions" eyebrow="SOURCE 02">
          <h3>NPCI · Q1 2025</h3>
          <p>
            Owner-supplied January, February and March workbooks. Classified
            state volumes remain observed; unclassified transactions stay in
            national totals.
          </p>
          <p>
            The local workbook copies reconcile. An independent fresh NPCI
            download has not been verified.
          </p>
          <a
            className="source-link"
            href="https://www.npci.org.in/what-we-do/upi/upi-ecosystem-statistics"
            target="_blank"
            rel="noreferrer"
          >
            NPCI ecosystem statistics <ArrowUpRight size={15} />
          </a>
        </Panel>
      </div>
      <div className="method-grid">
        <Panel title="How the estimates are calculated">
          <ol className="method-list">
            <li>
              <b>Recalculate rates from totals.</b> Sum weighted capable people
              and divide by the weighted population. Never average subgroup
              percentages.
            </li>
            <li>
              <b>Use actual intersections.</b> Online-banking capability among
              recent internet users comes from respondents who meet both
              conditions.
            </li>
            <li>
              <b>Preserve survey totals.</b> All states and recorded sex
              categories contribute, including provisional Himachal Pradesh
              estimates.
            </li>
          </ol>
        </Panel>
        <Panel title="What remains uncertain">
          <p>
            Exact design-based confidence intervals require additional
            frame/listing information absent from the supplied extracts.
          </p>
          <p>
            Fewer than 30 respondents is a display guard, not a precision
            guarantee. Differences are not significance tests.
          </p>
          <p>
            Household internet barriers cannot establish the causes of UPI
            exclusion or intervention effectiveness.
          </p>
        </Panel>
      </div>
      <Panel
        title="Official source reconciliation"
        action={<span className="pill">35 / 36 match displayed precision</span>}
      >
        <p>
          Himachal Pradesh: reproduced online-banking capability is 64.4%,
          versus 66.2% in official Table 12. The cause is unresolved; no values
          were overwritten. This is an online-banking check, not a direct
          UPI-rate validation.
        </p>
        <details>
          <summary>
            Inspect all state checks <ChevronRight size={15} />
          </summary>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>State / UT</th>
                  <th>Reproduced</th>
                  <th>Official</th>
                  <th>Difference · pp</th>
                </tr>
              </thead>
              <tbody>
                {d.validation.map((r) => (
                  <tr key={r.state_code}>
                    <td>
                      {
                        d.states.find((s) => s.state_code === r.state_code)
                          ?.state
                      }
                    </td>
                    <td>{r.computed_pct.toFixed(2)}%</td>
                    <td>{r.official_pct.toFixed(1)}%</td>
                    <td>{r.difference_pp.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
        <a
          className="source-link"
          href="https://mospi.gov.in/sites/default/files/publication_reports/CMST_report_m.pdf#page=124"
          target="_blank"
          rel="noreferrer"
        >
          Official report · Table 12, A85 <ArrowUpRight size={15} />
        </a>
      </Panel>
      <Panel title="Why redistribution does not validate rankings">
        <p>
          Proportional and population-based allocations preserve per-adult ranks
          by construction. Capability-based allocations build the relationship
          into the outcome. None recovers the real missing-state distribution.
        </p>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Hypothetical rule</th>
                <th>Rank correlation vs classified only</th>
                <th>Uses capability in allocation</th>
              </tr>
            </thead>
            <tbody>
              {d.allocation.map((r) => (
                <tr key={r.method}>
                  <td>{r.method.replaceAll("_", " ")}</td>
                  <td>{r.rank_corr_vs_excluded.toFixed(3)}</td>
                  <td>{r.uses_capability_in_allocation ? "Yes" : "No"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
      <div className="provenance">
        <Database size={21} />
        <div>
          <b>Dataset {dataset.id}</b>
          <p>Immutable aggregate snapshot · {dataset.period}</p>
        </div>
        <button
          className="secondary"
          onClick={() =>
            download(
              "upi-dataset-manifest.json",
              JSON.stringify(
                {
                  version: dataset.id,
                  period: dataset.period,
                  hashes: dataset.hashes,
                },
                null,
                2,
              ),
              "application/json",
            )
          }
        >
          <Download size={16} /> Source hashes
        </button>
      </div>
    </>
  );
}

function Saved({ onOpen }) {
  const [items, setItems] = useState(null),
    [error, setError] = useState(""),
    [deleting, setDeleting] = useState(null);
  async function refresh() {
    try {
      const d = await gql(savedQuery);
      setItems(d.comparisons);
    } catch (e) {
      setError(e.message);
    }
  }
  useEffect(() => {
    refresh();
  }, []);
  async function remove(id) {
    setDeleting(id);
    try {
      await gql("mutation($id:ID!){deleteComparison(id:$id)}", { id });
      await refresh();
    } catch (e) {
      setError(e.message);
    } finally {
      setDeleting(null);
    }
  }
  return (
    <>
      <Heading
        kicker="YOUR RESEARCH NOTES"
        title="Saved comparisons"
        description="Keep a population selection and its evidence together. Saved privately for this browser, with the original dataset version."
      />
      {error && <ErrorBox message={error} />}
      <Notice>
        This browser’s session cookie controls access. These notes are not an
        account backup; clearing cookies removes access. Save important findings
        separately.
      </Notice>
      {items === null ? (
        <Loading />
      ) : items.length === 0 ? (
        <div className="empty-card">
          <Bookmark size={36} />
          <h2>Your first comparison starts with a question.</h2>
          <p>Explore a population, then save its filters and add a note.</p>
          <a className="primary" href="#explore">
            Explore capability <ArrowRight size={17} />
          </a>
        </div>
      ) : (
        <div className="saved-grid">
          {items.map((r) => (
            <article className="panel saved-card" key={r.id}>
              <div className="saved-top">
                <span className="tag">
                  {new Date(r.createdAt).toLocaleDateString("en-IN")}
                </span>
                <button
                  className="icon-button"
                  aria-label={`Delete ${r.title}`}
                  disabled={deleting === r.id}
                  onClick={() => remove(r.id)}
                >
                  <Trash2 size={16} />
                </button>
              </div>
              <h2>{r.title}</h2>
              <p className="saved-rate">
                {pct(r.summary.rate)}
                <span> UPI-capable</span>
              </p>
              <div className="chips">
                {Object.entries(r.filters)
                  .filter(([, v]) => v !== "All")
                  .map(([k, v]) => (
                    <span key={k}>{v}</span>
                  ))}
                {Object.values(r.filters).every((v) => v === "All") && (
                  <span>All persons aged 15+</span>
                )}
              </div>
              {r.note && <p className="saved-note">{r.note}</p>}
              <p className="footnote">
                {number(r.summary.sample)} respondents · version {r.datasetId}
              </p>
              <button className="text-button" onClick={() => onOpen(r)}>
                Open comparison <ArrowRight size={15} />
              </button>
            </article>
          ))}
        </div>
      )}
    </>
  );
}

export function App() {
  const [page, setPage] = useState(location.hash.slice(1) || "overview"),
    [menu, setMenu] = useState(false),
    [initial, setInitial] = useState(null);
  const state = useRequest("query{dataset{id period payload hashes}}", {});
  useEffect(() => {
    const f = () => {
      setPage(location.hash.slice(1) || "overview");
      setMenu(false);
      window.scrollTo(0, 0);
    };
    window.addEventListener("hashchange", f);
    return () => window.removeEventListener("hashchange", f);
  }, []);
  function navigate(p) {
    location.hash = p;
  }
  const valid = pages.some(([p]) => p === page) ? page : "overview",
    dataset = state.data?.dataset;
  useEffect(() => {
    document.title = `${pages.find(([p]) => p === valid)?.[1]} · UPI Observatory`;
  }, [valid]);
  return (
    <div className="app">
      <a
        className="skip-link"
        href="#main"
        onClick={(e) => {
          e.preventDefault();
          document.getElementById("main").focus();
        }}
      >
        Skip to content
      </a>
      <aside id="navigation" className={`sidebar ${menu ? "open" : ""}`}>
        <a className="brand" href="#overview">
          <span className="brand-mark">
            <Activity size={26} />
          </span>
          <span>
            UPI<span className="brand-sub">OBSERVATORY</span>
          </span>
        </a>
        <p className="nav-label">THE CAPABILITY GAP</p>
        <nav aria-label="Main navigation">
          {pages.map(([id, label, Icon]) => (
            <a
              key={id}
              href={`#${id}`}
              aria-current={valid === id ? "page" : undefined}
              className={valid === id ? "active" : ""}
              onClick={() => {
                setMenu(false);
                if (id === "explore") setInitial(null);
              }}
            >
              <Icon size={18} />
              {label}
              {valid === id && <span className="nav-dot" />}
            </a>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <span className="live-dot" /> Historical snapshot
          <p>January–March 2025</p>
          <div className="sidebar-rule" />
          <p>
            Built on evidence.
            <br />
            Clear about uncertainty.
          </p>
          <a href="#methods">
            About the data <ArrowUpRight size={13} />
          </a>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <button
            className="menu-button"
            aria-label="Toggle navigation"
            aria-expanded={menu}
            aria-controls="navigation"
            onClick={() => setMenu(!menu)}
          >
            {menu ? <X /> : <Menu />}
          </button>
          <div className="breadcrumb">
            Research workspace <ChevronRight size={13} />
            <span>{pages.find(([id]) => id === valid)?.[1]}</span>
          </div>
          <span className="snapshot">
            <span /> Q1 2025 <span className="snapshot-divider">/</span> CMS-T +
            NPCI
          </span>
        </header>
        <main id="main" tabIndex={-1}>
          {state.loading ? (
            <Loading />
          ) : state.error ? (
            <ErrorBox message={state.error} />
          ) : valid === "overview" ? (
            <Overview dataset={dataset} navigate={navigate} />
          ) : valid === "explore" ? (
            <Explorer
              key={initial?.id || "default"}
              dataset={dataset}
              initial={initial}
              navigate={navigate}
            />
          ) : valid === "transactions" ? (
            <Transactions dataset={dataset} />
          ) : valid === "scenario" ? (
            <Scenario dataset={dataset} />
          ) : valid === "methods" ? (
            <Methods dataset={dataset} />
          ) : (
            <Saved
              onOpen={(r) => {
                setInitial(r);
                navigate("explore");
              }}
            />
          )}
          <footer className="page-footer">
            <span>
              UPI Observatory <span>·</span> Understanding capability, beyond
              transaction counts.
            </span>
            <a href="#methods">
              Definitions & limitations <ArrowUpRight size={12} />
            </a>
          </footer>
        </main>
      </div>
    </div>
  );
}

export class Boundary extends React.Component {
  state = { error: false };
  static getDerivedStateFromError() {
    return { error: true };
  }
  render() {
    return this.state.error ? (
      <div className="loading">
        <ErrorBox message="The page could not be displayed. Please reload." />
      </div>
    ) : (
      this.props.children
    );
  }
}
