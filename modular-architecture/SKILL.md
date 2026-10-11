---
name: modular-architecture
description: Modular-monolith architecture for backend code — layered modules behind facades, a fixed module order, one unit of work per use case. Use when adding a module, moving code between modules or layers, migrating a legacy module to this shape, placing a workflow that writes to several modules, or reviewing a diff that does any of these.
---

# Modular architecture

A backend is a set of **modules** in a fixed **module order**. Each module has the same layers, talks to lower modules only through their **facade**, and runs each use case in one **unit of work**. The default decisions, with reasons and rejected alternatives, are in [references/decisions.md](references/decisions.md). They are defaults: the project's own recorded decisions (ADRs) win.

Work out which **branch** you are on, then follow it:

| Branch | When | Go to |
|---|---|---|
| **Adopt** | First structural task in a project this skill has not reconciled yet (no pointer to this skill in the project's agent docs) | Step 1, then the branch the task needs |
| **Add** | A new module | Step 2 |
| **Migrate** | Legacy code moving into the target shape | Step 3 |
| **Review** | A diff that adds, moves or crosses modules | Step 4 |

## Step 1 — Reconcile with the project

Follow [references/reconcile.md](references/reconcile.md). In short:

1. Ask the user which **tier** applies: *full* (every decision, enforced by tests) or *light* (typed returns, SQL only in repositories, one transaction per request, no dead code). Small services usually want light.
2. Read the project's ADRs and agent docs. For every default decision, classify it: *agreed*, *project differs*, or *unrecorded*.
3. Put every *project differs* to the user once, with the default's trade-off: keep the project's choice or supersede its ADR. The project's answer stands until the user reopens it.
4. Turn every *unrecorded* decision the user accepts into a project ADR (use the `domain-modeling` skill when present).
5. Add one line to the project's agent docs (`AGENTS.md` / `CLAUDE.md`) naming this skill and the project's module order, so later runs skip this step.

Done when every decision in `decisions.md` is classified, each *differs* and *unrecorded* item has the user's answer, and the agent-docs line exists.

## Step 2 — Add a module

1. Place it in the module order: above every module its tables' foreign keys point at, below every module whose tables point at it. Ask the user when the graph does not settle it.
2. Create the layers (`api/ services/ repositories/ schemas/ models/`) and the facade (`__init__.py`). Create only the layers the module uses.
3. Add it to the enforcement tests' module list and to the **enforced** set from day one. Full tier only.

Done when the enforcement tests pass with the module enforced and its facade exports exactly what other modules call.

## Step 3 — Migrate a legacy module

Follow [references/playbook.md](references/playbook.md): modules go bottom-up, one per ticket series, each refactor **behaviour-frozen** (characterization tests and the API snapshot unchanged). The playbook carries the ticket slicing and what each ticket must prove.

Done when the module is in the enforced set with zero violations and the full test suite matches its baseline.

## Step 4 — Review a structural diff

1. Run the enforcement tests and the API snapshot test. Read every violation count, not just pass/fail.
2. Walk `decisions.md` rule by rule against the diff. Every rule gets a verdict: holds, violated (file:line), or not touched.
3. Check that the diff is **behaviour-frozen** when it is a refactor: no changed status codes, responses or side effects that no ticket asked for. Implementers sometimes fix a bug in passing; send that back.

Done when every rule has a verdict and every violation has a file:line.

## Bugs found on the way

A refactor exposes bugs. For each one, stop and ask the user: fix now, or **pin** it (a test asserting today's behaviour, commented `pinned, not endorsed` plus the bug link) and file it for later. When the user has said they are away, pin and file without asking, keep going, and list every such bug in your next report. Security or data-loss bugs are reported at once either way.

## Stack notes

For Python with FastAPI and SQLAlchemy/SQLModel, read [references/python-fastapi.md](references/python-fastapi.md). It holds the unit-of-work code, dependency wiring, test fixtures, pitfalls, and the enforcement-test templates in [templates/python/](templates/python/). For other stacks, keep the decisions and write equivalent enforcement tests.

## Optional — diagrams

When a picture would settle a question faster than prose (the module order, a cross-module workflow, a before/after of a migration), offer one and draw it only on a yes. See [references/diagrams.md](references/diagrams.md).
