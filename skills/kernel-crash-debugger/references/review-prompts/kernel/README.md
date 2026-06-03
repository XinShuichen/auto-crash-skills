# Kernel Review Prompt References

These files provide optional kernel-domain review context for
`kernel-crash-debugger`. They are not an installer, command set, or runtime
wrapper.

Start with:

- `review-core.md`
- `technical-patterns.md`
- `callstack.md`
- `false-positive-guide.md`
- `subsystem/subsystem.md`

Then load only subsystem files that match the current crash evidence, source
file, or suspected producer frontier. Do not bulk-load every subsystem prompt.
