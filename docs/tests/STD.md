# Software and System Test Document
## System-as-a-Graph (SaG)

Test strategy, environment, cases, and pass criteria for verifying that SaG meets its requirements — from individual function correctness up through end-to-end interactive and CI/CD pipeline behaviour.

---

| Field | Value |
|---|---|
| Document | Software and System Test Document (STD) |
| Product | System-as-a-Graph (SaG) |
| Version | 0.1 (Baseline Draft) |
| Date | 2026-06-29 |
| Status | Draft — for review |
| Standards | ISO/IEC/IEEE 29119-3 (test documentation); ISO/IEC/IEEE 12207:2026 (V&V) |
| Aligns to | SaG SRS v0.1, SaG SAD v0.1, SaG SDD v0.1 |
| Reuses | Software-as-a-Graph (`saag/`) test suite and infrastructure |

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Test Strategy](#2-test-strategy)
3. [Test Environment](#3-test-environment)
4. [Unit Tests](#4-unit-tests)
5. [Integration Tests](#5-integration-tests)
6. [System Tests](#6-system-tests)
7. [Performance and Scalability Tests](#7-performance-and-scalability-tests)
8. [Independence, Drift, and Gate Conformance Tests](#8-independence-drift-and-gate-conformance-tests)
9. [Acceptance Criteria](#9-acceptance-criteria)
10. [Traceability Matrix](#10-traceability-matrix)
11. [Appendices](#11-appendices)

---

## 1. Introduction

### 1.1 Purpose

This document specifies how SaG is tested. It defines the test strategy, cases, pass criteria, and procedures verifying that the system meets the SRS — covering structural data ingestion, model construction, analytical-data preparation, validation, analysis, simulation, drift detection, and the CI/CD deployment-suitability gate, across both the interactive (UI/API) and automation (CLI/CI) delivery mechanisms.

### 1.2 Scope

Testing spans six levels:

| Level | What it verifies | Section |
|---|---|---|
| Unit | Individual functions/services compute correct results | §4 |
| Integration | Subsystems compose correctly through the pipeline | §5 |
| System | End-to-end interactive and CI flows produce expected outputs | §6 |
| Performance | Operations complete within time budgets at each scale | §7 |
| Conformance | Independence guarantee, drift detection, and gate decisions are correct | §8 |
| Acceptance | All user- and automation-facing requirements are satisfied | §9 |

Consistent with SRS A-3 / SAD ADR-05, the learned-prediction layer is out of scope; no GNN/statistical-correlation validation appears here. The reused `saag/` analytical core retains its own unit suite (anti-patterns, structural metrics, simulation); this document adds the SaG envelope and re-verifies the reused capabilities in their SaG (structure-only) configuration.

### 1.3 References

| Document | Description |
|---|---|
| SaG SRS v0.1 | Software Requirements Specification |
| SaG SAD v0.1 | Software Architecture Description |
| SaG SDD v0.1 | Software Design Description |
| ISO/IEC/IEEE 29119-3 | Software testing — Test documentation |
| ISO/IEC/IEEE 12207:2026 | Software life cycle processes |

### 1.4 Document Conventions

- Test IDs follow `<LEVEL>-<MODULE>-<NN>` — e.g. `UT-MKV-01`, `IT-CSM-01`, `ST-GATE-01`, `IND-01`, `AC-01`.
- `@pytest.mark.<tag>` indicates the pytest marker used to select or exclude a test.
- Pass criteria use **shall** language matching the SRS requirement verified.
- Requirement cross-references use SRS v0.1 IDs (e.g. `SRS-CSM-010`).

### 1.5 Glossary

| Term | Definition |
|---|---|
| SUT | System under test |
| Overlay | Analytical Evaluation Data attached to a model (field or synthetic) |
| Independence guarantee | The invariant that analytical data never reaches structural analysis |
| Drift | Divergence between designed structure and runtime-observed structure |
| Gate | The CI deployment-suitability evaluation and decision |
| Reference system | A fixed, hand-curated topology used as a deterministic oracle |
| Mock source | A stub `IModelSetupSource` returning fixed payloads |

### 1.6 Change History

| Version | Date | Summary |
|---|---|---|
| 0.1 | 2026-06-29 | Initial baseline aligned to SaG SRS/SAD/SDD v0.1. |

---

## 2. Test Strategy

### 2.1 Test pyramid

| Level | Distribution | Speed | Infrastructure |
|---|---|---|---|
| Unit | ~65% | Milliseconds | None (pure Python, `MemoryRepository`, mock sources) |
| Integration | ~20% | Seconds | Neo4j (Docker) + test stores |
| System | ~10% | Seconds–minutes | Full stack + CLI/CI client |
| Conformance / Acceptance | ~5% | Minutes | Full environment |

### 2.2 Entry and exit criteria

**Entry:** code compiles; all unit tests pass locally; test Neo4j and test stores reachable; mock sources configured.

**Exit (release):** all planned tests executed; no Critical/High defects open; unit coverage ≥ 80% per new module; **all independence-conformance tests (§8.1) pass**; drift and gate conformance tests pass; performance budgets met; all acceptance criteria pass.

> The independence-conformance suite (§8.1) is a hard release gate: a single failure blocks release regardless of other results, because it protects the framework's core claim.

### 2.3 Schedule

| Phase | Trigger | Output |
|---|---|---|
| Unit | Continuous (TDD) | Coverage report, CI badge |
| Integration | Per module completion | Integration report |
| System | After integration passes | End-to-end report |
| Performance | After system stability | Benchmark CSV |
| Conformance | After system stability | Independence/drift/gate report |
| Acceptance | Before milestone | Signed acceptance checklist |
| Regression | Per CI run | Regression report |

---

## 3. Test Environment

### 3.1 Hardware

| Component | Minimum | Recommended |
|---|---|---|
| CPU | 2 cores | 4+ cores |
| RAM | 8 GB | 16 GB |
| Storage | 10 GB SSD | 50 GB SSD |

### 3.2 Software stack

| Software | Version | Purpose |
|---|---|---|
| Python | 3.11 | Runtime and tests |
| pytest (+cov, +timeout, +asyncio) | current | Test framework, coverage, async API tests |
| httpx | current | REST API test client |
| Node.js | 20+ | Next.js UI build/test |
| Neo4j | 5.x Community | Core System Model store |
| Docker / Compose | current | Stack and store isolation |
| python-ldap (or mock) | current | LDAP authenticator tests |

### 3.3 Markers and infrastructure

```ini
# pytest.ini (additions)
markers =
    slow: long-running tests
    integration: requires Neo4j on 7688
    api: requires the full Docker stack
    ingestion: requires mock external sources (CMDB/SCM/Package/Topology)
    gate: deployment-suitability gate scenarios
    security: LDAP/authorization scenarios
```

- **Unit** — `MemoryRepository` + in-memory test stores + mock `IModelSetupSource`; no external services.
- **Integration** — Neo4j on 7688 (`docker-compose.test.yml`); ephemeral Result and Field-Record stores.
- **System/API** — full stack (Neo4j, FastAPI 8000, Next.js 7000) plus a mock LDAP and mock source endpoints.

### 3.4 Mock external sources

Each `IModelSetupSource` has a deterministic stub returning a fixed payload for a known `Identity`, plus fault stubs that raise `SourceAccessError`, return malformed payloads, or omit required fields — exercising the MKV error paths (SRS-MKV-009).

### 3.5 Running tests

```bash
# Fast unit tests
pytest tests/ -m "not integration and not api" -v
# Integration (Neo4j on 7688)
docker compose -f docker-compose.test.yml up -d && pytest tests/ -m integration -v
# Full stack
docker compose up -d --build && pytest tests/ -m "api or gate" -v
# Independence conformance (release gate)
pytest tests/ -m "not api" -k "independence" -v
```

---

## 4. Unit Tests

### 4.1 MKV — Model Setup Data Generation

| Test ID | Description | Expected Result |
|---|---|---|
| UT-MKV-01 | `IModelSetupSource.test_connection` reports availability | Status reflects mock reachable/unreachable |
| UT-MKV-02 | Build Software Unit Version Inventory from CMDB payload | Inventory lists names/versions; effective version flagged |
| UT-MKV-03 | SCM fetch records file metadata | Each file carries name, path, commit, branch, package, timestamp |
| UT-MKV-04 | Manual topology entry accepted | Topology params merged into payload |
| UT-MKV-05 | Field/entity presence validation | Missing required field → `incomplete`/`failed` with error detail |
| UT-MKV-06 | Required-source access error | `status="failed"`, error `{reason, source, identity, ts}` recorded |
| UT-MKV-07 | Format incompatibility on a source | Reported and recorded; not silently dropped |
| UT-MKV-08 | Successful ingest emits Model Setup Data | `status="succeeded"`; artifact carries identity + provenance |

### 4.2 SUR — Scenario Generator

| Test ID | Description | Expected Result |
|---|---|---|
| UT-SUR-01 | Honour scenario inputs (scope/type/range/density/types) | Output reflects all inputs |
| UT-SUR-02 | Schema/field-name parity with field records | Generated records pass the field-record schema validator |
| UT-SUR-03 | Value-range constraint conformance | All values within configured ranges |
| UT-SUR-04 | Provenance recorded | Scenario name, time, identity, inputs persisted |
| UT-SUR-05 | Hand-off to AVH | `SyntheticDataset` accepted by `AnalyticalDataService` |

### 4.3 AVH — Analytical Data Preparation

| Test ID | Description | Expected Result |
|---|---|---|
| UT-AVH-01 | Prepare from synthetic | `AnalyticalEvaluationData(source_type="synthetic")` produced |
| UT-AVH-02 | Prepare from field records | `source_type="field"`; observations mapped to entity ids |
| UT-AVH-03 | Format/unreadable detection | Issue reported and recorded |
| UT-AVH-04 | Missing-field detection (synthetic) | Issue reported; partial run flagged |
| UT-AVH-05 | Source provenance preserved | `source_type`/`scenario_ref` retained downstream |

### 4.4 CSM — Core System Model

| Test ID | Description | Expected Result |
|---|---|---|
| UT-CSM-01 | Pre-build validation rejects malformed setup | `incomplete model`; no graph written |
| UT-CSM-02 | All mandated node types representable | System/Segment/CSCI/CSC/CSU/Role/Console/Processor/Network/Middleware/Comm/Topic/Message present |
| UT-CSM-03 | All mandated edge types representable | runs-on, uses-service, publishes, subscribes, depends-on, role-assignment present |
| UT-CSM-04 | `DEPENDS_ON` derivation (reused) | Dependent→dependency edges derived with weights |
| UT-CSM-05 | Identity stamp on nodes/edges | Every element carries `{project, platform, version}` |
| UT-CSM-06 | Model metadata recorded | setup-data ref, time, identity, status persisted |
| UT-CSM-07 | Unmatched analytical record reported | Observation with no structural counterpart flagged |
| UT-CSM-08 | Missing entity / invalid edge reported during build | Recorded with detail |

### 4.5 DAD — validation, analysis, findings (structure-only path)

| Test ID | Description | Expected Result |
|---|---|---|
| UT-DAD-01 | QoS conformance: Durability/Reliability/Lifespan/TransportPriority | Non-conformances detected per parameter |
| UT-DAD-02 | Pub/sub matching: topic with no publisher | Finding emitted |
| UT-DAD-03 | Pub/sub matching: topic with no consumer | Finding emitted |
| UT-DAD-04 | Same-named topics, differing content | Finding emitted |
| UT-DAD-05 | Cyclic dependency detection | Cycle reported with member ids |
| UT-DAD-06 | Broken/invalid/unmatched structural relationship | Finding emitted |
| UT-DAD-07 | Anti-pattern detection (reused) | Configured smells detected |
| UT-DAD-08 | Non-middleware comm consistency (source/target/message/direction) | Mismatch detected |
| UT-DAD-09 | Load-balancing distribution analysis | Violation of configured rule detected |
| UT-DAD-10 | Finding fields populated | id, type, description, affected entity, rule, evidence, severity all present |
| UT-DAD-11 | Result classification | "conformant" / "non-conformant" set per criterion |
| UT-DAD-12 | Causality links between findings | `caused_by` populated within one operation |
| UT-DAD-13 | What-if integrity guard | Integrity-breaking edit rejected; valid edit accepted |

### 4.6 Reused-core re-verification (SaG configuration)

| Test ID | Description | Expected Result |
|---|---|---|
| UT-RC-01 | `ValidationService` runs in structure-only mode | Prediction path not exercised; structural findings only |
| UT-RC-02 | Reused anti-pattern/structural tests pass unchanged | Existing `saag/` suite green |

### 4.7 Coverage targets (new modules)

| Module | Target |
|---|---|
| `ingestion/` | 80% |
| `scenario/` | 80% |
| `analytical/` | 80% |
| `orchestration/` (drift, findings, gate, reporting) | 82% |
| `identity/`, `security/` | 80% |
| **New-code total** | **≥ 80%** |

---

## 5. Integration Tests

Marker `@pytest.mark.integration` (Neo4j on 7688) unless noted.

### 5.1 Ingestion → Core System Model

| Test ID | Description | Expected Result |
|---|---|---|
| IT-INGEST-01 | Mock sources → Model Setup Data → CSM | Built graph matches the reference system node/edge counts |
| IT-INGEST-02 | Ingested model equals legacy JSON import | CSM from MKV is structurally identical to `import_graph.py` on the same reference system |
| IT-INGEST-03 | Required-source failure aborts build | No partial model persisted; `failed` recorded |

### 5.2 Overlay binding (independence-preserving)

| Test ID | Description | Expected Result |
|---|---|---|
| IT-OVERLAY-01 | Bind field overlay | Observations stored in separate store; structural graph unchanged |
| IT-OVERLAY-02 | Composed read model exposes both | DAD reads structure + overlay; analysis services receive structure only |

### 5.3 Drift detection

| Test ID | Description | Expected Result |
|---|---|---|
| IT-DRIFT-01 | Injected missing-at-runtime entity | `missing_at_runtime` finding for that entity |
| IT-DRIFT-02 | Injected runtime-only topic | `runtime_only_topic` finding |
| IT-DRIFT-03 | Injected attribute conflict | `attribute_drift` finding |

### 5.4 Deployment-suitability gate

| Test ID | Description | Expected Result |
|---|---|---|
| IT-GATE-01 | Four evaluation headings executed | Structural/interface/dependency/resource checks run |
| IT-GATE-02 | Weighted scoring | Score matches expected from rule weights/results |
| IT-GATE-03 | Per-unit independent operation ids | Distinct immutable results per unit |

### 5.5 API and persistence

| Test ID | Description | Expected Result | Marker |
|---|---|---|---|
| IT-API-01 | Identity selection endpoints | Projects/platforms/versions; effective flag set | api |
| IT-API-02 | Result retrieval is immutable | Re-running an operation never overwrites a prior `operation_id` | api |
| IT-API-03 | Report export contains mandated fields | Report includes identity, model, data source, op id/type, times, result, findings, severities | api |

---

## 6. System Tests

End-to-end flows across delivery mechanisms.

| Test ID | Scenario | Pass criteria |
|---|---|---|
| ST-E2E-01 | Interactive structure-only flow: select identity → ingest → build → analyze/validate → findings → report | All steps complete; findings classified; report exported |
| ST-SCEN-01 | Scenario simulation: SUR → AVH → overlay → simulate failure/load | Propagation path and top-entity indicators produced; structure unchanged |
| ST-DRIFT-01 | Field drift: upload field records → AVH → overlay → detect drift | All three drift categories detected against a seeded delta |
| ST-GATE-01 | CI gate: automation client → `/gate/evaluate` → decision | Machine-readable per-unit + batch result; blocking decision halts the pipeline |
| ST-CLI-01 | Same operations via CLI runners | Parity with API results for identical inputs |
| ST-CON-01 | Concurrent interactive + CI operations | Both complete; no cross-interference; results isolated |

---

## 7. Performance and Scalability Tests

| Test ID | Scale (components) | Pass criteria |
|---|---|---|
| PT-01 | small (~36) | Full ingest→build→analyze pass within budget |
| PT-02 | medium (~101) | Within budget; correctness preserved |
| PT-03 | large (~306) | Within budget |
| PT-04 | jumbo (~520) | Completes; memory within limits |
| PT-05 | Gate batch of N candidate units | Per-unit isolation; total time scales near-linearly |

Budgets are configurable; PT tests assert against the configured ceiling (SRS-NFR-040).

---

## 8. Independence, Drift, and Gate Conformance Tests

This section verifies the framework's load-bearing properties. **§8.1 is a hard release gate (§2.2).**

### 8.1 Independence guarantee

| Test ID | Description | Expected Result |
|---|---|---|
| IND-01 | Static import-separation | No module on the analysis path imports `analytical/`, `Observation`, `IFieldRecordRepository`, or simulation symbols; build fails otherwise |
| IND-02 | Output invariance under overlay | Structural analysis result is byte-identical with and without an overlay attached |
| IND-03 | Overlay non-mutation | Structural graph hash is identical before and after `bind_overlay` |
| IND-04 | Read-model isolation | Analysis services are constructed with the structural read model only; no handle to the observation store |

```python
@pytest.mark.parametrize("with_overlay", [False, True])
def test_structural_output_invariant_to_overlay(reference_model, field_overlay, with_overlay):
    if with_overlay:
        OverlayBinder().bind(reference_model.ref, field_overlay)   # writes to separate store
    result = AnalysisService(structural_repo(reference_model)).analyze_layer("system")
    assert canonical(result.structural) == EXPECTED_STRUCTURAL_HASH   # IND-02

def test_bind_overlay_does_not_mutate_structure(reference_model, field_overlay):
    before = structural_repo(reference_model).export_json()
    OverlayBinder().bind(reference_model.ref, field_overlay)
    after = structural_repo(reference_model).export_json()
    assert before == after                                            # IND-03
```

### 8.2 Drift detection conformance

| Test ID | Description | Expected Result |
|---|---|---|
| DR-01 | Recall on seeded deltas | All injected missing/unexpected/runtime-only/attribute deltas detected |
| DR-02 | No false drift on faithful runtime | Field overlay matching the model yields zero drift findings |
| DR-03 | Pre-registered projection respected | `observed_sets` projection matches the pre-registered mapping (no post-hoc change) |

### 8.3 Gate decision conformance

| Test ID | Description | Expected Result |
|---|---|---|
| GATE-01 | Blocking rule forces non-conformant | Any blocking-rule violation → "non-conformant" regardless of score |
| GATE-02 | Critical finding forces non-conformant | Critical severity → "non-conformant"; pipeline halt signalled |
| GATE-03 | Delta-aware: pre-existing structure not blocked | A known prior SPOF (in baseline) does not fail the gate |
| GATE-04 | Waiver honoured | A waivered entity/rule does not block; expired waiver does block |
| GATE-05 | Batch machine-readable result | Per-unit score/class/blocking-findings/decision + aggregate, machine-parseable |

```python
def test_intentional_spof_not_blocked_when_preexisting(gate, candidate_with_known_spof):
    result = gate.evaluate([candidate_with_known_spof], platform_version, profile)
    assert result[0].decision != "non-conformant"        # GATE-03: not a NEW regression

def test_blocking_rule_overrides_score(gate, candidate_high_score_blocking_violation):
    result = gate.evaluate([candidate_high_score_blocking_violation], platform_version, profile)
    assert result[0].decision == "non-conformant"        # GATE-01
```

### 8.4 Concurrency, identity, security

| Test ID | Description | Expected Result |
|---|---|---|
| CON-01 | Concurrent sessions on one model | Integrity and query consistency preserved (SRS-CSM-021) |
| CON-02 | Concurrent gate jobs | Process-specific models isolated; no shared mutable state |
| CON-03 | Append-only under concurrency | No result overwrite; idempotent on `operation_id` |
| TRC-01 | Identity threading | Every artifact retrievable by project/platform/version |
| TRC-02 | Determinism | Identical inputs/params → identical results |
| SEC-01 | LDAP auth | Valid credentials authenticate; invalid rejected |
| SEC-02 | Authorization scope | Operation outside scope denied |
| SEC-03 | Credential redaction | No credentials in logs, findings, reports, or exports |

---

## 9. Acceptance Criteria

| ID | Capability | Criterion | SRS |
|---|---|---|---|
| AC-01 | Identity-scoped workflow | User selects project/platform/version; effective version distinguished | SRS-DAD-002 |
| AC-02 | Model construction | Setup-data → CSM with status feedback | SRS-DAD-005 |
| AC-03 | Structure-only analysis | QoS, pub/sub, cyclic, anti-pattern findings produced without analytical data | SRS-DAD-010…019 |
| AC-04 | What-if | Non-destructive edits + re-analysis | SRS-DAD-020 |
| AC-05 | Simulation | Failure/load propagation with path and top-entity indicators | SRS-DAD-030…034 |
| AC-06 | Drift | Model-vs-runtime differences in all three categories | SRS-DAD-042 |
| AC-07 | Findings & reporting | Structured findings, causality, exportable report, immutable history | SRS-DAD-050…057 |
| AC-08 | CI gate | Single entry point; blocking halts pipeline; machine-readable batch result | SRS-DAD-060…064 |
| AC-09 | Independence | §8.1 suite passes in full | SRS-NFR-001/002 |
| AC-10 | Security | LDAP auth and scoped authorization enforced | SRS-NFR-030/031 |

---

## 10. Traceability Matrix

| SRS requirement group | Test IDs |
|---|---|
| SRS-MKV-001…009, SRS-EXT-001…005 | UT-MKV-01…08, IT-INGEST-01…03 |
| SRS-SUR-001…006 | UT-SUR-01…05 |
| SRS-AVH-001…005, SRS-EXT-010…011 | UT-AVH-01…05 |
| SRS-CSM-001…006 | UT-CSM-01…08, IT-INGEST-01…02 |
| SRS-CSM-010…013 | IT-OVERLAY-01…02, IND-02…04, UT-CSM-07 |
| SRS-CSM-020…023 | CON-01…03, IT-GATE-03 |
| SRS-DAD-010…019 | UT-DAD-01…09, UT-RC-01…02, AC-03 |
| SRS-DAD-020 | UT-DAD-13, AC-04 |
| SRS-DAD-030…034 | ST-SCEN-01, AC-05 |
| SRS-DAD-040…043 | IT-DRIFT-01…03, DR-01…03, ST-DRIFT-01, AC-06 |
| SRS-DAD-050…057 | UT-DAD-10…12, IT-API-02…03, AC-07 |
| SRS-DAD-060…064 | IT-GATE-01…03, GATE-01…05, ST-GATE-01, AC-08 |
| SRS-EXT-020, 030…032 | SEC-01…02, ST-CLI-01, ST-GATE-01 |
| SRS-EXT-040…041 | AC-01, IT-API-01 |
| SRS-NFR-001/002 | IND-01…04, AC-09 |
| SRS-NFR-010…012 | TRC-01…02, IT-API-02 |
| SRS-NFR-020 | CON-01…03, ST-CON-01 |
| SRS-NFR-030/031 | SEC-01…03, AC-10 |
| SRS-NFR-040 | PT-01…05 |

Requirements without an explicit mapping: none at the requirement-group level. Items deferred to critical design (rule sets, scoring method, report format) are tested through their configured reference values in §8.3 and §9.

---

## 11. Appendices

### Appendix A — Reference systems and seeded deltas

A fixed reference topology serves as the deterministic oracle for IT/ST tests. Seeded-delta fixtures (a removed entity, an added runtime-only topic, an attribute conflict, a new cyclic dependency, an intentional pre-existing SPOF) drive the drift (§8.2) and gate (§8.3) conformance tests.

### Appendix B — CI/CD configuration

The independence suite (§8.1) runs on every commit as a required check. Integration and gate suites run on the full stack per merge request. Coverage is reported per new module against §4.7 targets.

### Appendix C — Defect severity

| Severity | Definition |
|---|---|
| Critical | Independence violation, data loss, or incorrect gate "conformant" on a blocking violation |
| High | Incorrect finding/classification, drift miss, or failed isolation |
| Medium | Incorrect non-blocking behaviour or reporting field omission |
| Low | Cosmetic or message-quality issues |

### Appendix D — Mock-source contracts

Each mock `IModelSetupSource` documents its fixed payload, its fault modes (`SourceAccessError`, malformed payload, missing required field), and the `Identity` it answers for, so MKV error-path tests (UT-MKV-05…07) are deterministic.

---

*End of document.*