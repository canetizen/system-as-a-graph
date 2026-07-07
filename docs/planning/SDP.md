# Software Development Plan (SDP)
## System as a Graph (SaaG) Digital System Model
### Prepared in accordance with MIL-STD-498 (Data Item Description DI-IPSC-81427)

---

## 1. Scope

### 1.1 Identification

This document is the Software Development Plan (SDP) for the **System as a Graph (SaaG) Digital System Model** CSCI, prepared in the format defined by MIL-STD-498, Data Item Description DI-IPSC-81427. It plans the process by which the CSCI specified in `../requirements/SRS.md` is designed, built, and qualified.

### 1.2 System Overview

See `../requirements/SRS.md` §1.2 and `../design/SDD.md` §1.2 for the SaaG system overview. SaaG is decomposed into 6 CSCs (MSD, SCG, FRD, ADP, CSM, VAE — `../design/SDD.md` §4.1), 12 interfaces (`../design/IDD.md`), 5 data stores (`../design/DBDD.md`), and 31 SDD-CSU-aligned tests (`../test/STP.md`/`../test/STD.md`).

### 1.3 Document Overview

Section 3 states the development approach. Section 4 plans general and detailed development activities. Section 5 plans software transition. Section 6 gives the increment-based project schedule. Section 7 describes project organization and resources.

### 1.4 Relationship to Other Plans

This SDP governs the process that produces and consumes the rest of the SaaG document set: `../requirements/SRS.md` (requirements analysis), `../design/SDD.md`/`../design/IDD.md`/`../design/DBDD.md` (design), `../test/STP.md`/`../test/STD.md` (test planning), and `../reviews/CDR.md` (the open-items gate that must clear before design can be finalized and coding can proceed on the items it lists).

---

## 2. Referenced Documents

- MIL-STD-498, *Software Development and Documentation*, Data Item Description DI-IPSC-81427 (Software Development Plan).
- `../requirements/SRS.md`, `../design/SDD.md`, `../design/IDD.md`, `../design/DBDD.md`, `../test/STP.md`, `../test/STD.md`, `../reviews/CDR.md` — the SaaG MIL-STD-498 document set.

---

## 3. Overview of Required Work

### 3.1 Project Objectives

Design, build, and qualify the SaaG CSCI so that it satisfies every requirement in `../requirements/SRS.md`, consistent with the design in `../design/SDD.md`/`../design/IDD.md`/`../design/DBDD.md` and verified against `../test/STP.md`/`../test/STD.md`.

### 3.2 Development Approach

SaaG is developed **iteratively and incrementally**: each increment carries a subset of the CSCI's capability through requirements confirmation, design, coding, and test, rather than carrying the whole CSCI through each activity at once. Increments are sequenced by data dependency, reusing the dependency order already established in `../design/SDD.md` §4.2 (Concept of Execution) and `../test/STP.md` §5 (Test Schedule):

| Increment | Scope | Rationale |
|---|---|---|
| 1 | Determine tech stack and project structure | Establishes the foundation (language, frameworks, build tooling, repository layout) on which all subsequent increments build. |
| 2 | MSD component implementation and relevant sections in VAE | MSD is an independent data producer with no dependency on other CSCs; VAE sections included are those that drive the MSD production pipeline and consume its output. |
| 3 | SCG component implementation and relevant sections in VAE | SCG is an independent data producer; VAE sections included are those that drive the SCG production pipeline and consume its output. |
| 4 | FRD component implementation and relevant sections in VAE | FRD is an independent data producer; VAE sections included are those that drive the FRD production pipeline and consume its output. |
| 5 | Testing | End-to-end integration and qualification testing of the assembled CSCI, covering the full `../test/STP.md`/`../test/STD.md` test suite. |
| 6 | Packaging | Final assembly, packaging, and preparation of the qualified CSCI for transition into the target environment. |

Each increment repeats the activity cycle in Section 4.3 for its CSC(s) only.

**External interface mocking and adaptor layer**: All external interfaces (EXT-IF-01 through EXT-IF-07, `../design/IDD.md` §3.1) must be mocked during development because the real external systems are not available. An adaptor layer must be implemented to isolate the CSCI's internal logic from the specifics of each external interface, so that real interfaces can be integrated later by replacing only the adaptor implementations without modifying the CSC internals.

---

## 4. Plans for Performing Software Development Activities

### 4.1 Software Development Process

Within each increment: (a) confirm the applicable `../requirements/SRS.md` §3.2.x requirements for the CSC(s) in scope; (b) confirm/refine the applicable `../design/SDD.md` §5.x design (and `../design/IDD.md`/`../design/DBDD.md` sections it references); (c) implement the CSUs; (d) execute the applicable `../test/STP.md`/`../test/STD.md` test cases; (e) hold an increment review before the next increment begins. `../reviews/CDR.md` items relevant to an increment's CSC(s) must be `Resolved` (not `Open`) before that increment's coding activity begins.

### 4.2 General Plans for Software Development

**4.2.1 Software Development Methods**: structured decomposition following `../design/SDD.md`'s CSC/CSU breakdown; specific methodology tooling (e.g. modeling notation, code generation) is open per `../reviews/CDR.md`.

**4.2.2 Standards for Software Products**: coding standards, programming language(s), and build/version-control/CI tooling are open per `../reviews/CDR.md`. `../requirements/SRS.md` cites Jenkins (3.2.6.50) and JVM (3.2.5.8) as illustrative examples of a build-automation client and a runtime environment respectively — these are examples in the requirements text, not committed tooling decisions, and should be confirmed or replaced during design finalization.

**4.2.3 Reusable Software Products**: none identified in the current document set; to be assessed per increment.

**4.2.4 Handling of Critical Requirements**: the CSCI's security-critical requirement (LDAP-based authentication/authorization, `../requirements/SRS.md` 3.2.6.3, `../design/IDD.md` EXT-IF-06) is tracked with the same rigor as any other CDR.md item (CDR-21) and must be resolved before the VAE increment's coding activity begins.

**4.2.5 Recording Rationale**: design rationale is recorded at the point of decision — CSC-wide and CSCI-wide design decisions in `../design/SDD.md` §3/§5.x.1, database-wide decisions in `../design/DBDD.md` §3 — rather than duplicated in this plan.

**4.2.6 Access for Review**: acquirer/reviewer access arrangements to the document set and increment reviews are open per `../reviews/CDR.md`.

### 4.3 Plans for Performing Detailed Software Development Activities

For each increment (Section 3.2), the following activities are performed for that increment's CSC(s):

1. **Software Requirements Analysis** — confirm the `../requirements/SRS.md` §3.2.x requirements in scope for the increment.
2. **Software Design** — confirm/finalize the `../design/SDD.md` §5.x CSC/CSU design, the `../design/IDD.md` interfaces it uses, and the `../design/DBDD.md` stores it reads/writes.
3. **Software Coding** — implement the CSUs identified in `../design/SDD.md` §5.x for the increment's CSC(s), including the adaptor layer for external interfaces and mock implementations where real systems are unavailable.
4. **Unit and Integration Testing** — execute the `../test/STD.md` test cases traced to the increment's CSUs (per `../test/STP.md` §4).
5. **CSCI Qualification Testing** — once Increments 1–4 are complete, execute the full `../test/STP.md`/`../test/STD.md` test suite (all 31 test cases) against the assembled CSCI. Increment 5 (Testing) covers this activity in full, including any additional qualification tests needed beyond unit and integration testing.

---

## 5. Plans for Software Transition

Transition of the qualified CSCI into its target environment is performed through the production deployment pipeline described in `../requirements/SRS.md` 3.2.6.50/53/54 (Build Automation Tools/CLI, installation suitability evaluation, pipeline-blocking decisions). Specific transition logistics (installation procedures, user training materials, operational handover) are open per `../reviews/CDR.md` and are not yet defined in the current document set.

---

## 6. Project Schedule and Activity Network

Calendar dates are outside the scope of this document and depend on the project's overall schedule. The activity network follows the increment sequence in Section 3.2: Increment 1 (tech stack and project structure) → Increment 2 (MSD + relevant VAE sections) → Increment 3 (SCG + relevant VAE sections) → Increment 4 (FRD + relevant VAE sections) → Increment 5 (Testing) → Increment 6 (Packaging). An increment may not begin coding until the `../reviews/CDR.md` items affecting its CSC(s) are `Resolved`.

---

## 7. Project Organization and Resources

### 7.1 Project Organization

The following roles are needed; specific individuals, headcounts, and organizational/contractual structure are not defined in the current document set:

- Software/Project Lead — overall responsibility for this plan and increment reviews.
- Systems Engineer — maintains `../requirements/SRS.md`/`../design/SDD.md`/`../design/IDD.md`/`../design/DBDD.md` consistency across increments.
- CSC Development Team(s) — one per CSC (or grouped as needed per increment), implementing the CSUs in `../design/SDD.md` §5.x.
- Test Team — independent of the CSC development teams, executes `../test/STP.md`/`../test/STD.md` (per `../test/STP.md` §3.3).
- Configuration Management — manages versions of the document set and source code.
- Quality Assurance — audits conformance to this plan and to `../design/SDD.md`'s CSCI-wide design decisions.

### 7.2 Project Resources

**7.2.1 Personnel**: role-based only (Section 7.1); staffing levels open per `../reviews/CDR.md`.
**7.2.2 Facilities**: the test environment in `../test/STP.md` §3 (interface stand-ins, sample data) and its hardware (`CDR-15`, `CDR-16`) are required; specific facility/hardware provisioning is open per `../reviews/CDR.md`.
**7.2.3 Acquirer-Furnished Equipment, Software, Services, Documentation, and Facilities**: none identified in the current document set.
**7.2.4 Other Resources**: none identified.

---

## 8. Notes

None.
