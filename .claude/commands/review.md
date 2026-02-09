---
description: Review recent code changes for quality, correctness, and architecture compliance
allowed-tools: Read, Grep, Glob, Bash
agent: code-reviewer
---

Review the current code changes.

## Changed files

!`git diff --name-only 2>/dev/null || echo "no changes"`

## Detailed diff

!`git diff 2>/dev/null || git diff HEAD~1 2>/dev/null || echo "no diff available"`

Review these changes against CLAUDE.md checklist and docs/barb/ architecture.
