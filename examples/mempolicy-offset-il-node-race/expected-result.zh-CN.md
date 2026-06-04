# 预期分析形态

[English document](expected-result.md)

成功的分析不应停在 `__next_zones_zonelist()`。它应当证明下面这条链：

1. panic 是 `__next_zones_zonelist+0x8` 上的内核页故障，现场寄存器包含
   `RDI=0x3348`、`CR2=0x3350`。
2. faulting instruction `mov 0x8(%rdi), %ecx` 证明坏输入是非法的
   `struct zoneref *`。
3. caller 栈布局说明 `0x3348` 是传给 zonelist 迭代的 live `ac.zonelist`
   输入，而不是合法的 `preferred_zoneref`。
4. `ac.zonelist` 来自 `prepare_alloc_pages()` 中的
   `node_zonelist(preferred_nid, gfp_mask)`。
5. `preferred_nid` 来自 `MPOL_INTERLEAVE` 策略下的
   `interleave_nid()` / `offset_il_node()`。
6. 在 `v5.10.135.bsk.6` 上，`offset_il_node()` 仍然对共享的
   `pol->v.nodes` 做多次无快照读取。并发的
   `cpuset_change_task_nodemask()` -> `mpol_rebind_task()` 更新可以让
   `nodes_weight()`、`first_node()`、`next_node()` 看到不同版本的 nodemask。
7. 这种 reader/writer 失配会产出 `MAX_NUMNODES` 或其他非法 node id，随后被
   传进 `node_zonelist()`，最终坍缩成 `__next_zones_zonelist()` 消费的低地址
   假 zonelist 指针。
8. 主 upstream 修复是
   `276aeee1c5fc00df700f0782060beae126600472`
   `mm/mempolicy: fix a race between offset_il_node and mpol_rebind_task`。
9. 本地内核 tag `v5.10.135.bsk.6` 不包含该修复，也看不到明显等价的
   backport。

后续 upstream 工作如 `9685e6e30d116d72fb013b0bce261a676b7575c1` 和
`274519ed414bd2b9a77c5db78ee51778d37ceacf` 可以作为补充证据，但针对这类 crash
形态的首要根因修复仍然是 `276aeee1c5fc00df700f0782060beae126600472`。
