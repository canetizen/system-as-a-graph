# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## 5. Project Documentation Compliance

**All work must comply with the documentation under `docs/`.**

This project ("System as a Graph" / SaaG) is governed by a formal document set. Code, design, and planning decisions must not contradict these documents:

- `docs/requirements/SSS.md` - System/Subsystem Specification: top-level requirements across the 6 components.
- `docs/requirements/SRS.md` - Software Requirements Specification: requirements decomposed to CSU level, traceable to SSS.
- `docs/planning/SDP.md` - Software Development Plan: work breakdown structure and build sequencing.
- `docs/design/SDD.md` - Software Design Description: architecture and detailed design satisfying the SRS.
- `docs/design/UXD.md` - UI/UX Design Document: visual identity and interaction rules for the Operations Panel UI.
- `docs/design/CDR.md` - Critical Design Review register: open/resolved design decisions.
- `docs/test/STD.md` - Software Test Description: qualification test cases traced to SDD/SRS.

Before working on anything touching requirements, architecture, UI/UX, or testing, check the relevant document(s) first. If a request conflicts with what's documented, say so - don't silently ignore it or silently follow the code over the doc. `.tr.md` files are Turkish translations; the English document is authoritative.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.