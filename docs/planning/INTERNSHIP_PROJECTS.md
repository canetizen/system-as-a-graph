# 20-Day Internship Project Menu

SaaG models a system as a graph — software units, topics, messages, and hardware become nodes, and dependencies, publishing, and consuming become the connections between them — then runs checks and simulations over that graph instead of running the real system. The projects below are loosely inspired by that idea, sized for a student/early-career intern to complete in about 20 working days (4 weeks).

This is a **menu, not a checklist** — pick one project, not all seven. Each project is self-contained: it reads and writes only local files the intern creates or generates themselves, and produces output you can see directly (a console, a simple UI, or a report file). None of them connect to any external system, real or mocked. No programming language or framework is prescribed — the intern or mentor picks what's comfortable, except where noted.

Projects 1, 2, 3, and 5 share the same simple graph file format, so two of them can be sequenced back-to-back if a longer engagement is wanted later. Projects 6 and 7 can reuse the same sample graphs if useful, but don't have to.

---

## Project 1 — Graph Model Builder & Viewer

**Goal**: Read a small text file describing a system's parts (software units, topics, messages, servers) and how they connect, turn it into a graph, and let someone explore that graph visually.

**What you build**:
- A simple file format (YAML/JSON) for nodes and edges.
- A parser that builds a graph in memory.
- A viewer (web page or desktop UI) with search, filtering by node type, and zoom/pan.

**Week-by-week**:
- W1: design the file format + parser.
- W2: build the graph data structure + basic checks (e.g. reject a file that references a node that doesn't exist).
- W3: build the viewer.
- W4: polish, add sample graphs, write a short README.

**Done when**: a sample file with ~20-30 nodes of different types renders and can be searched/filtered/zoomed; a broken sample file produces a clear error instead of crashing.

---

## Project 2 — Architecture Rule Checker

**Goal**: Given a graph like Project 1's, automatically flag design problems: things that depend on each other in a circle, topics nobody publishes to, topics nobody reads from.

**What you build**:
- A small rule engine that runs over the graph and reports findings (what's wrong, where, how severe).
- Circular-dependency detection.
- Orphan-topic detection.
- 1-2 rules of your own choosing.

**Week-by-week**:
- W1: pick the rule set + design the "finding" shape (what, where, severity).
- W2: implement circular-dependency + orphan-topic checks.
- W3: implement 1-2 more rules + a findings list/report.
- W4: tests with hand-built graphs that each rule should catch, polish, README.

**Done when**: for each rule, there's a sample graph that triggers it and one that passes clean; findings print in a readable list with severity.

---

## Project 3 — Fake Traffic Simulator

**Goal**: Generate made-up message traffic flowing through a graph like Project 1's, then analyze it: who talks to whom the most, what happens if a node goes down.

**What you build**:
- A synthetic traffic generator driven by simple parameters (how many messages, how often, between which nodes).
- Basic analysis: busiest nodes/edges, message counts, and "if this node disappears, which nodes are directly affected."

**Week-by-week**:
- W1: design traffic parameters + generator.
- W2: generate and record traffic against a sample graph.
- W3: build the "busiest nodes" and "node removal impact" analyses.
- W4: tests, a couple of interesting sample scenarios, README.

**Done when**: running the generator twice with the same parameters gives comparable results; removing a node correctly lists its direct neighbors as affected.

---

## Project 4 — Findings Board & Report Export

**Goal**: Take a list of findings (e.g. from Project 2, or a hand-written sample list) and build a small dashboard to browse them, plus a way to export a report.

**What you build**:
- A findings list with fields (id, type, description, affected node, severity).
- Sorting/filtering by severity/type.
- Export to a simple report file (Markdown, CSV, or PDF — your choice).

**Week-by-week**:
- W1: design the findings data shape + load sample findings.
- W2: build sort/filter UI or CLI.
- W3: build report export.
- W4: polish, sample data, README.

**Done when**: a sample list of ~15-20 mixed-severity findings can be filtered/sorted correctly and exported to a readable report.

---

## Project 5 — Drift Detector (compare two graphs)

**Goal**: Compare two versions of a graph — a "designed" one and an "observed" one — and report what changed: things added, things removed, things that look different.

**What you build**:
- A diff tool that takes two graph files (same format as Project 1).
- Reports added nodes/edges, removed nodes/edges, and nodes/edges that exist in both but differ in some attribute.

**Week-by-week**:
- W1: reuse/adapt Project 1's file format and parser.
- W2: implement the added/removed comparison.
- W3: implement the "differs in attribute" comparison + a readable diff report.
- W4: tests with hand-built before/after pairs covering all 3 cases, polish, README.

**Done when**: a before/after pair exercising all three diff categories (added, removed, changed) produces a correct, readable report.

---

## Project 6 — Graph Database Selection & Benchmark

**Goal**: SaaG stores everything as a graph, so figure out which off-the-shelf graph database would actually be a good fit — compare a few candidates and benchmark them on the kind of data and queries SaaG would need. This one is evaluation/research-flavored rather than build-a-tool-from-scratch, and a good fit for an intern who likes measuring things as much as building them.

**What you build**:
- A short list of candidate graph databases (2-3, your choice — e.g. an embedded one and a couple of server-based ones), each installed and run **locally** (not a live external service — just software on your own machine or a local container).
- A handful of sample graphs at different sizes (small/medium/large), built with Project 1's file format or generated.
- A set of representative queries (e.g. "find all topics with no publisher," "find everything reachable from node X," "find all nodes of a given type with a given attribute value").
- A benchmark harness that loads each sample graph into each database and times bulk load, query execution (repeated runs, not a single sample), and rough memory/disk footprint.
- A written comparison with a recommendation and reasoning.

**Week-by-week**:
- W1: pick candidate databases, get each running locally, design the representative datasets and queries.
- W2: build a loader that gets sample graphs into each database consistently.
- W3: build the benchmark harness (repeatable timing, resource-usage capture) and run it across all dataset sizes.
- W4: write the comparison report with a clear recommendation, polish, README.

**Done when**: the same datasets and queries have been run against every candidate database with recorded, repeatable numbers; the report states each candidate's strengths/weaknesses and picks one with reasoning tied to the actual measurements.

*Note: this is the one project where picking specific databases to evaluate is the point, not a limitation on tooling — but they still run locally, never against a real external system.*

---

## Project 7 — Operation Control Panel

**Goal**: Build a polished UI for starting, watching, and reviewing a background job — the "kick off a task, see it run, check the result" experience common in dev tools. Deliberately not about graphs — this one is about live state, forms, and feedback.

**What you build**:
- A form to configure and start a new "operation" (a handful of simple parameters — you decide what the operation conceptually represents).
- A live-updating list of operations showing each one's status (queued/running/succeeded/failed) with progress indication.
- A way to cancel an operation mid-run.
- A details view for a finished operation showing its result, duration, and any error.
- All backed by a small local simulated engine (e.g. a fake task that ticks through states over a few seconds on its own) so the UI is driving real state changes, not just displaying static screenshots.

**Week-by-week**:
- W1: design the operation states/data model, sketch the layout.
- W2: build the start-operation form + the live list wired to the simulated engine's real state transitions.
- W3: build cancel + the finished-operation details view.
- W4: polish — responsive layout, transitions/animations, accessibility basics — and a README explaining how to run it.

**Done when**: starting an operation visibly progresses through queued → running → succeeded/failed on its own; cancelling mid-run works and is reflected immediately; a finished operation's details view shows the correct result and duration; the whole flow feels like one coherent tool, not a static mockup.
