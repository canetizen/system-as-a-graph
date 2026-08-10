# System as a Graph (SaaG)

**A static digital system model that represents a distributed publish–subscribe system's structural and relational architecture as a node-relationship graph — without ever running the target system.**

![License](https://img.shields.io/badge/license-Apache--2.0-green)
![Status](https://img.shields.io/badge/status-in--development-orange)

---

## Overview

SaaG models a target system's architecture as a typed graph: software units, middleware and communication services, processor/console units, topics, and messages become nodes; dependency, publishing, and consuming relationships between them become edges. Behavioral analysis is added not by executing components, but by overlaying **Analytical Evaluation Data** — derived from field records or from a scenario generator — onto this structural graph.

The model's primary purpose is architectural verification at design time: structural/circular dependencies, publisher–consumer matching, topic QoS conformance, hardware capacity conformance, and design patterns that violate architectural rules are all statically audited before any software unit is installed in the target environment. It also detects **architectural drift** between the designed structure and what is observed in the field, and supports hypothetical scenario analysis — evaluating how an entity going down, a spike in message density, or a bandwidth reduction would propagate through the architecture — without altering the structural model itself.

## Capability areas

Per the SRS, SaaG is organized into six Computer Software Components (CSCs) and ten Computer Software Units (CSUs):

| CSC | CSU | Abbreviation | Requirements |
|---|---|---|---|
| Model Setup Data Generation | MSD | MSD | 23 |
| Scenario Generator | SCG | SCG | 7 |
| Field Records Database | FRD | FRD | 5 |
| Analytical Data Preparation | ADP | ADP | 6 |
| Node-Relationship Based Core System Model | CSM-01, CSM-02 | CSM | 37 |
| Design Verification, Analysis and Evaluation | VAE-01, VAE-02, VAE-03, VAE-04 | VAE | 78 |
| **Total** | | | **156** |

## Current status

Implementation has begun. The CSCI is assembled from fourteen repositories — one per CSU, one for the shared contracts, one for the framework host, one for the web application, and this one. All ten CSUs are installed and served as components.

**MSD** and **VAE-01** are implemented, which is SDP Increment 1: an operator authenticates against a directory service, selects a project, platform and system version, reaches the four external data sources, and produces a Model Setup Data file through a background worker. `tests/acceptance/` runs that scenario end to end against the stand-in external systems. The remaining eight CSUs publish only a health endpoint so far.

## Documentation

| Document | Purpose |
|---|---|
| [`docs/requirements/SSS.md`](docs/requirements/SSS.md) | System/Subsystem Specification — the 112 CSCI-level requirements. |
| [`docs/requirements/SRS.md`](docs/requirements/SRS.md) | Software Requirements Specification — 156 CSU-scoped requirements derived from SSS. |
| [`docs/planning/SDP.md`](docs/planning/SDP.md) | Software Development Plan — WBS, 7-increment development schedule, and project structure. |
| [`docs/design/SDD.md`](docs/design/SDD.md) | Software Design Description — CSCI-wide design decisions, architecture, interfaces, database design, and CSU-level detailed design. |
| [`docs/design/UXD.md`](docs/design/UXD.md) | UI/UX Design Document — visual identity, layout, and interaction design for the VAE-01 Operations Panel. |
| [`docs/design/CDR.md`](docs/design/CDR.md) | Critical Design Review — open items register consolidating every design point left "to be determined during the critical design phase." |
| [`docs/test/STD.md`](docs/test/STD.md) | Software Test Description — qualification test cases and procedures mapped to SDD design elements and SRS requirements. |

The document set is fully traceable across documents.

## One framework, many components

Each CSU is a **separately built and separately installable distribution**, living
in its own repository, loaded at startup as a component into a single framework
process (SDD §1 decision 6). A CSU reaches its peers only by looking up a published
service specification in the framework's registry — never by importing another CSU
— so no CSU depends on another and the installed set is a deployment decision.

Three things follow, and they are the point of the arrangement:

- Adding a CSU to the CSCI is `pip install`; removing it is `pip uninstall`. The
  framework host names no CSU: it discovers them through the `saag.bundles` entry
  point each distribution declares.
- The CSCI runs with any subset installed, which is what makes the SDP's partially
  built CSCI a supported configuration rather than a temporary state.
  `GET /platform/bundles`, `/platform/components` and `/platform/services` report
  what is actually running.
- The external REST surface is assembled at runtime from the endpoints the
  installed CSUs publish, so it follows a CSU appearing or going away rather than
  being fixed at import time.

## This repository, and the others

This repository is the CSCI's **integration** repository. It publishes no
distribution: it says which versions of the CSU distributions make up a deployment,
holds the documents and the deployment stack, and carries the tests that can only
be run against the assembled CSCI.

| Repository | What it is |
|---|---|
| [`saag_contracts`](https://github.com/canetizen/saag_contracts) | Shared types, error model, document schemas, service specifications. Every CSU depends on it; it depends on no CSU |
| [`saag_platform`](https://github.com/canetizen/saag_platform) | Framework host, REST edge, background worker. Not a CSU |
| [`saag_msd`](https://github.com/canetizen/saag_msd) | MSD — Model Setup Data Generation |
| [`saag_scg`](https://github.com/canetizen/saag_scg) | SCG — Scenario Generator |
| [`saag_frd`](https://github.com/canetizen/saag_frd) | FRD — Field Records Database |
| [`saag_adp`](https://github.com/canetizen/saag_adp) | ADP — Analytical Data Preparation |
| [`saag_csm_model_manager`](https://github.com/canetizen/saag_csm_model_manager) | CSM-01 — Model Manager |
| [`saag_csm_data_binder`](https://github.com/canetizen/saag_csm_data_binder) | CSM-02 — Analytical Data Binder |
| [`saag_vae_operations_panel`](https://github.com/canetizen/saag_vae_operations_panel) | VAE-01 — Operations Panel |
| [`saag_vae_design_verifier`](https://github.com/canetizen/saag_vae_design_verifier) | VAE-02 — Design Verifier |
| [`saag_vae_design_analyzer`](https://github.com/canetizen/saag_vae_design_analyzer) | VAE-03 — Design Analyzer |
| [`saag_vae_design_evaluator`](https://github.com/canetizen/saag_vae_design_evaluator) | VAE-04 — Design Evaluator |
| [`saag_web`](https://github.com/canetizen/saag_web) | The operator's web application — a REST client, not a CSU |

Which version of each is deployed is decided in one place: this repository's
`pyproject.toml`. Until there is a package index to publish to (CDR-31), each is
resolved from its repository, and swapping a `git` entry for an index version is
the whole of that migration.

## Layout

```
docs/            # SSS, SRS, SDP, SDD, UXD, CDR, STD — one traceable set
pyproject.toml   # the composition: which distributions, at which versions
uv.lock          # the exact commits a deployment was built from
Dockerfile       # one image, every declared distribution installed
compose.yml      # deployment stack
compose.dev.yml  # the same plus the stand-in external systems
tests/
├── integration/ # the CSCI's composition: what it becomes once its CSUs are installed
├── acceptance/  # the SDP increments' demo scenarios
└── standins/    # stand-in external systems the CSCI is developed against
cli/             # VAE-01 command-line client, SDP Increment 7
LICENSE
```

## Getting started

The API runs on http://localhost:8000 and the web app on http://localhost:3000, whether run locally or via Docker.

### The CSCI (Python 3.11+)

The CSU distributions are resolved from their repositories, which are private, so
git needs a credential that may read them — `gh auth login` is enough:

```bash
uv sync
uv run uvicorn saag_platform.app:app --reload
```

That installs the twelve distributions this repository declares and starts the
framework host, which discovers whichever of them are present. Run the tests and
the linter:

```bash
uv run pytest
uv run ruff check .
```

Each CSU's own tests live in its own repository and run there; what runs here is
what needs the CSCI assembled.

To run the whole stack against the stand-in external systems, and the Increment 1
demo against it:

```bash
export GITHUB_TOKEN=$(gh auth token)     # the image build resolves the CSU repositories
docker compose -f compose.dev.yml up -d --wait
docker compose -f compose.dev.yml up gitea-seed          # one-time repository seeding
docker compose -f compose.dev.yml exec api python -m pytest tests/acceptance
```

The seeding step takes the unit trees it serves from `saag-msd`'s published test
data rather than from this repository, since that is where they live; `up
gitea-seed` brings up the step that extracts them.

```bash
```

To run a reduced CSCI — the state every SDP increment before the last is in — name
the bundles to install or the CSUs to leave out:

```bash
SAAG_BUNDLES="saag_msd.bundle" uv run uvicorn saag_platform.app:app
SAAG_BUNDLES_EXCLUDE="vae-02,vae-03,vae-04" uv run uvicorn saag_platform.app:app
```

### Working on a CSU

Point its entry in `[tool.uv.sources]` at a local checkout and `uv sync`:

```toml
saag-msd = { path = "../saag_msd", editable = true }
```

Its own repository is where its tests, lint and wheel build run; this one is where
you see it composed with the others.

### Web app (Next.js)

The operator's web application lives in its own repository,
[`saag_web`](https://github.com/canetizen/saag_web), and is built and tested there.
The dev stack below brings it up alongside the CSCI.

### Docker

Run the CSCI, the worker and the web application in containers, without installing
Python or Node locally. The image resolves the CSU repositories, so the build needs
a credential that may read them:

```bash
export GITHUB_TOKEN=$(gh auth token)
```

**Development** — hot reload, the stand-in external systems, and the tests
bind-mounted in:

```bash
docker compose -f compose.dev.yml up --build
```

**Production** — the declared distributions installed non-editable, no bind mounts,
no stand-ins:

```bash
docker compose up --build
```

Stop and remove containers:

```bash
docker compose -f compose.dev.yml down    # dev
docker compose down                       # prod
```

## License

Released under the Apache License 2.0 — see [`LICENSE`](LICENSE).
