# mempolicy `offset_il_node` Race Validation Example

[Chinese document](README.zh-CN.md)

This example documents the expected local validation shape for a panic in the
`MPOL_INTERLEAVE` allocation path. The public repository does not include a
crash dump, `vmlinux`, or kernel source files.

## Local Inputs

Put local-only files outside git tracking:

```text
local-testdata/mempolicy-offset-il-node-race/
  dump
  vmlinux
  linux-source/      # or an absolute symlink to the matching source tree
```

Then ask Codex to use `kernel-crash-debugger` with those paths and the matching
kernel source.

## Reference Panic

```text
BUG: unable to handle page fault for address: 0000000000003350
RIP: __next_zones_zonelist+0x8/0x40
Comm: offset_il_w
```

The expected analysis outcome is in
[expected-result.md](expected-result.md).

## Blind Validation Transcript

The raw Codex session transcript is available as
[session-019e916f-transcript.html](session-019e916f-transcript.html).
