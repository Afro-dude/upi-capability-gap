import test from "node:test";
import assert from "node:assert/strict";
import { loadDataset, validateDataset } from "../server/dataset.js";
import { analyze, scenario, summarize } from "../server/analysis.js";
const { payload: d } = await loadDataset();
test("national filters reconcile with the audited baseline", () => {
  const a = analyze(d, {});
  assert.equal(a.sample, 106631);
  assert.ok(Math.abs(a.rate - 0.48631557565) < 1e-9);
  assert.ok(Math.abs(a.excluded - 469465634.02) < 0.01);
  assert.equal(a.states.length, 36);
});
test("rate aggregation uses denominators rather than an average of rates", () => {
  const a = summarize([
    { adult_pop: 100, upi_capable_pop: 100, n_unweighted: 40 },
    { adult_pop: 900, upi_capable_pop: 0, n_unweighted: 40 },
  ]);
  assert.equal(a.rate, 0.1);
});
test("third category remains in national totals", () => {
  const full = analyze(d, {});
  const parts = ["Female", "Male", "Transgender"].map((sex) =>
    analyze(d, { sex }),
  );
  assert.equal(
    parts.reduce((s, p) => s + p.sample, 0),
    full.sample,
  );
  assert.ok(
    Math.abs(parts.reduce((s, p) => s + p.adults, 0) - full.adults) < 0.01,
  );
});
test("small and empty cells suppress rates without dropping their population", () => {
  const a = summarize([
    { adult_pop: 1000, upi_capable_pop: 500, n_unweighted: 5 },
  ]);
  assert.equal(a.rate, null);
  assert.equal(a.excluded, 500);
  assert.equal(summarize([]).rate, null);
});
test("filter labels are validated", () => {
  assert.throws(() => analyze(d, { state: "Atlantis" }));
  assert.throws(() => analyze(d, { age: "under 15" }));
  assert.throws(() => analyze(d, { sex: "All people" }));
});
test("scenario boundaries and invalid/state inputs", () => {
  assert.equal(scenario(d, {}, 0).newlyCapable, 0);
  const s = scenario(d, {}, 1);
  assert.equal(s.newlyCapable, s.baseline);
  assert.throws(() => scenario(d, {}, NaN));
  assert.throws(() => scenario(d, {}, 1.01));
  assert.throws(() => scenario(d, { state: "Himachal Pradesh" }, 0.1));
});
test("import rejects duplicate cells and partial quarters", () => {
  const a = structuredClone(d);
  a.segments.push(a.segments[0]);
  assert.throws(() => validateDataset(a));
  const b = structuredClone(d);
  b.months.pop();
  assert.throws(() => validateDataset(b));
});
test("import rejects allocated state volumes and unseen reference discrepancies", () => {
  const a = structuredClone(d);
  a.transactions[0].allocated_mn = 10;
  assert.throws(() => validateDataset(a));
  const b = structuredClone(d);
  b.validation[0].computed_pct += 2;
  b.validation[0].matches_published_precision = false;
  assert.throws(() => validateDataset(b));
});
test("dataset IDs are content addressed and repeatable", async () => {
  const a = await loadDataset(),
    b = await loadDataset();
  assert.equal(a.id, b.id);
  assert.equal(a.hashes["national_summary.csv"].length, 64);
});
