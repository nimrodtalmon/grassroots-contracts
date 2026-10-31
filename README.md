# Grassroots Contracts

The grassroots social contracts of Ehud Shapiro's GLP project, as a browsable site: a graph of the
contracts, each contract's text, the cascade from English to running code ("under the hood"), and a
live app for every compiled contract: four people, each with an agent running the compiled platform.

- **Site** (static): `index.html`, `data.js`, `stack/` (the cascade's layers, loaded on demand).
  Served by GitHub Pages and by the live server.
- **Live server**: `Dockerfile`, `render.yaml`. GLP at a pinned commit, with `live/overlay` on top:
  a generated live harness per contract (`programs/vglp/cva/live_<c>`), the server (`live_server`),
  and experimental contracts written for this site (`programs/<name>`): AGORA (barter), DAO, Funded DAO, Liquid DAO, Stays, Library, Joint Accounts and Recommendations; `tools/contracts.py` writes the last six.
  The app page is `live/web/app.html?c=<contract>`, driven by `live/web/specs/<c>.json`, read off
  each platform's menu declaration.

## Deploy on Render

New → Blueprint → this repository. The free plan works (it sleeps when idle and acts are slow on its small CPU); Starter is faster. At most MAX_WORLDS (default 3) contracts run at once.
A contract's world starts on its first visit (about a minute) and is dropped after an hour idle.

## Rebuild

With a GLP clone at the pinned commit and Dart installed:

    cp -r live/overlay/programs/* <GLP>/programs/ && bash tools/add_to_cascade.sh <GLP>
    python3 -I tools/contracts.py <GLP>                       # rewrites the six generated contracts
    (cd <GLP> && for c in agora dao fdao stay lib ldao joint rec; do bash cascade.sh $c; done)
    python3 -I tools/gen_harness.py <GLP>/cascade/<C>/platform.vglp <GLP>/programs/vglp/cva/live_<c> <C>
    python3 -I tools/build_specs.py <GLP> live/web/specs <pdf_contracts.json>
    python3 -I tools/build_data.py <pdf_contracts.json> <GLP> .
