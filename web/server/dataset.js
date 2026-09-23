import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import crypto from "node:crypto";
import { parse } from "csv-parse/sync";

export const repo = fileURLToPath(new URL("../../", import.meta.url));
const files = {
  national: "national_summary",
  conditional: "conditional_national",
  groups: "conditional_sector_gender",
  indicators: "funnel_national",
  segments: "segment_gap_table",
  states: "state_level",
  transactions: "state_capability_vs_usage",
  npci: "npci_national_summary",
  months: "npci_unclassified_share",
  validation: "official_state_validation",
  allocation: "npci_allocation_sensitivity",
  barriers: "barriers_household",
  overlap: "indicator_overlap_checks",
};
const strings = new Set([
  "state_code",
  "state",
  "sector_name",
  "gender_name",
  "age_band",
  "stage",
  "variable",
  "month",
  "period",
  "review_status",
  "uncertainty_status",
  "transaction_scope",
  "comparison_label",
  "source_url",
  "source_table",
  "method",
  "top_state",
  "interpretation",
  "benchmark_interpretation",
  "reason_no_internet_hh",
]);
const cast = (v, ctx) =>
  ctx.header || strings.has(ctx.column)
    ? v
    : v === ""
      ? null
      : v === "True"
        ? true
        : v === "False"
          ? false
          : Number.isFinite(Number(v))
            ? Number(v)
            : v;
const near = (a, b) => Math.abs(a - b) < Math.max(0.01, Math.abs(b) * 1e-8);
const check = (ok, message) => {
  if (!ok) throw new Error(`Dataset validation: ${message}`);
};
const sum = (rows, key) => rows.reduce((s, r) => s + r[key], 0);

export function validateDataset(d) {
  const n = d.national[0],
    p = d.npci[0];
  check(
    d.national.length === 1 && d.npci.length === 1,
    "one national record required",
  );
  check(
    d.states.length === 36 && new Set(d.states.map((s) => s.state)).size === 36,
    "36 unique states required",
  );
  const codes = new Set(d.states.map((s) => s.state_code)),
    states = new Set(d.states.map((s) => s.state));
  check(
    codes.size === 36 && [...codes].every((c) => /^\d{2}$/.test(c)),
    "state codes must remain two-digit strings",
  );
  for (const row of d.segments) {
    check(states.has(row.state), "unknown segment state");
    check(
      ["Rural", "Urban"].includes(row.sector_name) &&
        ["Female", "Male", "Transgender"].includes(row.gender_name) &&
        ["15-24", "25-34", "35-44", "45-59", "60+"].includes(row.age_band),
      "unknown demographic code",
    );
    check(
      Number.isFinite(row.adult_pop) &&
        row.adult_pop > 0 &&
        Number.isFinite(row.upi_capable_pop) &&
        row.upi_capable_pop >= 0 &&
        row.upi_capable_pop <= row.adult_pop &&
        row.n_unweighted > 0,
      "invalid population or sample count",
    );
  }
  check(
    new Set(
      d.segments.map((r) =>
        [r.state, r.sector_name, r.gender_name, r.age_band].join("|"),
      ),
    ).size === d.segments.length,
    "duplicate demographic cell",
  );
  check(
    near(sum(d.segments, "adult_pop"), n.adult_pop) &&
      near(sum(d.segments, "upi_capable_pop"), n.upi_capable_pop),
    "segment totals must reconcile",
  );
  check(
    near(n.gap_pop, n.adult_pop - n.upi_capable_pop) &&
      near(n.upi_capable_rate, n.upi_capable_pop / n.adult_pop),
    "national estimates inconsistent",
  );
  check(
    near(sum(d.states, "adult_pop"), n.adult_pop) &&
      near(sum(d.states, "upi_capable_pop"), n.upi_capable_pop),
    "state totals must reconcile",
  );
  for (const state of d.states) {
    const cells = d.segments.filter((r) => r.state === state.state);
    check(
      near(sum(cells, "adult_pop"), state.adult_pop) &&
        near(sum(cells, "upi_capable_pop"), state.upi_capable_pop) &&
        sum(cells, "n_unweighted") === state.n_unweighted,
      "state demographic cells must reconcile",
    );
    check(
      near(state.upi_capable_rate, state.upi_capable_pop / state.adult_pop),
      "state capability rate inconsistent",
    );
  }
  check(
    d.months.length === 3 &&
      new Set(d.months.map((r) => r.month)).size === 3 &&
      d.months.every((r) => ["Jan", "Feb", "Mar"].includes(r.month)),
    "exact Jan–Mar quarter required",
  );
  check(
    d.transactions.length === 36 &&
      new Set(d.transactions.map((r) => r.state)).size === 36 &&
      d.transactions.every(
        (r) => states.has(r.state) && r.allocated_mn === 0 && r.volume_mn >= 0,
      ),
    "unique classified-only state transactions required",
  );
  check(
    near(sum(d.transactions, "volume_mn"), p.classified_volume_mn) &&
      near(sum(d.months, "total_volume_mn"), p.total_volume_mn) &&
      near(sum(d.months, "unclassified_volume_mn"), p.unclassified_volume_mn),
    "transaction totals inconsistent",
  );
  check(
    near(
      p.classified_volume_mn + p.unclassified_volume_mn,
      p.total_volume_mn,
    ) &&
      near(
        p.unclassified_share_volume,
        p.unclassified_volume_mn / p.total_volume_mn,
      ),
    "unclassified share inconsistent",
  );
  for (const r of d.transactions) {
    const state = d.states.find((s) => s.state === r.state);
    check(
      near(r.txn_per_adult, (r.volume_mn * 1e6) / state.adult_pop) &&
        near(r.upi_capable_rate, state.upi_capable_rate),
      "transaction population join inconsistent",
    );
  }
  for (const r of d.months)
    check(
      r.total_volume_mn > 0 &&
        r.unclassified_volume_mn >= 0 &&
        r.unclassified_volume_mn <= r.total_volume_mn &&
        near(
          r.unclassified_share_volume,
          r.unclassified_volume_mn / r.total_volume_mn,
        ),
      "monthly coverage inconsistent",
    );
  check(
    d.validation.length === 36 &&
      new Set(d.validation.map((r) => r.state_code)).size === 36,
    "complete official reference required",
  );
  for (const r of d.validation) {
    check(codes.has(r.state_code), "unknown validation state");
    const matches = Math.abs(r.computed_pct - r.official_pct) <= 0.0500001;
    check(
      matches === r.matches_published_precision,
      "incorrect validation flag",
    );
    check(matches || r.state_code === "02", "unrecognised source discrepancy");
  }
  const c = d.conditional[0];
  check(
    near(
      c.online_capable_internet_users + c.internet_users_not_online_capable,
      c.internet_users,
    ),
    "conditional intersections inconsistent",
  );
  return d;
}

export async function loadDataset(root = repo) {
  const data = {},
    hashes = {};
  for (const [key, name] of Object.entries(files)) {
    const raw = await readFile(
      path.join(root, "data/processed", `${name}.csv`),
    );
    hashes[`${name}.csv`] = crypto
      .createHash("sha256")
      .update(raw)
      .digest("hex");
    data[key] = parse(raw, {
      columns: true,
      bom: true,
      skip_empty_lines: true,
      cast,
    });
  }
  validateDataset(data);
  const sourceManifest = JSON.parse(
    await readFile(path.join(root, "docs/source_manifest.json"), "utf8"),
  );
  const id = crypto
    .createHash("sha256")
    .update(JSON.stringify({ hashes, sourceManifest }))
    .digest("hex")
    .slice(0, 16);
  return {
    id,
    period: "January–March 2025",
    payload: data,
    hashes,
    sourceManifest,
  };
}
