"""tide.offload — offload a session as you go (``tide offload``).

``tide offload <session> [--cursor …] <note…>`` — ONE fast command: a
timestamped line is appended to the passport's ``## context``, ``--cursor``
replaces the body of ``## cursor``, the ``offloaded-at`` field is stamped.
Seconds, zero LLM.

The session is found by slug (nested resolve across all threads) or by the
``claude-session`` pin in the passport (the context-watch hook path).
"""

from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .io import atomic_write
from . import fields, paths, resolve, slug
from .arc.stream import StreamError

CONTEXT_SECTION = "## context"
CURSOR_SECTION = "## cursor — resume here"
NEXT_SECTION = "## next"
SUMMARY_SECTION = "## summary"
OFFLOADED_FIELD = "offloaded-at"
ETA_FIELD = "eta"
DELIVERABLE_FIELD = "deliverable"
DELIVERABLE_MAX = 60
_CLEAR_WORDS = ("-", "none")
CLAUDE_SESSION_FIELD = "claude-session"


class OffloadError(StreamError):
    """A user-facing offload error (no such session, nothing to write)."""


def _now_iso(now: Optional[datetime] = None) -> str:
    return (now or datetime.now()).isoformat(timespec="seconds")


# --- session resolution ------------------------------------------------------

def _session_dirs(root: Path) -> List[Path]:
    """Every OPEN nested session/run dir — delegated to :mod:`tide.resolve`."""
    return resolve.open_session_dirs(root)


def find_session(root: Path, ref: str) -> Optional[Path]:
    """Resolve the open nested session *ref* names, or None if absent.

    THE resolver lives in :mod:`tide.resolve` (one matcher for every surface);
    this thin alias only translates :class:`resolve.AmbiguousRefError` into the
    user-facing :class:`OffloadError`.
    """
    try:
        return resolve.find_session(root, ref)
    except resolve.AmbiguousRefError as exc:
        raise OffloadError("offload: {0}".format(exc)) from exc


def find_session_by_claude_id(root: Path, session_id: str) -> Optional[Path]:
    """The session whose passport pins ``claude-session: <session_id>``.

    Open sessions first; CLOSED ones are the fallback: the arc
    was closed but its chat keeps working — the pulse and the SessionEnd stamp
    still have somewhere to land, so the board does not go blind. A pulse into
    a closed arc is legal: it is that arc's own chat.
    """
    if not session_id:
        return None
    for entry in _session_dirs(root):
        pin = (fields.read_field(entry / "arc.md", CLAUDE_SESSION_FIELD) or "").strip()
        if pin == session_id:
            return entry
    for entry in resolve.closed_session_dirs(root):
        pin = (fields.read_field(entry / "arc.md", CLAUDE_SESSION_FIELD) or "").strip()
        if pin == session_id:
            return entry
    return None


# --- eta / deliverable --------------------------------------------------------

def parse_eta(raw: str, now: Optional[datetime] = None) -> str:
    """Normalize an ``--eta`` value to ISO with the local offset; ``""`` = clear.

    Accepts ``HH:MM`` (today, local — an already-past time stays today: it is
    then overdue, never rolled to tomorrow), ``DD.MM HH:MM`` (this year) or a
    full ISO stamp (naive → local offset). ``-``/``none`` clears the field.
    """
    value = " ".join((raw or "").split())
    if value.lower() in _CLEAR_WORDS:
        return ""
    base = (now or datetime.now()).astimezone()
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", value)
    m2 = re.fullmatch(r"(\d{1,2})\.(\d{1,2})\.? (\d{1,2}):(\d{2})", value)
    try:
        if m:
            dt = base.replace(hour=int(m.group(1)), minute=int(m.group(2)),
                              second=0, microsecond=0)
        elif m2:
            dt = datetime(base.year, int(m2.group(2)), int(m2.group(1)),
                          int(m2.group(3)), int(m2.group(4))).astimezone()
        else:
            dt = datetime.fromisoformat(value)
            dt = dt.astimezone() if dt.tzinfo is None else dt
    except ValueError:
        raise OffloadError(
            "offload: --eta {0!r} not understood — use HH:MM, 'DD.MM HH:MM', "
            "ISO, or '-' to clear".format(raw)
        ) from None
    return dt.isoformat(timespec="seconds")


def clean_deliverable(raw: str) -> str:
    """One line, ≤ ~60 chars (cut with «…»); ``-``/``none`` → ``""`` = clear."""
    value = " ".join((raw or "").split())
    if value.lower() in _CLEAR_WORDS:
        return ""
    if len(value) > DELIVERABLE_MAX:
        value = value[:DELIVERABLE_MAX - 1].rstrip() + "…"
    return value


# --- the offload write -------------------------------------------------------

def offload(root: Path, ref: str, *, note: str = "", cursor: str = "",
            next_steps: str = "", summary: str = "",
            eta: Optional[str] = None, deliverable: Optional[str] = None) -> Path:
    """Append *note* to ``## context``; optionally reset cursor, ``## next``, summary.

    RECORD FORM (board law, 07.07 — "agents write so it can be analyzed"):
    cursor = the CURRENT ACTION in one line, present tense ("wiring the board
    to the record form"); next = 1–3 next steps separated by " · "; note = what
    you decided/did, in plain words, no tech jargon up front. The board shows
    them literally: cursor → "now", next → "next".

    *summary* — WHAT THIS ARC HOLDS, one line, for whoever is choosing which
    arc to open. Before this, ``## summary`` was filled only at handoff, so
    live sessions carried a template stub and the orchestrator could not tell
    an arc holding three daily reports from an empty one. The line lives here,
    not in ``## context``: context is a log (grows), summary is a showcase
    (rewritten).

    *eta* / *deliverable* — WHEN the session will deliver and WHAT the human
    gets: passport fields ``eta:`` (ISO with offset) and ``deliverable:``,
    rewritten, not accumulated. ``None`` = leave alone, ``-``/``none`` = clear.
    """
    if eta is not None:
        eta = parse_eta(eta)
    if deliverable is not None:
        deliverable = clean_deliverable(deliverable)
    if eta is None and deliverable is None and not any(
            s.strip() for s in (note or "", cursor or "", next_steps or "", summary or "")):
        raise OffloadError(
            "offload: nothing to write — pass a note and/or --cursor/--next/--summary/--eta/--deliverable "
            "(rule: one line — where I am / what I decided / what's next)"
        )
    entry = find_session(Path(root), ref)
    if entry is None:
        names = ", ".join(e.name for e in _session_dirs(Path(root))) or "(none)"
        raise OffloadError(
            "offload: no open session matching {0!r}. Open sessions: {1}".format(ref, names)
        )
    return write_pulse(entry, note=note, cursor=cursor, next_steps=next_steps,
                       summary=summary, eta=eta, deliverable=deliverable)


def write_pulse(entry: Path, *, note: str = "", cursor: str = "",
                next_steps: str = "", summary: str = "",
                now: Optional[datetime] = None,
                eta: Optional[str] = None, deliverable: Optional[str] = None) -> Path:
    """Write a pulse to a KNOWN session dir — the resolution-free core of :func:`offload`.

    Callers that already hold the exact session dir MUST use this, not ``offload(root,
    ref)``: resolving by slug (:func:`find_session`) collides when sessions share a slug
    (every handoff pickup is ``NN-pickup`` → entry_slug ``pickup``), so a slug lookup
    lands the pulse on the FIRST same-slug session. That silently mis-stamped a fresh
    pickup's "thread taken" onto an OLDER sibling — the reception seam looked half-open
    on the real session (caught by a live 6-hop dogfood). Taking the exact dir
    removes the ambiguity entirely.

    *now* pins the timestamp (:mod:`tide.acts` writes acts through this same
    entry and must be able to set its own time in tests); defaults to now.
    """
    passport = entry / "arc.md"
    text = passport.read_text(encoding="utf-8")

    # A pulse with only --cursor/--next is still a pulse: without a line in
    # ``## context`` the thread screen counts it as nothing («0 pulses in
    # ## context») and the session looks idle while it works. So the cursor (or,
    # lacking it, the next step) lands in the journal as a short line of its own.
    if not (note or "").strip():
        note = _cursor_only_note(cursor, next_steps)

    if (note or "").strip():
        line = "- {0} — {1}".format(_now_iso(now), " ".join(note.split()))
        if CONTEXT_SECTION in text:
            head, _sep, tail = text.partition(CONTEXT_SECTION)
            rest = tail.split("\n## ", 1)  # don't swallow a section that follows
            trailing = ("\n## " + rest[1]) if len(rest) > 1 else "\n"
            # keep existing entries, drop a leftover template <placeholder> line
            body = [
                ln for ln in rest[0].splitlines()[1:]
                if ln.strip() and not ln.strip().startswith("<")
            ]
            body.append(line)
            text = head + CONTEXT_SECTION + "\n" + "\n".join(body) + "\n" + trailing.lstrip("\n")
        else:
            text = text.rstrip() + "\n\n{0}\n{1}\n".format(CONTEXT_SECTION, line)

    # The passport is assembled in memory and lands as one atomic replace.
    if (cursor or "").strip():
        text = _section_text(text, CURSOR_SECTION, " ".join(cursor.split()))
    if (next_steps or "").strip():
        text = _section_text(text, NEXT_SECTION, " ".join(next_steps.split()))
    if (summary or "").strip():
        text = _section_text(text, SUMMARY_SECTION, " ".join(summary.split()))
    if (cursor or "").strip() or (next_steps or "").strip():
        text = _log_plan_text(text, cursor, next_steps, now)
    atomic_write(passport, text)
    for key, value in ((ETA_FIELD, eta), (DELIVERABLE_FIELD, deliverable)):
        if value is None:
            continue
        if value:
            fields.set_field(passport, key, value)
        else:
            fields.remove_field(passport, key)
    fields.set_field(passport, OFFLOADED_FIELD, _now_iso(now))
    return passport


def _cursor_only_note(cursor: str, next_steps: str) -> str:
    """The ``## context`` line for a pulse that carried no note — or ``""``."""
    if (cursor or "").strip():
        return "cursor → " + " ".join(cursor.split())
    if (next_steps or "").strip():
        return "next → " + " ".join(next_steps.split())
    return ""


NEXT_LOG_SECTION = "## offload-log"
NEXT_LOG_KEEP = 40


def _log_plan_text(text: str, cursor: str, next_steps: str, now: Optional[datetime]) -> str:
    """Snapshot of every offload's ``--cursor``/``--next``: ``## next`` and
    ``## cursor`` get overwritten, while the seam sync checks the old session's
    tails against everything the new one has named — not just the latest.
    The last 40 snapshots are kept."""
    parts = []
    if (next_steps or "").strip():
        parts.append("next: " + " ".join(next_steps.split()))
    if (cursor or "").strip():
        parts.append("cursor: " + " ".join(cursor.split()))
    entry = "- {0} {1}".format(_now_iso(now), " | ".join(parts))
    old: List[str] = []
    if NEXT_LOG_SECTION in text:
        head, _sep, tail = text.partition(NEXT_LOG_SECTION)
        rest = tail.split("\n## ", 1)
        old = [ln for ln in rest[0].splitlines()[1:] if ln.strip()]
        trailing = ("\n## " + rest[1]) if len(rest) > 1 else "\n"
        body = (old + [entry])[-NEXT_LOG_KEEP:]
        text = head + NEXT_LOG_SECTION + "\n" + "\n".join(body) + "\n" + trailing
    elif CONTEXT_SECTION in text:  # before the log: writers appending to the passport end land in context
        head, _sep, tail = text.partition(CONTEXT_SECTION)
        text = head + "{0}\n{1}\n\n".format(NEXT_LOG_SECTION, entry) + CONTEXT_SECTION + tail
    else:
        text = text.rstrip() + "\n\n{0}\n{1}\n".format(NEXT_LOG_SECTION, entry)
    return text


def _log_plan(passport: Path, cursor: str, next_steps: str, now: Optional[datetime]) -> None:
    text = _log_plan_text(passport.read_text(encoding="utf-8"), cursor, next_steps, now)
    atomic_write(passport, text)


def _section_text(text: str, header: str, body: str) -> str:
    """*text* with the body of *header*'s section replaced (appended if absent)."""
    if header not in text:
        text = text.rstrip() + "\n\n{0}\n{1}\n".format(header, body)
    else:
        head, _sep, tail = text.partition(header)
        rest = tail.split("\n## ", 1)
        trailing = ("\n## " + rest[1]) if len(rest) > 1 else "\n"
        text = head + header + "\n" + body + "\n" + trailing
    return text


def _replace_section(passport: Path, header: str, body: str) -> None:
    """Replace the body of *header*'s section in *passport* (atomic rewrite)."""
    atomic_write(passport, _section_text(passport.read_text(encoding="utf-8"), header, body))


# --- the Stop-hook nudge -----------------------------------------------------

def _newest_mtime(d: Path) -> float:
    """Newest file mtime under *d* (0.0 when absent/empty)."""
    best = 0.0
    if not d.is_dir():
        return best
    for p in d.rglob("*"):
        try:
            if p.is_file():
                best = max(best, p.stat().st_mtime)
        except OSError:
            continue
    return best


# --- CLI + hook wiring -------------------------------------------------------

# A pulse CLAIMS the thread is finished only when a closure verb attaches to a CLOSABLE
# OBJECT (thread/arc/PR/delta/branch) — a bare "closed" also describes gates and
# steps ("start gate closed") and a substring match trained agents to avoid honest
# words in pulses. Both word orders, up to two words in between; verbs are
# past/perfect only (intent like "will close the thread later" must not warn). The link
# may NOT cross a clause boundary (,.;:—…): "start gate closed, planning the THREAD" —
# "thread" belongs to another clause, not a closure claim (second false hit).
_CLOSABLE = r"\b(?:threads?|arcs?|branch(?:es)?|prs?|deltas?)\b"
_CLOSED_VERB = r"\b(?:closed|merged|shipped|released|landed)\b"
_LINK = r"(?:{s}(?:\w+{s}){{0,2}})".format(s=r"[ \t]+")  # plain spaces only: any punctuation breaks the link
_CLOSURE_CLAIM = re.compile(
    r"{o}{l}{v}|{v}{l}{o}".format(o=_CLOSABLE, v=_CLOSED_VERB, l=_LINK),
    re.IGNORECASE,
)


def _closure_word_warning(passport: Path, blob: str) -> Optional[str]:
    """Warn when the pulse SAYS closed but its thread is OPEN on disk.

    The pulse lands in ``<thread>/arcs/<session>/arc.md``; the thread is the dir two
    levels up. If it isn't wrapped ``__…__`` (closed) yet the text claims closure, the
    board will still paint the nit live — nudge the human to close it for real.
    """
    low = (blob or "").lower()
    if not _CLOSURE_CLAIM.search(low):
        return None
    try:
        thread = passport.parent.parent.parent  # arc.md → session → arcs → thread
        if thread.is_dir() and not slug.is_closed_entry(thread.name):
            return ("tide: ⚠ the pulse says 'closed/merged', but thread {0} is OPEN on disk — "
                    "words don't convince the board. Close it for real: tide arc close {1}".format(
                        thread.name, slug.entry_slug(thread.name)))
    except Exception:  # noqa: BLE001  a warning must never break offload
        return None
    return None


def _cmd_offload(args) -> int:
    root = paths.require_tide_root()
    note = " ".join(getattr(args, "note", []) or [])
    cursor = getattr(args, "cursor", "") or ""
    next_steps = getattr(args, "next_steps", "") or ""
    summary = getattr(args, "summary", "") or ""
    passport = offload(root, args.session, note=note, cursor=cursor,
                       next_steps=next_steps, summary=summary,
                       eta=getattr(args, "eta", None),
                       deliverable=getattr(args, "deliverable", None))
    print("tide: offloaded → {0}".format(passport))
    warn = _closure_word_warning(passport, " ".join((note, cursor, next_steps)))
    if warn:
        print(warn, file=sys.stderr)
    return 0


def register(subparsers) -> None:
    """Add the top-level ``offload`` command (called by cli.py)."""
    p = subparsers.add_parser(
        "offload",
        help="offload as you go: a line into the session's '## context' "
             "(+ --cursor)",
    )
    p.add_argument("session", help="open session slug (nested resolve across threads)")
    p.add_argument("--cursor", help="WHAT YOU ARE DOING right now, one line, "
                                    "present tense ('wiring the board to the form')")
    p.add_argument("--next", dest="next_steps",
                   help="1-3 next steps separated by ' · ' — the board shows "
                        "them as what's next")
    p.add_argument("--summary",
                   help="ONE line: what this arc holds, for whoever is choosing "
                        "which arc to open — rewritten, not appended")
    p.add_argument("--eta",
                   help="WHEN you will deliver: HH:MM (today; past = overdue), "
                        "'DD.MM HH:MM' or ISO — stored as ISO, rewritten; '-' clears")
    p.add_argument("--deliverable",
                   help="WHAT the human will get, one short line (<=60 chars: "
                        "'PR #171', 'screenshot of the screen') — rewritten; '-' clears")
    p.add_argument("note", nargs="*", help="context note: what you decided or "
                                           "did, in plain words")
    p.set_defaults(func=_cmd_offload, _cmd="offload")
