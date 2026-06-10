---
name: kernel-crash-debugger
description: 用于分析 Linux kernel crash dump、vmcore/kdump、kernel panic、BUG、hang、watchdog、lockup、OOM、RCU stall、KASAN/KCSAN、lockdep，或基于 crash 证据搜索上游修复 commit。
---

# Kernel Crash Debugger 中文版

你的目标不是改写 crash 输出摘要，而是把现场证据收敛成可复核的机制链，并尽可能找到能切断该机制链的修复 commit。

## 必要输入

以下任何输入缺失时，必须先询问，不要直接下根因结论：

- `dump` 或 `vmcore`
- 与 dump 匹配的 `vmlinux`
- 与崩溃内核匹配的 kernel source tree，或明确说明源码不可用
- 用于保存 `analysis_report.md`、`ectm_scratchpad.md`、`context.json` 和 crash 输出的工作目录
- 可选的 upstream Linux cache，用于搜索修复 commit

## 硬规则

1. 进入实质分析后必须维护 ECTM 双表。
2. 只能使用 `scripts/crash_driver.py` 或直接运行 `crash`；所有命令输出必须保存到工作目录。大 dump、远端常驻 socket 或多轮交互优先使用 `scripts/crash_driver.py`，并先阅读 `references/crash-driver-remote.md`。
3. 先证据后结论；没有 producer 证据时，不要把 panic 函数、最后申请内存者、trap handler 或 consumer 解引用点直接写成根因。
4. 每个机制结论都必须能映射到原始输出、源码、反汇编、对象字段或 git diff。
5. 引用源码前必须核对版本对齐；未对齐时源码行只能作为机制参考。
6. 写清 producer frontier 前不要搜索修复 commit。
7. 根因不确定时，必须读取 `references/code-review-escalation.md` 并完成定向代码审计，再升格候选。
8. 最终输出必须是自包含 Markdown 报告和 JSON 上下文。

## 工作流

1. 对齐输入：dump、`vmlinux`、kernel source、work dir、upstream cache。
2. 先采集 `sys`、`bt`、`log`、`bt -l`；确定 panic 函数后补 `dis -l <function>`。
3. 初始化 `ectm_scratchpad.md`，写 Table A、Table B、当前 producer frontier 和下一条证伪动作。
4. 从指令和寄存器追到对象字段、源码表达式、helper 返回值、caller 控制流和 writer-side 更新。
5. 当 producer frontier 涉及计数器、引用计数、锁、RCU、快照、共享状态或 helper 返回语义时，暂停并做定向代码审计。
6. 使用 producer frontier 术语搜索修复 commit，不要用症状词主导搜索。
7. 写 `analysis_report.md`，更新 `context.json`，确认报告非空且 JSON 可解析。

## 参考文件

- `references/ectm.md`：每次分析必读。
- `references/report-format.md`：写最终报告前必读。
- `references/crash-driver-remote.md`：部署 `crash_driver.py`、启动 socket server、通过 socket 发命令、拉分页输出或关闭远端 server 前必读。
- `references/fix-commit-search.md`：搜索修复 commit 前必读。
- `references/code-review-escalation.md`：根因或候选排序不确定时必读。
- `references/review-prompts/kernel/`：上游英文 review prompts。只按当前代码审计缺口读取相关 prompt，不要修改这些 prompt。

## 输出契约

- `<work_dir>/analysis_report.md`
- `<work_dir>/ectm_scratchpad.md`
- `<work_dir>/context.json`
- `<work_dir>/crash_outputs/`

如果关键 gate 无法通过，结论必须以“未闭环”开头，并写明缺失证据。
