# agent-skills

Skills for coding agents (Claude Code, OpenCode, and any agent that reads `SKILL.md` folders).

| Skill | What it does |
|---|---|
| [modular-architecture](modular-architecture/SKILL.md) | Modular-monolith architecture for backend code: layered modules behind facades, a fixed module order, one unit of work per use case. Reconciles its default decisions with a project's own ADRs, migrates legacy modules behaviour-frozen, and ships enforcement tests for Python/FastAPI. |

## Install

Clone, then link each skill into the folders your agents read:

```sh
git clone <this repo> ~/Desktop/agent-skills
for dir in ~/.agents/skills ~/.claude/skills ~/.config/opencode/skills; do
  mkdir -p "$dir"
  ln -sfn ~/Desktop/agent-skills/modular-architecture "$dir/modular-architecture"
done
```
