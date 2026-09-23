# Verification

Verified on Windows with Node 24.18.0 and MongoDB 8.2.6.

- `npm test`: 14 passing tests, including real MongoDB/GraphQL integration.
- `npm run build`: production React bundle succeeds; fonts are served locally.
- `npm audit`: no reported vulnerabilities at installation.
- Browser checks: overview, demographic filtering, HP review note, scenario
  presets, NPCI state search, official reference details, saved comparison
  creation/reopening, and persistence after a server restart.
- Responsive checks: 1366px desktop and 390px mobile viewports, with working
  navigation and no horizontal page overflow on the mobile overview.
- Built app served successfully by Express, using the persistent local database.

The in-app browser did not report a completed CSV download event. The export
uses the standard Blob/download-anchor mechanism; verify file saving in your
normal browser as part of acceptance testing.

API tests run against a disposable, separate database. Browser checks left one
clearly labelled example comparison in the local demo browser.

## Public deployment verification — 23 September 2026

At https://upi-capability-gap.onrender.com, `/healthz` returned 200/ready.
GraphQL returned 106,631 respondents, 48.6316% national capability, and
46,946,563.4 hypothetically newly capable people under the 10% assumption.
The browser's rural-female filter returned 29.8% capability and 30,108
respondents. A clearly labelled example comparison was saved and remained
available after reloading the public HTTPS page. No browser console errors
were observed during the filter check.
