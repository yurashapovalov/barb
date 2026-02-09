---
description: Refactor code following architecture docs in docs/barb/. Shows plan and waits for approval.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Task
---

Refactor "$ARGUMENTS" following the architecture docs.

Steps:

1. **Read the doc.** Find the relevant doc in docs/barb/ for this area. Read it completely.
2. **Read the current code.** Understand what exists now. Read every file that will be affected.
3. **Make a plan.** Explain:
   - What changes (file by file)
   - What stays the same
   - What might break
   - What tests need updating
4. **STOP.** Present the plan and wait for confirmation. Do NOT start coding until user says "go" or "да" or "делай".
5. **Implement one file at a time.** After each file:
   - Run `ruff check` on that file
   - Run relevant `pytest`
   - If tests fail — fix before moving to next file
6. **After all files:** Run full `pytest tests/ -v`
7. **Git commit** each logical change separately
8. **Final review:** Use the code-reviewer agent to review all changes.

IMPORTANT: If during refactoring the doc and the code disagree — STOP and ask. Don't guess which is right.
