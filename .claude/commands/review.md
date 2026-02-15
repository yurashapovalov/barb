---
description: Review recent code changes for quality, correctness, and architecture compliance
allowed-tools: Read, Grep, Glob, Bash, Task
---

Review the current code changes. Determine which reviewers to invoke based on changed files.

## Changed files

!`git diff --name-only 2>/dev/null || echo "no changes"`

## Detailed diff

!`git diff 2>/dev/null || git diff HEAD~1 2>/dev/null || echo "no diff available"`

## Instructions

Look at the changed files above. Then:

1. If ANY Python files changed (`barb/`, `api/`, `assistant/`, `scripts/`, `config/`): invoke the **backend-reviewer** agent via the Task tool with the diff
2. If ANY frontend files changed (`front/`): invoke the **frontend-reviewer** agent via the Task tool with the diff
3. If both changed: invoke BOTH agents in parallel

Always invoke the **architect** agent as well — it checks cross-cutting architecture concerns.

Pass the full diff and file list to each agent. Wait for all agents to complete, then combine their output into a single review.
