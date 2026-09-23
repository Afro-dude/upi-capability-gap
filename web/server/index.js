import { fileURLToPath } from "node:url";
import express from "express";
import { connectDatabase, importDataset } from "./db.js";
import { loadDataset } from "./dataset.js";
import { createApp } from "./app.js";

const dev = process.argv.includes("--dev");
const dataset = await loadDataset();
const stopDb = await connectDatabase();
try {
  await importDataset(dataset);
} catch (error) {
  await stopDb();
  throw error;
}
const app = createApp({ activeVersion: dataset.id, dev });
let vite;
if (dev) {
  const { createServer } = await import("vite");
  vite = await createServer({
    configFile: fileURLToPath(new URL("../vite.config.js", import.meta.url)),
    server: { middlewareMode: true },
    appType: "spa",
  });
  app.use(vite.middlewares);
} else {
  const dist = fileURLToPath(new URL("../dist/", import.meta.url));
  app.use(express.static(dist));
  app.get("/{*path}", (req, res) => res.sendFile(dist + "index.html"));
}
const port = Number(process.env.PORT || 3000),
  host = process.env.HOST || "127.0.0.1";
const server = app.listen(port, host, () =>
  console.log(
    `UPI Observatory ready at http://${host}:${port} | dataset ${dataset.id}`,
  ),
);
async function shutdown() {
  server.close();
  await vite?.close();
  await stopDb();
  process.exit(0);
}
process.once("SIGINT", shutdown);
process.once("SIGTERM", shutdown);
