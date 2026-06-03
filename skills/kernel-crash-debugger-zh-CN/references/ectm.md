# ECTM

ECTM 把“看起来像什么”变成“证据如何一步步收窄机制”。分析过程中持续维护两张表。

## Table A：问题演进

| Version | 问题定义 | 新增证据 |
|---|---|---|
| V1 | 现象、panic 文本、crash 点 | `sys`、`bt`、`log` |
| V2 | 对象、字段、寄存器、源码表达式 | structs、`dis -l`、source |
| V3 | 机制、producer frontier、修复候选 | git diff、upstream commit、证伪 |

每当新增证据改变问题边界时更新问题定义。不要让 V1 的表象直接变成最终根因。

## Table B：候选机制

| ID | 假设 | 机制 | 预期指纹 | 验证 | 状态 |
|---|---|---|---|---|---|
| P1 | 当前最强路径 | 坏状态如何进入 consumer | 现场应出现什么 | 具体 crash/source/git 动作 | pending |
| P2 | 可证伪备选 | 另一条解释 | 与 P1 的区分点 | 最快证伪动作 | pending |

至少保留一条备选路径，直到被证伪或被更强机制覆盖。

## Producer Frontier

搜索修复 commit 前必须写清：

- victim 或 consumer；
- 坏值、坏状态或坏指针；
- 进入 consumer 前的最后赋值、源码表达式、helper 返回值、实参、索引或边界；
- 尚未闭环的输入、共享状态、writer-side 路径或读取窗口。

## Root Cause Gate

| Gate | PASS 条件 |
|---|---|
| producer frontier | 已定位坏值生产边界 |
| passive storage | 没把字段或栈槽无证据升为生产者 |
| execution path | 候选生产者和修复点位于实际路径 |
| shared state | reader 和 writer 是同一对象状态，或明确未闭环 |
| containment vs cause | 主修复切断坏输入产生，而非仅兜底 |
| fix anchor | commit 修改 producer frontier 或同一 reader-writer window |

任一关键 gate 失败时，最终结论必须以“未闭环”开头，并列出剩余证据缺口。
