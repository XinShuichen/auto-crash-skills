# Report Format

The report must be a self-contained engineering document, not a chat summary.

## Required Sections

```md
# Linux Kernel Crash Analysis Report

## Basic Information

| Field | Value |
|---|---|
| work directory | ... |
| dump / vmlinux | ... |
| kernel version / source ref | ... |
| panic text | ... |
| dump type | full or partial |

## Executive Conclusion

## Root Cause Gate Audit

## Investigation Log

## Deep Analysis

## Mechanism Chain

## Fix Commit Search

## Recommendations

## ECTM Table A

## ECTM Table B
```

## Evidence Blocks

Preserve the raw command, key output, and a short interpretation.

````md
### `bt`

```text
<raw output>
```

Interpretation: ...
````

## Code Explanation

When quoting source, include source tree identity, file, function, and relevant
code. Explain fields, locks, refcounts, lifetime, and call flow.

## Certainty

Separate root cause from trigger background and residual uncertainty.
