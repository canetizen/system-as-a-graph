# Critical Design Review (CDR) — Open Items Register
## System as a Graph (SaaG) Digital System Model

---

## 1. Purpose

This is not a MIL-STD-498 data item — Critical Design Review is a review milestone, not a deliverable format. This register exists to consolidate, in one place, every design point that `../requirements/SRS.md`, `SDD.md`, and `../test/STD.md` deliberately left as "to be determined during the critical design phase" rather than inventing a value. Its purpose is to give the CDR board a single checklist of decisions that must be closed before those documents (and the tests in `../test/STD.md` that depend on them) can be considered final.

## 2. Referenced Documents

- `../requirements/SRS.md`, `SDD.md`, `../test/STD.md` — the SaaG MIL-STD-498 document set.

## 3. How to Use This Register

Each item has a **Status**: `Open` (default, no decision yet), `Resolved` (decision made — record it and update the source document), or `Deferred` (explicitly pushed past this CDR to a later review, with reason noted). Resolving an item here means updating the corresponding source document to replace its "to be determined during the critical design phase" language with the actual decision, and re-running the affected `../test/STD.md` test case(s).

## 4. Open Items Register

### 4.1 Verification Rule Sets (VAE analysis depends on these)

| ID | Item | Source | Status |
|---|---|---|---|
| CDR-01 | Topic QoS conformance rules (durability, reliability, lifespan, transport priority) | SRS 3.2.6.20 | Open |
| CDR-02 | Which communication services are subject to external-to-middleware consistency verification | SRS 3.2.6.22 | Open |
| CDR-03 | Load-balancing rules for software-unit distribution across processor/console units | SRS 3.2.6.23 | Open |
| CDR-04 | Processor core allocation conformance rules | SRS 3.2.6.24 | Open |
| CDR-05 | Operating system settings conformance rules | SRS 3.2.6.25 | Open |
| CDR-06 | Runtime environment memory allocation conformance rules | SRS 3.2.6.26 | Open |
| CDR-07 | Architectural rules for design-pattern-violation detection | SRS 3.2.6.30 | Open |
| CDR-08 | Conforming / non-conforming classification rules and metrics | SRS 3.2.6.42 | Open |

### 4.2 Data and Process Definitions

| ID | Item | Source | Status |
|---|---|---|---|
| CDR-09 | Automatic network topology acquisition source and method | SRS 3.2.1.3; SDD §4.3 | Open |
| CDR-10 | Mandatory source-code-repository file list | SRS 3.2.1.15 | Open |
| CDR-11 | Definition of the system-wide simulation processes SCG's synthetic data feeds | SRS 3.2.2.2 | Open |
| CDR-12 | Analytical Evaluation Data format/content details | SRS 3.2.4.4 | Open |
| CDR-13 | Exportable report file format | SRS 3.2.6.49 | Open |
| CDR-14 | Installation-suitability conformance scoring method | SRS 3.2.6.52 | Open |

### 4.3 Capacity and Concurrency

| ID | Item | Source | Status |
|---|---|---|---|
| CDR-15 | Field Records Database storage hardware disk capacity | SRS 3.2.3.6; STD §3.2 | Open |
| CDR-16 | Concurrent user count for production-pipeline and analysis/simulation operations | SRS 3.2.5.19; STD §3.2 | Open |

### 4.4 Interface Protocols

| ID | Item | Source | Status |
|---|---|---|---|
| CDR-17 | EXT-IF-01 Configuration Management Database — communication method/protocol | SDD §4.3 | Open |
| CDR-18 | EXT-IF-02 Source Code Repository — communication method/protocol | SDD §4.3 | Open |
| CDR-19 | EXT-IF-03 Package Repository — communication method/protocol | SDD §4.3 | Open |
| CDR-20 | EXT-IF-05 System Field Data Recording Mechanism — communication method/protocol | SDD §4.3 | Open |
| CDR-21 | EXT-IF-06 LDAP Directory Service — communication method/protocol | SDD §4.3 | Open |
| CDR-22 | EXT-IF-07 Build Automation/CLI — communication method/protocol, and the machine-processable result format | SDD §4.3; SRS 3.2.6.54 | Open |
| CDR-23 | INT-IF-01 MSD → CSM handoff — communication method/protocol | SDD §4.3 | Open |
| CDR-24 | INT-IF-02 SCG → ADP handoff — communication method/protocol | SDD §4.3 | Open |
| CDR-25 | INT-IF-03 FRD → ADP handoff — communication method/protocol | SDD §4.3 | Open |
| CDR-26 | INT-IF-04 ADP → CSM handoff — communication method/protocol | SDD §4.3 | Open |
| CDR-27 | INT-IF-05 CSM → VAE access — communication method/protocol | SDD §4.3 | Open |
| CDR-28 | EXT-IF-04 Network Topology Data Source — communication method/protocol (distinct from CDR-09's automatic-vs-manual acquisition-method choice) | SDD §4.3 | Open |

### 4.5 Physical Storage Technology

| ID | Item | Source | Status |
|---|---|---|---|
| CDR-29 | Physical storage technology for each of the 5 data stores (e.g. property-graph DB vs. relational vs. document store for the Core System Model) | SDD §4.4 | Open |

### 4.6 Database Design Completeness

| ID | Item | Source | Status |
|---|---|---|---|
| CDR-30 | Working Model persistence — SDD §4.4's list of 5 data stores has no entity for the working model created/edited by the Working Model Editor | SDD §4.4; SDD §5.6.3.4; SRS 3.2.6.17 | Open |
| CDR-31 | Findings/Operations/Reports persistence — SDD §4.4's list of 5 data stores has no entity for the findings, operations, or reports produced/displayed by the Findings & Reporting Manager | SDD §4.4; SDD §5.6.3.10; SRS 3.2.6.44–49 | Open |
| CDR-32 | Entity schemas and detailed attribute definitions for all persisted data stores | SDD §4.4 | Open |

## 5. Impact if Left Unresolved

- **CDR-01–08** block `TC-VAE-06` (`../test/STD.md`) from being fully executable — that test case explicitly notes this dependency.
- **CDR-09–16** block full closure of the MSD, SCG, FRD, ADP, and VAE test cases they're cited in.
- **CDR-17–28** block finalizing `SDD.md` §4.3 and any integration testing across the 12 interfaces.
- **CDR-29, 32** block finalizing `SDD.md` §4.4's physical schema, entity schemas, and attribute definitions, and any performance/capacity testing.
- **CDR-30–31** block finalizing `SDD.md` §4.4's data-store inventory and any testing that depends on persisted Working Model, Finding, Operation, or Report data.

## 6. Notes

None.
