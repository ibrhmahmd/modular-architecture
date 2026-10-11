---
name: modular-architecture
description: Modular monolith architecture for backends — layered modules behind facades, a fixed module order, one unit of work per use case. Use when structuring a new backend, adding a module, moving code between modules or layers, migrating a legacy module, placing a workflow that writes to several modules, or reviewing a diff that does any of these.
---

# Modular architecture

A backend is a set of **modules** in a fixed **module order**. Each module has the same layers, talks to lower modules only through their **facade**, and runs each use case in one **unit of work**. The default decisions, with reasons and rejected alternatives, are in [references/decisions.md](references/decisions.md). They are defaults: the project's own recorded decisions (ADRs) win.

Work out which **branch** you are on, then follow it:

| Branch | When | Go to |
|---|---|---|
| **Adopt** | The project's agent docs (`AGENTS.md`, `CLAUDE.md`) have no line naming this skill | Step 1, then the branch the task needs |
| **Add** | A new module | Step 2 |
| **Migrate** | Legacy code moving into the target shape | Step 3 |
| **Review** | A diff that adds, moves or crosses modules | Step 4 |

The agent-docs line records the project's **tier**. *Full* applies every decision and enforces it with tests. *Light* applies only the decisions marked **L** in `decisions.md`, without facades, module order or enforcement tests; in a light project, steps 2–4 apply the L decisions to the code in hand and skip everything about enforcement.

## Step 1 — Reconcile with the project

Follow [references/reconcile.md](references/reconcile.md): choose the tier with the user, classify every default against the project's ADRs and code, settle each disagreement and gap with the user, record the answers as project ADRs, and leave the agent-docs line.

Done when every decision in the tier is classified, every *project differs* and *unrecorded* item has the user's answer recorded in the project, and the agent-docs line exists.

## Step 2 — Add a module

1. Place it in the module order: above every module its tables' foreign keys point at, below every module whose tables point at it. Ask the user when the graph does not settle it.
2. Create the layers the module uses (`api/ services/ repositories/ schemas/ models/`) and the facade (`__init__.py`).
3. Add it to the enforcement tests' module list and to the **enforced** set from day one.

Done when the enforcement tests pass with the module enforced and its facade exports exactly what other modules call.

## Step 3 — Migrate a legacy module

Follow [references/playbook.md](references/playbook.md): modules go bottom-up, each refactor **behaviour-frozen** (characterization tests and the API snapshot unchanged). The playbook carries the ticket slicing and what each ticket must prove.

Done when the module is in the enforced set with zero violations and the full test suite matches its baseline.

## Step 4 — Review a structural diff

1. Run the enforcement tests and the API snapshot test. Read every violation count, not just pass/fail.
2. Walk `decisions.md` rule by rule against the diff. Every rule in the tier gets a verdict: holds, violated (file:line), or not touched.
3. When the diff is a refactor, check it is **behaviour-frozen**: status codes, responses and side effects match the characterization tests, and any change a ticket did not ask for goes back to the implementer. Implementers sometimes fix a bug in passing.

Done when every rule in the tier has a verdict and every violation has a file:line.

## Bugs found on the way

A refactor exposes bugs. For each one, stop and ask the user: fix now, or **pin** it (a test asserting today's behaviour, commented `pinned, not endorsed` plus the bug link) and file it for later. When the user has said they are away, pin and file without asking, keep going, and list every such bug in your next report. Security or data-loss bugs go to the user at once either way.

## Stack notes

For Python with FastAPI and SQLAlchemy/SQLModel, read [references/python-fastapi.md](references/python-fastapi.md): unit-of-work code, dependency wiring, test fixtures, pitfalls, and the enforcement-test templates in [templates/python/](templates/python/). For other stacks, keep the decisions and write equivalent enforcement tests.

## Optional — diagrams

When a picture would settle a question faster than prose (the module order, a cross-module workflow, a before/after of a migration), offer one and draw it only on a yes. See [references/diagrams.md](references/diagrams.md).
