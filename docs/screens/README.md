# SaaG Screens Spec

A modern, lightweight screen-by-screen UX/UI design specification for the SaaG (System as a Graph) Digital System Model's user-facing component, **VAE**. Unlike the rest of `docs/` (SRS, SDD, IDD, STP/STD, CDR), this document set does not follow a MIL-STD-498 Data Item Description — none exists for UI/UX design.

Each screen has two layers, co-located in that screen's own folder: a `.md` spec (text + Mermaid diagrams, every claim traced back to SRS/SDD/IDD/CDR — the authoritative source) and its `*.html` wireframe variants (rendered visuals, built on one shared token system — see foundations §5 / [`style-guide.html`](00-foundations/style-guide.html)). The `.md` is what to cite; the wireframes are what to look at.

## Documents

| # | Document | Wireframe | Covers | Status |
|---|---|---|---|---|
| 00 | [spec.md](00-foundations/spec.md) | [style-guide.html](00-foundations/style-guide.html) | Shared vocabulary, personas, IA/nav map, design tokens, shared components | Drafted |
| 01 | [spec.md](01-auth-and-context-selection/spec.md) | [happy-path.html](01-auth-and-context-selection/happy-path.html) + [3 variants](01-auth-and-context-selection/spec.md) | Session & Authentication Manager (SDD §5.6.3.1, SRS 3.2.6.1–4) | Drafted |
| 02 | [spec.md](02-model-setup-data-workflow/spec.md) | [happy-path.html](02-model-setup-data-workflow/happy-path.html) + [3 variants](02-model-setup-data-workflow/spec.md) | Model Setup Data Workflow Manager (SDD §5.6.3.2, SRS 3.2.6.5–9) — includes triggering Core System Model creation, per SDD's traceability table | Drafted |
| 03 | [spec.md](03-analytical-data-workflow/spec.md) | [happy-path.html](03-analytical-data-workflow/happy-path.html) + [3 variants](03-analytical-data-workflow/spec.md) | Analytical Data Workflow Manager (SDD §5.6.3.3, SRS 3.2.6.10–14, 48) | Drafted |
| 04 | [spec.md](04-core-model-creation-and-structural-analysis/spec.md) | [happy-path.html](04-core-model-creation-and-structural-analysis/happy-path.html) + [3 variants](04-core-model-creation-and-structural-analysis/spec.md) | Structural & Dependency Analysis Engine (SDD §5.6.3.5, SRS 3.2.6.15–16, 18–19, 28–29) — read-only binding/matching status and dependency analysis on an existing model (the "create" trigger itself lives in `02`) | Drafted |
| 05 | [spec.md](05-model-visualization-and-navigation/spec.md) | [happy-path.html](05-model-visualization-and-navigation/happy-path.html) + [3 variants](05-model-visualization-and-navigation/spec.md) | Model Visualization & Navigation UI (SDD §5.6.3.9, SRS 3.2.6.43) | Drafted |
| 06 | [spec.md](06-working-model-editor/spec.md) | [happy-path.html](06-working-model-editor/happy-path.html) + [3 variants](06-working-model-editor/spec.md) | Working Model Editor (SDD §5.6.3.4, SRS 3.2.6.17) — flags that working-model persistence has no database entity anywhere in the doc set | Drafted |
| 07 | [spec.md](07-analysis-and-verification-results/spec.md) | [happy-path.html](07-analysis-and-verification-results/happy-path.html) + [3 variants](07-analysis-and-verification-results/spec.md) | Architectural Rule Verification + Simulation Analysis + Field Data Analysis Engines (SDD §5.6.3.6–8, SRS 3.2.6.20–27, 30–42) — flags that most rule verification content (CDR-01–08) is still open | Drafted |
| 08 | [spec.md](08-findings-and-reporting/spec.md) | [happy-path.html](08-findings-and-reporting/happy-path.html) + [3 variants](08-findings-and-reporting/spec.md) | Findings & Reporting Manager (SDD §5.6.3.10, SRS 3.2.6.44–47, 49) — flags that Finding/Operation/Report have no database entity at all | Drafted |
| 09 | [spec.md](09-installation-suitability-and-pipeline-gate/spec.md) | [happy-path.html](09-installation-suitability-and-pipeline-gate/happy-path.html) + [3 variants](09-installation-suitability-and-pipeline-gate/spec.md) | Installation Suitability Evaluator + Automation Interface (SDD §5.6.3.11–12, SRS 3.2.6.50–54) — flags the CLI-only Automation Client persona and an inferred manual-trigger extension | Drafted |

Sequencing follows the user's actual journey through VAE: login → set up data → build model → explore/edit → analyze → review findings → gate a release.

All 10 documents (00–09), and all 10 wireframes, are now drafted.
