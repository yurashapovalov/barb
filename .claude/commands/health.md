---
description: Check Barb project health — function count, test coverage, lint errors, TODOs
allowed-tools: Read, Bash, Grep, Glob
---

Check the current state of the Barb project. Report concisely as a dashboard.

1. **Functions:** Count functions in barb/functions/ vs target (107)
2. **Tests:** Find source files in barb/ without corresponding test files
3. **Lint:** Run `ruff check barb/ tests/ api/ assistant/`
4. **Git:** `git status --short`
5. **TODOs:** `grep -rn "TODO\|FIXME\|HACK\|XXX" barb/ assistant/ api/ --include="*.py"`