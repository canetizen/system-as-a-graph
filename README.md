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

Implementation has begun. The repository has the full documentation set, the component platform that hosts the CSUs, and a scaffolded Next.js frontend ([`web/`](web/)). All ten CSUs are installed and served as components.

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

Each CSU is a **separately built and separately installable distribution**, loaded at startup as a component into a single framework process (SDD §1 decision 6). A CSU reaches its peers only by looking up a published service specification in the framework's registry — never by importing another CSU — so no CSU depends on another and the installed set is a deployment decision.

Three things follow, and they are the point of the arrangement:

- Adding a CSU to the CSCI is `pip install`; removing it is `pip uninstall`. The platform names no CSU: it discovers them through the `saag.bundles` entry point each distribution declares.
- The CSCI runs with any subset installed, which is what makes the SDP's partially built CSCI a supported configuration rather than a temporary state. `GET /platform/bundles` and `GET /platform/services` report what is actually running.
- The external REST surface is assembled at runtime from the endpoints the installed CSUs publish, so it follows a CSU appearing or going away rather than being fixed at import time.

Each CSU will eventually live in its own repository; the directories below are already independent distributions, so that move changes no code.

## Repository layout

Every backend directory is one distribution and owns its own hexagonal boundary (`api/`, `use_cases/`, `model/`, `ports/`, `adapters/`) under `src/saag_*/`. `web/` and `cli/` implement the VAE-01 user-facing applications. See [Table 4 in the SDP](docs/planning/SDP.md#4-project-structure) for the full directory mapping.

```
docs/            # SSS, SRS, SDP, SDD, UXD, CDR, STD
web/             # VAE-01: web application
cli/             # VAE-01: command-line application
contracts/       # saag-contracts: shared types, error model, service specifications
platform/        # saag-platform: framework host and the CSCI's external REST edge
msd/             # MSD: Model Setup Data Generation
scg/             # SCG: Scenario Generator
frd/             # FRD: Field Records Database
adp/             # ADP: Analytical Data Preparation
csm/             # CSM: Node-Relationship Based Core System Model (CSM-01 model_manager, CSM-02 data_binder)
vae/             # VAE: Design Verification, Analysis and Evaluation (VAE-01 operations_panel, VAE-02 design_verifier, VAE-03 design_analyzer, VAE-04 design_evaluator)
tests/           # integration and acceptance tests
LICENSE          # Apache License 2.0
```

## Getting started

The API runs on http://localhost:8000 and the web app on http://localhost:3000, whether run locally or via Docker.

### Backend (Python 3.11+)

The twelve distributions form a [uv](https://docs.astral.sh/uv/) workspace, so one command installs them all editable into one environment:

```bash
uv sync
uv run uvicorn saag_platform.app:app --reload
```

Run tests and linting:

```bash
uv run pytest
uv run ruff check .
```

Each distribution is also testable on its own — the property that lets it move to its own repository:

```bash
cd msd && uv run pytest
```

To run the CSCI against the stand-in external systems, and the Increment 1 demo against it:

```bash
docker compose -f compose.dev.yml up -d --wait
docker compose -f compose.dev.yml up gitea-seed          # one-time repository seeding
docker compose -f compose.dev.yml exec api python -m pytest tests/acceptance
```

To run a reduced CSCI, name the bundles to install or the CSUs to leave out:

```bash
SAAG_BUNDLES="saag_msd.bundle" uv run uvicorn saag_platform.app:app
SAAG_BUNDLES_EXCLUDE="vae-02,vae-03,vae-04" uv run uvicorn saag_platform.app:app
```

Bundles are discovered from *installed* distribution metadata, so a newly added CSU appears only after `uv sync`, not on saving a file.

### Web app (Next.js)

```bash
cd web
npm install
npm run dev
```

Run end-to-end tests and linting:

```bash
npx playwright install --with-deps chromium # one-time browser download
npm run test:e2e
npm run lint
```

### Docker

Run the API and web app in containers, without installing Python or Node locally.

**Development** — hot reload, with source bind-mounted into the containers:

```bash
docker compose -f compose.dev.yml up --build
```

**Production** — standalone builds, no bind mounts:

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
