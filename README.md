# saag_web

**VAE-01 Operations Panel — the web application**

The operator-facing surface of the SaaG CSCI: a Next.js application that talks to
the CSCI over its external REST API. It is a **client**, not a CSU — it is not
installed as a component and does not appear in the CSCI's composition.

Part of [System as a Graph (SaaG)](https://github.com/canetizen/saag). The visual
identity, layout and interaction design it implements are specified in that
repository's `docs/design/UXD.md`.

## Running

```bash
npm install
npm run dev            # http://localhost:3000
```

The API is expected at http://localhost:8000; bring it up from the
[integration repository](https://github.com/canetizen/saag).

## Tests

```bash
npx playwright install --with-deps chromium   # one-time
npm run lint
npm run test:e2e
```
