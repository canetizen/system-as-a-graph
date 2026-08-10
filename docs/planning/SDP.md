# Software Development Plan (SDP): System as a Graph (SaaG)

**Definition:** This Software Development Plan (SDP) is the plan for performing the software development of the System as a Graph (SaaG) Computer Software Configuration Item (CSCI). It decomposes the work defined in the SRS into a Work Breakdown Structure (WBS) of functional deliverables, and sequences those deliverables into a series of incremental builds. Every WBS deliverable and every increment is traceable to the CSU-scoped requirements in the SRS, which are themselves traceable to the SSS via the SRS's own §7.

**Purpose:** The WBS (§1) establishes the full scope of development work, organized by Computer Software Component (CSC) and Computer Software Unit (CSU). The Incremental Development Plan (§2) sequences that work into a strictly serial series of builds — one increment at a time, in dependency-safe order. Each increment is scoped to one or more CSCs (their remaining CSUs) plus, where relevant, the corresponding slice of VAE-01 (Operations Panel), SaaG's front-door UI CSU, so that every increment produces an end-to-end, demonstrable capability.

---

## 1. Work Breakdown Structure

**Table 1. WBS Deliverable Distribution**

| No | Component | Abbreviation | CSUs | Deliverables |
|---|---|---|---|---|
| 1 | Model Setup Data Generation | SaaG-MSD | 1 | 1 |
| 2 | Scenario Generator | SaaG-SCG | 1 | 1 |
| 3 | Field Records Database | SaaG-FRD | 1 | 1 |
| 4 | Analytical Data Preparation | SaaG-ADP | 1 | 2 |
| 5 | Node-Relationship Based Core System Model | SaaG-CSM | 2 | 2 |
| 6 | Design Verification, Analysis and Evaluation | SaaG-VAE | 4 | 10 |
| **TOTAL** | | | **10** | **17** |

Each leaf bullet below cites the exact SRS requirement ID range it realizes.

- **SaaG**
  - **SaaG-MSD**
    - **MSD: Model Setup Data Generation** (MSD.1–23)
  - **SaaG-SCG**
    - **SCG: Scenario Generator** (SCG.1–7)
  - **SaaG-FRD**
    - **FRD: Field Records Database** (FRD.1–5)
  - **SaaG-ADP**
    - **ADP: Analytical Data Preparation**
      - Synthetic-Path Data Preparation (ADP.1, 3, 4, 6)
      - Field-Path Data Preparation (ADP.2, 5)
  - **SaaG-CSM**
    - **CSM-01: Model Manager** (CSM-01.1–31)
    - **CSM-02: Analytical Data Binder** (CSM-02.1–6)
  - **SaaG-VAE**
    - **VAE-01: Operations Panel**
      - Logging In & Setting Up Model Data (VAE-01.1–8)
      - Building & Viewing the Model (VAE-01.9, 19–20)
      - Editing the Model & Viewing Findings (VAE-01.17–18, 21–24)
      - Setting Up & Tracking Synthetic Data (VAE-01.11, 13–15)
      - Selecting & Tracking Field Data (VAE-01.10, 12, 16)
      - Recording Simulation Scenarios (VAE-01.25)
      - Reporting & Automating via CLI (VAE-01.26–27)
    - **VAE-02: Design Verifier** (VAE-02.1–22)
    - **VAE-03: Design Analyzer** (VAE-03.1–21)
    - **VAE-04: Design Evaluator** (VAE-04.1–8)

---

## 2. Incremental Development Plan

Increment 0 establishes the repository scaffolding, shared infrastructure, and documentation skeleton. The seven functional increments that follow are built one at a time, in dependency-safe order. Each increment delivers one or more CSCs' remaining CSUs plus the matching slice of VAE-01 (Operations Panel). Each increment also states the design, development, test, and packaging work needed to deliver it, plus its demo scenario. The SDD, UXD, CDR, and STD are updated within every increment to cover that increment's CSUs.

**Definition of Done (applies to every increment):** an increment is Done when (1) every deliverable in its CSU/Deliverable table is implemented and satisfies its SRS requirement(s); (2) every CDR item cited in its Design paragraph is Resolved or Deferred with a recorded reason; (3) everything in its Test paragraph passes; (4) every distribution in its Packaging paragraph builds, installs on its own alongside `saag-contracts`, and its bundle starts and reaches a valid state in the framework; (5) its Demo scenario runs end-to-end.

**Table 2. Increment Overview**

| # | Increment | CSUs delivered | CSCs complete |
|---|---|---|---|
| 0 | Project Scaffolding | — | — |
| 1 | Model Setup Data Generation | MSD | SaaG-MSD |
| 2 | Model Manager | CSM-01 | — |
| 3 | Design Verifier | VAE-02 | — |
| 4 | Synthetic Data Pipeline | SCG, ADP (synthetic slice) | SaaG-SCG |
| 5 | Field Data Pipeline | CSM-02, FRD, ADP (field slice) | SaaG-FRD, SaaG-ADP, SaaG-CSM |
| 6 | Design Analyzer | VAE-03 | — |
| 7 | Design Evaluator | VAE-04, VAE-01 (complete) | SaaG-VAE |

### Increment 0: Project Scaffolding

| CSU | Deliverable |
|---|---|
| — | Repository scaffolding, shared cross-CSC infrastructure, and documentation skeleton |

**Design:** No SRS requirements are implemented. Establishes the repository structure (§4), hexagonal directory conventions, and shared cross-CSC primitives every later increment depends on.

**Development:** Scaffold the repository per §4, stand up the base Docker Compose stack with placeholder services, initialize shared packages, and populate the `docs/` skeleton.

**Test:** Verify the repository builds and lints cleanly, placeholder services start healthy, and CI runs successfully against the empty scaffolding.

**Packaging:** Stand up the base Docker Compose stack and CI pipeline — no application services yet.

**Demo:** A clean checkout builds, lints, and brings up the full Docker Compose stack with no application logic, and every planned document has a placeholder under `docs/`.

**Architecture rebaseline (after Increment 0, before Increment 1):** the CSCI was rebaselined onto separately installable components — SDD §1 decision 6, §2.3.1 and §2.5 — which resolved CDR-24 to CDR-28 and opened CDR-31 and CDR-32. The scaffolding delivered here became twelve distributions, since split into a repository each (§4 Table 4a), and the aggregating application module was replaced by the framework host. No SRS requirement changed: this is a realization decision, and every requirement still traces to the same SDD §3 design element.

**Definition of Done:**
- [x] Repository scaffolded per §4 (per-CSU hexagonal layout, later split into a repository each)
- [x] Base Docker Compose stack and CI pipeline stood up
- [x] `docs/` skeleton populated for every planned document
- [x] Scaffolding builds, lints, and deploys cleanly
- [x] Every CSU distribution installs on its own and its bundle reaches a valid state in the framework
- [x] Demo run end-to-end

### Increment 1: Model Setup Data Generation

| CSU | Deliverable |
|---|---|
| MSD *(complete)* | Model Setup Data Generation (MSD.1–23) |
| VAE-01 *(ongoing)* | Logging In & Setting Up Model Data (VAE-01.1–8) |

**Completes:** SaaG-MSD

**Design:** MSD (SRS MSD.1–23) and the login/MSD-control screen (VAE-01.1–8) are fully designed. Still open: the exact protocol for each external connection and for LDAP, the topology method, and the required file list (CDR-09, CDR-10, CDR-17, CDR-18, CDR-19, CDR-20, CDR-22). The MSD → CSM-01 handoff is settled (CDR-24, SDD §2.3.1).

**Development:** Build the MSD backend — connect to, validate, and assemble data from the four external sources — plus login/session handling. On the frontend: login, project/platform/version selection, source configuration, and an MSD production/status screen.

**Test:** Verify MSD's five jobs (source connections, config pull, version tracking, file transfer, validation/assembly) and the login/production screens, then run an end-to-end MSD-file production.

**Packaging:** Stand up the MSD and VAE-01 distributions and the web service with a metadata database, a background worker, a settings template for the four sources plus LDAP, and stand-in external systems for demoing.

**Demo:** An operator authenticates via LDAP, selects a project/platform/system version, configures and connects to all four external data sources, triggers Model Setup Data production end-to-end, and observes accessibility status and any errors, producing a valid, verified Model Setup Data file.

**Definition of Done:**
- [x] MSD (MSD.1–23) and login/MSD-control (VAE-01.1–8) built and working
- [ ] CDR-09, CDR-10, CDR-17, CDR-18, CDR-19, CDR-20, CDR-22 resolved or deferred
- [x] MSD and login/workflow tests pass
- [x] Both distributions install on their own alongside `saag-contracts`, and their bundles reach a valid state in the framework
- [x] MSD/VAE-01/web services deploy together
- [x] Demo run end-to-end, automated as `tests/acceptance/`

The CDR items remain open, which is what keeps this increment from being Done. The
adapters shipped here *imply* answers to several — SQL over SQLAlchemy for the
configuration management database, git over HTTPS for the source repository, REST
for the package repository, an Ansible inventory for the topology, and LDAP direct
bind for the directory — so closing CDR-17 to CDR-20 and CDR-22 is now recording a
decision already made in code rather than making a new one. CDR-09 (automatic
versus manual topology acquisition) and CDR-10 (the mandatory file list) are
genuine choices: both paths are implemented and the shipped rules file carries a
provisional list.

### Increment 2: Model Manager

| CSU | Deliverable |
|---|---|
| CSM-01 *(complete)* | Model Manager (CSM-01.1–31) |
| VAE-01 *(ongoing)* | Building & Viewing the Model (VAE-01.9, 19–20) |

**Design:** Model Manager (SRS CSM-01.1–31) and the model-build/browsing screen (VAE-01.9, 19–20) are fully designed. Biggest gap: the model's storage technology and schema aren't decided (CDR-29–30); concurrency limits are also open (CDR-16). The CSM → VAE access mechanism is settled (CDR-28, SDD §2.3.1); what CSM-01 exposes through it is designed with this CSU.

**Development:** Build the Model Manager backend — turn Model Setup Data into a graph, keep it safe under concurrent access, support isolated evaluation copies — on a graph database. On the frontend: model browsing (search/filter/zoom/pan/attributes).

**Test:** Verify the model builds correctly, represents all node/relationship types, stays consistent under concurrent access, and browsing works — end-to-end, completing Increment 1's workflow test.

**Packaging:** Stand up the Model Manager service with a graph database and background-job handling for concurrency.

**Demo:** An operator builds the Core System Model from the Increment 1 Model Setup Data file, browses and visually navigates the resulting node-relationship structure (search/filter, zoom/pan, attribute display), while the model is served for concurrent multi-session access.

**Definition of Done:**
- [ ] Model Manager (CSM-01.1–31) and browsing screen (VAE-01.9,19–20) built and working
- [ ] CDR-16, CDR-29–30 resolved or deferred
- [ ] Model Manager and browsing tests pass, completing Increment 1's
- [ ] Model Manager service and graph database deploy together
- [ ] Demo run end-to-end

### Increment 3: Design Verifier

| CSU | Deliverable |
|---|---|
| VAE-02 *(complete)* | Design Verifier (VAE-02.1–22) |
| VAE-01 *(ongoing)* | Editing the Model & Viewing Findings (VAE-01.17–18, 21–24) |

**Design:** Design Verifier (SRS VAE-02.1–22) and the model-editor/findings screen (VAE-01.17–18, 21–24) are laid out, but most of the actual pass/fail rules are undecided — the biggest design gap in this plan (CDR-01–08).

**Development:** Build the Design Verifier's six checking engines against interim rules until CDR-01–08 close. On the frontend: the working-model editor (safe sandbox) and findings display/classification.

**Test:** Verify all six engines catch their fault conditions, editor changes never touch the real model, and findings display correctly — though some checks can only verify mechanics, not thresholds, until the rules close. End-to-end: edit and verify.

**Packaging:** Stand up the Design Verifier service — no new storage; it reads the model and writes findings to Increment 1's database.

**Demo:** An operator edits a working-model sandbox derived from the Core System Model (add/remove nodes/relationships, update attributes) and runs design verification against it — QoS conformance, publisher/consumer matching, resource/load-balancing checks, circular-dependency and architectural-rule detection — with findings presented, classified, and filterable.

**Definition of Done:**
- [ ] Design Verifier (VAE-02.1–22) and editor/findings screen (VAE-01.17–18,21–24) built and working
- [ ] CDR-01–08 — the biggest open item in this plan — resolved or deferred
- [ ] Verifier and editor/findings tests pass (to the extent rules allow)
- [ ] Design Verifier service deploys and runs
- [ ] Demo run end-to-end

### Increment 4: Synthetic Data Pipeline

| CSU | Deliverable |
|---|---|
| SCG *(complete)* | Scenario Generator (SCG.1–7) |
| ADP *(ongoing)* | Synthetic-Path Data Preparation (ADP.1, 3, 4, 6) |
| VAE-01 *(ongoing)* | Setting Up & Tracking Synthetic Data (VAE-01.11, 13–15) |

**Completes:** SaaG-SCG

**Design:** Scenario Generator (SRS SCG.1–7) and the synthetic-data setup screen (VAE-01.11, 13–15) are fully designed. Still open: what the synthetic data should simulate and the Analytical Evaluation Data format (CDR-11, CDR-12). The SCG → ADP handoff mechanism is settled (CDR-25, SDD §2.3.1); its call interface is defined with this CSU, once CDR-11 and CDR-12 allow.

**Development:** Build the Scenario Generator (capture inputs, produce and record traceable synthetic data) and the synthetic-intake half of Analytical Data Preparation. On the frontend: scenario input and production/status screens.

**Test:** Verify scenario inputs are captured, synthetic data matches the real system's structure, and the synthetic intake/assembly works — end-to-end, generating synthetic data and preparing analytical data.

**Packaging:** Stand up the Scenario Generator and Analytical Data Preparation services — no new storage; data streams straight through.

**Demo:** An operator defines scenario scope/type/interval/density/data types, triggers synthetic data production, and observes the produced data recorded and traceable to its inputs. The synthetic data is then prepared into Analytical Evaluation Data (AED), with production status tracked and any format/missing-field errors reported — completing SaaG-SCG.

**Definition of Done:**
- [ ] Scenario Generator (SCG.1–7) and setup screen (VAE-01.11, 13–15) built and working
- [ ] CDR-11, CDR-12 resolved or deferred
- [ ] Scenario Generator and synthetic-path tests pass
- [ ] Both services deploy together
- [ ] Demo run end-to-end

### Increment 5: Field Data Pipeline

| CSU | Deliverable |
|---|---|
| CSM-02 *(complete)* | Analytical Data Binder (CSM-02.1–6) |
| FRD *(complete)* | Field Records Database (FRD.1–5) |
| ADP *(complete)* | Field-Path Data Preparation (ADP.2, 5) |
| VAE-01 *(ongoing)* | Selecting & Tracking Field Data (VAE-01.10, 12, 16) |

**Completes:** SaaG-FRD, SaaG-ADP, SaaG-CSM

**Design:** Analytical Data Binder (SRS CSM-02.1–6) and Field Records Database (FRD.1–5) are fully designed, as are the field-record source-selection and binding-status screens (VAE-01.10, 12, 16). Still open: field-record storage capacity, the FRD external interface protocol, and the carried-over AED format decision (CDR-15, CDR-21, CDR-12). The FRD → ADP and ADP → CSM-02 handoff mechanisms are settled (CDR-26, CDR-27, SDD §2.3.1); their call interfaces are defined with these CSUs.

**Development:** Build the Field Records Database (upload/catalog/search), the field-intake half of Analytical Data Preparation, and the Data Binder (attach behavioral data without altering the model). On the frontend: field-record source-selection, upload/catalog, and binding-status screens.

**Test:** Verify records upload/catalog correctly, the field intake/assembly completes (never mixing with synthetic data), and binding matches data to the model without changing it — end-to-end, including a check that Increment 2's model is untouched.

**Packaging:** Stand up the Field Records Database and Data Binder services with a time-series database for telemetry; raw uploads are discarded after parsing.

**Demo:** The synthetic-sourced AED from Increment 4 is bound onto the Core System Model without altering its nodes/relationships, with binding status and provenance visible to the operator. The operator then selects System Field Records as the Analytical Evaluation Data source, uploads System Field Records (listing/searching/selecting them by project, platform, version, source, or upload time), and the resulting field-sourced AED is bound onto the model via the same source-agnostic binder — completing SaaG-FRD, SaaG-ADP (both the synthetic and field paths now work end-to-end), and SaaG-CSM.

**Definition of Done:**
- [ ] Data Binder (CSM-02.1–6), FRD (FRD.1–5), and field-selection/binding-status screens (VAE-01.10, 12, 16) built and working
- [ ] CDR-15, CDR-21, CDR-12 resolved or deferred
- [ ] Field-records, binder, and field-path tests pass, completing Increment 4's
- [ ] New services and telemetry database deploy together
- [ ] Demo run end-to-end

### Increment 6: Design Analyzer

| CSU | Deliverable |
|---|---|
| VAE-03 *(complete)* | Design Analyzer (VAE-03.1–21) |
| VAE-01 *(ongoing)* | Recording Simulation Scenarios (VAE-01.25) |

**Design:** Design Analyzer (SRS VAE-03.1–21) and the simulation-recording screen (VAE-01.25) are fully designed. No item names it directly, but it depends on one carried-over decision: the model's storage and schema (CDR-29–30).

**Development:** Build the Design Analyzer's three engines (synthetic-data simulation, field-data analysis, drift detection). On the frontend: simulation-scenario recording and high-volume field-trace charts.

**Test:** Verify all three engines produce correct results for their data sources and fault scenarios, and simulation metadata is recorded — end-to-end analysis-and-record run.

**Packaging:** Stand up the Design Analyzer service — no new storage; it reads Increment 2 and 5's databases.

**Demo:** An operator runs static analysis using synthetic-sourced AED (message/traffic flow, node/relationship-inactivity effects, load-density and fault-propagation analysis, resource-usage summaries) and using field-record-sourced AED (operational/health status, resource usage, error/timeout information, communication latency/loss, model-vs-runtime drift detection), with simulation scenario metadata (VAE-01.25) recorded against the results.

**Definition of Done:**
- [ ] Design Analyzer (VAE-03.1–21) and recording screen (VAE-01.25) built and working
- [ ] Carried-over CDR-29–30 resolved or deferred
- [ ] Design Analyzer tests pass
- [ ] Design Analyzer service deploys and runs
- [ ] Demo run end-to-end

### Increment 7: Design Evaluator

| CSU | Deliverable |
|---|---|
| VAE-04 *(complete)* | Design Evaluator (VAE-04.1–8) |
| VAE-01 *(complete)* | Reporting & Automating via CLI (VAE-01.26–27) |

**Completes:** SaaG-VAE

**Design:** Design Evaluator (SRS VAE-04.1–8) and the reporting/CLI screen (VAE-01.26–27) are fully designed. Still open: the scoring method, report file format, and CLI protocol/result format (CDR-13, CDR-14, CDR-23) — all should close before this final increment ships.

**Development:** Build the Design Evaluator (score candidates, force non-conforming on critical findings, run evaluations concurrently) and the CLI. Add PDF/JSON report generation and the report screen.

**Test:** Verify scoring, the forced non-conforming rule, concurrent evaluation, and CLI request/status — end-to-end CLI evaluation through decision and report, closing out every component.

**Packaging:** Stand up the Design Evaluator service, CLI package, and background-worker support with PDF generation — bringing every increment's services online together.

**Demo:** An automation client (e.g., Jenkins) submits an installation-suitability evaluation via CLI for one or more candidate software units; the system scores each unit against its evaluation headings and control rules, returns a blocking/non-blocking decision and machine-processable results concurrently and independently per unit, and a comprehensive summary/detailed report covering all verification, analysis, and evaluation results is generated — completing SaaG-VAE and all six CSCs.

**Definition of Done:**
- [ ] Design Evaluator (VAE-04.1–8) and reporting/CLI screen (VAE-01.26–27) built and working
- [ ] CDR-13, CDR-14, CDR-23 resolved or deferred
- [ ] Evaluator and CLI tests pass, completing the reporting test from Increments 3/6/7
- [ ] Full service stack deploys together
- [ ] Demo run end-to-end — all six components complete

---

## 3. Development Schedule

**Estimated completion: 2027-03-12.** Per §2, Increment 0 plus the seven functional increments are built strictly serially in dependency-safe order, starting **2026-07-20**. Each functional increment is a 3–6 week, demoable, end-to-end slice with backend and Operations Panel UI work running concurrently. One week = 5 business days (weekends excluded).

**Table 3. Increment Schedule Summary**

| Increment | Start | End | Duration |
|---|---|---|---|
| 0 — Project Scaffolding | 2026-07-20 | 2026-07-31 | 2w |
| 1 — Model Setup Data Generation | 2026-08-03 | 2026-08-28 | 4w |
| 2 — Model Manager | 2026-08-31 | 2026-10-02 | 5w |
| 3 — Design Verifier | 2026-10-05 | 2026-11-06 | 5w |
| 4 — Synthetic Data Pipeline | 2026-11-09 | 2026-12-04 | 4w |
| 5 — Field Data Pipeline | 2026-12-07 | 2027-01-01 | 4w |
| 6 — Design Analyzer | 2027-01-04 | 2027-02-12 | 6w |
| 7 — Design Evaluator | 2027-02-15 | 2027-03-12 | 4w |

**Figure 1. SaaG Development Schedule**

```mermaid
%%{init: { 'themeVariables': { 'excludeBkgColor': 'rgba(128,128,128,0.08)' } } }%%
gantt
    title SaaG Development Schedule (Estimated Completion: Mar 2027)
    dateFormat YYYY-MM-DD
    axisFormat %b %Y
    excludes weekends

    section Project Scaffolding
    Project Scaffolding (2w)      :scaffold1, 2026-07-20, 2026-07-31
    Inc 0 Demo (0d)               :milestone, demo0, after scaffold1, 0d

    section SaaG-MSD — Model Setup Data Generation
    Model Setup Data Generation MSD (4w)               :msd, 2026-08-03, 2026-08-28
    Inc 1 Demo (0d)                                    :milestone, demo1, after msd, 0d

    section SaaG-SCG — Scenario Generator
    Scenario Generator SCG (10d)                       :scg, 2026-11-09, 2026-11-20

    section SaaG-FRD — Field Records Database
    Field Records Database FRD (8d)                    :frd, 2026-12-18, 2026-12-29

    section SaaG-ADP — Analytical Data Preparation
    Synthetic-Path Data Preparation ADP (10d)          :adpa, 2026-11-23, 2026-12-04
    Inc 4 Demo (0d)                                    :milestone, demo4, after adpa, 0d
    Field-Path Data Preparation ADP (3d)                :adpb, 2026-12-30, 2027-01-01
    Inc 5 Demo (0d)                                    :milestone, demo5, after adpb, 0d

    section SaaG-CSM — Core System Model
    Model Manager CSM-01 (5w)                          :csm01, 2026-08-31, 2026-10-02
    Inc 2 Demo (0d)                                    :milestone, demo2, after csm01, 0d
    Analytical Data Binder CSM-02 (9d)                 :csm02, 2026-12-07, 2026-12-17

    section SaaG-VAE — Verification, Analysis, Evaluation
    Logging In & Setting Up Model Data VAE-01 (4w)       :vae01a, 2026-08-03, 2026-08-28
    Building & Viewing the Model VAE-01 (5w)               :vae01b, 2026-08-31, 2026-10-02
    Editing the Model & Viewing Findings VAE-01 (5w)       :vae01c, 2026-10-05, 2026-11-06
    Setting Up & Tracking Synthetic Data VAE-01 (4w) :vae01de, 2026-11-09, 2026-12-04
    Selecting & Tracking Field Data VAE-01 (20d) :vae01f, 2026-12-07, 2027-01-01
    Recording Simulation Scenarios VAE-01 (6w)           :vae01g, 2027-01-04, 2027-02-12
    Reporting & Automating via CLI VAE-01 (4w)             :vae01h, 2027-02-15, 2027-03-12
    Design Verifier VAE-02 (5w)                        :vae02, 2026-10-05, 2026-11-06
    Inc 3 Demo (0d)                                    :milestone, demo3, after vae02, 0d
    Design Analyzer VAE-03 (6w)                         :vae03, 2027-01-04, 2027-02-12
    Inc 6 Demo (0d)                                    :milestone, demo6, after vae03, 0d
    Design Evaluator VAE-04 (4w)                       :vae04, 2027-02-15, 2027-03-12
    Inc 7 Demo / Estimated Completion (0d)             :milestone, completion, after vae04, 0d
```

---

## 4. Project Structure

The CSCI is **fourteen repositories**, not one. Each CSU is a separately built and
separately installable distribution living in its own repository (SDD §1 decision 6,
§2.5); the shared contracts, the framework host and the operator's web application
are three more; and one repository integrates them.

Which version of each distribution makes up a deployment is decided in exactly one
place — the integration repository's `pyproject.toml`. Nothing else in the CSCI
names a version of anything.

**Table 4a. Repository Map**

| Repository | Distribution | Import package | What it is |
|---|---|---|---|
| `saag` | — | — | Integration: the composition, the documents, the deployment stack, and the tests that need the CSCI assembled |
| `saag_contracts` | `saag-contracts` | `saag_contracts` | Shared types, error model, document schemas, service specifications |
| `saag_platform` | `saag-platform` | `saag_platform` | Framework host, REST edge, background worker. Not a CSU |
| `saag_msd` | `saag-msd` | `saag_msd` | MSD |
| `saag_scg` | `saag-scg` | `saag_scg` | SCG |
| `saag_frd` | `saag-frd` | `saag_frd` | FRD |
| `saag_adp` | `saag-adp` | `saag_adp` | ADP |
| `saag_csm_model_manager` | `saag-csm-model-manager` | `saag_csm_model_manager` | CSM-01 |
| `saag_csm_data_binder` | `saag-csm-data-binder` | `saag_csm_data_binder` | CSM-02 |
| `saag_vae_operations_panel` | `saag-vae-operations-panel` | `saag_vae_operations_panel` | VAE-01 |
| `saag_vae_design_verifier` | `saag-vae-design-verifier` | `saag_vae_design_verifier` | VAE-02 |
| `saag_vae_design_analyzer` | `saag-vae-design-analyzer` | `saag_vae_design_analyzer` | VAE-03 |
| `saag_vae_design_evaluator` | `saag-vae-design-evaluator` | `saag_vae_design_evaluator` | VAE-04 |
| `saag_web` | — | — | The operator's web application. A REST client, not a CSU |

Every distribution depends on `saag-contracts` and on **no other CSU**, so the
dependency graph is one level deep and the repositories can be built, released and
worked on independently. It is enforced mechanically in each repository's own
continuous integration: the distribution is installed with the contracts and
nothing else, its tests run, and its wheel is built — a dependency on a sibling CSU
fails there as a missing module.

`saag_web` and the future command-line client sit outside the CSCI: both are clients
of its external REST surface, the CLI on the far side of EXT-IF-07 exactly as the
browser is on the far side of the web application. Neither is installed as a
component and neither appears in the CSCI's composition.

### 4.1 The integration repository

```text
saag/
├── README.md
├── pyproject.toml                     # the composition: which distributions, which versions
├── uv.lock                            # the exact commits a deployment was built from
├── .python-version
├── Dockerfile                         # one image, every declared distribution installed
├── compose.yml / compose.dev.yml      # deployment stack, and the same plus stand-ins
├── .env.example / .env                # settings template, and the development values
├── .github/                           # continuous integration
├── docs/
│   ├── requirements/                  # SSS, SRS (+ .tr translations)
│   ├── planning/                      # SDP (+ .tr)
│   ├── design/                        # SDD, UXD, CDR
│   └── test/                          # STD
├── cli/                               # VAE-01 command-line client, Increment 7
└── tests/
    ├── integration/                   # what the CSCI becomes once its CSUs are installed
    ├── acceptance/                    # the increments' demo scenarios
    └── standins/                      # stand-in external systems for development
```

The documents are one set in one repository on purpose: SSS to SRS to SDP to SDD to
STD traceability is by identifier across documents, and splitting them per CSU would
leave every coverage check in this document set unverifiable.

`tests/standins/` are the *deployment's* fixtures — a configuration management
database, a git server, a package registry, a topology tree, a directory service. A
CSU's own test data ships inside that CSU's distribution instead, so its tests need
nothing from here.

### 4.2 A CSU repository

Every CSU repository has the same shape, and `saag_contracts` and `saag_platform`
differ only in having no `bundle.py`:

```text
saag_msd/
├── README.md
├── LICENSE
├── pyproject.toml                     # this distribution alone
├── .github/                           # its own lint, test and wheel build
└── src/saag_msd/
    ├── bundle.py                      # the CSU's component
    ├── composition.py                 # the CSU's wiring
    ├── api/                           # inbound adapters
    ├── use_cases/
    ├── model/
    ├── ports/
    ├── adapters/                      # outbound adapters
    └── testing/                       # published test support + fixture data
└── tests/
    └── integration/                   # against real external systems
```

A member's `pyproject.toml` states only what is true of it in any repository — its
own metadata and a versioned dependency on the contracts. Three things that would
otherwise have to be edited when it moved were deliberately kept out of it: any
mention of a workspace, an unbounded dependency, and a licence declared somewhere
above it. The contracts sort as a third-party dependency of every CSU, because they
are one.

What the split still leaves open is where the distributions are published and how
their versions are chosen, which is CDR-31. Until it is closed the integration
repository resolves each from its repository, and swapping a `git` entry for an
index version is the whole of that migration.

**Table 5. Standard Hexagonal Directory Meaning**

| Directory | Meaning |
|---|---|
| `bundle.py` | The CSU's component: supplies its wiring's configuration from declared properties, publishes its provided service specifications, declares what it requires. The only module in a CSU that names the framework (SDD §2.5) |
| `composition.py` | The CSU's wiring: a function taking configuration as arguments and returning the wired object graph. Framework-free, so composition is testable without one |
| `api/` | Inbound adapters: **all** of them — REST endpoints, the implementations of the service specifications the CSU provides, message handlers — each calling CSU use cases |
| `use_cases/` | Application core: CSU workflows that implement SRS requirements |
| `model/` | Domain core: business objects, rules, and calculations owned by the CSU |
| `ports/` | Outbound ports: interfaces required by use cases for databases, files, queues, or external systems |
| `adapters/` | Outbound adapters: implementations of `ports/`, such as PostgreSQL, FalkorDB, LDAP, Git, REST, or file adapters |
| `testing/` | Test support the CSU *publishes*: doubles, a wired stub of itself, and fixture data, shipped in the distribution so a consuming CSU's repository can test against this CSU without installing it |
| `tests/` | Test suite scoped to the CSU, runnable on its own without the rest of the repository. `tests/integration/` holds the cases that need a real external system and skip without one |

---

## 5. Technology Stack

The technology choices below implement the WBS deliverables (§1) and are traceable to the same SRS requirement IDs used throughout this document.

**Table 6. Technology Stack Summary**

| Area | Technology | Usage |
|---|---|---|
| **Composition & Packaging** | | |
| Component framework | Pelix / iPOPO ~3.2 | Installs the CSUs as components in one process and mediates the internal interfaces INT-IF-01–05 through its service registry (SDD §1 decision 6, §2.3.1) |
| Distribution format | One wheel per CSU, discovered through a `saag.bundles` entry point | Installing a distribution is the whole act of adding a CSU (SDD §2.5) |
| Dependency management | uv, one lock file per repository | The integration repository's lock records the exact commit of every distribution a deployment was built from (SDP §4 Table 4a, CDR-31) |
| **Backend & API** | | |
| Backend language/runtime | Python | The CSUs and the framework host |
| External API | FastAPI (REST, JSON over HTTP) | The CSCI's single external surface, assembled at runtime from the endpoints the installed CSUs publish; Operations Panel and CLI/Jenkins integration (VAE-01.27) |
| Internal integration | Pelix service registry, in-process | The five internal interfaces; a remote transport is deliberately not used and not required (SDD §2.3.1, CDR-32) |
| CLI framework | Python (Click/Typer) | Automation-client interface (VAE-01.27) |
| **Data Storage** | | |
| Graph storage | FalkorDB | Core System Model with isolated model sets (CSM-01) |
| Relational storage | PostgreSQL | Structured metadata and VAE operations/findings records (MSD, FRD, VAE-01.23, VAE-01.25, VAE-01.26, VAE-02/03/04, VAE-04.8) |
| Time-series storage | VictoriaMetrics | Field-record telemetry (FRD.1, VAE-03.12–13,15) |
| **Frontend & UI** | | |
| Frontend framework | Next.js ^14.2 (React ^18.3) | Operations Panel (VAE-01) |
| Graph visualization | React Flow ^12.11 | Model browsing, search/filter, and non-destructive structural editing (VAE-01.17, VAE-01.19–20) |
| Charting / analytics visualization | Recharts ^3.9 + shadcn/ui Chart + ECharts ^6.1 | Findings, status, and KPI charts, plus high-volume field-trace charts (VAE-01.23, VAE-01.26, VAE-02/03/04) |
| UI component library | Refine ^5.0 + shadcn/ui (Radix UI) + Tailwind CSS ~3.4 | Login, CRUD/editing, findings, and report screens; LDAP-aware access-control provider (VAE-01, VAE-01.3) |
| Data/table/form layer | TanStack Query ^5.101 + TanStack Table ^8.21 + React Hook Form ^7.81 | Server-state caching, findings/report table state, and editing/login form state under Refine's hooks (VAE-01.17,21–23,26) |
| **Security & Authentication** | | |
| Authentication | LDAP direct bind (python-ldap/ldap3) | Operator authentication (VAE-01.3) |
| Session/token strategy | JWT (stateless) | REST session across UI and CLI (VAE-01.3) |
| Secrets management | Environment variables (.env) | LDAP/DB/JWT credential storage |
| **Infrastructure & Deployment** | | |
| Containerization | Docker Compose | Single-team deployment with no orchestration overhead |
| Deployment target | On-premises / private data center | LDAP and config-mgmt DB integration |
| **Background Processing & Status** | | |
| Background task execution | Procrastinate (PostgreSQL) | Long-running/concurrent operations with status, retries, chaining, and isolation (VAE-01.27, VAE-04.7, CSM-01.30, VAE-04.8) |
| Status delivery | SSE (UI) + REST polling (CLI) | Operation status delivery (VAE-01.15/16/27) |
| **External Integrations** | | |
| External-integration architecture | Ports and Adapters (Hexagonal) | Real adapters in production; fake adapters in development. Selected by the CSU's own composition, which the framework drives when it validates the CSU's component |
| Source code repository adapter | Git over HTTPS (token auth) | Source code, scripts, and config files (MSD.3, 17–20) |
| Package repository adapter | REST API (Artifactory/Nexus-style) | System Software Units Package Repository (MSD.4) |
| Configuration management DB adapter | Generic SQL adapter (SQLAlchemy) | External configuration management database (MSD.2, 8, 10–13) |
| **Reporting & Data Handling** | | |
| Report generation | PDF (WeasyPrint/ReportLab) + JSON | Summary/detailed reports; JSON shared with evaluator (VAE-01.26, VAE-04.8) |
| Raw upload retention | Discard after parsing | Minimum storage footprint (FRD.2) |
| **Testing** | | |
| Testing | pytest (backend) + Playwright (frontend/E2E) | Unit and full E2E coverage |

