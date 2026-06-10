# Crash Driver 远端工作流

当 dump 很大、目标机已有 `crash`/`vmlinux`/dump，或用户要求通过常驻
socket 多轮交互时，使用本 reference。

## 文件

- Skill 脚本：`scripts/crash_driver.py`
- 推荐远端路径：`/tmp/crash_driver.py`
- 推荐工作目录：`<dump-dir>/.crash-ai`
- 推荐 socket：`<dump-dir>/.crash-ai/crash-driver.sock`
- 原始输出：`<work-dir>/crash_outputs/`

## 目标机安全边界

遵守用户对目标机的限制。如果用户限制了目标机操作，不要额外运行 discovery
命令。需要更多 crash 证据时，优先给出精确的
`crash_driver.py --socket ...` 命令，让用户或父 agent 执行。

## 上传

IPv6 目标在远端路径里需要加方括号：

```bash
bgo scp scripts/crash_driver.py root@"[<ipv6>]":/tmp/crash_driver.py
```

如果没有 `bgo scp`，使用用户或环境明确允许的传输方式。不要默认认为
`scp -o ProxyJump=...` 可用。

## 启动常驻 Server

目标机上执行：

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

如果 SSH 断开后还要继续跑：

```bash
nohup python3 /tmp/crash_driver.py "$DUMP_DIR" \
  --server \
  --socket "$SOCK" \
  --page-size 65536 \
  > "$WORK/crash-driver-server.log" 2>&1 &
```

不要给 crash 加启动超时。大 dump 加载几十分钟是正常情况。

## 发命令

socket 出现后：

```bash
python3 /tmp/crash_driver.py --socket "$SOCK" --status
python3 /tmp/crash_driver.py --socket "$SOCK" -c "sys" > "$WORK/crash_outputs/sys.page1.txt"
python3 /tmp/crash_driver.py --socket "$SOCK" -c "bt" > "$WORK/crash_outputs/bt.page1.txt"
python3 /tmp/crash_driver.py --socket "$SOCK" -c "log" > "$WORK/crash_outputs/log.page1.txt"
python3 /tmp/crash_driver.py --socket "$SOCK" -c "bt -l" > "$WORK/crash_outputs/bt-l.page1.txt"
```

需要机器可解析输出时加 `--json`：

```bash
python3 /tmp/crash_driver.py --socket "$SOCK" -c "bt" --json
```

## 分页

大输出会分页。客户端会打印类似提示：

```text
more: --socket <socket> --page <result_id> <next_offset>
```

继续拉下一页：

```bash
python3 /tmp/crash_driver.py --socket "$SOCK" \
  --page <result_id> <next_offset> \
  > "$WORK/crash_outputs/<name>.page2.txt"
```

所有页都保存在 `crash_outputs/`，并把命令写入报告。

## 关闭

正常关闭：

```bash
python3 /tmp/crash_driver.py --socket "$SOCK" --shutdown
```

如果返回 `No such file or directory`，表示预期 case 路径下没有 server
socket。目标机受限时，不要因此扩大操作范围去跑额外进程检查，除非用户明确允许。

## 本次现场沉淀的重试点

- 有些跳板不支持一次性 remote exec。如果
  `ssh -K jump.byted.org -tt ssh root@host 'command'` 立即关闭，改为进入交互
  SSH shell，只输入被允许的命令和 `exit`。
- shutdown 失败不能自动扩大目标机操作权限。socket 不存在通常足以作为 cleanup
  结果记录。
- 派 subagent 审计时，目标机交互留在父 agent；subagent 只返回需要执行的 crash
  命令。
- 如果当前 workspace 下有 `linux-image-bsk/`，优先使用这个源码树做 source
  alignment，不要先去找其它内核 checkout。
