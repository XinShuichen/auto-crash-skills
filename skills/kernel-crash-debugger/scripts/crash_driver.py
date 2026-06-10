#!/usr/bin/env python3
"""
Small persistent driver for Linux crash(8).

Copy this file to a Linux machine that has crash, vmlinux and vmcore, then run:

    python3 crash_driver.py /path/to/workdir
    python3 crash_driver.py --vmlinux /path/vmlinux --dump /path/vmcore
    python3 crash_driver.py /path/to/workdir -c "bt"
    python3 crash_driver.py /path/to/workdir --server --socket /tmp/crash-driver.sock
    python3 crash_driver.py --socket /tmp/crash-driver.sock -c "bt"

Environment:
    CRASH_BIN                  crash binary path, default: crash
    CRASH_DRIVER_LOG_FILE      debug log path, default: /tmp/crash_driver.log
"""

import argparse
import datetime
import fcntl
import json
import os
import select
import socket
import subprocess
import sys
import threading
import time
import uuid


DEFAULT_PROMPT = "crash> "
DEFAULT_PAGE_SIZE = 64 * 1024


def log_debug(msg):
    log_file = os.environ.get("CRASH_DRIVER_LOG_FILE", "/tmp/crash_driver.log")
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            f.write(f"[{ts}] [DRIVER] {msg}\n")
    except Exception:
        pass


class CrashSession:
    def __init__(self, work_dir=None, vmlinux_path=None, dump_path=None, crash_bin=None):
        self.work_dir = os.path.abspath(work_dir or os.getcwd())
        self.process = None
        self.vmlinux_path = os.path.abspath(vmlinux_path) if vmlinux_path else None
        self.dump_path = os.path.abspath(dump_path) if dump_path else None
        self.crash_bin = crash_bin or os.environ.get("CRASH_BIN", "crash")
        self.io_lock = threading.Lock()
        self._pending_stdout = ""

        log_debug(f"Initializing CrashSession in {self.work_dir}")
        if not self.vmlinux_path or not self.dump_path:
            self._find_files()
        self._start_process()

    def _select_largest(self, paths):
        def size(path):
            try:
                return os.path.getsize(os.path.realpath(path))
            except OSError:
                return -1

        return max(paths, key=size)

    def _find_files(self):
        if not os.path.isdir(self.work_dir):
            raise FileNotFoundError(f"work directory does not exist: {self.work_dir}")

        vmlinux_candidates = []
        dump_candidates = []
        for name in os.listdir(self.work_dir):
            path = os.path.join(self.work_dir, name)
            if not (os.path.isfile(path) or os.path.islink(path)):
                continue

            lower_name = name.lower()
            if not self.vmlinux_path and name == "kernel_link":
                real_path = os.path.realpath(path)
                self.vmlinux_path = real_path if os.path.exists(real_path) else path
            if "vmlinux" in lower_name:
                vmlinux_candidates.append(path)
            if "vmcore" in lower_name or "dump" in lower_name or "core" in lower_name:
                dump_candidates.append(path)

        if not self.vmlinux_path and vmlinux_candidates:
            self.vmlinux_path = self._select_largest(vmlinux_candidates)
        if not self.dump_path and dump_candidates:
            self.dump_path = self._select_largest(dump_candidates)
        if not self.vmlinux_path:
            raise FileNotFoundError(f"no vmlinux file found in {self.work_dir}")
        if not self.dump_path:
            raise FileNotFoundError(f"no vmcore/dump file found in {self.work_dir}")

        self.vmlinux_path = os.path.abspath(self.vmlinux_path)
        self.dump_path = os.path.abspath(self.dump_path)

    def _start_process(self):
        cmd = [self.crash_bin, self.vmlinux_path, self.dump_path]
        log_debug(f"Starting crash process: {cmd}")
        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=self.work_dir,
            bufsize=0,
        )
        log_debug(f"Crash process started, pid={self.process.pid}")

        fd = self.process.stdout.fileno()
        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        self._sync_startup()

    def _startup_failure(self, prefix, output=""):
        rc = self.process.poll() if self.process else None
        try:
            output = (output or "") + self._read_stdout_nonblocking(1.0, 256 * 1024)
        except Exception:
            pass

        snippet = " ".join((output or "").split())
        if len(snippet) > 1600:
            snippet = snippet[:800] + " ... " + snippet[-800:]

        message = (
            f"{prefix}; crash_returncode={rc}; crash_bin={self.crash_bin}; "
            f"vmlinux={self.vmlinux_path}; dump={self.dump_path}; "
            f"output={snippet or '<empty>'}"
        )
        log_debug(message)
        return RuntimeError(message)

    def _read_stdout_nonblocking(self, timeout_s, max_bytes=1024 * 1024):
        if not self.process or not self.process.stdout:
            return ""

        fd = self.process.stdout.fileno()
        deadline = time.time() + max(0.0, float(timeout_s))
        chunks = []
        total = 0

        while True:
            remaining = deadline - time.time()
            if remaining <= 0:
                break

            try:
                readable, _, _ = select.select([fd], [], [], remaining)
            except Exception:
                break
            if not readable:
                break

            while True:
                try:
                    data = os.read(fd, 8192)
                except BlockingIOError:
                    break
                except Exception:
                    return "".join(chunks)
                if not data:
                    break

                chunks.append(data.decode("utf-8", errors="replace"))
                total += len(data)
                if total >= max_bytes:
                    break

            if total >= max_bytes:
                break

        return "".join(chunks)

    def _read_until_token(self, token, timeout_s=None, also_accept_prompt=False):
        start = time.time()
        buf = self._pending_stdout
        self._pending_stdout = ""

        while True:
            if token in buf:
                idx = buf.find(token)
                before = buf[:idx]
                after = buf[idx + len(token):]
                newline = after.find("\n")
                if newline != -1:
                    after = after[newline + 1:]
                else:
                    after += self._read_stdout_nonblocking(0.05)
                if after.startswith(DEFAULT_PROMPT):
                    after = after[len(DEFAULT_PROMPT):]
                self._pending_stdout = after
                return before, True

            if also_accept_prompt and DEFAULT_PROMPT in buf:
                idx = buf.find(DEFAULT_PROMPT)
                before = buf[:idx]
                self._pending_stdout = buf[idx + len(DEFAULT_PROMPT):]
                return before, True

            if timeout_s is not None:
                elapsed = time.time() - start
                if elapsed >= timeout_s:
                    self._pending_stdout = buf
                    return buf, False
                wait_s = min(0.5, timeout_s - elapsed)
            else:
                wait_s = 0.5

            chunk = self._read_stdout_nonblocking(wait_s)
            if chunk:
                buf += chunk
            elif self.process and self.process.poll() is not None:
                self._pending_stdout = buf
                return buf, False

    def _sync_startup(self):
        time.sleep(0.2)
        self._pending_stdout = self._read_stdout_nonblocking(0.05, 256 * 1024)
        if self.process.poll() is not None:
            raise self._startup_failure("crash exited before startup sync", self._pending_stdout)

        marker = self._new_marker()
        with self.io_lock:
            try:
                self.process.stdin.write(b"set scroll off\n")
                self.process.stdin.write(f"echo {marker}\n".encode("utf-8"))
                self.process.stdin.flush()
            except BrokenPipeError:
                raise self._startup_failure("crash pipe broke during startup sync", self._pending_stdout)

        out, ok = self._read_until_token(marker, timeout_s=None, also_accept_prompt=False)
        if self.process.poll() is not None:
            raise self._startup_failure("crash exited during startup sync", out)
        if not ok:
            raise self._startup_failure("crash startup sync failed", out)

    def _new_marker(self):
        return f"__CRASH_DRIVER_SPLIT_{uuid.uuid4().hex}__"

    def run_command(self, cmd, output_file=None):
        log_debug(f"run_command: {cmd}")
        if not self.process or self.process.poll() is not None:
            raise RuntimeError("crash process is not running")

        try:
            self._pending_stdout += self._read_stdout_nonblocking(0.001)
            if self._pending_stdout.startswith(DEFAULT_PROMPT):
                self._pending_stdout = self._pending_stdout[len(DEFAULT_PROMPT):]
        except Exception:
            pass

        marker = self._new_marker()
        full_cmd = f"{cmd}\necho {marker}\n"
        with self.io_lock:
            try:
                self.process.stdin.write(full_cmd.encode("utf-8"))
                self.process.stdin.flush()
            except BrokenPipeError:
                raise RuntimeError("crash process pipe broken")

        initial = self._pending_stdout
        self._pending_stdout = ""
        out, ok = self._read_until_token(marker, timeout_s=None, also_accept_prompt=False)
        result = initial + out

        if not ok:
            raise RuntimeError(f"crash exited before completing command: {cmd}")

        result = self._clean_output(result, cmd)
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(result)
            return output_file
        return result.strip()

    def _clean_output(self, output, cmd):
        lines = output.replace("\r\n", "\n").splitlines()
        cleaned = []
        command_seen = False
        for line in lines:
            if line.startswith(DEFAULT_PROMPT):
                line = line[len(DEFAULT_PROMPT):]
            stripped = line.strip()
            if not command_seen and stripped in (cmd.strip(), f"{DEFAULT_PROMPT}{cmd}".strip()):
                command_seen = True
                continue
            if stripped.startswith("echo __CRASH_DRIVER_SPLIT_"):
                continue
            if stripped == DEFAULT_PROMPT.strip():
                continue
            cleaned.append(line)
        return "\n".join(cleaned).strip()

    def close(self):
        log_debug("Closing crash session")
        if not self.process:
            return

        if self.process.poll() is None:
            try:
                self.process.stdin.write(b"quit\n")
                self.process.stdin.flush()
            except Exception:
                pass
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                self.process.kill()
        self.process = None


class PagedResultStore:
    def __init__(self):
        self._results = {}
        self._lock = threading.Lock()

    def put(self, text):
        result_id = uuid.uuid4().hex
        with self._lock:
            self._results[result_id] = text or ""
        return result_id

    def page(self, result_id, offset=0, page_size=DEFAULT_PAGE_SIZE):
        with self._lock:
            if result_id not in self._results:
                raise KeyError(f"unknown result_id: {result_id}")
            text = self._results[result_id]

        offset = max(0, int(offset))
        page_size = max(1, int(page_size or DEFAULT_PAGE_SIZE))
        next_offset = min(len(text), offset + page_size)
        data = text[offset:next_offset]
        done = next_offset >= len(text)
        return {
            "result_id": result_id,
            "offset": offset,
            "next_offset": next_offset,
            "page_size": page_size,
            "total_size": len(text),
            "done": done,
            "data": data,
        }


class CrashSocketServer:
    def __init__(self, socket_path, session, default_page_size=DEFAULT_PAGE_SIZE):
        self.socket_path = os.path.abspath(socket_path)
        self.session = session
        self.default_page_size = int(default_page_size or DEFAULT_PAGE_SIZE)
        self.results = PagedResultStore()
        self._listener = None
        self._stop = threading.Event()

    def handle_request(self, request):
        op = request.get("op")
        try:
            if op == "run":
                command = (request.get("command") or "").strip()
                if not command:
                    raise ValueError("missing command")
                output = self.session.run_command(command)
                result_id = self.results.put(output)
                return self._ok(self.results.page(
                    result_id,
                    offset=0,
                    page_size=request.get("page_size", self.default_page_size),
                ))

            if op == "page":
                result_id = request.get("result_id")
                if not result_id:
                    raise ValueError("missing result_id")
                return self._ok(self.results.page(
                    result_id,
                    offset=request.get("offset", 0),
                    page_size=request.get("page_size", self.default_page_size),
                ))

            if op == "status":
                process = getattr(self.session, "process", None)
                return self._ok({
                    "vmlinux": getattr(self.session, "vmlinux_path", None),
                    "dump": getattr(self.session, "dump_path", None),
                    "crash_pid": getattr(process, "pid", None),
                    "alive": process is None or process.poll() is None,
                })

            if op == "shutdown":
                self._stop.set()
                return self._ok({"shutting_down": True})

            raise ValueError(f"unknown op: {op}")
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def _ok(self, payload):
        response = {"ok": True}
        response.update(payload)
        return response

    def serve_forever(self):
        socket_dir = os.path.dirname(self.socket_path)
        if socket_dir:
            os.makedirs(socket_dir, exist_ok=True)
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)

        self._listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._listener.bind(self.socket_path)
        self._listener.listen(16)
        log_debug(f"Crash socket server listening on {self.socket_path}")

        try:
            while not self._stop.is_set():
                try:
                    conn, _ = self._listener.accept()
                except OSError:
                    if self._stop.is_set():
                        break
                    raise
                with conn:
                    self._handle_connection(conn)
        finally:
            self.shutdown(close_session=True)

    def _handle_connection(self, conn):
        file = conn.makefile("rwb")
        line = file.readline()
        if not line:
            return
        try:
            request = json.loads(line.decode("utf-8"))
        except json.JSONDecodeError as exc:
            response = {"ok": False, "error": f"invalid json: {exc}"}
        else:
            response = self.handle_request(request)
        file.write((json.dumps(response, ensure_ascii=False) + "\n").encode("utf-8"))
        file.flush()

    def shutdown(self, close_session=False):
        self._stop.set()
        if not close_session:
            try:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                    sock.connect(self.socket_path)
            except OSError:
                pass
        listener = self._listener
        self._listener = None
        if listener:
            try:
                listener.close()
            except OSError:
                pass
        if close_session:
            self.session.close()
        try:
            if os.path.exists(self.socket_path):
                os.unlink(self.socket_path)
        except OSError:
            pass


class CrashSocketClient:
    def __init__(self, socket_path):
        self.socket_path = os.path.abspath(socket_path)

    def request(self, payload):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.connect(self.socket_path)
            file = sock.makefile("rwb")
            file.write((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))
            file.flush()
            line = file.readline()
        if not line:
            raise RuntimeError("empty response from crash socket server")
        return json.loads(line.decode("utf-8"))

    def run(self, command, page_size=None):
        payload = {"op": "run", "command": command}
        if page_size is not None:
            payload["page_size"] = page_size
        return self.request(payload)

    def page(self, result_id, offset, page_size=None):
        payload = {
            "op": "page",
            "result_id": result_id,
            "offset": int(offset),
        }
        if page_size is not None:
            payload["page_size"] = page_size
        return self.request(payload)

    def status(self):
        return self.request({"op": "status"})

    def shutdown(self):
        return self.request({"op": "shutdown"})


def read_paste_block():
    print("paste crash commands, finish with a single '.' line", file=sys.stderr)
    lines = []
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        if line.rstrip("\n") == ".":
            break
        lines.append(line)
    return "".join(lines).rstrip("\n")


def interactive_loop(session):
    print(f"connected: vmlinux={session.vmlinux_path} dump={session.dump_path}", file=sys.stderr)
    print("type :quit to exit, :paste for multi-line command input", file=sys.stderr)
    while True:
        try:
            cmd = input("crash-driver> ")
        except EOFError:
            print(file=sys.stderr)
            break
        except KeyboardInterrupt:
            print(file=sys.stderr)
            continue

        if not cmd.strip():
            continue
        if cmd.strip() in (":q", ":quit", "quit", "exit"):
            break
        if cmd.strip() == ":paste":
            cmd = read_paste_block()
            if not cmd:
                continue

        try:
            output = session.run_command(cmd)
        except Exception as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            continue

        if output:
            print(output)


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Persistent multi-round driver for Linux crash(8).")
    parser.add_argument("work_dir", nargs="?", default=".", help="directory containing vmlinux and vmcore")
    parser.add_argument("--vmlinux", help="explicit vmlinux path")
    parser.add_argument("--dump", help="explicit vmcore/dump path")
    parser.add_argument("--crash-bin", default=os.environ.get("CRASH_BIN", "crash"), help="crash binary path")
    parser.add_argument("--server", action="store_true", help="start a persistent Unix socket server")
    parser.add_argument("--socket", help="Unix socket path for server or client mode")
    parser.add_argument("--page-size", type=int, default=DEFAULT_PAGE_SIZE, help="maximum bytes returned per page")
    parser.add_argument("--page", nargs=2, metavar=("RESULT_ID", "OFFSET"), help="fetch a stored output page")
    parser.add_argument("--status", action="store_true", help="query a Unix socket server")
    parser.add_argument("--shutdown", action="store_true", help="ask a Unix socket server to exit")
    parser.add_argument("--json", action="store_true", help="print raw JSON responses in socket client mode")
    parser.add_argument("-c", "--command", action="append", help="run command and exit; may be repeated")
    parser.add_argument("-o", "--output", help="write single command output to file")
    return parser.parse_args(argv)


def default_socket_path(work_dir):
    return os.path.join(os.path.abspath(work_dir), "crash-driver.sock")


def print_socket_response(response, socket_path=None, as_json=False):
    if as_json:
        print(json.dumps(response, ensure_ascii=False, indent=2))
        return
    if not response.get("ok"):
        print(f"ERROR: {response.get('error', 'unknown error')}", file=sys.stderr)
        return

    data = response.get("data")
    if data is not None:
        if data:
            print(data, end="" if data.endswith("\n") else "\n")
        if not response.get("done", True):
            print(
                "more: --socket {socket} --page {result_id} {next_offset}".format(
                    socket=socket_path or "<socket>",
                    result_id=response["result_id"],
                    next_offset=response["next_offset"],
                ),
                file=sys.stderr,
            )
        return

    for key in sorted(k for k in response.keys() if k != "ok"):
        print(f"{key}: {response[key]}")


def run_socket_client(args):
    client = CrashSocketClient(args.socket)
    responses = []
    if args.status:
        responses.append(client.status())
    if args.page:
        result_id, offset = args.page
        responses.append(client.page(result_id, offset, page_size=args.page_size))
    if args.command:
        for command in args.command:
            responses.append(client.run(command, page_size=args.page_size))
    if args.shutdown:
        responses.append(client.shutdown())
    if not responses:
        raise ValueError("--socket client mode needs --command, --page, --status, or --shutdown")

    exit_code = 0
    for response in responses:
        if not response.get("ok"):
            exit_code = 1
        print_socket_response(response, socket_path=args.socket, as_json=args.json)
    return exit_code


def run_socket_server(args):
    socket_path = args.socket or default_socket_path(args.work_dir)
    session = CrashSession(
        work_dir=args.work_dir,
        vmlinux_path=args.vmlinux,
        dump_path=args.dump,
        crash_bin=args.crash_bin,
    )
    server = CrashSocketServer(socket_path, session, default_page_size=args.page_size)
    print(f"crash socket server listening: {socket_path}", file=sys.stderr)
    server.serve_forever()
    return 0


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    session = None
    try:
        if args.server:
            return run_socket_server(args)

        if args.socket:
            return run_socket_client(args)

        session = CrashSession(
            work_dir=args.work_dir,
            vmlinux_path=args.vmlinux,
            dump_path=args.dump,
            crash_bin=args.crash_bin,
        )

        if args.command:
            if args.output and len(args.command) != 1:
                raise ValueError("--output can only be used with one --command")
            for command in args.command:
                result = session.run_command(command, output_file=args.output)
                if not args.output and result:
                    print(result)
            return 0

        interactive_loop(session)
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        if session:
            session.close()


if __name__ == "__main__":
    sys.exit(main())
