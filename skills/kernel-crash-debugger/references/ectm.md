# ECTM

ECTM turns "what the crash looks like" into "how evidence narrows the
mechanism." Maintain two tables throughout analysis.

## Table A: Problem Evolution

| Version | Problem definition | New evidence |
|---|---|---|
| V1 | Symptom, panic text, crash point | `sys`, `bt`, `log` |
| V2 | Objects, fields, registers, source expressions | structs, `dis -l`, source |
| V3 | Mechanism, producer frontier, fix candidates | git diff, upstream commit, falsification |

Update the problem definition whenever new evidence changes it. Never let a V1
symptom become the final root cause.

## Table B: Candidate Mechanisms

| ID | Hypothesis | Mechanism | Expected fingerprint | Verification | Status |
|---|---|---|---|---|---|
| P1 | Strongest current path | How the bad state enters the consumer | What the dump should show | Concrete crash/source/git action | pending |
| P2 | Falsifiable alternative | Another explanation | How it differs from P1 | Fastest falsification | pending |

Keep at least one alternative until it is falsified or strictly dominated.

## Producer Frontier

Before searching for a fix commit, write:

- victim or consumer;
- bad value, bad state, or bad pointer;
- last assignment, source expression, helper return, argument, index, or boundary before the consumer;
- unclosed input, shared state, writer-side path, or read window.

## Root Cause Gate

| Gate | PASS condition |
|---|---|
| producer frontier | Bad value production boundary is identified |
| passive storage | Dump fields or stack slots are not treated as producers without writer evidence |
| execution path | Candidate producer and fix are reachable on the actual path |
| shared state | Reader and writer touch the same object and state, or the gap is explicit |
| containment vs cause | Main fix cuts bad input production, not just a downstream guard |
| fix anchor | Commit modifies producer frontier or the same reader-writer window |

If a key gate fails, the final conclusion starts with "Not closed" and lists
remaining evidence gaps.
