# System as a Graph (SaaG)

**A static digital system model that represents a distributed publish–subscribe system's structural and relational architecture as a node-relationship graph — without ever running the target system.**

![License](https://img.shields.io/badge/license-Apache--2.0-green)
![Status](https://img.shields.io/badge/status-documentation--only-orange)

---

## Overview

SaaG models a target system's architecture as a typed graph: software units, middleware and communication services, processor/console units, topics, and messages become nodes; dependency, publishing, and consuming relationships between them become edges. Behavioral analysis is added not by executing components, but by overlaying **Analytical Evaluation Data** — derived from field records or from a scenario generator — onto this structural graph.

The model's primary purpose is architectural verification at design time: structural/circular dependencies, publisher–consumer matching, topic QoS conformance, hardware capacity conformance, and design patterns that violate architectural rules are all statically audited before any software unit is installed in the target environment. It also detects **architectural drift** between the designed structure and what is observed in the field, and supports hypothetical scenario analysis — evaluating how an entity going down, a spike in message density, or a bandwidth reduction would propagate through the architecture — without altering the structural model itself.

## Capability areas

Per the SRS, SaaG is organized into six capability areas:

| Capability Area | Abbreviation | Requirements |
|---|---|---|
| Model Setup Data Generation | MSD | 19 |
| Scenario Generator | SCG | 7 |
| Field Records Database | FRD | 6 |
| Analytical Data Preparation | ADP | 6 |
| Node-Relationship Based Core System Model | CSM | 20 |
| Design Verification, Analysis and Evaluation | VAE | 54 |
| **Total** | | **112** |

## Current status

This repository currently contains the **MIL-STD-498 documentation set and VAE UI screen specifications** for SaaG. No implementation exists yet — there is no application code, CLI, API, or UI beyond the wireframes referenced below.

## Documentation

| Document | Purpose |
|---|---|
| [`docs/requirements/SRS.md`](docs/requirements/SRS.md) | Software Requirements Specification — the 112 CSCI requirements. |
| [`docs/design/SDD.md`](docs/design/SDD.md) | Software Design Description — CSC/CSU decomposition. |
| [`docs/design/IDD.md`](docs/design/IDD.md) | Interface Design Description — external and internal interfaces. |
| [`docs/design/DBDD.md`](docs/design/DBDD.md) | Database Design Description — the 5 persistent data stores. |
| [`docs/planning/SDP.md`](docs/planning/SDP.md) | Software Development Plan. |
| [`docs/reviews/CDR.md`](docs/reviews/CDR.md) | Critical Design Review — open items register. |
| [`docs/test/STP.md`](docs/test/STP.md) | Software Test Plan. |
| [`docs/test/STD.md`](docs/test/STD.md) | Software Test Description — the 31 test cases. |
| [`docs/screens/README.md`](docs/screens/README.md) | VAE screen-by-screen UX/UI specification (00–09) with wireframes. |
| [`docs/planning/IPM.md`](docs/planning/IPM.md) | Internship Project Menu — 20-day internship project ideas, loosely inspired by SaaG. |

The document set follows MIL-STD-498 (Data Item Descriptions DI-IPSC-81427/81433/81435/81436/81437/81438/81439) and is mutually traceable across documents.

## Repository layout

```
docs/
  requirements/  # SRS
  design/        # SDD, IDD, DBDD
  planning/      # SDP, internship project menu
  reviews/       # CDR
  test/          # STP, STD
  screens/       # VAE UX/UI screen specs + HTML wireframes (00-09)
LICENSE
```

## License

Released under the Apache License 2.0 — see [`LICENSE`](LICENSE).
