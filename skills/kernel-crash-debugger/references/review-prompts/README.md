# Bundled Kernel Review Prompt References

This directory contains a curated subset of
`https://github.com/masoncl/review-prompts`.

Only Linux kernel prompt/reference files needed by `kernel-crash-debugger` are
included. The original multi-agent setup scripts, non-kernel prompt sets,
workflow examples, and unrelated helper scripts are not bundled.

`kernel-crash-debugger` loads these files on demand through
`references/code-review-escalation.md` when crash evidence still has a real
producer-side gap.

License details are preserved in `LICENSE` and in the repository-level
`THIRD_PARTY_NOTICES.md`.
