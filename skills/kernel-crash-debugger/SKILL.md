---
name: kernel-crash-debugger
description: Use when analyzing Linux kernel crash dumps, vmcore/kdump files, kernel panic, BUG, hang, watchdog, lockup, OOM, RCU stall, KASAN/KCSAN, lockdep, or searching for an upstream fix commit from crash evidence.
---

# Kernel Crash Debugger

Your job is not to summarize crash output. Your job is to turn crash evidence
into a reproducible mechanism chain and, when possible, find the commit that
cuts that chain.

## Required Inputs

If any item is missing, ask for it before making root cause claims:

- `dump` or `vmcore`
- `vmlinux` matching the dump
- kernel source tree matching the crashed kernel, or a clear statement that source is unavailable
- work directory for `analysis_report.md`, `ectm_scratchpad.md`, `context.json`, and crash outputs
- optional upstream Linux cache for fix search

## Hard Rules

1. Always maintain ECTM tables for non-trivial analysis.
2. Use `scripts/crash_session.py` or direct `crash` only; keep all command outputs in the work directory.
3. Evidence before conclusion. Do not call the panic function, last allocator, trap handler, or consumer dereference the root cause without producer evidence.
4. Every mechanism claim must map to raw output, source code, disassembly, object fields, or a git diff.
5. Verify source alignment before quoting source as fact. If source does not match the dump, downgrade source lines to mechanism hints.
6. Do not search for fix commits until the producer frontier is written.
7. If root cause is uncertain, read `references/code-review-escalation.md` and perform targeted review before promoting a candidate.
8. Final output must be self-contained Markdown plus JSON context.

## Workflow

1. Align inputs: dump, `vmlinux`, kernel source, work dir, upstream cache.
2. Collect first evidence: `sys`, `bt`, `log`, and `bt -l`; add `dis -l <function>` once the panic function is known.
3. Initialize `ectm_scratchpad.md` with Table A, Table B, current producer frontier, and next falsification step.
4. Trace from instruction and registers to object fields, source expressions, helper returns, caller control flow, and writer-side updates.
5. When the producer frontier involves counters, refcounts, locks, RCU, snapshots, shared state, or helper return semantics, pause and run targeted code review.
6. Search fix commits using producer frontier terms, not symptom text.
7. Write `analysis_report.md`, update `context.json`, verify both are non-empty and parseable.

## References

- `references/ectm.md`: read for every analysis.
- `references/report-format.md`: read before writing a final report.
- `references/fix-commit-search.md`: read before upstream/local fix search.
- `references/code-review-escalation.md`: read when root cause or candidate ranking is uncertain.
- `references/review-prompts/kernel/`: upstream English review prompts. Read only the prompt files relevant to the current code review gap.

## Output Contract

- `<work_dir>/analysis_report.md`
- `<work_dir>/ectm_scratchpad.md`
- `<work_dir>/context.json`
- `<work_dir>/crash_outputs/`

If a gate cannot pass, the conclusion must start with "Not closed" and name
the missing evidence.
