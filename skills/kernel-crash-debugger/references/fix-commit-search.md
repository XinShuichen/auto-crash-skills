# Fix Commit Search

Fix search answers two questions: which commit cuts the producer frontier, and
whether the crashed kernel already contains it.

## Preconditions

Before searching, write the producer frontier in ECTM. Do not use panic
function names, fault addresses, log text, OOM text, or retry symptoms as the
primary search anchor.

## Scope

- Use the crashed kernel source only for local mechanism analysis.
- Use an upstream Linux cache for fix search when available.
- Prefer `stable/linux-<major>.<minor>.y`, then mainline branches.
- Do not depend on live network fetch during analysis.

## Search Anchors

Prefer:

- producer function or helper return site;
- same shared object and field;
- writer-side update, rebind, reconfiguration;
- refcount, lock, RCU, memory ordering, snapshot changes;
- validation before the consumer.

Downgrade:

- consumer fallback or defensive checks;
- log-only changes;
- already-included commits;
- different object shape or unreachable call path;
- commits that fix a similar symptom through a different top-level operation, unless they modify the same shared helper used by the actual stack.

## Negative Ranking

Before promoting a candidate, write why stronger-looking symptom matches are
not the main fix. A candidate is weak if it only changes a later delete/remove
check while the producer frontier is an earlier helper return, skipped writer
update, or semantic misuse of a refcount.

For refcount/mapcount/rmap bugs, rank commits by the first edge that makes the
counter wrong:

1. helper semantic fix that prevents a wrong skip;
2. caller control-flow fix that restores the writer update;
3. writer-side locking/ordering around the counter update;
4. consumer-side recheck, retry, or assertion removal.

## Candidate Ranking

| Rank | Commit | Title | Change site | Mechanism match | Included? | Conclusion |
|---|---|---|---|---|---|---|
| 1 | `<sha>` | ... | producer frontier | high | no | main fix |

A main fix must explain which edge of the mechanism chain it cuts.
