# 定向代码审计升级

当 ECTM 仍有实质缺口时，用本 reference 补充 kernel 领域审计。它不是泛泛风格评审。

## 触发条件

在以下情况升格根因或主修复前，必须先读本文件：

- 根因不确定，或 Root Cause Gate 无法通过；
- 坏值来自字段、表达式、helper 返回、计数器、引用计数或共享状态；
- caller 根据 helper 返回值改变控制流；
- 候选只修改 consumer、fallback、retry、范围检查或症状；
- 报告只解释 consumer 为什么崩，但没解释坏状态为什么产生。

## 必读 Review Prompts

先读取：

1. `references/review-prompts/kernel/review-core.md`
2. `references/review-prompts/kernel/technical-patterns.md`
3. `references/review-prompts/kernel/callstack.md`
4. `references/review-prompts/kernel/subsystem/subsystem.md`

如果要升格或排除相似修复，还需读取：

5. `references/review-prompts/kernel/false-positive-guide.md`

只加载与当前路径或符号匹配的 subsystem guide，不要一次性加载全部 prompt。review-prompts 保持英文原文。

## 审计问题

1. 这个值的语义是什么：生命周期、状态、边界、所有权、引用计数、缓存还是派生结果？
2. 哪些路径写入或重新解释同一对象和字段？
3. 进入 consumer 前最后的赋值、表达式、helper 返回或实参是什么？
4. caller 如何解释 helper 返回值或共享状态？
5. reader 和 writer 是否受同一锁、序列、RCU 规则或快照保护？
6. 候选修的是 producer 路径，还是只隐藏 consumer 症状？

## 计数器、引用计数与 Mapcount 审计

如果坏状态是计数器、引用计数或 mapcount，不要停在“计数器是旧的”。必须审计该计数本应在哪里递减，以及哪个 helper 返回值或控制流分支会跳过该递减。

必查项：

- 定位修改计数的 writer primitive，而不只是 reader 谓词。
- 追踪对象或页表删除与计数更新之间所有 early return、`continue`、`break` 和 helper 返回分支。
- 如果 helper 把生命周期引用计数转换成“shared”“mapped”“owned”“busy”等语义状态，必须把临时引用污染作为一等嫌疑。
- 下游加锁、重试或“在锁下检查”的补丁，只有在切断错误计数产生路径时，才能作为主修复。

## 大页与页表共享审计

对 hugetlb、THP 或其他页表共享路径，看到旧的 `page_mapped()`/rmap 证据时，必须先穿透 unmap helper 与 sharing helper，再排序修复。

必查项：

- 在 unmap 代码中找出页表项删除到 rmap/mapcount 递减的精确边。
- 审计那些会决定 caller 是否继续遍历叶子 PTE、是否跳过逐页 rmap 删除的 helper 返回值。
- 对 PMD/PUD 共享，必须区分页表页生命周期引用与真实共享语义。
- 搜索修复候选时使用 helper 与语义错配词，例如 `<helper>`、`refcount`、`page_count`、`mapcount`、`rmap`、`unshare` 和 `shared page table`，不要只搜最终 BUG 点。

## 输出

追加到 `ectm_scratchpad.md`：

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
