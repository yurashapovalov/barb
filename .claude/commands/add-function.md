---
description: Add a new trading function to barb/functions with full workflow (code, SIGNATURES, tests, review)
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Task
---

Add the trading function "$ARGUMENTS" to barb/functions.

Follow these steps exactly:

1. Read docs/barb/functions-architecture.md — find the function spec, which module it belongs to, algorithm details
2. Read the target module file to understand existing style and patterns
3. Explain your implementation plan: algorithm, edge cases, which smoothing method
4. Implement the function following existing patterns in the module
5. Add the function to SIGNATURES dict in the same module
6. Register in barb/functions/__init__.py if needed
7. Write tests in the corresponding test file:
   - Basic functionality test
   - Edge case: empty DataFrame, NaN handling, single row
   - TradingView match test: compare output against known TradingView values
8. Run: `ruff check barb/ tests/`
9. Run: `pytest tests/ -v --tb=short`
10. If everything passes: `git add -A && git commit -m "add $ARGUMENTS function"`
11. Use the code-reviewer agent to review your changes

If any step fails — stop, explain what went wrong, ask for guidance.
