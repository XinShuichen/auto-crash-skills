# Auto Crash Skills

[Chinese README](README.zh-CN.md)

Auto Crash Skills packages the `kernel-crash-debugger` Codex skill for Linux
kernel vmcore/kdump analysis. The skill guides an AI agent to collect crash
evidence, maintain an evidence-to-mechanism trail, review relevant kernel code,
and search for the fix commit that cuts the producer-side failure chain.

## What Is Included

- `skills/kernel-crash-debugger/SKILL.md`: the installed skill entry point.
- `skills/kernel-crash-debugger/scripts/crash_session.py`: a direct `crash`
  command runner that saves outputs under the analysis work directory.
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

The installer copies the skill to `${HOME}/.codex/skills/kernel-crash-debugger`
by default. Override the destination with `CODEX_HOME` or `CODEX_SKILLS_DIR`.
You can also set `CRASH_SKILL_LANG=en` or `CRASH_SKILL_LANG=zh-CN`.

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

## Direct Crash Script

```bash
python3 skills/kernel-crash-debugger/scripts/crash_session.py collect \
  --dump-dir /path/to/case \
  --work-dir /path/to/case/.crash-ai \
  --command sys \
  --command bt \
  --command log \
  --command "bt -l"
```

The script writes local files only. It does not publish reports or upload
artifacts.

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
