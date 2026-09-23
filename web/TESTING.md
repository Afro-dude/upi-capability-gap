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
