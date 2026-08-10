# saag_contracts

**Shared contracts for the SaaG CSCI**

Cross-CSU types, the common error model, the Model Setup Data document schema, and the service specifications every internal interface is realized through (SDD §2.3.1). Depended on by every CSU; depends on no CSU.

Part of [System as a Graph (SaaG)](https://github.com/canetizen/saag) — a static digital system model
of a distributed publish–subscribe system. The requirements, design and test
documents for the whole CSCI live in that repository; this one holds one
distribution of it.

## What this repository is

One independently built and independently installable distribution, `saag-contracts`.
It depends on `saag-contracts` and on **no other CSU**: peers are reached by
looking up a published service specification in the component framework's
registry, never by importing them (SDD §1 decision 6). Adding this CSU to a
running CSCI is installing this distribution; removing it is uninstalling it.

## Layout

```
src/saag_contracts/
├── bundle.py        # the component: publishes what this CSU provides, declares what it requires
├── composition.py   # the wiring, framework-free
├── api/             # inbound adapters — REST endpoints and provided-service implementations
├── use_cases/       # application core
├── model/           # domain core
├── ports/           # outbound ports
└── adapters/        # outbound adapters
tests/               # this CSU's own suite, runnable with nothing else installed
```

## Building and testing

```bash
uv sync
uv run pytest
uv run ruff check .
uv build --wheel
```

`saag-contracts` is resolved from the configured package index. Until one is in
place (CDR-31), install it from its repository:

```bash
uv pip install git+https://github.com/canetizen/saag_contracts.git
```
