"""Native scheduler descriptions for offline local execution."""

from __future__ import annotations

import os
from pathlib import Path
from xml.sax.saxutils import escape

from .models import ScheduleReceipt, ScheduleRequest, ScheduleSpec


def build_native_schedule(request: ScheduleRequest) -> ScheduleSpec:
    """Build a launchd or Task Scheduler definition without network actions."""

    if request.frequency == "weekly" and request.weekday is None:
        raise ValueError("weekday is required for weekly schedules")
    if request.platform == "macos":
        command = (
            "/usr/bin/python3",
            "-m",
            "escala_server.lifecycle",
            "run-scheduled",
            "--data-root",
            "data_root",
        )
        kind = "launchd"
    else:
        command = (
            "python.exe",
            "-m",
            "escala_server.lifecycle",
            "run-scheduled",
            "--data-root",
            "data_root",
        )
        kind = "task_scheduler"
    return ScheduleSpec(
        platform=request.platform,
        kind=kind,
        frequency=request.frequency,
        local_time=request.local_time,
        weekday=request.weekday,
        command=command,
    )


def render_native_schedule(schedule: ScheduleSpec) -> str:
    """Render a platform-native schedule with redacted local paths."""

    if schedule.kind == "launchd":
        hour, minute = schedule.local_time.split(":")
        interval = (
            f"      <key>Weekday</key>\n      <integer>{schedule.weekday + 1}</integer>\n"
            if schedule.frequency == "weekly" and schedule.weekday is not None
            else ""
        )
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
            '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
            '<plist version="1.0"><dict>\n'
            "  <key>Label</key><string>com.escala.local.review</string>\n"
            "  <key>Comment</key><string>Escala Local offline review</string>\n"
            "  <key>ProgramArguments</key><array>\n"
            + "".join(
                f"    <string>{escape(value)}</string>\n" for value in schedule.command
            )
            + "  </array>\n"
            "  <key>StartCalendarInterval</key><dict>\n"
            f"    <key>Hour</key><integer>{int(hour)}</integer>\n"
            f"    <key>Minute</key><integer>{int(minute)}</integer>\n"
            + interval
            + "  </dict>\n</dict></plist>\n"
        )
    day = schedule.weekday if schedule.frequency == "weekly" else "*"
    day_value = "*" if day == "*" else str(day)
    return (
        '<?xml version="1.0" encoding="UTF-16"?>\n'
        '<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">\n'
        "  <RegistrationInfo><Description>Escala Local offline review</Description></RegistrationInfo>\n"
        "  <Triggers><CalendarTrigger><ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay>"
        f"<StartBoundary>2026-01-01T{schedule.local_time}:00</StartBoundary></CalendarTrigger></Triggers>\n"
        f'  <Actions Context="Author"><Exec><Command>{escape(schedule.command[0])}</Command>'
        f"<Arguments>{escape(' '.join(schedule.command[1:]))}</Arguments></Exec></Actions>\n"
        f"  <Settings><MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy><DayOfWeek>{day_value}</DayOfWeek>"
        "<RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable></Settings>\n"
        "</Task>\n"
    )


def write_native_schedule(schedule: ScheduleSpec, destination: Path) -> ScheduleReceipt:
    """Write a schedule file below the installer machine's data root."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    content = render_native_schedule(schedule)
    temporary = destination.with_name(f".{destination.name}.tmp")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, destination)
    return ScheduleReceipt(
        status="pass",
        platform=schedule.platform,
        kind=schedule.kind,
        frequency=schedule.frequency,
        relative_path=f".escala-schedules/{destination.name}",
    )
