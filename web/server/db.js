import mongoose from "mongoose";
import { mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";

export const Dataset = mongoose.model(
  "Dataset",
  new mongoose.Schema(
    {
      id: { type: String, unique: true, required: true },
      period: String,
      payload: mongoose.Schema.Types.Mixed,
      hashes: mongoose.Schema.Types.Mixed,
      sourceManifest: mongoose.Schema.Types.Mixed,
    },
    { timestamps: true },
  ),
);
export const Comparison = mongoose.model(
  "Comparison",
  new mongoose.Schema(
    {
      owner: { type: String, required: true, index: true },
      datasetId: { type: String, required: true },
      title: String,
      note: String,
      filters: mongoose.Schema.Types.Mixed,
      summary: mongoose.Schema.Types.Mixed,
    },
    { timestamps: true },
  ),
);

export async function connectDatabase(uri = process.env.MONGODB_URI) {
  let local;
  if (!uri) {
    if (process.env.NODE_ENV === "production")
      throw new Error("Set MONGODB_URI in production.");
    const dir = fileURLToPath(
      new URL("../.local/mongo-data/", import.meta.url),
    );
    const binaries = fileURLToPath(
      new URL("../.local/mongo-binaries/", import.meta.url),
    );
    await mkdir(dir, { recursive: true });
    await mkdir(binaries, { recursive: true });
    console.log(
      "Starting local MongoDB. The first run downloads the official database binary; later runs reuse it.",
    );
    const { MongoMemoryServer } = await import("mongodb-memory-server-core");
    local = await MongoMemoryServer.create({
      binary: { downloadDir: binaries },
      instance: { dbPath: dir, storageEngine: "wiredTiger", dbName: "upi" },
    });
    uri = local.getUri("upi");
  }
  try {
    await mongoose.connect(uri, { serverSelectionTimeoutMS: 10000 });
    await Promise.all([Dataset.init(), Comparison.init()]);
  } catch (error) {
    await mongoose.disconnect();
    if (local) await local.stop({ doCleanup: false });
    throw error;
  }
  return async () => {
    await mongoose.disconnect();
    if (local) await local.stop({ doCleanup: false });
  };
}

export async function importDataset(data) {
  // Immutable, content-addressed dataset versions preserve saved comparisons.
  await Dataset.updateOne(
    { id: data.id },
    { $setOnInsert: data },
    { upsert: true },
  );
  return data.id;
}
