# Migration playbook

How to move a legacy codebase into the target shape one module at a time, with the running system's behaviour **frozen**: the API contract and observable behaviour are identical before and after every ticket, bugs included.

## Order and setup

1. Migrate **bottom-up** in the module order: a module is migrated only after every module below it, so its facade calls land on finished facades.
2. Before the first module, the full-tier setup must exist: enforcement tests in report-only mode (every module listed, the enforced set empty), and an **API snapshot** test (the generated OpenAPI spec, or the equivalent for the stack, compared to a committed file).
3. Record the **baseline**: run the full suite on a fresh database and save the list of failing tests. Every later gate is compared to this list. A test that only fails because of the date or leftover data is a bug of its own: file it and add it to the baseline with that reason, never silently.

## Slicing a module into tickets

A large module takes three tickets; a small one (few endpoints, no cross-module writes) can merge them. Each ticket is a separate branch and review.

| # | Ticket | Proves |
|---|---|---|
| 1 | **Characterize + move the HTTP layer + facade.** Write characterization tests for every endpoint of the module. Move routers, HTTP schemas and service factories into `<module>/api/`. Build the facade and rewire every caller in other modules to it. | Characterization tests and API snapshot unchanged by the move; route registration order unchanged (a path parameter route registered first shadows literal routes); nothing imports the old locations. |
| 2 | **Move cross-module workflows up.** Each workflow that writes to a higher module moves into the highest module involved (D6), in one unit of work. Add the module's notifier port (D7). | The moved endpoints' characterization tests and the snapshot unchanged; an atomicity test (step injected to fail → nothing persisted; success → everything persisted); the lower module no longer imports the higher one. |
| 3 | **Flatten + unit of work + enforce.** Collapse any slice or sub-package structure into the layers (D1). Services and repositories take the injected unit of work (D3), repositories become classes (D11), interfaces without two adapters go (D8), dead code goes (D13). Add the module to the enforced set. | Zero violations for the module with it enforced; characterization tests and snapshot unchanged; gate matches the baseline. |

Write each ticket's proof list into the ticket itself, so the reviewer checks the same list the implementer worked to.

## Characterization tests

They pin what the system does today so a refactor can prove it changed nothing.

- Hit the real HTTP layer and a real database (a local throwaway instance, never a shared or production one).
- Seed data the test creates itself, tagged with a unique value per run, and clean it up. Never mutate shared fixtures or well-known rows.
- Assert exactly what was observed: one status code, the exact error type, the exact shape. No `status in (200, 404)`, no branching on the response.
- Pin quirks as they are, commented `current behaviour (pinned, not endorsed)` with the bug link (see the bug rule in `SKILL.md`).
- Run each new file three times in a row; it must pass every time.
- No secrets or real credentials in test literals.

## Running a ticket

- Split the work into steps small enough to review in one sitting (characterize, then move, then rewire, then delete), committing between steps.
- Whoever implements, the reviewer re-runs the proof list personally: the enforcement tests, the snapshot, the module's characterization tests, then the full gate on a fresh database compared to the baseline. A self-reported "all green" counts for nothing.
- A refactor diff carries no behaviour change. When an implementer fixes a bug in passing, revert it in the refactor and file the bug.
- Docs move with the code: when a ticket moves a path the project's agent docs mention, update the line in the same ticket.

## Done

The migration is done when every module is in the enforced set, the legacy shared HTTP folders hold only cross-cutting code, and the suite matches the baseline minus the bugs fixed since. Fixing pinned bugs is its own phase afterwards: each fix updates its characterization pin and the snapshot if the API changes, in a ticket that names that change.
