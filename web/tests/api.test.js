import test, { before, after } from "node:test";
import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";
import { MongoMemoryServer } from "mongodb-memory-server-core";
import { connectDatabase, importDataset, Dataset } from "../server/db.js";
import { loadDataset } from "../server/dataset.js";
import { createApp } from "../server/app.js";

let mongo, stopDb, server, url, data;
before(async () => {
  // A separate temporary database: never touch the application's saved notes.
  mongo = await MongoMemoryServer.create({
    binary: {
      downloadDir: fileURLToPath(
        new URL("../.local/mongo-binaries/", import.meta.url),
      ),
    },
  });
  stopDb = await connectDatabase(mongo.getUri("upi_test"));
  data = await loadDataset();
  await importDataset(data);
  server = createApp({ activeVersion: data.id }).listen(0, "127.0.0.1");
  await new Promise((resolve) => server.once("listening", resolve));
  url = `http://127.0.0.1:${server.address().port}/graphql`;
});
after(async () => {
  if (server) await new Promise((resolve) => server.close(resolve));
  await stopDb?.();
  await mongo?.stop();
});
async function request(query, variables = {}, cookie = "", headers = {}) {
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(cookie ? { Cookie: cookie } : {}),
      ...headers,
    },
    body: JSON.stringify({ query, variables }),
  });
  return {
    status: response.status,
    body: await response.json(),
    cookie: response.headers.get("set-cookie")?.split(";")[0],
    headers: response.headers,
  };
}
const save = `mutation($version:ID!,$filters:Filters!){saveComparison(version:$version,filters:$filters,title:"Test comparison",note:"Test only"){id datasetId summary filters}}`;

test("GraphQL serves the validated baseline and immutable version", async () => {
  const r = await request("{dataset{id} analysis{rate sample states{state}}}");
  assert.equal(r.status, 200);
  assert.equal(r.body.errors, undefined);
  assert.equal(r.body.data.dataset.id, data.id);
  assert.equal(r.body.data.analysis.sample, 106631);
  assert.equal(r.body.data.analysis.states.length, 36);
  assert.match(r.headers.get("content-security-policy"), /script-src 'self'/);
  assert.equal(r.headers.get("cache-control"), "no-store");
  await importDataset({ ...data, period: "Should not overwrite" });
  assert.equal((await Dataset.findOne({ id: data.id })).period, data.period);
});
test("saved comparisons persist with server-calculated figures and browser ownership", async () => {
  const r = await request(save, {
    version: data.id,
    filters: { sector: "Rural", sex: "Female" },
  });
  assert.equal(r.body.errors, undefined);
  const saved = r.body.data.saveComparison;
  assert.ok(saved.summary.sample > 30);
  assert.equal(saved.filters.sex, "Female");
  const own = await request(
    "{comparisons{id datasetId summary}}",
    {},
    r.cookie,
  );
  assert.equal(own.body.data.comparisons[0].id, saved.id);
  const other = await request("{comparisons{id}}");
  assert.deepEqual(other.body.data.comparisons, []);
  const remove = "mutation($id:ID!){deleteComparison(id:$id)}";
  assert.equal(
    (await request(remove, { id: saved.id }, other.cookie)).body.data
      .deleteComparison,
    false,
  );
  assert.equal(
    (await request(remove, { id: saved.id }, r.cookie)).body.data
      .deleteComparison,
    true,
  );
  assert.deepEqual(
    (await request("{comparisons{id}}", {}, r.cookie)).body.data.comparisons,
    [],
  );
});
test("old saved dataset versions remain queryable after another import", async () => {
  await importDataset({ ...data, id: "test-later-version" });
  assert.equal(
    (await request("query($id:ID!){dataset(version:$id){id}}", { id: data.id }))
      .body.data.dataset.id,
    data.id,
  );
  assert.match(
    (await request('query{dataset(version:"missing"){id}}')).body.errors[0]
      .message,
    /not found/,
  );
});
test("invalid filters and scenario assumptions fail without fabricated results", async () => {
  assert.match(
    (await request('{analysis(filters:{state:"Atlantis"}){rate}}')).body
      .errors[0].message,
    /Unknown state/,
  );
  assert.match(
    (await request("{scenario(share:1.1){newlyCapable}}")).body.errors[0]
      .message,
    /between 0 and 1/,
  );
  assert.match(
    (
      await request(
        '{scenario(share:0.1,filters:{state:"Himachal Pradesh"}){newlyCapable}}',
      )
    ).body.errors[0].message,
    /unavailable/,
  );
  const r = await request("{scenario(share:0.1){newlyCapable}}");
  assert.ok(Math.abs(r.body.data.scenario.newlyCapable - 46946563.402) < 0.01);
});
test("cross-origin writes and oversized or complex requests are rejected", async () => {
  assert.equal(
    (
      await request("{comparisons{id}}", {}, "", {
        Origin: "https://untrusted.example",
      })
    ).status,
    403,
  );
  assert.equal((await request("x".repeat(13000))).status, 400);
  assert.equal(
    (
      await request(
        "{" +
          Array.from({ length: 121 }, (_, i) => `a${i}:comparisons{id}`).join(
            " ",
          ) +
          "}",
      )
    ).status,
    400,
  );
  assert.equal(
    (await request("{comparisons{id}}", { unused: "x".repeat(40000) })).status,
    413,
  );
});
