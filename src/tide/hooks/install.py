"""tide.hooks.install — ``tide install-hooks``: wire the Claude Code hooks.

The merge-safe wiring itself lives DOWN in :mod:`tide.harness` (domain).
This module is the thin adapter above it: the ``tide install-hooks`` CLI verb and
the internal ``tide hook …`` dispatch group that settings.json entries call back
into. The wiring names are re-exported so existing imports keep working.
"""

from __future__ import annotations

# Re-exports: the wiring machinery lives in tide.harness (domain).
from ..harness import (  # noqa: F401 — public re-exports
    ASK_GATE_CMD,
    ASK_GATE_MATCHER,
    CLAUDE_DIRNAME,
    CONTEXT_WATCH_CMD,
    EDIT_GATE_CMD,
    EDIT_MATCHER,
    HOOKS_KEY,
    InstallError,
    PRE_TOOL_USE_EVENT,
    SESSION_END_CMD,
    SESSION_END_EVENT,
    SESSION_START_CMD,
    SESSION_START_EVENT,
    SETTINGS_FILE,
    STOP_EVENT,
    _command_present,
    _hook_block,
    TIDE_HOOKS,
    _load,
    install_hooks,
    merge_ask_gate,
    merge_hooks,
    merge_pre_tool_use,
    merge_session_end,
    merge_session_start,
    merge_stop_context_watch,
    missing_hooks,
    missing_hooks_at,
    settings_path,
)
from . import edit_gate, session_start


# --- CLI wiring ------------------------------------------------------------

def _cmd_install_hooks(args) -> int:
    from .. import paths

    root = paths.require_tide_root()
    path, notes = install_hooks(root)
    print("tide: hooks wired in {0}".format(path))
    if notes:
        for note in notes:
            print("  + {0}".format(note))
    else:
        print("  (already wired — nothing to change)")
    return 0


def register(subparsers) -> None:
    """Add the top-level ``install-hooks`` command (called by cli.py)."""
    p = subparsers.add_parser(
        "install-hooks",
        help="wire the Claude Code hooks into .claude/settings.json (merge-safe)",
    )
    p.set_defaults(func=_cmd_install_hooks, _cmd="install-hooks")


def register_hook_group(subparsers) -> None:
    """Add the internal ``hook`` dispatch group (the commands settings.json calls)."""
    p = subparsers.add_parser(
        "hook", help="internal: dispatched Claude Code hooks"
    )
    hsub = p.add_subparsers(dest="hook_cmd", metavar="<hook>")

    ss = hsub.add_parser("session-start", help="SessionStart: board + role + warnings")
    ss.set_defaults(func=session_start.cmd_session_start, _cmd="hook session-start")

    eg = hsub.add_parser("edit-gate", help="PreToolUse: block edits with no open arc")
    eg.set_defaults(func=edit_gate.cmd_edit_gate, _cmd="hook edit-gate")

    ag = hsub.add_parser(
        "ask-gate",
        help="PreToolUse: with no human in the window, AskUserQuestion is "
             "turned into a written question instead of a dialog",
    )
    from .ask_gate import cmd_ask_gate  # lazy: keep hook wiring import-light
    ag.set_defaults(func=cmd_ask_gate, _cmd="hook ask-gate")

    cw = hsub.add_parser(
        "context-watch",
        help="Stop: context is full — block once with `tide offload`",
    )
    from .context_watch import cmd_context_watch  # lazy: keep hook wiring import-light
    cw.set_defaults(func=cmd_context_watch, _cmd="hook context-watch")

    se = hsub.add_parser(
        "session-end",
        help="SessionEnd: stamp ended: on this sid's session passport (closing bookend)",
    )
    from . import session_end  # lazy: keep hook wiring import-light
    se.set_defaults(func=session_end.cmd_session_end, _cmd="hook session-end")
