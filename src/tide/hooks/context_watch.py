"""tide.hooks.context_watch — Stop hook ``tide hook context-watch``: context watchman.

One rule: when the session's context is full, tell the agent once to run
``tide offload`` (write down where it stands, what was decided, what is next) so
nothing is lost when the context is cleared or compacted. No handoff ladder, no
launching of sessions.

* The fill is counted ONLY through :mod:`tide.context_fill`.
* Threshold: ``$TIDE_CTX_LIMIT`` tokens (default :data:`DEFAULT_LIMIT`).
* One nudge per session: the passed level is stamped in the session passport
  (``ctx-ping: <k tokens> <time> <tokens>``) and not repeated.
* Silent: outside a tide project, with no session arc, on the continuation after a
  block (``stop_hook_active``), below the threshold. Any error is a silent exit 0.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from .. import fields, offload, paths, slug

LIMIT_ENV = "TIDE_CTX_LIMIT"
DEFAULT_LIMIT = 200_000
CTX_PING_FIELD = "ctx-ping"


def limit() -> int:
    """The context threshold in tokens; env overrides, garbage falls back to the default."""
    raw = (os.environ.get(LIMIT_ENV) or "").strip().replace("_", "").replace(" ", "")
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_LIMIT
    return value if value > 0 else DEFAULT_LIMIT


def _k(tokens: int) -> int:
    return int(round(tokens / 1000.0))


def _ref(entry: Path) -> str:
    return "{0}/{1}".format(slug.entry_slug(entry.parent.parent.name),
                            slug.entry_slug(entry.name))


def offload_text(entry: Path, tokens: int) -> str:
    """The block reason: the context is full, run offload now."""
    return (
        "tide: the context is full ({0}k tokens). Run tide offload now, it takes 10 seconds:\n"
        "  tide offload {1} --cursor \"<what you are doing now>\" --next \"<steps separated by · >\" "
        "\"<what you decided / did>\"\n"
        "One line for each, no reports. Then end the turn."
    ).format(_k(tokens), _ref(entry))


def fill_tokens(payload: dict, session: str) -> Optional[int]:
    from .. import context_fill

    target = payload.get("transcript_path") or session
    if not target:
        return None
    res = context_fill.context_fill(target)
    return int(res["tokens"]) if res else None


def _session_entry(root: Path, session: str) -> Optional[Path]:
    if not session:
        return None
    return offload.find_session_by_claude_id(Path(root), session)


def _already_pinged(passport: Path, threshold: int) -> bool:
    raw = (fields.read_field(passport, CTX_PING_FIELD) or "").strip().split(" ", 1)[0]
    try:
        return int(raw) >= _k(threshold)
    except ValueError:
        return False


def watch(root: Path, payload: dict, *, now: Optional[datetime] = None) -> Optional[str]:
    """The Stop-block reason when the context is full and not yet nudged, else None."""
    session = str(payload.get("session_id") or payload.get("session") or "")
    entry = _session_entry(root, session)
    if entry is None or payload.get("stop_hook_active"):
        return None
    tokens = fill_tokens(payload, session)
    threshold = limit()
    if tokens is None or tokens < threshold:
        return None
    passport = entry / "arc.md"
    if _already_pinged(passport, threshold):
        return None
    fields.set_field(passport, CTX_PING_FIELD, "{0} {1} {2}".format(
        _k(threshold), (now or datetime.now()).isoformat(timespec="seconds"), tokens))
    return offload_text(entry, tokens)


def cmd_context_watch(args) -> int:
    """``tide hook context-watch`` — Stop: the context-fill watchman."""
    try:
        root = paths.find_tide_root()
        if root is None:
            return 0
        try:
            payload = json.loads(sys.stdin.read() or "{}")
        except (ValueError, OSError):
            return 0
        if not isinstance(payload, dict):
            return 0
        reason = watch(root, payload)
        if reason:
            print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
    except Exception as exc:  # noqa: BLE001 — a hook must never raise
        print("tide: [context-watch] skipped: {0}".format(exc), file=sys.stderr)
    return 0
