# Targeted Code Review Escalation

This reference provides kernel domain review when ECTM still has a real gap. It
is not general style review.

## Trigger

Read this file before promoting a root cause or main fix when:

- root cause is uncertain, or a Root Cause Gate cannot pass;
- a bad value comes from a field, expression, helper return, counter, refcount, or shared state;
- caller control flow changes based on helper return value;
- a candidate only changes a consumer, fallback, retry, range check, or symptom;
- the report explains why the consumer crashed but not why the bad state was produced.

## Required Review Prompts

Load these first:

1. `references/review-prompts/kernel/review-core.md`
2. `references/review-prompts/kernel/technical-patterns.md`
3. `references/review-prompts/kernel/callstack.md`
4. `references/review-prompts/kernel/subsystem/subsystem.md`

If promoting or rejecting a similar fix, also read:

5. `references/review-prompts/kernel/false-positive-guide.md`

Load only subsystem guides matching the current file path or symbol. Do not
bulk-load every prompt.

## Review Questions

1. What does this value mean: lifetime, state, bound, ownership, refcount, cache, or derived result?
2. Which paths write or reinterpret the same object and field?
3. What is the last assignment, expression, helper return, or argument before the consumer?
4. How does the caller interpret helper return values or shared state?
5. Are reader and writer protected by the same lock, sequence, RCU rule, or snapshot?
6. Does the candidate fix the producer path or only hide the consumer symptom?

## Counter, Refcount, and Mapcount Review

If the bad state is a counter/refcount/mapcount, do not stop at "the counter is
stale." Audit how the counter was supposed to be decremented, and which helper
return or control-flow edge can skip that decrement.

Required checks:

- Identify the writer primitive that changes the counter, not only the reader predicate.
- Trace all early returns, `continue`, `break`, and helper-return branches between page-table/object removal and the counter update.
- If a helper converts a lifetime refcount into semantic state such as "shared", "mapped", "owned", or "busy", treat transient references as a first-class suspect.
- A downstream lock, retry, or "check under lock" fix is not the main fix unless it cuts the path that produced the wrong counter value.

## Huge Page and Page-Table Sharing Review

For hugetlb, THP, or other page-table sharing paths, stale
`page_mapped()`/rmap evidence must be traced through unmap helpers and sharing
helpers before ranking fixes.

Required checks:

- In unmap code, find the exact edge from page-table entry removal to rmap/mapcount decrement.
- Review helpers whose return value changes whether the caller iterates leaf PTEs or skips per-page rmap removal.
- For PMD/PUD sharing, separate page-table-page lifetime references from actual sharing semantics.
- Search fix candidates using the helper and semantic mismatch terms, for example `<helper>`, `refcount`, `page_count`, `mapcount`, `rmap`, `unshare`, and `shared page table`, rather than the final BUG site alone.

## Output

```md
### Targeted Code Review: <topic>

| Question | Conclusion | Evidence |
|---|---|---|
| value semantics | ... | `<file>:<line>` |
| producer/update path | ... | ... |
| helper/caller effect | ... | ... |
| synchronization | ... | ... |
| candidate ranking | ... | ... |

Promotion/demotion conclusion: ...
```
