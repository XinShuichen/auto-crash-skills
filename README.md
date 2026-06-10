# Auto Crash Skills

[Chinese README](README.zh-CN.md)

Auto Crash Skills packages the `kernel-crash-debugger` Codex skill for Linux
kernel vmcore/kdump analysis. The skill guides an AI agent to collect crash
evidence, maintain an evidence-to-mechanism trail, review relevant kernel code,
and search for the fix commit that cuts the producer-side failure chain.

## What Is Included

- `skills/kernel-crash-debugger/SKILL.md`: the installed skill entry point.
- `skills/kernel-crash-debugger/scripts/crash_driver.py`: the supported
  `crash(8)` driver for one-shot commands, interactive use, and persistent
  Unix socket sessions.
- `skills/kernel-crash-debugger/references/`: ECTM, report format, fix-search,
  and targeted review escalation references.
- `skills/kernel-crash-debugger/references/review-prompts/`: a curated
  kernel-only subset of third-party review prompt references.
- `skills/kernel-crash-debugger-zh-CN/`: Chinese localization overlay for
  `SKILL.md`, UI metadata, and non-review-prompt references.

## Install

```bash
git clone https://github.com/XinShuichen/auto-crash-skills.git
cd auto-crash-skills
./install.sh
```

The default install is English. To install the Chinese skill text instead, run:

```bash
./install.sh --lang zh-CN
```

The installer copies the skill to `${HOME}/.agents/skills/kernel-crash-debugger`
by default. Override the destination with `CODEX_SKILLS_DIR`. You can also set
`CRASH_SKILL_LANG=en` or `CRASH_SKILL_LANG=zh-CN`.

To install into the current workspace instead of the Codex global skills
directory, run:

```bash
./install.sh --current-dir
```

This creates `./.agents/skills/kernel-crash-debugger` under the directory where
the command is run.

If you want an AI assistant to install this skill for you, copy the prompt from
[INSTALL_FOR_AI.md](INSTALL_FOR_AI.md).

## Validated Environment

The current blind validation run used:

- Codex CLI: `codex-cli 0.136.0`
- Model: `gpt-5.4`
- Reasoning effort: `xhigh`

## Usage

Start a new Codex session after installation and ask it to use
`kernel-crash-debugger`. Provide the case paths:

```text
dump file: /path/to/case/dump
vmlinux: /path/to/case/vmlinux
kernel source: /path/to/linux/source
work directory: /path/to/case/.crash-ai
upstream Linux cache: /path/to/upstream/linux  # optional
```

Expected outputs are:

```text
analysis_report.md
ectm_scratchpad.md
context.json
crash_outputs/
```

## Crash Driver Script

```bash
python3 skills/kernel-crash-debugger/scripts/crash_driver.py /path/to/case \
  -c sys \
  -c bt \
  -c log \
  -c "bt -l"
```

For large dumps, start a persistent socket server once and send commands through
the socket:

```bash
python3 skills/kernel-crash-debugger/scripts/crash_driver.py /path/to/case \
  --server \
  --socket /path/to/case/.crash-ai/crash-driver.sock \
  --page-size 65536

python3 skills/kernel-crash-debugger/scripts/crash_driver.py \
  --socket /path/to/case/.crash-ai/crash-driver.sock \
  -c "bt"
```

See `references/crash-driver-remote.md` inside the skill for remote deployment,
pagination, and shutdown details.

## Validation Examples

The public repository does not ship crash dumps, `vmlinux`, or private kernel
source. The tracked examples document the expected validation shape for local
cases:

- [examples/hugetlb-pmd-share](examples/hugetlb-pmd-share/README.md):
  hugetlbfs PMD sharing panic, with a local reproducer and a blind-validation
  transcript.
- [examples/mempolicy-offset-il-node-race](examples/mempolicy-offset-il-node-race/README.md):
  `MPOL_INTERLEAVE` / cpuset rebinding panic at `__next_zones_zonelist`, with a
  blind-validation transcript and expected root-cause chain.

## Privacy

Crash dumps, logs, hostnames, paths, command lines, and kernel reports can
contain secrets or production identifiers. Do not share artifacts that contain
such information.

## License

This repository is released under the MIT License. Bundled third-party review
prompt materials retain their original MIT license and copyright notice.
