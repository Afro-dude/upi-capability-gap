# UPI Observatory — MERN application

React frontend, Express/Node GraphQL server, and MongoDB persistence. Uses the
audited aggregates in `../data/processed/`; no raw respondent data or Python
server is required to run it.

## Run locally

Install Node.js 24 LTS (or a supported version >=22.12), then from this folder:

```sh
npm ci
npm run dev
```

Open **http://127.0.0.1:3000**. On Windows, use `npm.cmd` if PowerShell blocks
`npm.ps1`. Keep the terminal running. Stop with Ctrl+C.

Without `MONGODB_URI`, development starts a real local MongoDB process and
persists it under `.local/mongo-data/`. The first run downloads the official
MongoDB binary (about 800 MB on Windows); subsequent runs reuse the cached
binary. Interrupted downloads resume when you restart. No separate MongoDB
installation is necessary. An existing MongoDB server can instead be configured
in `.env` using the example file. Do not run two copies against the same local
database directory.

## Pages

- **Overview:** audited national estimates, separate participation indicators,
  conditional internet-user estimates, and household internet barriers.
- **Capability explorer:** weighted state, age, sector and sex filters; small
  sample suppression; alphabetical comparison table; CSV export.
- **NPCI transactions:** observed classified volumes and a state scatter plot,
  with national missing attribution clearly shown. No redistribution or fitted line.
- **What-if calculator:** a user-assumed share times the estimated excluded
  population. National demographic groups only; no ML or transaction forecasting.
- **Methods & sources:** definitions, official reconciliation, allocation
  assumptions and downloadable source hashes.
- **Saved comparisons:** MongoDB-backed notes, filters and immutable dataset
  versions. The server computes the saved statistics.

Saved notes belong to a randomly generated HttpOnly browser cookie. They are
not user accounts or cross-device backups. The cookie expires after 30 days;
clearing it removes access. Do not use this demo to store confidential notes.

## Validation and builds

```sh
npm test
npm run build
npm start
```

Tests use a separate temporary MongoDB database and do not delete application
notes. They verify aggregation, suppression, scenario bounds, source validation,
immutable imports, browser isolation, deletion ownership and request limits.
The first test run also needs the MongoDB binary if it is not already cached.

Production assets are generated in `dist/`, including locally served fonts.
`npm start` serves the built app and GraphQL from the same origin.

## Data imports

Run the existing offline Python pipeline to regenerate the aggregates. Then:

```sh
npm run import:data
```

With the automatic local database, stop the app before running the import
command; only one process may own its database directory. The server also
validates and imports the current aggregates on startup. Restart it after an
import to activate the new snapshot. Import checks reject duplicate demographic
cells, invalid states/demographics, incomplete quarters, inconsistent populations,
mismatched transaction joins, redistributed observed volumes and unknown
official-reference failures. Raw state-month duplicate checks remain in the
upstream Python pipeline.

The snapshot ID hashes the aggregate file hashes and source manifest. Existing
versions are never overwritten, so saved comparisons can reopen their original
figures. Keep `data/processed/` and `docs/source_manifest.json` alongside `web/`
when distributing the application.

## Hosting configuration

The repository includes a Render configuration. Follow
[the deployment guide](../docs/DEPLOYMENT.md) for the production branch,
Atlas network access, health checks and the final website URL.

Build first, then set these environment variables on the host:

```dotenv
NODE_ENV=production
HOST=0.0.0.0
PORT=3000
APP_ORIGIN=https://your-real-domain.example
MONGODB_URI=mongodb+srv://<credentials-and-cluster>/upi
```

Use your host's secret store for the URI, HTTPS for the public app, and a
restricted database user. Production requires an external MongoDB URI; the
automatic local database is for development. Supply the aggregate files in the
deployment as described above. Account-based sign-in and shared team workspaces
are not part of this version.

The API exposes POST `/graphql`; there is no REST analytics API or FastAPI
service. It enforces same-origin JSON requests, input and query limits, rate
limits, and cookie-scoped note access. Configure `APP_ORIGIN` to the exact
external origin when deploying behind a reverse proxy.
