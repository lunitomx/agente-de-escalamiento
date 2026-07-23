"""CLI for health and native scheduling on an installed machine."""

from __future__ import annotations

import argparse
from pathlib import Path

from .models import InstallRequest, ScheduleRequest
from .runtime import LifecycleRuntime
from .scheduler import build_native_schedule, render_native_schedule


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ESCALA Local lifecycle")
    sub = parser.add_subparsers(dest="command", required=True)
    status = sub.add_parser("status")
    _add_request_arguments(status)
    start = sub.add_parser("start")
    _add_request_arguments(start)
    stop = sub.add_parser("stop")
    _add_request_arguments(stop)
    schedule = sub.add_parser("schedule")
    schedule.add_argument("--platform", choices=("macos", "windows"), required=True)
    schedule.add_argument("--install-root", type=Path, required=True)
    schedule.add_argument("--data-root", type=Path, required=True)
    schedule.add_argument("--frequency", choices=("daily", "weekly"), default="daily")
    schedule.add_argument("--time", dest="local_time", default="08:30")
    args = parser.parse_args(argv)
    if args.command == "schedule":
        request = ScheduleRequest(
            platform=args.platform,
            install_root=args.install_root,
            data_root=args.data_root,
            frequency=args.frequency,
            local_time=args.local_time,
        )
        print(render_native_schedule(build_native_schedule(request)), end="")
        return 0
    request = InstallRequest(
        platform=args.platform,
        version=args.version,
        install_root=args.install_root,
        data_root=args.data_root,
        database_path=args.database_path,
        exchange_root=args.exchange_root,
    )
    runtime = LifecycleRuntime(request)
    result = (
        runtime.start()
        if args.command == "start"
        else runtime.stop()
        if args.command == "stop"
        else runtime.status()
    )
    print(result.model_dump_json())
    return 0


def _add_request_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--platform", choices=("macos", "windows"), required=True)
    parser.add_argument("--version", default="0.0.0")
    parser.add_argument("--install-root", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--database-path", type=Path, required=True)
    parser.add_argument("--exchange-root", type=Path)
