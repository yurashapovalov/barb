---
description: Write or improve tests for a file or function. Uses test-writer agent.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
agent: test-writer
---

Write or improve tests for "$ARGUMENTS".

If a specific file or function is given:
1. Read the source file
2. Read docs/barb/functions-architecture.md if it's a trading function
3. Check if test file exists — if yes, read it and improve; if no, create it
4. Write comprehensive tests following the patterns in existing test files

If no argument given:
1. Find Python files in barb/ and assistant/ without corresponding test files
2. Show the list and ask which one to cover first
