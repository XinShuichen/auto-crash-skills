# mempolicy `offset_il_node` 竞态验证示例

[English document](README.md)

本示例记录 `MPOL_INTERLEAVE` 分配路径 panic 的本地验证形态。公开仓库不包含
crash dump、`vmlinux` 或 kernel source 文件。

## 本地输入

把本地文件放在不进入 git 的目录中：

```text
local-testdata/mempolicy-offset-il-node-race/
  dump
  vmlinux
  linux-source/      # 或指向匹配源码树的绝对路径 symlink
```

随后让 Codex 使用 `kernel-crash-debugger`，并提供这些路径和匹配的
kernel source。

## 参考 Panic

```text
BUG: unable to handle page fault for address: 0000000000003350
RIP: __next_zones_zonelist+0x8/0x40
Comm: offset_il_w
```

预期分析结果见 [expected-result.zh-CN.md](expected-result.zh-CN.md)。

## Blind Validation Transcript

Codex 原始 session transcript 见
[session-019e9145-transcript.html](session-019e9145-transcript.html)。
