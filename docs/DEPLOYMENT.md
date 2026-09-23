# Deploy the MERN application

## Current status

Live site: **https://upi-capability-gap.onrender.com**.

Deployment verified on 23 September 2026: the health check and GraphQL queries
return successfully; national results and demographic filters match the audited
baseline; a saved comparison remains available after a browser reload. Render
connects to the Atlas `upi` database using the restricted application user.
Local development remains available at http://127.0.0.1:3000.

## Render configuration

The repository contains `render.yaml` for a free Node web service. It serves the
React build and Express/GraphQL API together. The MongoDB database remains in
Atlas. Render Singapore is the nearest available Render region to the chosen
Atlas Mumbai database; they do not need to be in the same region to connect.

1. Sign in to Render and create a Blueprint from this repository, using branch
   `feature/mern-application`. The latest cleanup and deployment fixes live on
   that review branch. Alternatively create a Node web service using the
   settings in the table below.
2. Enter `MONGODB_URI` directly in Render's secret environment settings. Use the
   `upi_app` user and `/upi` database path. Never commit the URI or paste it into
   a public issue, PR, screenshot or README.
3. Copy the service's outbound IP ranges from Render and add them to Atlas's
   IP access list. Keep access limited to those ranges and your development IP.
4. Deploy and wait for the `/healthz` check to pass.
5. Verify overview, filters, scenario results and a saved comparison at the
   actual HTTPS URL. If the URL changes, update README with the verified URL.

| Setting | Value |
|---|---|
| Root directory | Repository root (leave blank) |
| Build command | `npm --prefix web ci --include=dev && npm --prefix web run build` |
| Start command | `npm --prefix web start` |
| Node version | `24.18.0` |
| Health check | `/healthz` |
| Host | `0.0.0.0` |
| Port | Use Render's provided `PORT` |
| Environment | `NODE_ENV=production`, `TRUST_PROXY_HOPS=1` |
| Database | Secret `MONGODB_URI` |

Do not set the root directory to `web`: the app must also read `data/processed`
and `docs/source_manifest.json`. Build dependencies must be installed for Vite.
The app uses Render's `RENDER_EXTERNAL_URL` for same-origin checks. Set
`APP_ORIGIN` explicitly if using a custom domain. `TRUST_PROXY_HOPS=1` is for
Render's reverse proxy; review this setting for a different host.

Automatic deployments are off until the review branches have been merged and
the desired production branch selected. Free services can have cold starts;
MongoDB data is stored externally and survives app restarts.

## Local DNS troubleshooting

This computer's default DNS resolver refused the Atlas SRV lookup. A
process-local `MONGODB_DNS_SERVERS=8.8.8.8` setting allowed the connection.
It belongs in the local ignored `.env` file only; do not add it to Render unless
its own environment has a demonstrated DNS problem. No system DNS was changed.

## Retired application

The replaced Streamlit code, tests, dependencies, old screenshots and superseded
PBIX have been removed from this branch. Git history preserves prior revisions.
The corrected Power BI report remains as a separate deliverable. The previous
Streamlit-hosted service must be retired in its hosting account after the MERN
site is verified; removing repository files does not delete a hosted service.

References: [Render Node deployment](https://render.com/docs/deploy-node-express-app),
[Blueprint specification](https://render.com/docs/blueprint-spec),
[Render environment variables](https://render.com/docs/environment-variables).
