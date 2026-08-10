# Critical Design Review (CDR): System as a Graph (SaaG)

**Definition:** Critical Design Review is a review milestone, not a deliverable format. This register consolidates, in one place, every design point that the SSS, SRS, and SDD deliberately left as "to be determined during the critical design phase" rather than inventing a value.

**Purpose:** This register gives the CDR board a single checklist of decisions that must be closed before those documents can be considered final. Each item has a **Status**: `Open` (default, no decision yet), `Resolved` (decision made — record it and update the source document), or `Deferred` (explicitly pushed past this CDR to a later review, with reason noted). Resolving an item means updating the corresponding source document to replace its "to be determined during the critical design phase" language with the actual decision.

---

## 1. Open Items Register

### 1.1 Verification Rule Sets (VAE-02/VAE-01 depend on these)

| ID | Item | Source | Status |
|---|---|---|---|
| CDR-01 | Topic QoS conformance rules (Durability, Reliability, Lifespan, Transport Priority) | SRS VAE-02.5–8 | Open |
| CDR-02 | Which communication services are subject to external-to-middleware consistency verification | SRS VAE-02.12 | Open |
| CDR-03 | Load-balancing rules for software-unit distribution across processor/console units | SRS VAE-02.13 | Open |
| CDR-04 | Processor core allocation conformance rules | SRS VAE-02.14–16 | Open |
| CDR-05 | Operating system settings conformance rules | SRS VAE-02.17 | Open |
| CDR-06 | Runtime environment memory allocation conformance rules | SRS VAE-02.18 | Open |
| CDR-07 | Architectural rules for design-pattern-violation detection | SRS VAE-02.22 | Open |
| CDR-08 | Conforming / non-conforming classification rules and metrics | SRS VAE-01.18 | Open |

### 1.2 Data and Process Definitions

| ID | Item | Source | Status |
|---|---|---|---|
| CDR-09 | Automatic network topology acquisition source and method | SRS MSD.6 | Open |
| CDR-10 | Mandatory source-code-repository file list | SRS MSD.19 | Open |
| CDR-11 | Definition of the system-wide simulation processes SCG's synthetic data feeds | SRS SCG.2 | Open |
| CDR-12 | Analytical Evaluation Data format/content details | SRS ADP.4 | Open |
| CDR-13 | Exportable report file format | SRS VAE-01.26 | Open |
| CDR-14 | Installation-suitability conformance scoring method | SRS VAE-04.6 | Open |

### 1.3 Capacity and Concurrency

| ID | Item | Source | Status |
|---|---|---|---|
| CDR-15 | Field Records Database storage hardware disk capacity | SSS-FRD.6 (infrastructure constraint; no SRS CSU requirement) | Open |
| CDR-16 | Concurrent user/operation count for production-pipeline and analysis/simulation operations | SRS CSM-01.30 | Open |

### 1.4 Interface Protocols

| ID | Item | Source | Status |
|---|---|---|---|
| CDR-17 | EXT-IF-01 Configuration Management Database — communication method/protocol | SDD §2.3 | Open |
| CDR-18 | EXT-IF-02 Source Code Repository — communication method/protocol | SDD §2.3 | Open |
| CDR-19 | EXT-IF-03 Software Units Package Repository — communication method/protocol | SDD §2.3 | Open |
| CDR-20 | EXT-IF-04 Network Topology Data Source — communication method/protocol (distinct from CDR-09's automatic-vs-manual acquisition-method choice) | SDD §2.3 | Open |
| CDR-21 | EXT-IF-05 System Field Data Recording Mechanism — communication method/protocol | SDD §2.3 | Open |
| CDR-22 | EXT-IF-06 LDAP Directory Service — communication method/protocol | SDD §2.3 | Open |
| CDR-23 | EXT-IF-07 Build Automation Tools / CLI — communication method/protocol, and the machine-processable result format | SDD §2.3; SRS VAE-04.8 | Open |
| CDR-24 | INT-IF-01 MSD → CSM-01 handoff — communication method/protocol | SDD §2.3 | **Resolved** — in-process component-registry service call. Specification `saag.int-if-01.model-setup-data-provisioning`, provider advertising `saag.contract.version`. See SDD §2.3.1. |
| CDR-25 | INT-IF-02 SCG → ADP handoff — communication method/protocol | SDD §2.3 | **Resolved** — in-process component-registry service call. Specification `saag.int-if-02.synthetic-data-handoff`, provider advertising `saag.contract.version`. See SDD §2.3.1. |
| CDR-26 | INT-IF-03 FRD → ADP handoff — communication method/protocol | SDD §2.3 | **Resolved** — in-process component-registry service call. Specification `saag.int-if-03.field-records-handoff`, provider advertising `saag.contract.version`. See SDD §2.3.1. |
| CDR-27 | INT-IF-04 ADP → CSM-02 handoff — communication method/protocol | SDD §2.3 | **Resolved** — in-process component-registry service call. Specification `saag.int-if-04.analytical-data-handoff`, provider advertising `saag.contract.version`. See SDD §2.3.1. |
| CDR-28 | INT-IF-05 CSM → VAE access — communication method/protocol | SDD §2.3 | **Resolved** — in-process component-registry service call. Specification `saag.int-if-05.core-system-model-access`, provider advertising `saag.contract.version`. See SDD §2.3.1. |

### 1.5 Physical Storage and Database Completeness

| ID | Item | Source | Status |
|---|---|---|---|
| CDR-29 | Physical storage technology for each of the 7 data stores (e.g. property-graph DB vs. relational vs. document store for the Core System Model) | SDD §2.4 | Open |
| CDR-30 | Entity schemas and detailed attribute definitions for all 7 persisted data stores | SDD §2.4 | Open |

### 1.6 Component Packaging and Composition

Opened by the decision that resolved CDR-24 to CDR-28: making each CSU a separately installable component (SDD §1 decision 6, §2.5) settles how the CSUs communicate but raises two questions of its own.

| ID | Item | Source | Status |
|---|---|---|---|
| CDR-31 | Distribution index and per-CSU release process — where the CSU distributions are published and how their versions are selected once each CSU lives in its own repository | SDD §2.5 | Open |
| CDR-32 | Transport for a CSU that must run outside the framework process, should one ever need to. Not required by the current design, which is single-process; recorded because SDD §2.3.1 deliberately keeps the option open | SDD §2.3.1 | Deferred — no such requirement exists; to be reopened only if one appears |

---

## 2. Impact if Left Unresolved

- **CDR-01–08** block SDD §3.6.2–§3.6.1 (Design Verifier and Findings & Reporting Manager design elements) from being fully specifiable, and leave STD test cases TC-VAE02-02, TC-VAE02-04, TC-VAE02-05, TC-VAE02-06, and TC-VAE01-06 unable to state a concrete pass/fail threshold until resolved.
- **CDR-09–16** block full closure of the MSD, SCG, ADP, VAE-01, and VAE-04 requirements and design elements they are cited against, and leave STD test cases TC-ADP-03 (CDR-12), TC-VAE04-01 (CDR-14), and TC-CSM01-04 (CDR-16) unable to state concrete acceptance data until resolved.
- **CDR-17–23** block finalizing SDD §2.3 for the 7 external interfaces and any future integration testing across them. They are unaffected by the resolution of CDR-24–28: each is a protocol choice against a system outside the CSCI boundary, which the CSCI's internal composition does not touch.
- **CDR-24–28** are **Resolved** (SDD §2.3.1). The internal interfaces no longer block SDD §2.3, and STD TC-PLT-01 verifies the mechanism. What remains open for four of the five is the *content* they carry, not the method: their call interfaces are defined alongside their providers, gated on CDR-11 and CDR-12.
- **CDR-29–30** block finalizing SDD §2.4's physical schema and any future performance/capacity testing.
- **CDR-31** blocks moving each CSU to its own repository; until it is closed the distributions are built from one repository, which the design supports but does not intend as the end state.
