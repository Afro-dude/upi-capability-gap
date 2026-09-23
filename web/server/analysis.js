const allowed = {
  sector: ["All", "Rural", "Urban"],
  sex: ["All", "Female", "Male", "Transgender"],
  age: ["All", "15-24", "25-34", "35-44", "45-59", "60+"],
};
export function normalizeFilters(input = {}, data) {
  const f = {
    state: "All",
    sector: "All",
    sex: "All",
    age: "All",
    ...Object.fromEntries(
      Object.entries(input || {}).filter(([, v]) => v != null),
    ),
  };
  for (const [k, v] of Object.entries(allowed))
    if (!v.includes(f[k])) throw new Error(`Invalid ${k} selection`);
  if (f.state !== "All" && !data.states.some((s) => s.state === f.state))
    throw new Error("Unknown state");
  return f;
}
export function summarize(rows) {
  const total = (key) => rows.reduce((n, r) => n + r[key], 0);
  const adults = total("adult_pop"),
    capable = total("upi_capable_pop"),
    sample = total("n_unweighted");
  return {
    adults,
    capable,
    excluded: adults - capable,
    sample,
    rate: sample >= 30 && adults > 0 ? capable / adults : null,
    suppressed: sample < 30,
  };
}
export function analyze(data, input) {
  const filters = normalizeFilters(input, data);
  const rows = data.segments.filter(
    (r) =>
      (filters.state === "All" || r.state === filters.state) &&
      (filters.sector === "All" || r.sector_name === filters.sector) &&
      (filters.sex === "All" || r.gender_name === filters.sex) &&
      (filters.age === "All" || r.age_band === filters.age),
  );
  const groups = new Map();
  for (const r of rows) {
    const key = r.state;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(r);
  }
  const stateRows = [...groups]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([state, values]) => ({
      state,
      ...summarize(values),
      review: data.states.find((s) => s.state === state).review_status,
    }));
  const ages = allowed.age
    .slice(1)
    .map((age) => ({
      age,
      ...summarize(rows.filter((r) => r.age_band === age)),
    }));
  return { filters, ...summarize(rows), states: stateRows, ages };
}
export function scenario(data, input, share) {
  if (!Number.isFinite(share) || share < 0 || share > 1)
    throw new Error("Assumed share must be between 0 and 1");
  const result = analyze(data, input);
  if (result.filters.state !== "All")
    throw new Error("State scenarios are unavailable");
  return {
    baseline: result.suppressed ? null : result.excluded,
    share,
    newlyCapable: result.suppressed ? null : result.excluded * share,
    sample: result.sample,
    suppressed: result.suppressed,
  };
}
