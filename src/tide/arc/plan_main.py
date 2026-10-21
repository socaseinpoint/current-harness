"""tide.arc.plan_main — "## read first" in a thread's ``plan.md`` (decision No. 24).

The section a thread must state before its first piece of work: at least three
lines — the task (as a link), whom to deliver to and over which channel, whom not
to duplicate. This is what gets lost first on a handoff and what a new session
cannot infer on its own.

Readers:

* :func:`tide.arc.templates.thread_plan_md` — the scaffold with three hints
  (:data:`HINTS`) at thread birth;
* :func:`gate` — an advisory start gate: a warning only, never blocks the pulse;

Pure disk reads, no writes.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, NamedTuple, Optional

PLAN_FILE = "plan.md"
HEADING = "## read first"
PREFIX = "## read first"        # the heading is matched by prefix — the tail is up to the author
MIN_LINES = 3

# Scaffold hints: in angle brackets, like all tide placeholders — never counted
# as a live line.
HINTS = (
    "<the thread's task — as a link>",
    "<whom and over which channel to deliver the result (session, owner)>",
    "<whom not to duplicate — neighbouring threads and sessions>",
)

# Marker in the thread passport: the thread was born with the "read first" scaffold
# and must fill it at the start gate. No marker — an old thread: warning only.
REQUIRED_FIELD = "plan-main"
REQUIRED_VALUE = "required"

_STEP = re.compile(r"(?m)^\s*-\s*\[[ x>]\]")
_PULSE = re.compile(r"^\s*-\s*\d{4}-\d{2}-\d{2}T\d{2}:\d{2}")
_MECHANICAL = "intake seam closed mechanically"


def _is_live(line: str) -> bool:
    s = line.strip().lstrip("-*").strip()
    if not s or s.startswith("<") or s.startswith("<!--"):
        return False
    return s not in ("—", "-", "–") and not s.startswith("— ")


def section(text: str) -> Optional[List[str]]:
    """Lines of the "read first" section in the plan text; None — no section at all."""
    out: List[str] = []
    inside = found = False
    for ln in (text or "").splitlines():
        if ln.startswith("## "):
            if inside:
                break
            inside = ln.startswith(PREFIX)
            found = found or inside
            continue
        if inside:
            out.append(ln.rstrip())
    return out if found else None


def live_lines(thread_dir: Path) -> List[str]:
    """Live "read first" lines of the thread (no hints or dashes); [] — none."""
    body = read(thread_dir)
    return [ln.strip() for ln in (body or []) if _is_live(ln)]


def read(thread_dir: Path) -> Optional[List[str]]:
    """Raw section lines from ``<thread>/plan.md``; None — no plan or no section."""
    plan = Path(thread_dir) / PLAN_FILE
    try:
        text = plan.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    return section(text)


def is_scaffold(thread_dir: Path) -> bool:
    """plan.md is an untouched scaffold: no steps, no ``final:``, no live "read first".
    Such a thread can be dropped as empty (``drop-thread``)."""
    plan = Path(thread_dir) / PLAN_FILE
    try:
        text = plan.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    if _STEP.search(text) or re.search(r"(?m)^final:", text):
        return False
    body = section(text)
    return body is not None and not [ln for ln in body if _is_live(ln)]


def required(thread_dir: Path) -> bool:
    """The thread was born under decision No. 24 (marker :data:`REQUIRED_FIELD` in the passport)."""
    try:
        from .. import fields
        from . import stream
        raw = fields.read_field(stream.passport_path(Path(thread_dir)), REQUIRED_FIELD)
    except Exception:  # noqa: BLE001
        return False
    return (raw or "").strip() == REQUIRED_VALUE


class Verdict(NamedTuple):
    block: bool      # True — the pulse does not go through (start gate of a new thread)
    reason: str      # a readable reason / warning


def problem(thread_dir: Path) -> Optional[str]:
    """What is wrong with the thread's "read first" — or None if it holds three live lines."""
    plan = Path(thread_dir) / PLAN_FILE
    body = read(thread_dir)
    if body is None:
        where = "no plan.md" if not plan.is_file() else "plan.md has no section"
        return ("{0} \"{1}\" ({2}) — write at least {3} lines: task · whom and over "
                "which channel to deliver · whom not to duplicate").format(
                    where, HEADING, plan, MIN_LINES)
    live = [ln for ln in body if _is_live(ln)]
    if len(live) >= MIN_LINES:
        return None
    hints = sum(1 for ln in body if ln.strip().lstrip("-* ").startswith("<"))
    state = "is empty" if not live and not hints else (
        "holds only hints" if not live else
        "holds {0} of {1} live lines".format(len(live), MIN_LINES))
    return ("section \"{0}\" in {1} {2} — write at least {3} lines instead of the hints: "
            "task · whom and over which channel to deliver · whom not to duplicate").format(
                HEADING, plan, state, MIN_LINES)


def _real_pulses(passport: Path) -> int:
    try:
        text = passport.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return 0
    n, inside = 0, False
    for ln in text.splitlines():
        if ln.startswith("## "):
            inside = ln.strip() == "## context"
            continue
        if inside and _PULSE.match(ln) and _MECHANICAL not in ln:
            n += 1
    return n


def thread_pulsed(thread_dir: Path) -> bool:
    """Whether the thread has had at least one real pulse (in any of its sessions)."""
    arcs = Path(thread_dir) / "arcs"
    if not arcs.is_dir():
        return False
    return any(_real_pulses(p / "arc.md") for p in arcs.iterdir()
               if p.is_dir() and (p / "arc.md").is_file())


def gate(session_dir: Path) -> Optional[Verdict]:
    """Start-gate of the "read first" section for a session's pulse — ADVISORY only.

    Never blocks: an empty section or one that still holds the scaffold hints in a
    fresh ``plan.md`` is reported as a warning (and only on the session's first
    pulse), the pulse itself always goes through. Returns None when all is filled
    or *session_dir* is not a thread session.
    """
    session_dir = Path(session_dir)
    thread = session_dir.parent.parent
    try:
        from . import stream
        if not stream.is_thread(thread):
            return None
    except Exception:  # noqa: BLE001 — the gate must never break a pulse
        return None
    why = problem(thread)
    if why is None or _real_pulses(session_dir / "arc.md"):
        return None
    return Verdict(False, "tide: ⚠ {0} (decision No. 24; the pulse is recorded).".format(why))


__all__ = ["HEADING", "HINTS", "MIN_LINES", "PLAN_FILE", "PREFIX", "REQUIRED_FIELD",
           "REQUIRED_VALUE", "Verdict", "gate", "is_scaffold", "live_lines", "problem",
           "read", "required", "section", "thread_pulsed"]
