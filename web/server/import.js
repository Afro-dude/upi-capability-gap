import { connectDatabase, importDataset } from "./db.js";
import { loadDataset } from "./dataset.js";
// Administrative CLI only. No public dataset-upload endpoint.
const data = await loadDataset();
const stop = await connectDatabase();
try {
  await importDataset(data);
  console.log(`Validated and imported dataset ${data.id}`);
} finally {
  await stop();
}
