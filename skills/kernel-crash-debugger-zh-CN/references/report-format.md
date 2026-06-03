# 报告格式

报告必须是自包含工程文档，不是对话摘要。

## 必要章节

```md
# Linux Kernel Crash Analysis Report

## 基础信息

| Field | Value |
|---|---|
| work directory | ... |
| dump / vmlinux | ... |
| kernel version / source ref | ... |
| panic text | ... |
| dump type | full or partial |

## 结论先行

## Root Cause Gate 审计

## 调查日志

## 深度分析

## 机制证据链

## 修复 Commit 搜索

## 建议

## ECTM Table A

## ECTM Table B
```

## 证据块

保留原始命令、关键输出和简要分析。

````md
### `bt`

```text
<raw output>
```

简要分析：...
````

## 代码解释

引用源码时写明源码树身份、文件、函数和相关代码。随后解释字段、锁、引用计数、生命周期和调用流。

## 确定性

区分根因、触发背景和残余不确定性。
