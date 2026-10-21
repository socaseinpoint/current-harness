"""tide.harness — the hook floor every tide project must carry (merge-safe wiring).

The session-life mechanics (start banner, edit gate, ask gate, context watch,
``ended:`` bookend) all ride Claude Code hooks in the PROJECT's
``.claude/settings.json``. The wiring is called by ``tide install-hooks``.

The single load-bearing rule is **MERGE-not-clobber**: a real ``.claude/
settings.json`` already carries the human's own hooks (e.g. rtk), permissions,
env. We parse the whole document, append our entries to the relevant hook
**event lists** (never replacing them), and re-serialise — so every pre-existing
key and hook survives. Re-running is idempotent: an entry already pointing at our
command is detected and not duplicated.

Pure helpers operate on a settings ``dict``; :func:`install_hooks` does the I/O.
The CLI wiring (``tide install-hooks``, the ``tide hook …`` dispatch group) stays
in :mod:`tide.hooks.install` — the thin adapter above this module.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Tuple

from . import io as _io
from .arc.stream import StreamError

# settings.json location + the exact commands/matcher we install.
CLAUDE_DIRNAME = ".claude"
SETTINGS_FILE = "settings.json"
HOOKS_KEY = "hooks"

SESSION_START_EVENT = "SessionStart"
SESSION_END_EVENT = "SessionEnd"
PRE_TOOL_USE_EVENT = "PreToolUse"
STOP_EVENT = "Stop"

SESSION_START_CMD = "tide hook session-start"
EDIT_GATE_CMD = "tide hook edit-gate"
EDIT_MATCHER = "Edit|Write|MultiEdit"
ASK_GATE_CMD = "tide hook ask-gate"
ASK_GATE_MATCHER = "AskUserQuestion"
CONTEXT_WATCH_CMD = "tide hook context-watch"
SESSION_END_CMD = "tide hook session-end"


# The canonical set — every (event, command) :func:`merge_hooks` wires. The one
# list doctor checks a settings.json against.
TIDE_HOOKS: Tuple[Tuple[str, str], ...] = (
    (SESSION_START_EVENT, SESSION_START_CMD),
    (PRE_TOOL_USE_EVENT, EDIT_GATE_CMD),
    (PRE_TOOL_USE_EVENT, ASK_GATE_CMD),
    (STOP_EVENT, CONTEXT_WATCH_CMD),
    (SESSION_END_EVENT, SESSION_END_CMD),
)


def hook_name(command: str) -> str:
    """``tide hook ask-gate`` → ``ask-gate`` (the short name humans read)."""
    return command.replace("tide hook ", "")


class InstallError(StreamError):
    """A hook-install error (e.g. a settings.json that is not valid JSON).

    Subclasses :class:`tide.arc.stream.StreamError` so ``cli.main`` catches it on
    the same ``except`` arm (prints ``tide: …``, exits nonzero).
    """


def settings_path(root: Path) -> Path:
    """Path to the project ``.claude/settings.json`` for *root*."""
    return Path(root) / CLAUDE_DIRNAME / SETTINGS_FILE


# --- pure merge helpers ----------------------------------------------------

def _load(path: Path) -> dict:
    """Parse an existing settings.json (``{}`` when absent); raise on bad JSON."""
    p = Path(path)
    if not p.is_file():
        return {}
    text = p.read_text(encoding="utf-8")
    if not text.strip():
        return {}
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError) as exc:
        raise InstallError(
            "install-hooks: {0} is not valid JSON ({1}) — fix it before "
            "installing hooks".format(p, exc)
        )
    if not isinstance(data, dict):
        raise InstallError(
            "install-hooks: {0} is not a JSON object".format(p)
        )
    return data


def _command_present(groups: List[dict], command: str) -> bool:
    """True when any hook in *groups* already points at *command* (idempotency)."""
    for group in groups:
        if not isinstance(group, dict):
            continue
        for hook in group.get(HOOKS_KEY, []) or []:
            if isinstance(hook, dict) and hook.get("command") == command:
                return True
    return False


def _hook_block(command: str) -> dict:
    """A single command-hook block ``{"type": "command", "command": …}``."""
    return {"type": "command", "command": command}


def merge_session_start(hooks: dict) -> bool:
    """Append the SessionStart entry to *hooks* (merge-not-clobber); return changed.

    No-op (returns False) when our command is already wired.
    """
    groups = hooks.setdefault(SESSION_START_EVENT, [])
    if _command_present(groups, SESSION_START_CMD):
        return False
    groups.append({HOOKS_KEY: [_hook_block(SESSION_START_CMD)]})
    return True


def merge_pre_tool_use(hooks: dict) -> bool:
    """Append the PreToolUse edit-gate entry to *hooks*; return whether it changed.

    Adds a matcher-scoped group (``Edit|Write|MultiEdit``) alongside any existing
    PreToolUse groups (e.g. the human's own). No-op when already wired.
    """
    groups = hooks.setdefault(PRE_TOOL_USE_EVENT, [])
    if _command_present(groups, EDIT_GATE_CMD):
        return False
    groups.append(
        {"matcher": EDIT_MATCHER, HOOKS_KEY: [_hook_block(EDIT_GATE_CMD)]}
    )
    return True


def merge_ask_gate(hooks: dict) -> bool:
    """Append the PreToolUse ask-gate entry to *hooks*; return whether it changed.

    in an unattended session (no human in the window) ``AskUserQuestion``
    silently wedges the session — the gate turns the question into a written note. Matcher-scoped to ``AskUserQuestion``. No-op when already wired.
    """
    groups = hooks.setdefault(PRE_TOOL_USE_EVENT, [])
    if _command_present(groups, ASK_GATE_CMD):
        return False
    groups.append(
        {"matcher": ASK_GATE_MATCHER, HOOKS_KEY: [_hook_block(ASK_GATE_CMD)]}
    )
    return True


def merge_session_end(hooks: dict) -> bool:
    """Append the SessionEnd entry to *hooks*; return whether it changed.

    The closing bookend: ``ended:`` lands on the session's passport by mechanics,
    so the board tells "conversation finished" from "went quiet". No-op when wired.
    """
    groups = hooks.setdefault(SESSION_END_EVENT, [])
    if _command_present(groups, SESSION_END_CMD):
        return False
    groups.append({HOOKS_KEY: [_hook_block(SESSION_END_CMD)]})
    return True


def merge_stop_context_watch(hooks: dict) -> bool:
    """Append the Stop context-watch entry to *hooks*; return whether it changed.

    The context watchman: when the context is full it blocks the stop once with
    the exact ``tide offload`` command. Nothing goes on SubagentStop. No-op (False)
    when already wired.
    """
    groups = hooks.setdefault(STOP_EVENT, [])
    if _command_present(groups, CONTEXT_WATCH_CMD):
        return False
    groups.append({HOOKS_KEY: [_hook_block(CONTEXT_WATCH_CMD)]})
    return True


def merge_hooks(data: dict) -> List[str]:
    """Merge the five tide hook entries into a settings *data* dict; return notes.

    Mutates *data* in place (creating ``hooks`` if absent) and returns a list of
    human-readable "installed …" notes — empty when everything was already wired.
    """
    hooks = data.setdefault(HOOKS_KEY, {})
    if not isinstance(hooks, dict):
        raise InstallError(
            "install-hooks: existing '{0}' key is not a JSON object".format(HOOKS_KEY)
        )
    notes: List[str] = []
    if merge_session_start(hooks):
        notes.append("{0} → {1}".format(SESSION_START_EVENT, SESSION_START_CMD))
    if merge_pre_tool_use(hooks):
        notes.append(
            "{0} [{1}] → {2}".format(PRE_TOOL_USE_EVENT, EDIT_MATCHER, EDIT_GATE_CMD)
        )
    if merge_ask_gate(hooks):
        notes.append(
            "{0} [{1}] → {2}".format(PRE_TOOL_USE_EVENT, ASK_GATE_MATCHER, ASK_GATE_CMD)
        )
    if merge_stop_context_watch(hooks):
        notes.append("{0} → {1}".format(STOP_EVENT, CONTEXT_WATCH_CMD))
    if merge_session_end(hooks):
        notes.append("{0} → {1}".format(SESSION_END_EVENT, SESSION_END_CMD))
    return notes


def missing_hooks(data: dict) -> List[str]:
    """Short names of the :data:`TIDE_HOOKS` absent from a settings *data* dict
    (each looked up under its own event), in canonical order."""
    hooks = data.get(HOOKS_KEY) if isinstance(data, dict) else None
    hooks = hooks if isinstance(hooks, dict) else {}
    out: List[str] = []
    for event, command in TIDE_HOOKS:
        groups = hooks.get(event)
        if not (isinstance(groups, list) and _command_present(groups, command)):
            out.append(hook_name(command))
    return out


def missing_hooks_at(path: Path) -> List[str]:
    """:func:`missing_hooks` of the settings.json at *path* (follows a ``.claude``
    link); an unreadable / non-JSON file misses them all."""
    try:
        data = _load(path)
    except (InstallError, OSError):
        data = {}
    return missing_hooks(data)


# --- I/O -------------------------------------------------------------------

def install_hooks(root: Path) -> Tuple[Path, List[str]]:
    """Write the hook entries into ``<root>/.claude/settings.json`` (merge-safe).

    Returns ``(settings_path, notes)``; *notes* is empty on a re-run (idempotent).
    The whole document is preserved — only our entries are appended.
    """
    path = settings_path(root)
    data = _load(path)
    notes = merge_hooks(data)
    if notes:
        _io.atomic_write(path, json.dumps(data, indent=2) + "\n")
    return path, notes
