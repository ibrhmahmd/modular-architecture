# Optional diagrams

Diagrams are offered, never produced unasked. Offer one when it would settle a question faster than prose, say which diagram and why in one line, and draw it only after the user says yes.

## Which diagram for which moment

| Moment | Diagram | Shows |
|---|---|---|
| Reconcile: proposing the module order | Layer stack or dependency graph | Modules bottom→top, with the foreign-key edges that decided each position |
| Reconcile: the code's current tangle | Dependency graph (current state) | Today's cross-module imports, cycles highlighted |
| Migrate ticket 2: a workflow moving up | Sequence diagram | The use case in the highest module calling lower facades inside one unit of work, then the notifier after commit |
| Migrate: before/after of a module | Architecture delta | Old folders and imports versus the layered module |
| Migration progress | Kanban or timeline | Each module's three tickets and their status |
| Explaining the data model | ER / database schema | Tables per module, ownership coloured by module |

## How to draw

Use the `diagram-design` skill when it is installed (it produces self-contained HTML/SVG and handles the project's style guide on first use). Without it, offer a Mermaid block in Markdown. Build every diagram from facts read in the repo (the actual module list, imports and tables), never from the defaults in `decisions.md`.

Save diagrams where the project keeps docs (for example `docs/architecture/`) only when the user wants them kept; otherwise show them and leave nothing behind.
