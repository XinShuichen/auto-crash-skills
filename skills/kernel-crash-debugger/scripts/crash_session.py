#!/usr/bin/env python3
"""Small command runner for the Linux crash utility."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path


DEFAULT_COMMANDS = ["sys", "bt", "log", "bt -l"]


def safe_name(command: str) -> str:
    name = re.sub(r"[^A-Za-z0-9_.-]+", "_", command.strip()).strip("_")
    return name[:80] or "command"


def find_file(dump_dir: Path, explicit: str | None, names: list[str]) -> Path:
    if explicit:
        path = Path(explicit).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"file not found: {path}")
        return path

    for name in names:
        path = dump_dir / name
        if path.is_file():
            return path

    candidates = []
    for pattern in ("*.vmcore", "*.dump", "dump.*", "vmcore.*"):
        candidates.extend(p for p in dump_dir.glob(pattern) if p.is_file())
    if candidates:
        return sorted(candidates)[0]

    raise FileNotFoundError(f"none of {names} found in {dump_dir}")


def run_one(
    crash_bin: str,
    vmlinux: Path,
    dump: Path,
    command: str,
    output_dir: Path,
    timeout: int,
) -> dict[str, object]:
    stamp = int(time.time() * 1000)
    command_file = output_dir / f"{safe_name(command)}_{stamp}.cmd"
    output_file = output_dir / f"{safe_name(command)}_{stamp}.txt"
    command_file.write_text(f"set scroll off\n{command}\nquit\n", encoding="utf-8")

    argv = [crash_bin, "-i", str(command_file), str(vmlinux), str(dump)]
    started = time.time()
    try:
        proc = subprocess.run(
            argv,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
        )
        output_file.write_text(proc.stdout, encoding="utf-8", errors="replace")
        return {
            "command": command,
            "output": str(output_file),
            "returncode": proc.returncode,
            "elapsed_sec": round(time.time() - started, 3),
        }
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout or ""
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")
        output_file.write_text(output + "\n[TIMEOUT]\n", encoding="utf-8", errors="replace")
        return {
            "command": command,
            "output": str(output_file),
            "returncode": None,
            "timeout": True,
            "elapsed_sec": round(time.time() - started, 3),
        }


def collect(args: argparse.Namespace) -> int:
    dump_dir = Path(args.dump_dir).expanduser().resolve()
    if not dump_dir.is_dir():
        raise FileNotFoundError(f"dump directory not found: {dump_dir}")

    crash_bin = shutil.which(args.crash_bin) if "/" not in args.crash_bin else args.crash_bin
    if not crash_bin:
        raise FileNotFoundError(f"crash binary not found: {args.crash_bin}")

    dump = find_file(dump_dir, args.dump, ["dump", "vmcore"])
    vmlinux = find_file(dump_dir, args.vmlinux, ["vmlinux"])
    work_dir = Path(args.work_dir).expanduser().resolve() if args.work_dir else dump_dir / ".crash-ai"
    output_dir = work_dir / "crash_outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    commands = args.command or DEFAULT_COMMANDS
    results = [
        run_one(str(crash_bin), vmlinux, dump, command, output_dir, args.timeout)
        for command in commands
    ]

    summary = {
        "dump_dir": str(dump_dir),
        "dump": str(dump),
        "vmlinux": str(vmlinux),
        "work_dir": str(work_dir),
        "crash_bin": str(crash_bin),
        "results": results,
    }
    summary_file = work_dir / "crash_session_summary.json"
    summary_file.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if all(r.get("returncode") == 0 and not r.get("timeout") for r in results) else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Linux crash commands and store local outputs.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    collect_parser = sub.add_parser("collect", help="run one or more crash commands")
    collect_parser.add_argument("--dump-dir", required=True, help="directory containing dump/vmcore and vmlinux")
    collect_parser.add_argument("--dump", help="explicit dump/vmcore path")
    collect_parser.add_argument("--vmlinux", help="explicit vmlinux path")
    collect_parser.add_argument("--work-dir", help="output directory, default: <dump-dir>/.crash-ai")
    collect_parser.add_argument("--crash-bin", default="crash", help="crash executable, default: crash")
    collect_parser.add_argument("--timeout", type=int, default=180, help="timeout per command in seconds")
    collect_parser.add_argument("--command", action="append", help="crash command to run; repeatable")
    collect_parser.set_defaults(func=collect)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
