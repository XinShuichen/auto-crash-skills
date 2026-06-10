# Crash Driver Remote Workflow

Use this reference when the dump is large, the target machine already has
`crash`, `vmlinux`, and the dump, or the user asks to interact with crash over a
persistent socket.

## Files

- Skill script: `scripts/crash_driver.py`
- Recommended remote path: `/tmp/crash_driver.py`
- Recommended work directory: `<dump-dir>/.crash-ai`
- Recommended socket: `<dump-dir>/.crash-ai/crash-driver.sock`
- Raw outputs: `<work-dir>/crash_outputs/`

## Target Safety

Follow the user's target-machine restrictions. When the user limits target
operations, do not run discovery commands beyond the allowed set. If more crash
evidence is needed, prefer returning exact `crash_driver.py --socket ...`
commands for the user or parent agent to run.

## Upload

For IPv6 targets, bracket the address in remote-copy specs:

```bash
bgo scp scripts/crash_driver.py root@"[<ipv6>]":/tmp/crash_driver.py
```

If `bgo scp` is not available, use the transfer method approved by the user or
local environment. Do not assume direct `scp -o ProxyJump=...` will work.

## Start A Persistent Server

On the target:

```bash
DUMP_DIR=/var/crash/bak-<timestamp>
WORK=$DUMP_DIR/.crash-ai
SOCK=$WORK/crash-driver.sock

mkdir -p "$WORK/crash_outputs"
chmod +x /tmp/crash_driver.py
export CRASH_BIN=/usr/bin/crash
export CRASH_DRIVER_LOG_FILE="$WORK/crash_driver.log"

python3 /tmp/crash_driver.py "$DUMP_DIR" \
  --server \
  --socket "$SOCK" \
  --page-size 65536
```

For a session that must survive SSH disconnect:

```bash
nohup python3 /tmp/crash_driver.py "$DUMP_DIR" \
  --server \
  --socket "$SOCK" \
  --page-size 65536 \
  > "$WORK/crash-driver-server.log" 2>&1 &
```

There is intentionally no crash startup timeout. Large dumps can take tens of
minutes to load.

## Send Commands

After the socket exists:

```bash
python3 /tmp/crash_driver.py --socket "$SOCK" --status
python3 /tmp/crash_driver.py --socket "$SOCK" -c "sys" > "$WORK/crash_outputs/sys.page1.txt"
python3 /tmp/crash_driver.py --socket "$SOCK" -c "bt" > "$WORK/crash_outputs/bt.page1.txt"
python3 /tmp/crash_driver.py --socket "$SOCK" -c "log" > "$WORK/crash_outputs/log.page1.txt"
python3 /tmp/crash_driver.py --socket "$SOCK" -c "bt -l" > "$WORK/crash_outputs/bt-l.page1.txt"
```

Use `--json` if the response needs to be parsed by another tool:

```bash
python3 /tmp/crash_driver.py --socket "$SOCK" -c "bt" --json
```

## Pagination

Large outputs are paginated. The client prints a follow-up hint like:

```text
more: --socket <socket> --page <result_id> <next_offset>
```

Fetch the next page:

```bash
python3 /tmp/crash_driver.py --socket "$SOCK" \
  --page <result_id> <next_offset> \
  > "$WORK/crash_outputs/<name>.page2.txt"
```

Keep all pages in `crash_outputs/` and record the command in the report.

## Shutdown

Clean shutdown:

```bash
python3 /tmp/crash_driver.py --socket "$SOCK" --shutdown
```

If the socket path returns `No such file or directory`, treat that as "no server
is listening at this expected case path." Do not run extra process inspection on
a restricted target unless the user explicitly permits it.

## Retry Notes From Field Use

- Some jump hosts reject one-shot remote exec. If
  `ssh -K jump.byted.org -tt ssh root@host 'command'` closes immediately, open
  an interactive SSH shell and type only the allowed command plus `exit`.
- Do not let a failed shutdown broaden the target-machine operation set. A
  missing socket is usually enough for cleanup when target operations are
  restricted.
- When delegating to subagents, keep target interaction in the parent agent.
  Subagents should return exact crash commands instead of opening new target
  sessions.
- If the current workspace contains `linux-image-bsk/`, use that source tree
  first for source alignment before looking for another kernel checkout.
