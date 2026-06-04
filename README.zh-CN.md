# Auto Crash Skills

[English README](README.md)

Auto Crash Skills 打包了用于 Linux kernel vmcore/kdump 分析的
`kernel-crash-debugger` Codex skill。这个 skill 会引导 AI agent 采集 crash
证据、维护从证据到机制的链路、审计相关内核代码，并搜索能切断 producer-side
故障链的修复 commit。

## 包含内容

- `skills/kernel-crash-debugger/SKILL.md`：安装后的 skill 入口。
- `skills/kernel-crash-debugger/scripts/crash_session.py`：直接运行 `crash`
  命令并把输出保存到分析工作目录的脚本。
- `skills/kernel-crash-debugger/references/`：ECTM、报告格式、修复搜索和定向
  review escalation reference。
- `skills/kernel-crash-debugger/references/review-prompts/`：经过裁剪的
  kernel-only 第三方 review prompt reference。
- `skills/kernel-crash-debugger-zh-CN/`：中文本地化 overlay，包含中文
  `SKILL.md`、UI metadata 和非 review-prompt references。

## 安装

```bash
git clone https://github.com/XinShuichen/auto-crash-skills.git
cd auto-crash-skills
./install.sh
```

默认安装英文版。如果要安装中文 skill 文本，运行：

```bash
./install.sh --lang zh-CN
```

默认安装到 `${HOME}/.codex/skills/kernel-crash-debugger`。可以用
`CODEX_HOME` 或 `CODEX_SKILLS_DIR` 覆盖目标目录，也可以用
`CRASH_SKILL_LANG=en` 或 `CRASH_SKILL_LANG=zh-CN` 选择语言。

如果想让 AI 助手代为安装这个 skill，请复制
[INSTALL_FOR_AI.zh-CN.md](INSTALL_FOR_AI.zh-CN.md) 里的 prompt。

## 验证环境

当前 blind validation 使用：

- Codex CLI：`codex-cli 0.136.0`
- 模型：`gpt-5.4`
- 推理等级：`xhigh`

## 使用

安装后重新打开 Codex session，并要求它使用 `kernel-crash-debugger`。提供以下
case 路径：

```text
dump file: /path/to/case/dump
vmlinux: /path/to/case/vmlinux
kernel source: /path/to/linux/source
work directory: /path/to/case/.crash-ai
upstream Linux cache: /path/to/upstream/linux  # 可选
```

预期输出：

```text
analysis_report.md
ectm_scratchpad.md
context.json
crash_outputs/
```

## 直接运行 crash 脚本

```bash
python3 skills/kernel-crash-debugger/scripts/crash_session.py collect \
  --dump-dir /path/to/case \
  --work-dir /path/to/case/.crash-ai \
  --command sys \
  --command bt \
  --command log \
  --command "bt -l"
```

脚本只写本地文件，不发布报告，也不会上传分析产物。

## 验证示例

公开仓库不包含 crash dump、`vmlinux` 或私有内核源码。当前跟踪的本地验证示例有：

- [examples/hugetlb-pmd-share](examples/hugetlb-pmd-share/README.zh-CN.md)：
  hugetlbfs PMD sharing panic，包含本地 reproducer 和 blind validation
  transcript。
- [examples/mempolicy-offset-il-node-race](examples/mempolicy-offset-il-node-race/README.zh-CN.md)：
  `MPOL_INTERLEAVE` / cpuset rebinding 导致的 `__next_zones_zonelist` panic，
  包含 blind validation transcript 和预期根因链。

## 隐私

Crash dump、日志、主机名、路径、命令行和内核报告都可能包含密钥或生产环境标识。
公开分享前需要确认 artifacts 不包含这些信息。

## 协议

本仓库使用 MIT License 发布。内置第三方 review prompt 材料保留原始 MIT
license 和版权声明。
