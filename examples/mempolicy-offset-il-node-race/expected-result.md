# Expected Analysis Shape

[Chinese document](expected-result.zh-CN.md)

A successful analysis should not stop at `__next_zones_zonelist()`. It should
prove this chain:

1. The panic is a kernel page fault at `__next_zones_zonelist+0x8` with
   `RDI=0x3348` and `CR2=0x3350`.
2. The faulting instruction (`mov 0x8(%rdi), %ecx`) proves the bad input is an
   invalid `struct zoneref *`.
3. The caller-side stack layout shows `0x3348` is the live `ac.zonelist` input
   to `first_zones_zonelist()` / zonelist iteration, not a valid
   `preferred_zoneref`.
4. `ac.zonelist` comes from `node_zonelist(preferred_nid, gfp_mask)` inside
   `prepare_alloc_pages()`.
5. `preferred_nid` comes from `interleave_nid()` / `offset_il_node()` for an
   `MPOL_INTERLEAVE` policy.
6. On `v5.10.135.bsk.6`, `offset_il_node()` still reads the shared
   `pol->v.nodes` multiple times without a local snapshot. A concurrent
   `cpuset_change_task_nodemask()` -> `mpol_rebind_task()` update can change the
   nodemask between `nodes_weight()`, `first_node()`, and `next_node()`.
7. That reader/writer mismatch can produce `MAX_NUMNODES` or another invalid
   node id, which is then passed into `node_zonelist()` and collapses into the
   low bogus zonelist pointer consumed by `__next_zones_zonelist()`.
8. The main upstream fix is
   `276aeee1c5fc00df700f0782060beae126600472` (`mm/mempolicy: fix a race between offset_il_node and mpol_rebind_task`).
9. The local kernel tag `v5.10.135.bsk.6` does not contain that fix or an
   obvious equivalent backport.

Later upstream work such as `9685e6e30d116d72fb013b0bce261a676b7575c1` and
`274519ed414bd2b9a77c5db78ee51778d37ceacf` is relevant supporting evidence, but
the primary root-cause fix for this crash shape is `276aeee1c5fc00df700f0782060beae126600472`.
