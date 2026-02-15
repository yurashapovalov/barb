---
description: Audit documentation against code — with optional verification of findings
allowed-tools: Read, Grep, Glob, Bash, Task, Write
---

Audit documentation files against actual code.

$ARGUMENTS

## Instructions

### Step 1: Audit

If a specific file path is given, audit that single file using the **doc-auditor** agent.
If no file is given, audit ALL files in `docs/barb/` — invoke a separate **doc-auditor** agent for each file in parallel.

Each agent saves results to `docs/barb/audits/{filename}-audit.md`.

### Step 2: Summary

After all audits complete, read the audit files from `docs/barb/audits/` and produce a combined summary:
- Total claims across all docs
- Accuracy per document
- Top issues (sorted by severity: WRONG first, then OUTDATED)

### Step 3: Verify (if `--verify` in arguments)

If the user passed `--verify`:
1. Read each audit file from `docs/barb/audits/`
2. Extract all non-ACCURATE claims (WRONG, OUTDATED, MISSING)
3. For each claim, invoke the **audit-verifier** agent to independently verify
4. Collect results and report conflicts (where verifier DISPUTED the auditor)

This step is optional because it's expensive (one agent per claim). Use it when accuracy matters.
