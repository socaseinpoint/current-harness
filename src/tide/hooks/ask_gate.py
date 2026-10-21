"""tide.hooks.ask_gate — PreToolUse ``tide hook ask-gate``: a question is not a dialog.

Problem: in an UNATTENDED session (a headless / background run with nobody in the
window) ``AskUserQuestion`` silently hangs the session — the dialog waits for a
human who is not there.

Gate: in a session marked unattended (``$TIDE_UNATTENDED`` set to a truthy value)
where there was no live human message in the last :data:`HUMAN_WINDOW_MIN` minutes,
``AskUserQuestion`` is denied with a reason telling the agent to write the question
down and carry on with the recommended option. The question itself is appended as a
line to ``<project>/.tide/state/blocked-asks.jsonl``.

A live human message is a transcript record ``type: user`` with ``origin.kind:
human`` and real text (not a tool_result, not a system-reminder / task-notification),
and NOT the first such record of the file (that is the session's launch prompt).

Silent (pass, exit 0, prints nothing): another tool, ``TIDE_ASK_GATE=off``, the
session is not marked unattended (a person sits in their own terminal), a live
human message inside the window. Any error is a pass (fail-open): the gate never
breaks a session.

A denial is a PreToolUse ``hookSpecificOutput`` JSON with ``permissionDecision:
deny`` on stdout and exit 0, so the reason reaches the model whole.
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, List, Optional

from .. import paths

# The "human in the window" window: a live human message no older than this many
# minutes lets the dialog through.
HUMAN_WINDOW_MIN = 10

TOOL_NAME = "AskUserQuestion"
OFF_ENV = "TIDE_ASK_GATE"
UNATTENDED_ENV = "TIDE_UNATTENDED"

BLOCKED_ASKS_FILE = "blocked-asks.jsonl"
NOT_RECORDED = "not recorded"

# How much of the transcript tail we read: a live session's file grows to tens of MB.
TAIL_BYTES = 4 * 1024 * 1024

# Text beginnings that do NOT count as a human: task notifications, system
# inserts, messages from neighbouring sessions.
NOT_HUMAN_PREFIXES = (
    "<task-notification",
    "<system-reminder",
    "Another Claude session sent a message",
)

DENY_TEMPLATE = (
    "This is not a failure: no dialog here. This session is unattended (no live human "
    "message in the last {window} min), so a dialog would hang it silently. Write the "
    "question down (tide offload <session> --cursor \"question: ...\") and carry on "
    "with the option you recommend; the answer will arrive later and you adjust. "
    "Wait only for what is irreversible or goes outside. The question was recorded: "
    "{recorded}."
)


# --- transcript: was there a live human message------------------------------

def _text_of(content) -> Optional[str]:
    """Message text: a string or the text blocks of a list; tool_result → None."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_result":
                return None
            if block.get("type") == "text" and isinstance(block.get("text"), str):
                parts.append(block["text"])
        return "\n".join(parts) if parts else None
    return None


def _is_human_record(rec) -> bool:
    """``type: user`` with ``origin.kind: human`` (text not checked)."""
    if not isinstance(rec, dict) or rec.get("type") != "user":
        return False
    origin = rec.get("origin")
    return isinstance(origin, dict) and origin.get("kind") == "human"


def _human_text(rec) -> Optional[str]:
    """Text of a live human message — or None if the record is not one."""
    if not _is_human_record(rec):
        return None
    message = rec.get("message")
    if not isinstance(message, dict):
        return None
    text = _text_of(message.get("content"))
    if text is None:
        return None
    if text.lstrip().startswith(NOT_HUMAN_PREFIXES):
        return None
    return text


def _parse_ts(raw) -> Optional[datetime]:
    """``2026-10-09T08:07:05.253Z`` → aware UTC datetime."""
    if not isinstance(raw, str) or not raw:
        return None
    try:
        ts = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)


def _records(lines: Iterable[bytes]):
    for line in lines:
        try:
            yield json.loads(line)
        except (ValueError, UnicodeDecodeError):
            continue


def _first_human_uuid(path: Path) -> Optional[str]:
    """``uuid`` of the first human record from the start of the file (launch prompt)."""
    with open(path, "rb") as fh:
        for rec in _records(fh):
            if _is_human_record(rec):
                return str(rec.get("uuid") or rec.get("timestamp") or "")
    return None


def _tail_lines(path: Path, size: Optional[int] = None) -> List[bytes]:
    """The last ~*size* bytes of the file as lines (the first, truncated one, dropped)."""
    size = TAIL_BYTES if size is None else size
    with open(path, "rb") as fh:
        fh.seek(0, os.SEEK_END)
        end = fh.tell()
        start = max(0, end - size)
        fh.seek(start)
        data = fh.read()
    lines = data.split(b"\n")
    if start > 0 and lines:
        lines = lines[1:]
    return [ln for ln in lines if ln.strip()]


def has_live_human(transcript: Path, *, now: Optional[datetime] = None,
                   window_min: int = HUMAN_WINDOW_MIN) -> bool:
    """Whether the transcript has a live human message in the last *window_min* minutes."""
    path = Path(transcript)
    if not path.is_file():
        return False
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=window_min)
    first = _first_human_uuid(path)
    for rec in _records(_tail_lines(path)):
        if _human_text(rec) is None:
            continue
        key = str(rec.get("uuid") or rec.get("timestamp") or "")
        if first is not None and key == first:
            continue  # launch prompt — not a human in the window
        ts = _parse_ts(rec.get("timestamp"))
        if ts is not None and ts >= cutoff:
            return True
    return False


# --- recording the question for the question catcher-----------------------------------------

def _questions(tool_input) -> list:
    """``[{question, header, options: [label…]}]`` from tool_input.questions."""
    out = []
    raw = tool_input.get("questions") if isinstance(tool_input, dict) else None
    if not isinstance(raw, list):
        return out
    for q in raw:
        if not isinstance(q, dict):
            continue
        options = []
        for opt in q.get("options") or []:
            if isinstance(opt, dict):
                options.append(str(opt.get("label") or ""))
            elif isinstance(opt, str):
                options.append(opt)
        out.append({"question": str(q.get("question") or ""),
                    "header": str(q.get("header") or ""),
                    "options": options})
    return out


def record_blocked_ask(payload: dict, *, now: Optional[datetime] = None) -> Optional[Path]:
    """Append the question as a line to ``<project>/.tide/state/blocked-asks.jsonl``.

    The root is :func:`tide.paths.find_tide_root` from the input ``cwd``. No root → None (not recorded).
    """
    cwd = str(payload.get("cwd") or "") or os.getcwd()
    root = paths.find_tide_root(Path(cwd))
    if root is None:
        return None
    stamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    row = {
        "id": str(uuid.uuid4()),
        "ts": stamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "project": Path(root).name,
        "claude_session": str(payload.get("session_id") or ""),
        "cwd": cwd,
        "questions": _questions(payload.get("tool_input")),
        "answered": None,
    }
    target = paths.state_dir(Path(root)) / BLOCKED_ASKS_FILE
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return target


# --- decision -----------------------------------------------------------------

def deny_reason(payload: dict, *, now: Optional[datetime] = None) -> Optional[str]:
    """The denial text — or None (pass). Writes blocked-asks on denial."""
    if payload.get("tool_name") != TOOL_NAME:
        return None
    if (os.environ.get(OFF_ENV) or "").strip().lower() == "off":
        return None
    if (os.environ.get(UNATTENDED_ENV) or "").strip().lower() in ("", "0", "off", "false", "no"):
        return None  # a person sits in their own terminal
    transcript = payload.get("transcript_path")
    if transcript and has_live_human(Path(str(transcript)), now=now):
        return None
    try:
        recorded = record_blocked_ask(payload, now=now)
    except Exception:  # noqa: BLE001 — recording must not get in the way of the denial
        recorded = None
    return DENY_TEMPLATE.format(
        window=HUMAN_WINDOW_MIN,
        recorded=str(recorded) if recorded else NOT_RECORDED,
    )


def deny_output(reason: str) -> dict:
    """The PreToolUse denial JSON."""
    return {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}


def cmd_ask_gate(args) -> int:
    """``tide hook ask-gate`` — PreToolUse on AskUserQuestion; always exit 0."""
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        if not isinstance(payload, dict):
            return 0
        reason = deny_reason(payload)
        if reason:
            print(json.dumps(deny_output(reason), ensure_ascii=False))
    except Exception:  # noqa: BLE001 — fail-open: the gate never breaks a session
        pass
    return 0
