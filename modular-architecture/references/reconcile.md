# Reconcile the defaults with a project

Run once per project, before the first structural change. The output is a project whose recorded decisions cover every default in [decisions.md](decisions.md), either agreeing, differing on purpose, or declined.

## 1. Pick the tier

Ask the user, with the project's size in front of them (module count, lines of code, team size):

- **Full:** every decision, enforced by the import-graph and API-snapshot tests.
- **Light:** only the decisions marked **L**: one transaction per request, SQL only in repositories, validation split by kind, repositories without business rules, typed returns, no dead code. No facades, module order or enforcement tests.

A project can move from light to full later; that move is an *adopt* run of its own.

## 2. Survey what exists

Find the facts yourself; never ask the user for something the repo can tell you.

- Recorded decisions: `docs/adr/`, `docs/decisions/`, `adr/`, architecture sections in `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `README.md`.
- Actual shape: the modules package, how each module is laid out, where routers and HTTP schemas live, how sessions are opened (count the call sites), whether interfaces have more than one implementation, cross-module imports (cycles, imports inside functions), the foreign-key graph (schema files or models).

## 3. Classify every default

For each decision in the chosen tier, record one of:

| Class | Meaning | Action |
|---|---|---|
| **Agreed** | A project ADR or the code already follows it | Nothing |
| **Project differs** | A project ADR chose otherwise | Ask once (step 4) |
| **Unrecorded** | No ADR; the code may or may not follow it | Propose (step 5) |

Where the code contradicts the project's *own* ADR, note it as migration work, not as a disagreement.

## 4. Surface each disagreement once

Present each *project differs* item with: the project's choice, the default, the concrete trade-off in this codebase (cite files), and a recommendation. The user keeps the project's choice or supersedes the ADR. Record the answer in the project (a superseding ADR, or a line in the existing ADR noting the default was considered). Never re-raise a settled item in later runs unless the user reopens it.

## 5. Record the unrecorded

Walk the user through each *unrecorded* default against what the code does today. Each accepted decision becomes a short project ADR (use the `domain-modeling` skill when installed; otherwise one file per decision: context, decision, rejected options, consequences). Write them in the project's terms: its module names, its order, its file paths. Declined defaults get no ADR; note them in the agent-docs line so they are not proposed again.

## 6. Leave a pointer

Add one line to the project's agent docs, for example:

> Architecture: modular monolith per the `modular-architecture` skill; decisions in `docs/adr/`; module order bottom→top: auth, people, billing, reports. Declined defaults: D9.

Full tier: also copy the enforcement tests from the stack notes, set the module order, and start with the enforced set empty (report-only) until each module is migrated.
