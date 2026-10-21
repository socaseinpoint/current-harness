"""tide.sessions — small session-life helpers shared by the hooks.

:func:`is_side_sid` tells a service side chat of the SDK host from the session
itself; :func:`is_closed_passport` tells a sealed (closed) arc passport.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional


def is_side_sid(sid: str, env: Optional[Dict[str, str]] = None) -> bool:
    """True when *sid* is a service side chat of the SDK host («Summarize this agent
    result…»), never the session itself — the one filter is
    :func:`tide.context_fill.is_side_transcript`."""
    from . import context_fill  # lazy: the hooks import sessions on every prompt

    e = os.environ if env is None else env
    base = Path(e.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude")) / "projects"
    return context_fill.is_side_sid(sid, root=base)


def is_closed_passport(pp: Optional[Path]) -> bool:
    """True when passport *pp* belongs to a CLOSED arc — never re-bound to a new chat.

    Closed is tide's seal (:func:`tide.arc.stream.close`): the session dir or its
    thread dir wrapped in ``__…__``, and ``status: done`` in the passport. A sealed arc is
    history, its ``claude-session:``/``title:`` stay as they were.
    """
    if pp is None:
        return False
    from . import fields, slug  # lazy: keep sessions light for the hooks

    p = Path(pp)
    entry = p.parent if p.name.endswith(".md") else p
    if any(slug.is_closed_entry(seg) for seg in entry.parts):
        return True
    pf = p if p.name.endswith(".md") else p / "arc.md"
    return (fields.read_field(pf, "status") or "").strip().lower() in ("done", "closed")
