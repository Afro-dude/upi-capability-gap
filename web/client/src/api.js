export async function gql(query, variables = {}, signal) {
  const response = await fetch("/graphql", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify({ query, variables }),
    signal,
  });
  const body = await response.json();
  if (!response.ok || body.errors?.length)
    throw new Error(
      body.errors?.[0]?.message || "The request failed. Please try again.",
    );
  return body.data;
}
export const analysisQuery = `query($version:ID!,$filters:Filters!){analysis(version:$version,filters:$filters){filters adults capable excluded sample rate suppressed states{state rate sample excluded review} ages{age rate sample suppressed}}}`;
export const savedQuery = `query{comparisons{id title note datasetId filters summary createdAt}}`;
export function download(name, text, type = "text/plain") {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 30000);
}
export const pct = (n) => (n == null ? "—" : `${(n * 100).toFixed(1)}%`);
export const number = (n) =>
  n == null ? "—" : Math.round(n).toLocaleString("en-IN");
export const crore = (n) => (n == null ? "—" : (n / 1e7).toFixed(1));
