# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Project Context

[Describe your project here. Agents read this for background context.]

## Agent Teams

This project uses aurorie-teams. Agents are in `.claude/agents/`.

Routing rules are in `.claude/routing.json` — edit to customize which keywords
route to which team.

To invoke: use the `orchestrator` agent for most tasks, or invoke a team lead
directly (e.g., `aurorie-backend-lead`) for single-team work.

## Sequential Workflows

Define multi-step cross-team workflows here. Example:

### Feature Development (Product → Backend)
1. Invoke `aurorie-product-lead` to write a PRD.
   When complete, find the actual task-id in `.claude/workspace/tasks/` and note the artifact path.
2. Invoke `aurorie-backend-lead` with:
   `input_context: "artifact: .claude/workspace/artifacts/product/<actual-task-id>/prd.md\nImplement the features described in the PRD."`
   Replace `<actual-task-id>` with the UUID written by step 1.

## Workspace

Runtime files in `.claude/workspace/` (gitignored):
- `tasks/` — one JSON file per active task
- `artifacts/` — team outputs as `<team>/<task-id>/`

## Customizing

- Workflow behavior: edit `.claude/workflows/<team>.md`
- Routing rules: edit `.claude/routing.json`
