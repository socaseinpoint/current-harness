"""tide.acts — the ACT: one line in a session passport, a single writer.

An act is what a session did, said so it still reads a year later:
**what · proof · address**. A pulse, a check with proof and "builder dispatched"
are one and the same gesture, so they share one place: the ``## context``
section of the passport of the session the gesture came from. There used to be
two places (the work log and the session passport), and nothing could stitch
the day's history back together from them.

Grammar (the human's word, 2026-09-02), verbatim::

    - 2026-09-02T16:17:32 — act: what was done · proof: how · word: «…» · #66.4

* field separator is ``" · "`` (space, middle dot, space);
* the work address comes LAST: ``#66`` is the whole work, ``#66.4`` its item 4;
* an act is ALWAYS one line. Newlines collapse to spaces
  (:func:`tide.offload.write_pulse` does that itself, and rightly so), and long
  text does not go into an act at all: :data:`ACT_MAX` is the ceiling, above it
  :class:`ValueError`. A long proof goes into the thread as a file; the act gets
  the path.

An act is born ONLY inside a session (thread decision 37: the human confirms
through chat, the board is a display). :func:`caller_session` finds the
caller's session via ``$CLAUDE_CODE_SESSION_ID``; no session means no act, and
that is not an error: verbs are called from scripts and from other machines,
and must not fail there.

There is one writer — :func:`write_act` on top of
:func:`tide.offload.write_pulse`. The reader is :func:`read_acts`: the acts of
every session of one thread as one list, newest first, filterable by work
address. Two views live on top of it: ``tide work show`` (work log = acts +
legacy lines of the file) and ``tide thread`` (the feed of
:func:`head_session`, the thread's leading session).

Long text not fitting in an act is not a problem but a rule: :func:`spill_proof`
puts the full proof as a file in the session's ``workspace/proofs/``, and
:func:`file_proof` builds the act's proof from its first line plus the file
path. Truncating a proof is not allowed — since the log became a VIEW over acts,
a truncated proof would be the only record.
"""

from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, NamedTuple, Optional

from . import fields, offload, paths, slug

# Act length ceiling — timestamp included, i.e. exactly the line the human sees
# in the passport. Three hundred characters is about two screen lines; anything
# longer is a report, not an act, and belongs in a file.
ACT_MAX = 300

KIND = "act"
SEP = " · "
PROOF_LABEL = "proof"
WORD_LABEL = "word"

# «· #66» or «· #66.4» at the very end of the line
_REF_RE = re.compile(r"(?:^|\s·\s)#(\d{1,4})(?:\.(\d{1,4}))?\s*$")
# «- 2026-09-02T16:17:32 — act text»
_ACT_LINE_RE = re.compile(r"^-\s+(\S+?)\s+—\s+(.*)$")


class Act(NamedTuple):
    """One act: when, what was written, at which address and in whose passport."""

    at: datetime
    text: str
    ref: str
    session: Path


# --- address -----------------------------------------------------------------

def make_ref(work: object, item: Optional[object] = None) -> str:
    """Work address for an act: ``"66"`` or ``"66.4"`` (no hash sign).

    *work* is the work number or its folder name (``66-acts-in-one-place``): the
    leading number is taken, because verbs hold the folder in hand.
    """
    raw = str(work or "").strip()
    num = raw.partition("-")[0].strip()
    if not num.isdigit():
        return ""
    ref = str(int(num))
    if item is not None and str(item).strip().isdigit():
        ref = "{0}.{1}".format(ref, int(str(item).strip()))
    return ref


# --- writer -----------------------------------------------------------------

def compose(what: str, *, proof: Optional[str] = None,
            word: Optional[str] = None, ref: Optional[str] = None) -> str:
    """Act body per the grammar — without the timestamp and the leading «- ».

    Empty fields are simply omitted: an act without proof is more honest than
    one with an empty «proof:».
    """
    body = _flat(what)
    if not body:
        raise ValueError("act: empty act — say what was done")
    parts = ["{0}: {1}".format(KIND, body)]
    if _flat(proof):
        parts.append("{0}: {1}".format(PROOF_LABEL, _flat(proof)))
    if _flat(word):
        parts.append("{0}: «{1}»".format(WORD_LABEL, _flat(word)))
    tail = _flat(ref).lstrip("#")
    if tail:
        parts.append("#" + tail)
    return SEP.join(parts)


def write_act(session_dir: Path, what: str, *, proof: Optional[str] = None,
              word: Optional[str] = None, ref: Optional[str] = None,
              now: Optional[datetime] = None) -> str:
    """Append an act to ``## context`` of the *session_dir* passport; return the line.

    Writes through :func:`tide.offload.write_pulse` — there is no second writer
    of ``## context`` and there must not be one. An act longer than
    :data:`ACT_MAX` is not written at all: :class:`ValueError` with a hint on
    where long text goes.
    """
    body = compose(what, proof=proof, word=word, ref=ref)
    stamp = (now or datetime.now()).isoformat(timespec="seconds")
    line = "- {0} — {1}".format(stamp, body)
    if len(line) > ACT_MAX:
        raise ValueError(
            "act: {0} chars over the {1} ceiling — an act is one line «what · proof · "
            "address». Put long text in the thread as a file and give the act the path.".format(
                len(line), ACT_MAX))
    offload.write_pulse(Path(session_dir), note=body, now=now)
    return line


def fit_proof(what: str, proof: object, *, word: Optional[str] = None,
              ref: Optional[str] = None) -> str:
    """The proof, trimmed from the tail just enough for the act to fit :data:`ACT_MAX`.

    An EMERGENCY path, not the normal one: a truncated proof is a lost proof,
    because the work log is now a VIEW over acts, not a second store. Long text
    goes into a file (:func:`spill_proof`) with a path in the act
    (:func:`file_proof`); we land here only when writing the file failed — the
    start of a proof with «…» beats an empty string. Empty string if it does not
    fit even without the proof.
    """
    flat = _flat(proof)
    if not flat:
        return ""
    over = _over(what, flat, word=word, ref=ref)
    if over <= 0:
        return flat
    keep = len(flat) - over - 1  # one char for the ellipsis
    if keep < 1:
        return ""
    return flat[:keep].rstrip() + "…"


def _over(what: str, proof: str, *, word: Optional[str] = None,
          ref: Optional[str] = None) -> int:
    """How many chars an act with this proof exceeds the ceiling by (≤0 means it fits)."""
    room = len("- {0} — ".format(datetime.now().isoformat(timespec="seconds")))
    return room + len(compose(what, proof=proof, word=word, ref=ref)) - ACT_MAX


# --- long proof: a file, not a truncation ------------------------------------

PROOFS_DIRNAME = "proofs"


def spill_proof(session_dir: Path, proof: object, *, ref: str = "",
                now: Optional[datetime] = None) -> Path:
    """The full proof as a file in the session's ``workspace/proofs/``; return the path.

    The human's word, 2026-09-02: "one line, long text goes to a file". An act is
    one line by construction, but a three-paragraph proof is still a proof — and
    it must not be truncated: the work log became a VIEW over acts, so the
    truncation would be the only record. So long text moves to a file next to
    the session that wrote it, and the act gets the first line and the path.

    The file name is the work address, item and timestamp
    (``66.4-20260902-195413.md``): you can tell what the proof is for without
    opening it.
    """
    stamp = (now or datetime.now())
    name = "{0}-{1}.md".format(_flat(ref).lstrip("#") or "act",
                               stamp.strftime("%Y%m%d-%H%M%S"))
    d = Path(session_dir) / "workspace" / PROOFS_DIRNAME
    d.mkdir(parents=True, exist_ok=True)
    f = d / name
    head = "# proof{0} · {1}".format(
        " · #" + _flat(ref).lstrip("#") if _flat(ref) else "",
        stamp.isoformat(timespec="seconds"))
    f.write_text("{0}\n\n{1}\n".format(head, str(proof or "").strip()),
                 encoding="utf-8")
    return f


def proof_ref(session_dir: Path, proof_file: Path) -> str:
    """The proof file path as read in an act — relative to the session folder.

    The act lives in that very session's passport, so its folder is the natural
    origin: ``workspace/proofs/66.4-….md`` is shorter than an absolute path and
    says exactly the same.
    """
    try:
        return str(Path(proof_file).relative_to(Path(session_dir)))
    except ValueError:
        return str(proof_file)


def file_proof(what: str, proof: object, where: str, *,
               word: Optional[str] = None, ref: Optional[str] = None) -> str:
    """The act's proof when the full text moved to a file: first line + path.

    The first line of a proof is what the author wrote FOR THE HUMAN (check norm
    of 07-31: short for the human, technical detail below), so that is what
    stays in the act; it is shortened only if the act does not fit even with it.
    The path is never cut — without it the record no longer leads to the proof,
    and that is the whole point.
    """
    first = _flat(str(proof or "").strip().split("\n", 1)[0])
    if not where:
        return fit_proof(what, first, word=word, ref=ref)
    over = _over(what, "{0} · {1}".format(first, where) if first else where,
                 word=word, ref=ref)
    if over <= 0:
        return "{0} · {1}".format(first, where) if first else where
    keep = len(first) - over - 1
    if keep < 1:
        return where
    return "{0}… · {1}".format(first[:keep].rstrip(), where)


def _flat(value: object) -> str:
    """One line, no newlines or extra spaces (an act is always one line)."""
    return " ".join(str(value or "").split())


# --- who writes------------------------------------------------------------

def caller_session(root: Optional[Path] = None) -> Optional[Path]:
    """The session-arc folder of the current caller — or None.

    Same mechanism as ``work.resolve_caller_thread``:
    ``$CLAUDE_CODE_SESSION_ID`` → :func:`tide.offload.find_session_by_claude_id`
    in the caller's project. None when the sid is unset, the project is not a
    tide project, or no passport with that pin exists; then no act is born.
    """
    sid = (os.environ.get("CLAUDE_CODE_SESSION_ID") or "").strip()
    if not sid:
        return None
    origin = Path(root) if root is not None else paths.find_tide_root()
    if origin is None:
        return None
    try:
        return offload.find_session_by_claude_id(Path(origin), sid)
    except OSError:
        return None


# --- reader -----------------------------------------------------------------

def read_acts(thread_dir: Path, *, ref: Optional[str] = None) -> List[Act]:
    """Acts of ALL sessions of thread *thread_dir* as one list, newest first.

    *ref* filters by address: ``"66"`` yields both ``#66`` and ``#66.4``;
    ``"66.4"`` only item 4. The hash sign is optional.

    Closed sessions are read the same as open ones: a thread's history does not
    shrink because an arc was closed.
    """
    sessions = _thread_sessions(Path(thread_dir))
    want = _flat(ref).lstrip("#")
    rows: List[tuple] = []
    order = 0
    for entry in sessions:
        for at, text, addr in _session_acts(entry):
            order += 1
            if want and not _ref_matches(addr, want):
                continue
            rows.append((at, order, Act(at, text, addr, entry)))
    rows.sort(key=lambda r: (r[0], r[1]), reverse=True)
    return [r[2] for r in rows]


def head_session(thread_dir: Path) -> Optional[Path]:
    """The thread's leading session — the one whose acts are "what is happening now". Or None.

    Canon #1: a thread is led by the NEWEST ACCEPTED session — derived, not
    stamped. Derived by three questions, from most honest to cheapest, over open
    sessions not released by hand (``dismissed:``), newest first:

    1. which has a real claude chat on disk (the take happened in fact);
    2. which at least has ``claude-session:`` stamped (the take happened on paper);
    3. simply the newest open one — better to name a live session than say nothing.

    The first question weeds out a GHOST: raising an offer mints a sid and stamps
    it before the session ever speaks; if the spawn fails, the passport keeps a
    chat id that never existed. The board catches the same ghost with its own
    ``_head_session``, but it already has parsed sessions at hand while here we
    have files — the answer is shared, not the code.
    """
    live = []
    for entry in sorted(_thread_sessions(Path(thread_dir)), reverse=True):
        if slug.is_closed_entry(entry.name):
            continue
        pp = entry / "arc.md"
        if (fields.read_field(pp, "dismissed") or "").strip():
            continue
        live.append((entry, (fields.read_field(pp, "claude-session") or "").strip()))
    if not live:
        return None
    return (next((e for e, sid in live if sid and _has_transcript(e, sid)), None)
            or next((e for e, sid in live if sid), None)
            or live[0][0])


def _has_transcript(entry: Path, sid: str) -> bool:
    """Does the session have a REAL chat on disk (``~/.claude/projects/…/<sid>.jsonl``).

    First where this project's chat lives (the directory is the cwd with ``/``
    and ``.`` replaced by hyphens — that is how claude names it); on a miss, a
    glob across all projects, because sessions are not always started from the
    root.
    """
    base = Path(os.environ.get("CLAUDE_CONFIG_DIR")
                or (Path.home() / ".claude")) / "projects"
    root = paths.find_tide_root(entry)
    if root is not None:
        encoded = str(root).replace("/", "-").replace(".", "-")
        if (base / encoded / "{0}.jsonl".format(sid)).is_file():
            return True
    try:
        return any(base.glob("*/{0}.jsonl".format(sid)))
    except OSError:
        return False


def strip_ref(text: str) -> str:
    """Act body without the trailing address — for callers that place the address themselves."""
    return _REF_RE.sub("", text or "").rstrip()


# --- merge sieve: one for engine and board -------------------------------------

def act_what(text: str) -> str:
    """«act: what was done · proof: … · #66.4» → «what was done» — the act's first field.

    It is also the only field an act is recognised by: in an act the proof is a
    field of its own, while in a log line it is baked into the text, so there is
    nothing to compare as a whole.
    """
    head = strip_ref(text or "").split(SEP)[0].strip()
    kind = KIND + ": "
    return head[len(kind):].strip() if head.startswith(kind) else head


def sift_journal(entries: List[tuple], rows: List[Act]) -> List[object]:
    """File log entries that have NO TWIN ACT — a sieve by GESTURE.

    ONE merge point for everyone. The log has two readers — the
    engine (:func:`tide.arc.work.journal_view`) and the board
    (`_work_journal_view`) — and before this function each carried its own copy
    of the rule: they had already drifted apart in the comparison formula, and
    drifting further they would have shown the human two different histories of
    one work.

    *entries* are file records as ``(timestamp, first body line, what to
    return)``: the readers' log line shapes differ (one with «- », one without),
    so parsing the line stays with them, while the RULE lives here.
    *rows* are this work's acts (:class:`Act`).

    Rule: an entry is dropped only if the same gesture already arrived as an
    act — same MINUTE and one body starts with the other. The sieve is by
    gesture, not by the time of the first act: acts land in the passport not
    only through the verbs' double write but also by hand — on a live work
    there are thirteen log lines without a twin between the first act and the
    first verb, and a time cut-off would have wiped them off the screen along
    with their proofs.

    An act cancels EXACTLY ONE entry: two identical gestures in one minute (a
    re-dispatched builder) are two events, and the second must not be lost.
    """
    used = [False] * len(rows)
    out: List[object] = []
    for at, body, payload in entries:
        if not _take_twin(at, body, rows, used):
            out.append(payload)
    return out


def _take_twin(at: Optional[datetime], body: str, rows: List[Act],
               used: List[bool]) -> bool:
    """Find and CLAIM this entry's twin act; False if there is none."""
    if at is None:
        return False
    minute = at.replace(second=0, microsecond=0)
    head = _flat(body).casefold()
    if not head:
        return False
    for i, r in enumerate(rows):
        if used[i] or r.at.replace(second=0, microsecond=0) != minute:
            continue
        what = _flat(act_what(r.text)).casefold()
        if what and (head.startswith(what) or what.startswith(head)):
            used[i] = True
            return True
    return False


def _ref_matches(addr: str, want: str) -> bool:
    """``#66`` matches both ``66`` and ``66.4``; ``#66.4`` only itself."""
    return addr == want or addr.startswith(want + ".")


def _thread_sessions(thread: Path) -> List[Path]:
    """The thread's sessions — open and closed, in file order."""
    sub = thread / paths.ARCS_DIRNAME
    if not sub.is_dir():
        return []
    return [p for p in sorted(sub.iterdir())
            if p.is_dir() and slug.is_entry(p.name) and (p / "arc.md").is_file()]


def _session_acts(entry: Path) -> List[tuple]:
    """``(datetime, text, address)`` for each ``## context`` line of the passport.

    A line without a parseable timestamp is skipped: an act without a time
    cannot be placed in the feed, and guessing one would be lying.
    """
    try:
        text = (entry / "arc.md").read_text(encoding="utf-8")
    except OSError:
        return []
    if offload.CONTEXT_SECTION not in text:
        return []
    body = text.partition(offload.CONTEXT_SECTION)[2].split("\n## ", 1)[0]
    out = []
    for ln in body.splitlines():
        m = _ACT_LINE_RE.match(ln.strip())
        if not m:
            continue
        try:
            at = datetime.fromisoformat(m.group(1))
        except ValueError:
            continue
        line = m.group(2).strip()
        addr = ""
        hit = _REF_RE.search(line)
        if hit:
            addr = hit.group(1) if not hit.group(2) else "{0}.{1}".format(*hit.groups())
        out.append((at, line, addr))
    return out


__all__ = ["ACT_MAX", "Act", "PROOFS_DIRNAME", "act_what", "caller_session",
           "compose", "file_proof", "fit_proof", "head_session", "make_ref",
           "proof_ref", "read_acts", "sift_journal", "spill_proof", "strip_ref",
           "write_act"]
