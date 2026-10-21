"""tide.arc.work — "works": human work-cards as arcs under ``.tide/arcs/works/``.

A work is an arc-kind entity (``kind: work``): a dir ``NN-<slug>/`` holding a
``work.md`` passport — meta fields + free text (a task or a problem, no card
types) + ``## plan`` + ``## checklist`` + ``## fixes`` + ``## log``. The live
board renders these files as cards and its ``/work-*`` handlers are the HUMAN's
hand; these CLI verbs are the AGENT's deterministic gestures over the same
files, so a status move or a journal line can never be forgotten (the first live
run proved they are: the agent checked an item and moved no status).

The signed model lives with the instance (work-cycle.md, 16.07); the
machine here: **open → taken → review → done**.

* ``plan``    — put the agreed-to-be plan as free text into ``## plan``; the
  agent's word, so it moves NO status.
* ``propose`` — offer checklist items as ``- [?]``: visible, numbered, but not
  yet the plan — only the human's "yes" turns them into ``- [ ]``.
  ``--replace`` withdraws the standing offers first (agreed items untouched);
  a work sitting in review comes back to taken — there is a question on the
  table again.
* ``agree``   — that "yes" when it is SAID, not clicked: flips the named
  ``- [?]`` items (or every standing offer) into ``- [ ]`` and writes the
  human's word into the journal; ``--drop`` withdraws a rejected offer
  instead. REQUIRES ``--word`` and moves no status.
* ``fix``     — the human's afterthoughts at the gate: appends items to
  ``## fixes`` ALREADY agreed (``- [ ]``), because ``--word`` — his remark
  verbatim — IS the agreement, and asking him to sign what he just asked for
  would be a second gate. A work sitting in review comes back to taken: there
  is work on the table again.
* ``drop``    — withdraw an AGREED item N; REQUIRES ``--word`` (editing a
  signed agreement is the human's hand only). A standing ``- [?]`` does not
  go here: an offer has its own answer — ``agree --drop``.
* ``take``    — open → taken (+ ``taken-by``/``taken-at``); starts on the
  human's word, recorded when given.
* ``step``    — the work's address in the thread plan: ``step: N``. Can be set
  by hand, but usually arrives on its own together with the thread (see below).
* ``dispatch``— "builder dispatched: name" as a journal line. MOVES NO STATUS:
  it is an event, not a state. Only on taken; a repeat is one more line.
* ``check``   — mark item N with a REQUIRED ``--proof``; when ALL AGREED items
  are checked AND no offer is left standing, a taken work auto-moves to review
  — gesture 4 can't be forgotten. A ``- [?]`` item is refused: it is still an
  offer.
* ``uncheck`` — unmark item N; a review work falls back to taken.
* ``close``   — any live status → done; REQUIRES ``--word`` (the human's word:
  closing is the human's gate, the word is recorded in the journal). That word
  also ACCEPTS every checked item at once — see below.
* ``reopen``  — done → back to a live status BY THE PASSPORT: ``taken-by`` set —
  back to the assignee (taken, or straight to review if the checklist is
  closed); not set — open.
* ``title``   — rewrite the H1; the name is what the human signed, so it moves
  only with ``--word`` and never moves the status.
* ``add`` / ``list`` / ``show`` — housekeeping (``add`` mirrors the board form).
  ``add --cand NN`` BIRTHS a work from a candidate in one gesture: the
  candidate's text lands as a draft in ``## plan``, the candidate itself leaves
  the shelf for ``candidates/__dropped__/`` (recoverable), and the link is a
  passport field ``from-cand: NN`` — decision 38, 02.09: it is a fact of birth,
  not a gesture on the act feed, and must not depend on whether the board
  button has a session of its own.

The work's name is the H1, NOT the first checklist item: ``add`` births a work
with an empty ``## checklist``. A name-twin item happened three times — nobody ever did it, it lied to the counter (0/6 instead of 0/5), and
there was nothing to drop it with. The checklist is built in
conversation: ``propose`` → the human's "yes".

## Where a work is headed: ``thread:`` and ``step:``

``thread:`` — the responsible thread, ``step:`` — the step number in its plan
(``<thread>/plan.md``, section ``## steps``, the current one marked ``[>]``).
Together they answer "where is this work going": without a step, works hang in a
flat list — you see what is being done, not why.

Both arrive ON THEIR OWN from the session that created the work (``add``/``plan``/
``propose``) or took it (``take``) — the agent already knows which session it
writes from. Previously only ``take`` wrote the thread, i.e. AFTER the human's
"yes": he was called to look at the plan in the thread's tab, and the work was
not there yet. An already set thread is never overwritten by
automation — explicit wins.

A step without a thread is meaningless, so it follows the thread: the thread
changed — re-read from its plan; the thread was cleared — the step is cleared
too. No ``plan.md``, no ``## steps`` section, nothing marked ``[>]`` — the field
is simply not set. No guessing: a false address is worse than none.

An item is a SHORT title on its own line plus an optional description on the
lines below it, indented by two spaces::

    - [?] Retrain the handoff ritual
      handoff skill: draft first — then curation

The human signs steps on the board, so the title has to be readable at a glance
and the details wait below for whoever wants them. Only ``- [`` lines count as
items: a description never shifts a number, so "item 3" means the same line for
the CLI, the board and the human. ``propose``/``checklist``/``fix`` take the two
apart at a ``\n`` inside the item argument — first line the title, the rest the
description (same convention as ``plan``).

An item carries TWO facts and only the first one is a checkbox: "done" is the
agent's ``- [x]`` with its proof, "accepted" is the human's hand afterwards.
Acceptance therefore lives in JOURNAL lines — the checklist format never changes,
so nothing that already reads a passport has to relearn it::

    - 2026-07-30 14:02 — item 2 accepted by hand              (board, one item)
    - 2026-07-30 14:05 — all done items accepted by word      (close, the lot)

The agent has NO per-item acceptance verb: that gesture is the human's hand on
the board. ``close`` writes the mass line (when anything is checked) right before
the closing word — one word accepts what it closes. ``show`` reads both lines
back and marks an item that has both facts ``✓✓``; the mass line speaks for the
work as it was closed, so it counts only while the work IS closed — a ``reopen``
touches no acceptance (history is never rubbed out), but the checklist moves on
and only per-item acceptance survives it.

Items live in TWO sections — ``## checklist`` then ``## fixes`` — and the numbering
runs straight through them in file order: with four items in the checklist the
first fix is item 5. Every hand (``check``, ``uncheck``, ``agree``, the board)
counts the same way, so a number said out loud means one line everywhere.

Every gesture lands as an ACT in the passport of the session that made it
(:mod:`tide.acts`) — and NOWHERE ELSE. Since the journal rework ``_journal`` no
longer appends to ``## log`` of ``work.md``: there is one place, the journal a
reader sees is a VIEW over the acts plus whatever the file already holds
(:func:`journal_view`, printed by :func:`show`), and every ``## log`` written
before that day is read as it is, forever — nothing is migrated or cleaned up.
All logic is plain functions (argparse-free); :func:`register` wires the thin
handlers.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .. import io as _io, numbering, paths, slug
from . import stream

WORKS_DIRNAME = "works"
_STAMP_FMT = "%Y-%m-%d %H:%M"
# three item states: agreed-open « », done «x», proposed by the agent «?»
_ITEM_RE = re.compile(r"^- \[( |x|\?)\] (.*)$")
PROPOSED = "?"
_STATUS_RE = re.compile(r"^status: .*$", re.M)
_DEADLINE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LIVE = ("open", "taken", "review")
PLAN_TITLE = "plan"
CHECKLIST_TITLE = "checklist"
# the human's afterthoughts at the gate — items, same numbering, own section
FIXES_TITLE = "fixes"
JOURNAL_TITLE = "log"
# the human's acceptance lives in JOURNAL LINES, the checklist format is untouched:
# "- [x]" — done, ✓✓ — done AND accepted (the second fact is read from the journal only)
ACCEPTED_MARK = "✓✓"
ACCEPT_ALL_LINE = "all done items accepted by word"
# lax about the stamp (the per-item line is written by the board HAND, not us),
# strict about the phrase. The same gesture also arrives as an ACT ("act: … · #NN"),
# so kind and address are optional: one acceptance, two places it can be written
# since the journal rework
_ACT_KIND = r"(?:\w+: )?"
_ACT_TAIL = r"(?: · #\d{1,4}(?:\.\d{1,4})?)?"
_ACCEPT_ONE_RE = re.compile(r"^- .+ — {0}item (\d+) accepted by hand{1}\s*$".format(
    _ACT_KIND, _ACT_TAIL))
_ACCEPT_ALL_RE = re.compile(r"^- .+ — {0}{1}{2}\s*$".format(
    _ACT_KIND, re.escape(ACCEPT_ALL_LINE), _ACT_TAIL))
# thread plan step: "- [>] 3. step name | what is done | result: "…""
# state — [x] passed, [>] current, [ ] future (written by curate.validate_step)
_PLAN_STEP_RE = re.compile(r"^- \[([x>~ ])\]\s*(\d{1,3})\.\s*(.*)$")
PLAN_STEPS_TITLE = "steps"
CURRENT_STEP = ">"
# A step the thread retired without doing — dissolved into another step, or found
# unnecessary. Parsed so a reader's count matches the file a human is looking at;
# a step invisible to the parser is how a plan and its screen start disagreeing.
RETIRED_STEP = "~"
# a work card is read at a glance on the board — longer is a warning, not a bar
TITLE_MAX = 80
_TITLE_IN_JOURNAL = 60

# tide.slug drops Cyrillic entirely, but work titles may be written in Russian:
# transliterate them (the board solved this the same way — serve_live._CYR2LAT).
# Keys are \u escapes for the lowercase Cyrillic alphabet (U+0430..U+044F, U+0451).
_CYR2LAT = {
    "\u0430": "a", "\u0431": "b", "\u0432": "v", "\u0433": "g", "\u0434": "d", "\u0435": "e",
    "\u0436": "zh", "\u0437": "z", "\u0438": "i", "\u0439": "y", "\u043a": "k", "\u043b": "l",
    "\u043c": "m", "\u043d": "n", "\u043e": "o", "\u043f": "p", "\u0440": "r", "\u0441": "s",
    "\u0442": "t", "\u0443": "u", "\u0444": "f", "\u0445": "h", "\u0446": "c", "\u0447": "ch",
    "\u0448": "sh", "\u0449": "sch", "\u044a": "", "\u044b": "y", "\u044c": "", "\u044d": "e",
    "\u044e": "yu", "\u044f": "ya", "\u0451": "e",
}


class WorkError(stream.StreamError):
    """A user-facing works error (bad transition, unknown key, missing proof …)."""


# --- paths / parsing ---------------------------------------------------------

def works_dir(root: Path) -> Path:
    """``<project>/.tide/arcs/works`` — the works live beside the stream."""
    return paths.arcs_dir(root) / WORKS_DIRNAME


def _work_slug(text: str) -> str:
    """Short latin handle for a (usually Russian) work title."""
    lat = "".join(_CYR2LAT.get(ch, ch) for ch in text.lower())
    return slug.short_slug(lat) or "work"


def _find(root: Path, key: str) -> Path:
    """Resolve a work dir by NN, NN-slug or slug; fail loud on 0 or 2+ hits.

    A bare number matches too: ``1`` is the work ``01-…`` — humans type what
    ``add`` printed, minus the leading zero. Numbers are unique per project,
    so the shortcut cannot make a key ambiguous.
    """
    wdir = works_dir(root)
    key = (key or "").strip().rstrip("/")
    if not key:
        raise WorkError("work: empty key")
    want_num = int(key) if key.isdigit() else None
    hits = []
    for p in sorted(wdir.iterdir()) if wdir.is_dir() else []:
        if not p.is_dir() or not (p / "work.md").is_file():
            continue
        num, _, rest = p.name.partition("-")
        if key in (p.name, num, rest) or (
                want_num is not None and num.isdigit()
                and int(num) == want_num):
            hits.append(p)
    if not hits:
        raise WorkError(
            "work: no work {0!r} in {1} "
            "(works are named 01, 02, … — see tide work list)".format(
                key, wdir))
    if len(hits) > 1:
        raise WorkError(
            "work: key {0!r} is ambiguous: {1}".format(
                key, ", ".join(p.name for p in hits)))
    return hits[0]


def _read(wdir: Path) -> Tuple[Path, str]:
    f = wdir / "work.md"
    return f, f.read_text(encoding="utf-8")


def _status_of(text: str) -> str:
    m = re.search(r"^status:\s*(\S+)", text, re.M)
    if not m:
        raise WorkError("work: passport has no status field")
    return m.group(1)


def _set_status(text: str, new: str) -> str:
    return _STATUS_RE.sub("status: " + new, text, count=1)


def _journal(text: str, line: str, *, wdir: Optional[Path] = None,
             item: Optional[int] = None, what: Optional[str] = None,
             proof: Optional[str] = None, word: Optional[str] = None,
             now: Optional[datetime] = None) -> str:
    """Record a gesture — as an ACT in the calling session's passport. NOTHING goes to the file.

    No second storage is left: ``## log`` of the work
    file is no longer appended, *text* is returned as is. The journal is read as
    a view over the acts (:func:`journal_view`), and ``## log`` sections already
    written in old ``work.md`` files are read from there FOREVER — nobody
    migrates or cleans them.

    *line* — the journal wording of the gesture; it stayed a parameter because
    the act text is taken from it when *what* is not given, and because the
    verbs name the gesture with it in human words. *what* sets the act text when
    the journal wording does not fit (in the journal the human's word is sewn
    into the line, in an act it has its own field).

    *wdir* — the work folder, i.e. the act's ADDRESS (``#NN``). Without it the
    gesture lands nowhere: with file writes gone, a call without *wdir* is an
    orphan event. No calling session — no act either, and the verb does not
    fail: verbs are called from scripts and tests too.
    """
    if wdir is not None:
        _act(wdir, what if what is not None else _journal_body(line),
             item=item, proof=proof, word=word, now=now)
    return text


def _journal_body(line: str) -> str:
    """"- 2026-09-02 16:13 — text" → "text" (the act stamps its own time)."""
    m = re.match(r"^-\s+\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(?::\d{2})?\s+—\s+(.*)$",
                 line, re.S)
    return m.group(1).strip() if m else line.lstrip("- ").strip()


def _act(wdir: Path, what: str, *, item: Optional[int] = None,
         proof: Optional[str] = None, word: Optional[str] = None,
         now: Optional[datetime] = None) -> None:
    """A soft "journal → act" bridge: writes if there is somewhere to, silent if not.

    Three things it was written for:
    * address — ``#NN`` of the work, ``#NN.M`` for a per-item gesture;
    * a long proof neither breaks the verb nor gets lost: the full text goes as a
      FILE into the session's ``workspace/proofs/``, and the act gets the proof's
      first line plus the file path (the human's word 02.09: "one line, the long
      part as a file"). Proofs may no longer be clipped: the work journal became
      a view over the acts, and a clipping would be the only record;
    * ANY error is swallowed — the act is the gesture's display, not the gesture.
    """
    try:
        from .. import acts
        entry = acts.caller_session()
        if entry is None:
            return
        ref = acts.make_ref(Path(wdir).name, item)
        try:
            acts.write_act(entry, what, proof=proof, word=word, ref=ref, now=now)
        except ValueError:
            short = _spilled_proof(acts, entry, what, proof,
                                   word=word, ref=ref, now=now)
            if not short:
                return
            acts.write_act(entry, what, proof=short, word=word, ref=ref, now=now)
    except Exception:  # noqa: BLE001  an act must never break the verb
        return


def _spilled_proof(acts, entry: Path, what: str, proof: Optional[str], *,
                   word: Optional[str], ref: str,
                   now: Optional[datetime] = None) -> str:
    """A proof too long for an act: put it into a file, return "first line · path".

    Could not write the file (nowhere, permissions, disk) — fall back to a clip
    with "…": the start of a proof is worse than the whole, but better than a
    gesture with no trace.
    """
    try:
        f = acts.spill_proof(entry, proof, ref=ref, now=now)
        return acts.file_proof(what, proof, acts.proof_ref(entry, f),
                               word=word, ref=ref)
    except OSError:
        return acts.fit_proof(what, proof, word=word, ref=ref)


def _stamp(now: Optional[datetime]) -> str:
    return (now or datetime.now()).strftime(_STAMP_FMT)


def _is_continuation(line: str) -> bool:
    """An indented, non-empty line — the description of the item above it.

    Read leniently (any indent), written strictly (two spaces): a hand-edited
    passport shouldn't lose its details over a stray space.
    """
    return bool(line[:1].isspace() and line.strip())


def _item_end(lines: List[str], start: int) -> int:
    """End (exclusive) of the item block opened at *start* — its description."""
    end = start + 1
    while end < len(lines) and _is_continuation(lines[end]):
        end += 1
    return end


def item_blocks(text: str) -> List[Tuple[str, str, str]]:
    """Every checklist item as ``(state, title, description)``, in file order.

    State is ``" "``/``"x"``/``"?"``; the description is the indented block
    under the title (dedented, ``""`` when the item has none).
    """
    lines = text.splitlines()
    out = []
    for j, ln in enumerate(lines):
        m = _ITEM_RE.match(ln)
        if not m:
            continue
        tail = lines[j + 1:_item_end(lines, j)]
        out.append((m.group(1), m.group(2), "\n".join(t.strip() for t in tail)))
    return out


def all_items(text: str) -> List[Tuple[str, str]]:
    """Every checklist item as ``(state, title)`` — description left aside.

    File order IS the numbering every hand addresses items by (CLI, board,
    human) — proposals and fixes included, both sections read as one run, so
    "item 3" means the same line everywhere.
    """
    return [(st, title) for st, title, _ in item_blocks(text)]


def _count_items(lines: List[str]) -> int:
    """How many items sit in *lines* — what a new one lands after."""
    return sum(1 for ln in lines if _ITEM_RE.match(ln))


def _split_item(text: str) -> Tuple[str, List[str]]:
    """``"Title\\ndetails"`` → title + description lines (blanks dropped)."""
    parts = (text or "").split("\n")
    title = " ".join(parts[0].split())
    if not title:
        raise WorkError(
            "work: item without a title — the first line is the title, "
            "details below")
    return title, [" ".join(p.split()) for p in parts[1:] if p.strip()]


def _item_lines(state: str, text: str) -> List[str]:
    """One item as file lines: ``- [s] Title`` + its two-space description."""
    title, desc = _split_item(text)
    return ["- [{0}] {1}".format(state, title)] + ["  " + d for d in desc]


def items(text: str) -> List[Tuple[bool, str]]:
    """The AGREED checklist as ``(done, text)`` pairs, in file order.

    Proposed items (``- [?]``) are left out on purpose: an offer is not the
    plan, so it neither counts as progress nor holds review back.
    """
    return [(st == "x", t) for st, t in all_items(text) if st != PROPOSED]


def _mark_item(text: str, index: int, done: bool) -> Tuple[str, str]:
    """Set item *index* (1-based) to *done*; returns (new_text, item_text)."""
    lines = text.splitlines()
    n = 0
    for j, ln in enumerate(lines):
        m = _ITEM_RE.match(ln)
        if not m:
            continue
        n += 1
        if n != index:
            continue
        if m.group(1) == PROPOSED:
            raise WorkError(
                "work: item {0} is still an offer, waiting for the human's "
                "\"yes\" (not agreed yet — cannot be checked)".format(index))
        if (m.group(1) == "x") == done:
            state = "is already checked" if done else "is not checked anyway"
            raise WorkError("work: item {0} {1}".format(index, state))
        lines[j] = "- [{0}] {1}".format("x" if done else " ", m.group(2))
        return "\n".join(lines) + "\n", m.group(2)
    raise WorkError("work: no item {0} (the checklist has {1})".format(index, n))


# --- verbs -------------------------------------------------------------------

def new_work(
    root: Path,
    text: str,
    deadline: Optional[str] = None,
    for_project: Optional[str] = None,
    now: Optional[datetime] = None,
) -> Path:
    """Create ``works/NN-<slug>/work.md`` — mirrors the board's "create" form.

    The checklist is born EMPTY: the work's name is the H1, not its first step.
    The responsible thread and its step arrive from the
    authoring session if it sits in a thread — the work shows up in the
    thread's tab right away, not after the human's "yes".
    """
    title = " ".join((text or "").split())
    if not title:
        raise WorkError("work: empty work")
    if deadline and not _DEADLINE_RE.match(deadline):
        raise WorkError("work: bad deadline {0!r} (need YYYY-MM-DD)".format(deadline))
    wdir = works_dir(root)
    wdir.mkdir(parents=True, exist_ok=True)
    name = "{0}-{1}".format(numbering.next_num(wdir), _work_slug(title))
    d = wdir / name
    d.mkdir()
    stamp = (now or datetime.now()).strftime("%Y-%m-%d")
    body = (
        "# {t}\n\nkind: work\nproject: {p}\nstatus: open\ncreated: {c}\n{dl}"
        "\n## checklist\n"
    ).format(t=title, p=for_project or "", c=stamp,
             dl="deadline: {0}\n".format(deadline) if deadline else "")
    body, _ = _autostamp_thread(root, body, now, d)
    _io.atomic_write(d / "work.md", body)
    return d


# Candidate header: H1 "# NN-slug" and two fields. The body is everything below.
_CAND_META_RE = re.compile(r"^(from|dropped):\s")


def _candidate_gist(text: str) -> str:
    """A candidate's idea without the service header (H1 + ``from:``/``dropped:``).

    We cut by the KNOWN shape of a candidate file, not with a generic frontmatter
    parser: the candidate body is free prose, and its very first line often looks
    like a key ("engine mechanics: verb …"). The narrow rule will not eat it.
    """
    lines = text.splitlines()
    i = 1 if lines[:1] and lines[0].startswith("# ") else 0
    while i < len(lines) and (not lines[i].strip() or _CAND_META_RE.match(lines[i])):
        i += 1
    return "\n".join(lines[i:]).strip()


def new_work_from_candidate(
    root: Path,
    text: str,
    cand: str,
    deadline: Optional[str] = None,
    for_project: Optional[str] = None,
    now: Optional[datetime] = None,
) -> Tuple[Path, str]:
    """Birth a work FROM A CANDIDATE in one gesture: create + carry over + drop.

    The human's rule 01.08 — "no duplicates": a candidate that went into a work
    no longer belongs to the shelf. It used to be two independent gestures held
    together by the agent's memory alone: in one day ten were dropped after the
    fact, and until then the shelf duplicated the table. Here the link is
    mechanical — it cannot be forgotten, because it is one verb.

    The work's name comes FROM THE ARGUMENT, not from the candidate: a
    candidate slug is a long handle ("174-birth-of-work-from-candidate"), unfit
    as a work title (the norm is a 2–4 word name). The candidate's text lands
    as a DRAFT in ``## plan``: a draft, not an agreement. The work is born a
    plain ``open`` and goes through the whole plan → propose → human "yes"
    cycle like any other — birth from a candidate skips nothing.

    The candidate goes to ``candidates/__dropped__/`` the same way as the
    board's cross (:func:`tide.arc.curate.drop_candidate`) — off the shelf, but
    not off the disk. The link "born from candidate NN" lands as a passport
    field ``from-cand: NN`` (decision 38, 02.09) — NOT as an act: an act lives in
    the calling session's passport (:func:`tide.acts.caller_session`), and the
    board button `/work-from-cand` is pressed without a session — the act would
    simply never be born and the link would be lost silently. The field is set
    once, here, and no other verb touches it — like
    ``created:``.
    Returns ``(work_dir, candidate_stem)``.
    """
    # neighbouring domains — local import, the way _root and candidate._cmd_drop do it
    from .candidate import _resolve as _resolve_cand
    from .curate import drop_candidate

    cdir = paths.candidates_dir(root)
    cfile = _resolve_cand(cdir, cand)
    if cfile is None:
        raise WorkError(
            "work: no candidate {0!r} in {1}".format(cand, cdir))
    stem = cfile.stem
    gist = _candidate_gist(cfile.read_text(encoding="utf-8"))
    # create FIRST: a bad title or deadline must fail before the candidate
    # leaves the shelf — otherwise the gesture falls apart halfway
    d = new_work(root, text, deadline=deadline, for_project=for_project, now=now)
    num = stem.partition("-")[0]
    if num.isdigit():
        f, doc = _read(d)
        doc = _set_meta(doc, "from-cand", num)
        _io.atomic_write(f, doc)
    if gist:
        set_plan(root, d.name, gist, now=now)
    drop_candidate(root, stem)
    return d, stem


def _section(lines: List[str], title: str) -> Optional[Tuple[int, int]]:
    """``(head, end)`` line indices of section *title*; *end* is exclusive."""
    try:
        head = next(i for i, ln in enumerate(lines)
                    if ln.startswith("## " + title))
    except StopIteration:
        return None
    end = head + 1
    while end < len(lines) and not lines[end].startswith("## "):
        end += 1
    return head, end


def _require_live(wdir: Path, text: str) -> None:
    """Guard the verbs that write into a work: a closed one is reopened first."""
    if _status_of(text) == "done":
        raise WorkError(
            "work: {0} is closed — tide work reopen first".format(wdir.name))


def _review_ready(text: str) -> bool:
    """The review gate: every AGREED item checked AND no offer left standing.

    «Every» spans both sections — a fix is an item like any other, so an
    unchecked one in ``## fixes`` holds the gate exactly as an unchecked step in
    ``## checklist`` does.

    A standing ``- [?]`` means the plan itself is still open — the work waits
    for the human's word, not for a verdict.
    """
    its = items(text)
    return (bool(its) and all(done for done, _ in its)
            and not any(st == PROPOSED for st, _ in all_items(text)))


def _resync_status(
    text: str,
    now: Optional[datetime] = None,
    wdir: Optional[Path] = None,
) -> Tuple[str, Optional[str]]:
    """Re-hang the review gate after the checklist moved under it.

    One place for both directions: a checked last item (or a withdrawn last
    offer) closes the gate, an unchecked item (or a fresh offer agreed into the
    plan) re-opens it. ``done`` is never touched — that one is the human's.
    Returns ``(text, moved_to)``; *moved_to* is None when nothing moved.

    *wdir* — the act's address. The gate move is made by automation, but the
    event is no less real than a check: "the work is finished and waits for the
    human" is exactly what people watch the thread feed for. ``_resync_status``
    is called only by verbs that hold the work folder, so the address is always
    there.
    """
    st = _status_of(text)
    if st == "taken" and _review_ready(text):
        text = _set_status(text, "review")
        return _journal(text, "- {0} — all items checked → review, waiting "
                              "for the human to close".format(_stamp(now)),
                        wdir=wdir, what="all items checked → review, waiting "
                                        "for the human to close",
                        now=now), "review"
    if st == "review" and not _review_ready(text):
        text = _set_status(text, "taken")
        return _journal(text, "- {0} — checklist incomplete again → taken".format(
            _stamp(now)), wdir=wdir, what="checklist incomplete again → taken",
            now=now), "taken"
    return text, None


def set_plan(
    root: Path,
    key: str,
    text: str,
    now: Optional[datetime] = None,
) -> Tuple[str, bool, str]:
    """Put the plan (free text) into ``## plan`` — the agent's word, not a move.

    The section is created before ``## checklist`` when absent. The status is
    deliberately untouched: proposing a plan is not taking the work, and the
    "yes" stays with the human — but the thread (and its step) are set right
    here, before his "yes": otherwise the human is called to look at the plan
    in the thread's tab where the work is not yet. Returns
    ``(slug, replaced, owner)``.
    """
    body = (text or "").strip("\n").rstrip()
    if not body.strip():
        raise WorkError("work: empty plan — give the text")
    wdir = _find(root, key)
    f, doc = _read(wdir)
    _require_live(wdir, doc)
    lines = doc.splitlines()
    block = ["## plan", ""] + body.split("\n") + [""]
    found = _section(lines, PLAN_TITLE)
    if found:
        head, end = found
        lines = lines[:head] + block + lines[end:]
    else:
        at = _section(lines, CHECKLIST_TITLE)
        cut = at[0] if at else next(
            (i for i, ln in enumerate(lines) if ln.startswith("## ")), len(lines))
        lines = lines[:cut] + block + lines[cut:]
    doc = "\n".join(lines)
    if not doc.endswith("\n"):
        doc += "\n"
    doc = _journal(doc, "- {0} — plan {1} by the agent".format(
        _stamp(now), "updated" if found else "proposed"), wdir=wdir, now=now)
    doc, owner = _autostamp_thread(root, doc, now, wdir)
    _io.atomic_write(f, doc)
    return wdir.name, bool(found), owner


def _proposal_words(first: int, last: int, replaced: bool = False) -> str:
    """One wording for the print and the journal line — singular or a span."""
    one = first == last
    what = "item {0}".format(first) if one else "items {0}–{1}".format(first, last)
    waits = "waits" if one else "wait"
    head = ("offers replaced: " if replaced else "proposed ")
    return "{0}{1} ({2} for the human's \"yes\")".format(head, what, waits)


def _drop_proposals(lines: List[str]) -> List[str]:
    """Every ``- [?]`` item WITH its description gone; the rest untouched."""
    out: List[str] = []
    j = 0
    while j < len(lines):
        m = _ITEM_RE.match(lines[j])
        if m and m.group(1) == PROPOSED:
            j = _item_end(lines, j)
            continue
        out.append(lines[j])
        j += 1
    return out


def propose(
    root: Path,
    key: str,
    texts: List[str],
    replace: bool = False,
    now: Optional[datetime] = None,
) -> Tuple[str, int, int, bool, str]:
    """Append ``- [?]`` items to the checklist — an offer, not the plan.

    A ``\\n`` inside an item splits title from description (see the module
    docstring). With *replace* the standing offers are withdrawn first — the
    agent rethought the steps, and stale ``- [?]`` lines would only crowd the
    board; agreed ``- [ ]``/``- [x]`` items are never touched.

    Numbering is file-order (proposals included), so the journal names the very
    numbers the human sees on the board. ``check`` refuses these items until the
    human's "yes" turns them into ``- [ ]``. A work sitting in review comes back
    to taken: there is a fresh question on the table, so it is not waiting to be
    closed. The thread (and its step) are set here too if not yet set: the
    items go to the human for a "yes", and the thread's tab must already show
    them. Returns ``(slug, first, last, reopened, owner)``.
    """
    texts = [t for t in texts if t and t.strip()]
    if not texts:
        raise WorkError("work: empty offer — give the items")
    blocks = [_item_lines(PROPOSED, t) for t in texts]  # validates the titles
    wdir = _find(root, key)
    f, doc = _read(wdir)
    _require_live(wdir, doc)
    lines = doc.splitlines()
    if replace:
        lines = _drop_proposals(lines)
    found = _section(lines, CHECKLIST_TITLE)
    if not found:
        raise WorkError("work: passport has no ## checklist section")
    head, end = found
    at = end
    while at > head + 1 and not lines[at - 1].strip():
        at -= 1  # land right after the last item, before the section's blank tail
    # numbers are counted at the LANDING spot, not over the whole file: with a
    # ## fixes section below, an offer appended to the checklist takes number 5
    # and pushes the fixes down — that is the number the human will see
    first = _count_items(lines[:at]) + 1
    last = first + len(texts) - 1
    doc = "\n".join(lines[:at] + [ln for b in blocks for ln in b] + lines[at:])
    if not doc.endswith("\n"):
        doc += "\n"
    doc = _journal(doc, "- {0} — {1}".format(
        _stamp(now), _proposal_words(first, last, replace)), wdir=wdir, now=now)
    reopened = _status_of(doc) == "review"
    if reopened:
        doc = _set_status(doc, "taken")
        doc = _journal(doc, "- {0} — items proposed — the work is back in "
                            "progress (review → taken)".format(_stamp(now)),
                       wdir=wdir,
                       what="items proposed — the work is back in progress "
                            "(review → taken)", now=now)
    doc, owner = _autostamp_thread(root, doc, now, wdir)
    _io.atomic_write(f, doc)
    return wdir.name, first, last, reopened, owner


def _item_number(raw: str, key: str) -> int:
    """Parse an item number typed on the CLI, or refuse in tide's own words.

    The hints print a literal ``N`` for the number, and a person pastes the line
    before substituting. argparse's ``type=int`` would answer that with "invalid
    int value: 'N'" — the parser's voice, at the exact moment the message was
    trying to teach. So the number arrives as text and lands here.
    """
    s = (raw or "").strip()
    if s.isdigit() and int(s) > 0:
        return int(s)
    return _bad_number(s, key)


def _bad_number(s: str, key: str) -> int:
    raise WorkError(
        "work: {0!r} is not an item number — put a number in place of N "
        "(the first item is 1). Numbers are shown by tide work show {1}".format(s, key))


def _require_word(word: Optional[str], whose: str = "the human agrees",
                  *, kept: str = "", howto: str = "") -> str:
    """The human's word IS the agreement — no word, no gesture (as in ``close``).

    THE ONE place the requirement lives, so every caller — CLI, board, API — is
    refused with the same sentence. The CLI parsers deliberately do NOT mark
    ``--word`` argparse-required: these are the human's SIGNATURE
    gestures, met in a person's first hour, and argparse would answer them with
    "the following arguments are required: --word" — the parser's words, no hint
    of what to do next. Dropping ``required`` lets the miss reach this guard,
    which says what happened, *kept* — what stayed as it was — and *howto*, the
    command with the key already filled in. The refusal itself is unchanged: a
    blank or whitespace word is still no word.
    """
    w = (word or "").strip()
    if not w:
        raise WorkError('work: {0}{1} — call with --word "their word verbatim"{2}'.format(
            whose,
            ", {0}".format(kept) if kept else "",
            ". {0}".format(howto) if howto else ""))
    return w


def _proposed_block(lines: List[str], index: int) -> Tuple[int, int, str]:
    """``(start, end, title)`` of the PROPOSED item *index*; *end* is exclusive.

    Refuses an item that is no longer an offer — agreeing twice, or over a
    checked item, would silently rewrite what the human already signed.
    """
    n = 0
    for j, ln in enumerate(lines):
        m = _ITEM_RE.match(ln)
        if not m:
            continue
        n += 1
        if n != index:
            continue
        if m.group(1) != PROPOSED:
            raise WorkError(
                "work: item {0} is {1} — it is no longer an offer".format(
                    index, "checked" if m.group(1) == "x" else "agreed"))
        return j, _item_end(lines, j), m.group(2)
    raise WorkError("work: no item {0} (the checklist has {1})".format(index, n))


def _steps_words(nums: List[int]) -> str:
    """"item 2" / "items 2, 4" — the numbers the human sees on the board."""
    if len(nums) == 1:
        return "item {0}".format(nums[0])
    return "items {0}".format(", ".join(str(n) for n in nums))


def agree(
    root: Path,
    key: str,
    indexes: Optional[List[int]] = None,
    word: Optional[str] = None,
    now: Optional[datetime] = None,
) -> Tuple[str, List[int], bool, Optional[str]]:
    """``- [?]`` → ``- [ ]`` by the human's WORD — the "yes" as it is said.

    The "yes" used to be a board button; in a chat it is a word, and a word only
    counts when it is written down — so *word* is required and lands in the
    journal verbatim. Empty *indexes* means every standing offer (the "yes" came
    for the lot). Descriptions ride along untouched. Agreement is not progress:
    a fresh ``- [ ]`` is something still to do, so a work parked in review comes
    back to taken. Returns ``(slug, numbers, was_all, moved_to)``.
    """
    w = _require_word(
        word, kept="the items stay offers",
        howto='tide work agree {0} {1} --word "their word"; '
             'what is proposed — tide work show {0}'.format(
                 key, " ".join(str(n) for n in (indexes or [])) or "--all"))
    wdir = _find(root, key)
    f, doc = _read(wdir)
    _require_live(wdir, doc)
    lines = doc.splitlines()
    nums = sorted(set(indexes or []))
    every = not nums
    if every:
        nums = [i for i, (st, _) in enumerate(all_items(doc), 1) if st == PROPOSED]
        if not nums:
            raise WorkError(
                "work: no proposed items — nothing to agree")
    for n in nums:
        j, _, title = _proposed_block(lines, n)
        lines[j] = "- [ ] {0}".format(title)
    doc = "\n".join(lines)
    if not doc.endswith("\n"):
        doc += "\n"
    if every:
        doc = _journal(doc, "- {0} — offers confirmed by word: «{1}»".format(
            _stamp(now), w), wdir=wdir, what="offers confirmed", word=w,
            now=now)
    else:
        for n in nums:
            doc = _journal(doc, "- {0} — item {1} confirmed by word: «{2}»".format(
                _stamp(now), n, w), wdir=wdir, item=n,
                what="item {0} confirmed".format(n), word=w, now=now)
    doc, moved = _resync_status(doc, now, wdir)
    _io.atomic_write(f, doc)
    return wdir.name, nums, every, moved


def drop_proposed(
    root: Path,
    key: str,
    indexes: List[int],
    word: Optional[str] = None,
    now: Optional[datetime] = None,
) -> Tuple[str, List[int], Optional[str]]:
    """The other half of the answer: "no" to offer *N* — the item is gone.

    Removes the ``- [?]`` line WITH its description (a withdrawn offer leaves no
    orphan details) and journals the word that dropped it. Cut from the back so
    the numbers still ahead don't slide out from under us; the journal names the
    numbers the human saw. Dropping the LAST offer can finish a work whose items
    are all checked — the gate is re-hung here. Returns
    ``(slug, numbers, moved_to)``.
    """
    w = _require_word(
        word, "dropping an offer is the human's word too", kept="nothing dropped",
        howto='tide work agree {0} --drop {1} --word "their word"'.format(
            key, " ".join(str(n) for n in (indexes or [])) or "N"))
    nums = sorted(set(indexes or []))
    if not nums:
        raise WorkError("work: drop by number: --drop N (several allowed)")
    wdir = _find(root, key)
    f, doc = _read(wdir)
    _require_live(wdir, doc)
    lines = doc.splitlines()
    for n in reversed(nums):
        j, end, _ = _proposed_block(lines, n)
        lines = lines[:j] + lines[end:]
    doc = "\n".join(lines)
    if not doc.endswith("\n"):
        doc += "\n"
    for n in nums:
        doc = _journal(doc, "- {0} — item {1} dropped by word: «{2}»".format(
            _stamp(now), n, w), wdir=wdir, item=n,
            what="proposed item {0} dropped".format(n), word=w, now=now)
    # in the same order we cut — from the tail: otherwise the second shift drifts
    for n in reversed(nums):
        doc = _shift_refs(doc, n, now, wdir)
    doc, moved = _resync_status(doc, now, wdir)
    _io.atomic_write(f, doc)
    return wdir.name, nums, moved


def _shift_refs(text: str, removed: int, now: Optional[datetime] = None,
                wdir: Optional[Path] = None) -> str:
    """Fix up LIVE references to item numbers after item *removed* is dropped.

    An item number is the address of a line in the file, and dropping shifts
    everything below. There are exactly two live references to that address,
    and both are read RIGHT NOW: the ``at:`` cursor (the board underlines the
    item with it) and the acceptance lines in the journal (✓✓ is derived from
    them — see :func:`accepted_items`). Both get fixed, otherwise they would
    point at someone else's item: a false address is worse than a lost one.

    The other journal lines are narrative, not addresses: "item 3 ✓ "text""
    carries the item's own text and reads as history ("back then it was third").
    History is not rubbed out. For the same reason a dropped acceptance is not
    erased but muted with a note — the human's word stays in the file, it just
    stops being an address.
    """
    cur = re.search(r"^at:\s*(\d+)\s*$", text, re.M)
    if cur:
        n = int(cur.group(1))
        if n == removed:
            text = _set_meta(text, "at", "")
            text = _journal(text, "- {0} — cursor cleared: its item was dropped".format(
                _stamp(now)), wdir=wdir, now=now)
        elif n > removed:
            text = _set_meta(text, "at", str(n - 1))
            text = _journal(text, "- {0} — cursor moved to item {1} "
                                  "(numbers shifted)".format(_stamp(now), n - 1),
                            wdir=wdir, item=n - 1, now=now)
    lines = text.splitlines()
    found = _section(lines, JOURNAL_TITLE)
    if not found:
        return text
    for j in range(found[0], found[1]):
        m = _ACCEPT_ONE_RE.match(lines[j])
        if not m:
            continue
        n = int(m.group(1))
        if n == removed:
            lines[j] = lines[j].rstrip() + " (item dropped)"
        elif n > removed:
            lines[j] = re.sub(r"— item \d+ accepted by hand\s*$",
                              "— item {0} accepted by hand".format(n - 1), lines[j])
    return "\n".join(lines) + "\n"


def _agreed_block(lines: List[str], index: int) -> Tuple[int, int, str]:
    """``(start, end, title)`` of the AGREED and NOT checked item *index*.

    An offer and a checked item do not go here: each has its own answer, and
    neither is dropped with the gesture that edits the agreement (see
    :func:`drop_item`).
    """
    n = 0
    for j, ln in enumerate(lines):
        m = _ITEM_RE.match(ln)
        if not m:
            continue
        n += 1
        if n != index:
            continue
        if m.group(1) == PROPOSED:
            raise WorkError(
                "work: item {0} is still an offer, not an agreement; it is "
                "answered with \"no\": tide work agree <key> --drop {0} --word "
                "\"word\"".format(index))
        if m.group(1) == "x":
            raise WorkError(
                "work: item {0} is checked — dropping it would erase the done "
                "work with its proof; tide work uncheck {0} first".format(index))
        return j, _item_end(lines, j), m.group(2)
    raise WorkError("work: no item {0} (the checklist has {1})".format(index, n))


def drop_item(
    root: Path,
    key: str,
    index: int,
    word: Optional[str] = None,
    now: Optional[datetime] = None,
) -> Tuple[str, str, Optional[str]]:
    """Drop agreed item *index* — REQUIRES ``--word``.

    The agreement is signed by the human, and only he edits it: ``--word`` is
    how he asked to drop it. Before this verb there was NOTHING to drop a plain
    item with: ``agree --drop`` answers only a standing
    ``- [?]``, and ``checklist`` replaces the whole checklist with "agreed"
    items, i.e. bypasses the "yes" gate.

    The item leaves with its description (orphaned details help no one), live
    references to numbers are fixed up (:func:`_shift_refs`), and the last
    undone item, once gone, may close the gate — the status is re-hung right
    here. Returns ``(slug, title, moved_to)``.
    """
    w = _require_word(
        word, "only the human can drop an agreed item",
        kept="item {0} stays in place".format(index),
        howto='tide work drop {0} {1} --word "their word"'.format(key, index))
    if index < 1:
        raise WorkError("work: item numbers start at 1")
    wdir = _find(root, key)
    f, doc = _read(wdir)
    _require_live(wdir, doc)
    lines = doc.splitlines()
    j, end, title = _agreed_block(lines, index)
    doc = "\n".join(lines[:j] + lines[end:])
    if not doc.endswith("\n"):
        doc += "\n"
    doc = _journal(doc, "- {0} — item {1} «{2}» dropped by word: «{3}»".format(
        _stamp(now), index, title, w), wdir=wdir, item=index,
        what="item {0} «{1}» dropped".format(index, title), word=w, now=now)
    doc = _shift_refs(doc, index, now, wdir)
    doc, moved = _resync_status(doc, now, wdir)
    _io.atomic_write(f, doc)
    return wdir.name, title, moved


def set_checklist(
    root: Path,
    key: str,
    texts: List[str],
    force: bool = False,
    now: Optional[datetime] = None,
) -> str:
    """Replace the checklist with the AGREED items (gesture 1: lay out).

    A ``\\n`` inside an item splits title from description, as in ``propose``.
    Refuses when checked items exist (progress would be erased) unless *force*
    — the human's explicit word. Journals the agreement.
    """
    texts = [t for t in texts if t and t.strip()]
    if not texts:
        raise WorkError("work: empty checklist — give the items")
    blocks = [_item_lines(" ", t) for t in texts]  # validates the titles
    wdir = _find(root, key)
    f, text = _read(wdir)
    _require_live(wdir, text)
    if any(done for done, _ in items(text)) and not force:
        raise WorkError(
            "work: the checklist has checked items — replacing erases progress "
            "(--force only on the human's word)")
    lines = text.splitlines()
    found = _section(lines, CHECKLIST_TITLE)
    if not found:
        raise WorkError("work: passport has no ## checklist section")
    head, end = found
    block = ["## checklist"] + [ln for b in blocks for ln in b] + [""]
    text = "\n".join(lines[:head] + block + lines[end:])
    if not text.endswith("\n"):
        text += "\n"
    text = _journal(text, "- {0} — checklist agreed: {1} item(s)".format(
        _stamp(now), len(texts)), wdir=wdir,
        what="checklist agreed: {0} item(s)".format(len(texts)), now=now)
    _io.atomic_write(f, text)
    return wdir.name


def _fixes_anchor(lines: List[str]) -> int:
    """Where a fresh ``## fixes`` is born: after ``## checklist``, before the log.

    The section has one place in the file and the whole numbering leans on it —
    fixes come after the checklist, so their numbers continue it, and before the
    journal, which stays last (``_journal`` appends to the tail of the file).
    """
    checklist = _section(lines, CHECKLIST_TITLE)
    if checklist:
        return checklist[1]
    journal = _section(lines, JOURNAL_TITLE)
    if journal:
        return journal[0]
    return len(lines)


def _fix_words(first: int, last: int) -> str:
    """One wording for the print and the journal — singular or a span."""
    if first == last:
        return "fix {0} added".format(first)
    return "fixes {0}–{1} added".format(first, last)


def add_fixes(
    root: Path,
    key: str,
    texts: List[str],
    word: Optional[str] = None,
    now: Optional[datetime] = None,
) -> Tuple[str, int, int, bool]:
    """The human's afterthoughts at the gate → ``## fixes``, already agreed.

    He looked at the finished work and said "and this too" — that remark IS the
    agreement, so the items land as ``- [ ]`` straight away and *word* is
    required: without it there is nothing making them the plan, and a ``- [?]``
    would ask him to sign what he has just asked for.

    Numbers continue the checklist (see the module docstring): with four items
    above, the first fix is 5 — the journal names the numbers the board shows.
    A work parked in review comes back to taken; there is work on the table
    again, not a verdict. Returns ``(slug, first, last, reopened)``.
    """
    texts = [t for t in texts if t and t.strip()]
    if not texts:
        raise WorkError("work: empty fix — give the items")
    w = _require_word(
        word, "a fix carries the human's afterthought", kept="nothing added",
        howto='tide work fix {0} "what to finish" --word "their word"'.format(key))
    blocks = [_item_lines(" ", t) for t in texts]  # validates the titles
    wdir = _find(root, key)
    f, doc = _read(wdir)
    _require_live(wdir, doc)
    lines = doc.splitlines()
    body = [ln for b in blocks for ln in b]
    found = _section(lines, FIXES_TITLE)
    if found:
        head, end = found
        at = end
        while at > head + 1 and not lines[at - 1].strip():
            at -= 1  # after the last fix, before the section's blank tail
        tail = body
    else:
        at = _fixes_anchor(lines)
        gap = [""] if at and lines[at - 1].strip() else []
        tail = gap + ["## " + FIXES_TITLE] + body + [""]
    first = _count_items(lines[:at]) + 1
    last = first + len(texts) - 1
    doc = "\n".join(lines[:at] + tail + lines[at:])
    if not doc.endswith("\n"):
        doc += "\n"
    doc = _journal(doc, "- {0} — {1} by word: «{2}»".format(
        _stamp(now), _fix_words(first, last), w), wdir=wdir,
        what=_fix_words(first, last), word=w, now=now)
    reopened = _status_of(doc) == "review"
    if reopened:
        doc = _set_status(doc, "taken")
        doc = _journal(doc, "- {0} — a fix put it back in progress (review → taken)".format(
            _stamp(now)), wdir=wdir,
            what="a fix put it back in progress (review → taken)", now=now)
    _io.atomic_write(f, doc)
    return wdir.name, first, last, reopened


def _head_title(text: str) -> Tuple[int, str]:
    """``(line index, title)`` of the passport's H1 — the name the board shows."""
    for j, ln in enumerate(text.splitlines()):
        if ln.startswith("# "):
            return j, ln[2:].strip()
    raise WorkError("work: passport has no title — the first line is \"# …\"")


def _clip(text: str, limit: int) -> str:
    """Cut a title down to one journal line's worth."""
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "…"


def set_title(
    root: Path,
    key: str,
    title: str,
    word: Optional[str] = None,
    now: Optional[datetime] = None,
) -> Tuple[str, str, str, bool]:
    """Rewrite the H1 — REQUIRES the human's word, moves no status.

    The name is what the human signed up to, so the agent may only carry it over
    with the word that asked for the rename, and that word lands in the journal
    beside the old name — a renamed work still reads back. The dir slug is left
    alone: it is the address the board, the journal and every other hand already
    hold. A done work renames too (its history has to stay readable), and the
    caller says so out loud. Returns ``(slug, old, new, was_done)``.
    """
    new = " ".join((title or "").split())
    if not new:
        raise WorkError("work: empty title — give the work a name")
    w = _require_word(
        word, "the human renames a work", kept="the title stays as it was",
        howto='tide work title {0} "new title" --word "their word"'.format(key))
    wdir = _find(root, key)
    f, text = _read(wdir)
    j, old = _head_title(text)
    if new == old:
        raise WorkError("work: {0} is already named that".format(wdir.name))
    lines = text.splitlines()
    lines[j] = "# " + new
    text = "\n".join(lines)
    if not text.endswith("\n"):
        text += "\n"
    text = _journal(text, "- {0} — renamed by word: «{1}» (was: {2})".format(
        _stamp(now), w, _clip(old, _TITLE_IN_JOURNAL)), wdir=wdir,
        what="renamed (was: {0})".format(_clip(old, _TITLE_IN_JOURNAL)),
        word=w, now=now)
    _io.atomic_write(f, text)
    return wdir.name, old, new, _status_of(text) == "done"


def _set_meta(text: str, key: str, value: str, after: str = "created") -> str:
    """Set ``key: value`` in the passport meta; empty *value* removes the line.

    An existing key is rewritten in place; a new key lands right after *after*
    (``created:`` by default, i.e. the head of the meta block). Order inside the
    block is irrelevant to the parsers — every hand reads meta line-by-line by
    regex — but a human reads the file too, and ``step:`` right under ``thread:``
    says "the thread and its step" at a glance instead of making him hunt.
    """
    pat = re.compile(r"^{0}:\s*.*$".format(re.escape(key)), re.M)
    if not value:
        return re.sub(r"^{0}:\s*.*\n?".format(re.escape(key)), "", text,
                      count=1, flags=re.M)
    if pat.search(text):
        return pat.sub("{0}: {1}".format(key, value), text, count=1)
    anchor = after if re.search(r"^{0}: .*$".format(re.escape(after)), text, re.M) \
        else "created"
    return re.sub(r"^({0}: .*)$".format(re.escape(anchor)),
                  "\\g<0>\n{0}: {1}".format(key, value),
                  text, count=1, flags=re.M)


def resolve_caller_thread(work_root: Path) -> Optional[str]:
    """The thread of the session that invoked us, as an address — or None.

    Reads ``$CLAUDE_CODE_SESSION_ID`` → the session arc pinned to it IN THE
    CALLER's own project (which may differ from where the work lives). Returns
    the bare thread slug when the caller sits in the same project as the work,
    else the cross-project address ``<project>/<thread>``. None when there is no
    sid, the caller isn't a tide session, or nothing matches — then ``take``
    records no owner and the human attaches one on the board (fork "by hand").

    Public because ``arc.artifact`` stamps ``from-arc:`` off the same answer —
    one address for "where this came from", wherever it is asked.
    """
    import os
    sid = (os.environ.get("CLAUDE_CODE_SESSION_ID") or "").strip()
    if not sid:
        return None
    from .. import offload  # lazy: avoid an import cycle at module load
    origin = paths.find_tide_root()
    if origin is None:
        return None
    entry = offload.find_session_by_claude_id(origin, sid)
    if entry is None:
        return None
    try:
        thread = entry.parents[1].name  # …/NN-@thread/arcs/NN-session
    except IndexError:
        return None
    if origin.resolve() == Path(work_root).resolve():
        return thread
    return "{0}/{1}".format(origin.name, thread)


def thread_dir(root: Path, thread: str) -> Optional[Path]:
    """The thread's directory by the address on the card — in this project or a neighbour.

    ``thread:`` is either a bare slug (``26-@release``) or a cross-project
    address (see :func:`resolve_caller_thread`). A neighbouring project is
    looked up in the roster; no roster or no such thread — None, and the reader
    is simply left without a plan (no guessing).
    """
    ref = (thread or "").strip().rstrip("/")
    if not ref:
        return None
    project, _, tail = ref.rpartition("/")
    if project:
        from .candidate import _resolve_target_root
        try:
            root = _resolve_target_root(project)
        except Exception:  # no roster / no project — the address just doesn't resolve
            return None
    d = paths.arcs_dir(root)
    if not d.is_dir():
        return None
    want = _thread_key(tail)
    return next((p for p in sorted(d.iterdir())
                 if p.is_dir() and _thread_key(p.name) == want), None)


def plan_steps(root: Path, thread: str) -> List[Tuple[int, str, str]]:
    """Thread plan steps as ``(number, state, name)`` — empty when there is no plan.

    Reads ``<thread>/plan.md``, section ``## steps``. A step's name is what comes
    before the first ``|``: a step line carries three fields (name · what is done
    · result), and the first is what meets the human's eye.

    The ``## steps`` heading may be missing — half the live plans put the steps
    right under the header. Then the whole file is read: the step line shape
    (``- [x] N. …``) is narrow enough not to be confused with prose, and "no
    plan" on a six-step plan is exactly the screen lie all this was about.
    """
    d = thread_dir(root, thread)
    if d is None:
        return []
    plan = d / "plan.md"
    if not plan.is_file():
        return []
    try:
        lines = plan.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return []
    found = _section(lines, PLAN_STEPS_TITLE) or (0, len(lines))
    out = []
    for ln in lines[found[0]:found[1]]:
        m = _PLAN_STEP_RE.match(ln)
        if m:
            out.append((int(m.group(2)), m.group(1),
                        m.group(3).split("|")[0].strip()))
    return out


def current_plan_steps(root: Path, thread: str) -> List[int]:
    """Numbers of the thread plan's current steps — empty when nobody named one.

    Two live ways to say "we are here": the ``[>]`` mark on a step line and the
    prose heading ``## current step — 9 (…) and 10 (…)``. The mark is older, the
    heading is written by hand, and the release thread lives by it — reading only
    the mark, we said "step not set" where the human wrote it in plain text, and
    works were born without an address. The mark takes priority: it sits on the
    step line itself and is unambiguous.

    There may be SEVERAL steps (a fork runs in parallel) — the heading allows
    that explicitly, hence a list rather than one number.
    """
    marked = [n for n, st, _ in plan_steps(root, thread) if st == CURRENT_STEP]
    if marked:
        return marked
    d = thread_dir(root, thread)
    if d is None:
        return []
    plan = d / "plan.md"
    if not plan.is_file():
        return []
    try:
        text = plan.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    line = re.search(r"^##\s*current step\s*[—-]\s*(.+)$", text, re.M)
    if not line:
        return []
    known = {n for n, _, _ in plan_steps(root, thread)}
    return [int(n) for n in re.findall(r"\b(\d{1,3})\b", line.group(1))
            if int(n) in known]


def current_plan_step(root: Path, thread: str) -> Optional[int]:
    """The first of :func:`current_plan_steps` — or None when none is named.

    None is more honest than guessing "probably the first": the work then stays
    without an address, and that shows.
    """
    return next(iter(current_plan_steps(root, thread)), None)


def plan_step_title(root: Path, thread: str, step: int) -> str:
    """The name of step *step* in the thread plan — "" when it could not be read."""
    return next((t for n, _, t in plan_steps(root, thread) if n == step), "")


def _follow_step(
    root: Path,
    text: str,
    thread: str,
    now: Optional[datetime] = None,
    wdir: Optional[Path] = None,
) -> Tuple[str, Optional[int]]:
    """Re-read ``step:`` from the plan of thread *thread* — the step always follows the thread.

    The thread changed or arrived — the old step address refers to another plan,
    so the field is not topped up but RESET: read — a new number, not read —
    cleared. Each move is a journal line.
    """
    was = re.search(r"^step:\s*(\d+)\s*$", text, re.M)
    step = current_plan_step(root, thread) if thread else None
    if step is None:
        if not was:
            return text, None
        text = _set_meta(text, "step", "")
        return _journal(text, "- {0} — step cleared (not in the thread plan)".format(
            _stamp(now)), wdir=wdir, what="plan step cleared (not in the thread plan)",
            now=now), None
    if was and int(was.group(1)) == step:
        return text, step
    text = _set_meta(text, "step", str(step), after="thread")
    title = plan_step_title(root, thread, step)
    return _journal(text, "- {0} — plan step → {1}{2} (from the thread plan)".format(
        _stamp(now), step, " «{0}»".format(title) if title else ""), wdir=wdir,
        what="plan step → {0}{1} (from the thread plan)".format(
            step, " «{0}»".format(title) if title else ""),
        now=now), step


def _autostamp_thread(
    root: Path,
    text: str,
    now: Optional[datetime] = None,
    wdir: Optional[Path] = None,
) -> Tuple[str, str]:
    """Set the thread (and its step) from the authoring session if the card has none.

    Called by ``add``/``plan``/``propose`` — i.e. the work gets its address
    BEFORE the human's "yes", not after. An already set thread is
    left alone: explicit — the human's hand or ``take --thread`` — beats
    automation. Returns ``(text, owner)``; *owner* is empty when nothing was set.
    """
    if re.search(r"^thread:\s*\S", text, re.M):
        return text, ""
    owner = resolve_caller_thread(root)
    if not owner:
        return text, ""
    text = _set_meta(text, "thread", owner)
    text = _journal(text, "- {0} — responsible thread → {1} (authoring session)".format(
        _stamp(now), owner), wdir=wdir,
        what="responsible thread → {0} (authoring session)".format(owner), now=now)
    text, _ = _follow_step(root, text, owner, now, wdir)
    return text, owner


def set_thread(
    root: Path,
    key: str,
    thread: Optional[str],
    source: str = "the human's hand",
    now: Optional[datetime] = None,
) -> str:
    """Set/clear the responsible thread (``thread:``). Empty *thread* clears it.

    ``step:`` follows: a new thread has its own plan, and without a thread a step
    address is meaningless (see :func:`_follow_step`).
    """
    wdir = _find(root, key)
    f, text = _read(wdir)
    val = (thread or "").strip()
    text = _set_meta(text, "thread", val)
    line = ("- {0} — responsible thread → {1} ({2})".format(_stamp(now), val, source)
            if val else
            "- {0} — thread cleared ({1})".format(_stamp(now), source))
    text = _journal(text, line, wdir=wdir, now=now)
    text, _ = _follow_step(root, text, val, now, wdir)
    _io.atomic_write(f, text)
    return wdir.name


def set_step(
    root: Path,
    key: str,
    step: Optional[int],
    word: Optional[str] = None,
    now: Optional[datetime] = None,
) -> Tuple[str, Optional[int], str]:
    """Set/clear ``step:`` by hand — when auto-pickup stayed silent.

    A step lives only with a thread: without ``thread:`` the number has nothing to
    bind to, and the card would lie with an address in someone else's plan. The
    number is deliberately NOT checked against the plan — plans are edited on
    the go, and a work may target a step that is still being written; a check
    would be a gate where a note is needed.
    Returns ``(slug, step, title)``.
    """
    wdir = _find(root, key)
    f, text = _read(wdir)
    m = re.search(r"^thread:\s*(\S+)", text, re.M)
    if step is None:
        if not re.search(r"^step:\s*\S", text, re.M):
            raise WorkError("work: {0} — no step is set anyway".format(wdir.name))
        text = _set_meta(text, "step", "")
        text = _journal(text, "- {0} — step cleared{1}".format(
            _stamp(now), " by word: «{0}»".format(word.strip())
            if word and word.strip() else ""), wdir=wdir, what="plan step cleared",
            word=word, now=now)
        _io.atomic_write(f, text)
        return wdir.name, None, ""
    if step < 1:
        raise WorkError("work: plan steps start at 1")
    if not m:
        raise WorkError(
            "work: {0} has no thread — a step is an address IN THE THREAD PLAN; "
            "first tide work thread {0} --set <thread>".format(wdir.name))
    text = _set_meta(text, "step", str(step), after="thread")
    title = plan_step_title(root, m.group(1), step)
    text = _journal(text, "- {0} — plan step → {1}{2} (by hand)".format(
        _stamp(now), step, " «{0}»".format(title) if title else ""), wdir=wdir,
        what="plan step → {0}{1} (by hand)".format(
            step, " «{0}»".format(title) if title else ""), now=now)
    _io.atomic_write(f, text)
    return wdir.name, step, title


def take(
    root: Path,
    key: str,
    by: Optional[str] = None,
    word: Optional[str] = None,
    thread: Optional[str] = None,
    now: Optional[datetime] = None,
) -> Tuple[str, Optional[str]]:
    """open → taken: stamp ``taken-by``/``taken-at`` + owner thread + journal.

    The responsible thread is *thread* when given, else auto-resolved from the
    caller's session (fork "and auto"); None when unresolvable — and together
    with the thread its current step, ``step:``, is re-read. Usually by the time
    of ``take`` the thread is already set by ``add``/``plan``; here it is
    confirmed (and the step address refreshed: while the work was being agreed,
    the plan may have stepped on). Returns ``(slug, owner)`` so the caller can
    say which thread now owns the work.
    """
    wdir = _find(root, key)
    f, text = _read(wdir)
    st = _status_of(text)
    if st == "done":
        raise WorkError("work: {0} is closed — tide work reopen first".format(wdir.name))
    if st != "open":
        raise WorkError("work: {0} is already taken (status: {1})".format(wdir.name, st))
    text = _set_status(text, "taken")
    # taken-by/taken-at live right after status (the board parses them as meta)
    who = (by or "").strip() or "agent"
    at = (now or datetime.now()).strftime("%Y-%m-%dT%H:%M")
    text = re.sub(r"^(status: .*)$",
                  "\\1\ntaken-by: {0}\ntaken-at: {1}".format(who, at),
                  text, count=1, flags=re.M)
    owner = (thread or "").strip() or resolve_caller_thread(root)
    if owner:
        text = _set_meta(text, "thread", owner)
    note = " on the word: «{0}»".format(word.strip()) if word and word.strip() else ""
    tail = " · thread {0}".format(owner) if owner else ""
    text = _journal(text, "- {0} — taken ({1}){2}{3}".format(
        _stamp(now), who, note, tail), wdir=wdir,
        what="taken ({0}){1}".format(who, tail), word=word, now=now)
    if owner:
        text, _ = _follow_step(root, text, owner, now, wdir)
    _io.atomic_write(f, text)
    return wdir.name, owner


def dispatch(
    root: Path,
    key: str,
    to: str,
    now: Optional[datetime] = None,
) -> Tuple[str, str]:
    """The "builder dispatched" trace — a FACT in the journal, moves no status.

    Lesson of 01.08: the orchestrator took a work,
    reported to the human and wrote "with the worker" in its pulses — but never
    sent the worker a message. The work sat silent for three hours, the board
    showed a build that was not happening. The dispatch queue lived IN THE
    ORCHESTRATOR'S HEAD, with nothing to check it against: the only sign of
    life was the cursor, and that is set by the very worker that was never
    started.

    Hence the gesture: dispatched a builder — tell the file. The status
    deliberately does not move — "builder dispatched" is not a state of the
    work but an event that happened to it; the open→taken→review→done state
    machine stays exactly the same. For the same reason a repeated dispatch is
    not an error but one more line: workers get re-dispatched (crashed,
    replaced, a second one added), and each dispatch is a fact with its own
    time.

    Only onto a TAKEN work: a dispatch on open is a hole in the cycle (no plan
    yet, no "yes" from the human, nobody answers for the work), on review the
    build is over and waits for the hand, on done the work is closed. Returns
    ``(slug, who)``.
    """
    who = " ".join((to or "").split())
    if not who:
        raise WorkError(
            "work: who was dispatched? — nobody dispatched, status untouched; "
            'dispatch is called with --to "name". '
            'tide work dispatch {0} --to "builder name"'.format(key))
    wdir = _find(root, key)
    f, text = _read(wdir)
    st = _status_of(text)
    if st == "done":
        raise WorkError(
            "work: {0} is closed — tide work reopen first".format(wdir.name))
    if st != "taken":
        raise WorkError(
            "work: {0} is not in progress (status: {1}) — builders go to a TAKEN "
            "work: plan agreed, work taken, then dispatch".format(wdir.name, st))
    text = _journal(text, "- {0} — builder dispatched: {1}".format(
        _stamp(now), who), wdir=wdir, now=now)
    _io.atomic_write(f, text)
    return wdir.name, who


def _item_text(text: str, index: int) -> str:
    """Text of item *index* (from 1) — or WorkError if there is no such item."""
    n = 0
    for ln in text.splitlines():
        m = _ITEM_RE.match(ln)
        if not m:
            continue
        n += 1
        if n == index:
            return m.group(2)
    raise WorkError("work: no item {0} (the checklist has {1})".format(index, n))


def at(
    root: Path,
    key: str,
    index: Optional[int],
    now: Optional[datetime] = None,
) -> Tuple[str, str]:
    """The work cursor: `at: N` — WHICH ITEM the assignee is on right now.

    The only honest source for underlining the current item on the board.
    There was nothing to derive it from: the journal only knows
    "item N ✓" — the past, the last one finished; and the "first unchecked"
    heuristic already lied to the human — items are done out of order, and
    fixes come mixed in. So the cursor is not derived but SET by a gesture:
    started an item — say so.

    An empty *index* clears the cursor. The cursor is not a status: it gates
    nothing and blocks nothing, it is an "I am here" mark. It clears itself when
    its item is checked (see ``check``), and goes stale on the board together
    with the work: the board trusts `at:` only while the work is alive by its
    journal — a crashed agent will not lie with an underline for days.

    Returns ``(slug, item_text)``; *item_text* is empty when the cursor is cleared.
    """
    wdir = _find(root, key)
    f, text = _read(wdir)
    if index is None:
        if not re.search(r"^at:\s*.*$", text, re.M):
            raise WorkError("work: {0} — no cursor is set anyway".format(wdir.name))
        text = _set_meta(text, "at", "")
        text = _journal(text, "- {0} — cursor cleared".format(_stamp(now)),
                        wdir=wdir, now=now)
        _io.atomic_write(f, text)
        return wdir.name, ""
    if index < 1:
        raise WorkError("work: item numbers start at 1")
    item = _item_text(text, index)
    text = _set_meta(text, "at", str(index))
    text = _journal(text, "- {0} — cursor on item {1} «{2}»".format(
        _stamp(now), index, item), wdir=wdir, item=index, now=now)
    _io.atomic_write(f, text)
    return wdir.name, item


def check(
    root: Path,
    key: str,
    index: int,
    proof: str,
    now: Optional[datetime] = None,
) -> Tuple[str, bool]:
    """Mark item *index* with *proof*; auto taken → review when all are done.

    Returns ``(slug, reviewed)`` — *reviewed* is True when this check moved the
    work to review (all items done), so the caller can say it out loud.
    """
    if not (proof or "").strip():
        raise WorkError("work: a check without proof is no gesture — "
                        "give --proof \"what was done\"")
    wdir = _find(root, key)
    f, text = _read(wdir)
    st = _status_of(text)
    if st not in ("taken", "review"):
        raise WorkError(
            "work: {0} is not taken (status: {1}) — tide work take first".format(
                wdir.name, st))
    text, item_text = _mark_item(text, index, True)
    text = _journal(text, "- {0} — item {1} ✓ «{2}»: {3}".format(
        _stamp(now), index, item_text, proof.strip()), wdir=wdir, item=index,
        what="item {0} ✓ «{1}»".format(index, item_text), proof=proof, now=now)
    # the cursor clears itself when its item is closed (fix 15): keeping "I am
    # here" on a done item is a lie, and demanding a second gesture from the agent
    # guarantees it will be forgotten. A cursor on ANOTHER item is left alone:
    # there may be several workers, and this check does not cancel someone else's mark
    if re.search(r"^at:\s*{0}\s*$".format(index), text, re.M):
        text = _set_meta(text, "at", "")
    text, moved = _resync_status(text, now, wdir)
    _io.atomic_write(f, text)
    return wdir.name, moved == "review"


def uncheck(
    root: Path,
    key: str,
    index: int,
    reason: Optional[str] = None,
    now: Optional[datetime] = None,
) -> str:
    """Unmark item *index*; a review work honestly falls back to taken."""
    wdir = _find(root, key)
    f, text = _read(wdir)
    st = _status_of(text)
    if st not in ("taken", "review"):
        raise WorkError(
            "work: {0} is not taken (status: {1}) — tide work take first".format(
                wdir.name, st))
    text, item_text = _mark_item(text, index, False)
    why = ": {0}".format(reason.strip()) if reason and reason.strip() else ""
    text = _journal(text, "- {0} — item {1} unchecked «{2}»{3}".format(
        _stamp(now), index, item_text, why), wdir=wdir, item=index,
        what="item {0} unchecked «{1}»".format(index, item_text),
        proof=reason, now=now)
    text, _ = _resync_status(text, now, wdir)
    _io.atomic_write(f, text)
    return wdir.name


def close(root: Path, key: str, word: str,
          now: Optional[datetime] = None) -> Tuple[str, int]:
    """Any live status → done. The human's word is REQUIRED — it IS the gate.

    The same word ACCEPTS the work it closes: when anything is checked, the mass
    acceptance line lands right before the closing one, so every "done" gets
    its "accepted" in one gesture (the human doesn't tick a done work item by
    item to say he took it). Nothing checked — nothing to accept, no line.
    Returns ``(slug, accepted)`` — how many checked items that word took.
    """
    if not (word or "").strip():
        raise WorkError(
            "work: done is set by the human, {0} stays open — close only "
            'with --word "their word". tide work close {0} --word "their word"'.format(key))
    wdir = _find(root, key)
    f, text = _read(wdir)
    if _status_of(text) == "done":
        raise WorkError("work: {0} is already closed".format(wdir.name))
    accepted = sum(1 for done, _ in items(text) if done)
    text = _set_status(text, "done")
    if accepted:
        # acceptance is a gesture like any other: it lands both in the journal
        # and as an act, otherwise `show` only sees it for those who read the file
        text = _journal(text, "- {0} — {1}".format(_stamp(now), ACCEPT_ALL_LINE),
                        wdir=wdir, what=ACCEPT_ALL_LINE, now=now)
    text = _journal(text, "- {0} — closed on the human's word: «{1}»".format(
        _stamp(now), word.strip()), wdir=wdir,
        what="closed on the human's word", word=word, now=now)
    _io.atomic_write(f, text)
    return wdir.name, accepted


def reopen(root: Path, key: str, word: Optional[str] = None,
           now: Optional[datetime] = None) -> Tuple[str, str]:
    """done → back to a LIVE status by the passport. Acceptances are untouched:
    the journal is history, it is not rubbed out.

    Where exactly is read from the card, not stamped "open". A work with
    ``taken-by`` does not become nobody's because it was reopened: the assignee
    is still on it, and nobody unchecked anything — "open" would lie about both
    facts at once. Hence:
    ``taken-by`` set → taken, and if the checklist is closed too — straight to
    review (all done, the human just changed his mind about closing); no
    ``taken-by`` → open.

    The mass acceptance line stays where it was written; it just stops speaking
    for the checklist once the work is live again (see the module docstring).
    Returns ``(slug, status)`` — where the work went back to.
    """
    wdir = _find(root, key)
    f, text = _read(wdir)
    if _status_of(text) != "done":
        raise WorkError("work: {0} is open anyway".format(wdir.name))
    who = re.search(r"^taken-by:\s*(\S.*)$", text, re.M)
    note = " on the word: «{0}»".format(word.strip()) if word and word.strip() else ""
    if who:
        text = _set_status(text, "taken")
        text = _journal(text, "- {0} — reopened{1} → taken ({2})".format(
            _stamp(now), note, who.group(1).strip()), wdir=wdir, word=word,
            what="reopened → taken ({0})".format(who.group(1).strip()),
            now=now)
        text, _ = _resync_status(text, now, wdir)  # checklist closed → straight to review
    else:
        text = _set_status(text, "open")
        text = _journal(text, "- {0} — reopened{1}".format(_stamp(now), note),
                        wdir=wdir, what="reopened", word=word, now=now)
    _io.atomic_write(f, text)
    return wdir.name, _status_of(text)


# --- list / show -------------------------------------------------------------

def render_list(root: Path) -> str:
    """The works board as text: live first (deadline order), closed below."""
    wdir = works_dir(root)
    rows = []
    for p in sorted(wdir.iterdir()) if wdir.is_dir() else []:
        f = p / "work.md"
        if not p.is_dir() or not f.is_file():
            continue
        text = f.read_text(encoding="utf-8")
        title = next((ln[2:].strip() for ln in text.splitlines()
                      if ln.startswith("# ")), p.name)
        st = _status_of(text)
        its = items(text)
        props = sum(1 for s, _ in all_items(text) if s == PROPOSED)
        m = re.search(r"^deadline:\s*(\S+)", text, re.M)
        dl = m.group(1) if m else ""
        rows.append((st == "done", dl or "9999", p.name, st, its, dl, title, props))
    if not rows:
        return "tide: no works ({0})".format(wdir)
    rows.sort(key=lambda r: (r[0], r[1], r[2]))
    out = []
    for _, _, name, st, its, dl, title, props in rows:
        done_n = sum(1 for d, _ in its if d)
        out.append("{0:<34} {1:<7} {2}/{3}{4}{5}  {6}".format(
            name, st, done_n, len(its),
            "+{0}?".format(props) if props else "",
            "  due " + dl if dl else "", title))
    return "\n".join(out)


def _thread_key(ref: str) -> str:
    """A comparable key of a thread address: the tail of a cross-project address, no number.

    ``thread:`` on a card is either a bare thread slug or a neighbouring
    project's address (``<project>/<thread>``, see :func:`resolve_caller_thread`)
    — comparing the strings as they are would lose half the matches.
    """
    tail = (ref or "").strip().rstrip("/").rsplit("/", 1)[-1]
    return slug.entry_slug(tail) or tail


def thread_works(root: Path, thread: str,
                 live_only: bool = True) -> List[Dict[str, object]]:
    """Works the thread *thread* is responsible for — one record per card.

    Record: ``num``, ``slug`` (folder name), ``title`` (H1), ``status``,
    ``taken_by`` (who is on it, "" — nobody), ``done``/``total`` over the
    AGREED checklist (offers are not progress, see :func:`items`), ``at`` — the
    assignee's cursor (0 when not set) — and ``step``, the thread plan step
    number (0 when there is no address): by it the reader lays works out under
    their steps. Order is by folder name, i.e. by number: the reader sorts as it
    likes.

    ``taken_by`` rides next to the status because the reader (the handoff seed)
    needs to CROSS-CHECK them: a passport can be inconsistent, and trusting the
    status alone would lie to the receiving session.

    A broken card is skipped silently: the reader of this list (the handoff seed)
    must not fail because of one passport without ``status``.
    """
    want = _thread_key(thread)
    wdir = works_dir(root)
    out: List[Dict[str, object]] = []
    for p in sorted(wdir.iterdir()) if wdir.is_dir() else []:
        f = p / "work.md"
        if not p.is_dir() or not f.is_file():
            continue
        try:
            text = f.read_text(encoding="utf-8")
            st = _status_of(text)
        except (OSError, WorkError):
            continue
        m = re.search(r"^thread:\s*(\S+)", text, re.M)
        if not m or _thread_key(m.group(1)) != want:
            continue
        if live_only and st not in LIVE:
            continue
        its = items(text)
        cur = re.search(r"^at:\s*(\d+)\s*$", text, re.M)
        by = re.search(r"^taken-by:\s*(\S.*)$", text, re.M)
        stp = re.search(r"^step:\s*(\d+)\s*$", text, re.M)
        out.append({
            "num": p.name.partition("-")[0],
            "slug": p.name,
            "title": next((ln[2:].strip() for ln in text.splitlines()
                           if ln.startswith("# ")), p.name),
            "status": st,
            "taken_by": by.group(1).strip() if by else "",
            "done": sum(1 for d, _ in its if d),
            "total": len(its),
            "at": int(cur.group(1)) if cur else 0,
            "step": int(stp.group(1)) if stp else 0,
        })
    return out


def accepted_items(text: str, acts_lines: Optional[List[str]] = None) -> List[int]:
    """Numbers of the items the human has ACCEPTED, read off the journal.

    Two hands write acceptance, both as journal lines (see the module
    docstring): the board takes one item at a time, ``close`` takes everything
    checked with one word. The mass line is read only while the work is closed —
    it accepted the checklist as it stood at that moment, and after a ``reopen``
    the checklist moves on. Read inside ``## log`` alone: a passport's free
    text may well quote the same words without being a record of a gesture.

    *acts_lines* — the same gestures arriving as ACTS in a session passport (work
    66 item 1: the journal became a view over the acts). Acceptance is read from
    both places as a UNION, not "the new instead of the old": the board hand has
    no session and writes only to the file, ``close`` from a session writes both
    there and as an act — losing either would lie about acceptance in half the
    live works.
    """
    lines = text.splitlines()
    found = _section(lines, JOURNAL_TITLE)
    journal = (lines[found[0]:found[1]] if found else []) + list(acts_lines or [])
    nums = set()
    for ln in journal:
        m = _ACCEPT_ONE_RE.match(ln)
        if m:
            nums.add(int(m.group(1)))
    if (_status_of(text) == "done"
            and any(_ACCEPT_ALL_RE.match(ln) for ln in journal)):
        nums |= {i for i, (st, _) in enumerate(all_items(text), 1) if st == "x"}
    return sorted(nums)


def _mark_accepted(text: str, acts_lines: Optional[List[str]] = None) -> str:
    """Append ``✓✓`` to every checked-AND-accepted item — display only.

    The file keeps the plain ``- [x]`` line: acceptance is a journal fact, and
    rewriting the checklist for it would fork the format every other hand reads.
    An accepted item that was later unchecked wears no mark — the two facts are
    shown together or not at all.
    """
    nums = accepted_items(text, acts_lines)
    if not nums:
        return text
    lines = text.splitlines()
    n = 0
    for j, ln in enumerate(lines):
        m = _ITEM_RE.match(ln)
        if not m:
            continue
        n += 1
        if n in nums and m.group(1) == "x":
            lines[j] = "{0} {1}".format(ln.rstrip(), ACCEPTED_MARK)
    return "\n".join(lines)


# "- 2026-09-02 16:13 — …" and "- 2026-09-02T16:13:37 — …": the journal writes
# minutes, an act seconds, and they have to be read as one feed
_JRN_AT_RE = re.compile(
    r"^-\s+(\d{4}-\d{2}-\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?\s+—")


def _journal_at(line: str) -> Optional[datetime]:
    """Timestamp of a journal line — or None if it has none."""
    m = _JRN_AT_RE.match(line)
    if not m:
        return None
    d = [int(x) for x in m.group(1).split("-")]
    return datetime(d[0], d[1], d[2], int(m.group(2)), int(m.group(3)),
                    int(m.group(4) or 0))


def _journal_entries(text: str) -> List[Tuple[Optional[datetime], List[str]]]:
    """The file's ``## log`` as records: ``(stamp, lines)``, in file order.

    A record is a ``- …`` line plus everything indented under it: a check per the
    31.07 norm writes a short line for the human, a blank line and the technical
    details below, and splitting it while merging would show half a proof.
    """
    lines = text.splitlines()
    found = _section(lines, JOURNAL_TITLE)
    if not found:
        return []
    out: List[Tuple[Optional[datetime], List[str]]] = []
    for ln in lines[found[0] + 1:found[1]]:
        if ln.startswith("- "):
            out.append((_journal_at(ln), [ln]))
        elif out:
            out[-1][1].append(ln)
        elif ln.strip():
            out.append((None, [ln]))
    while out and not any(l.strip() for l in out[-1][1]):
        out.pop()
    return out


def work_acts(root: Path, wdir: Path, text: str) -> List[object]:
    """Acts of this work — all sessions of its thread, newest first; ``[]`` if no thread.

    The address is read off the card (``thread:``), the filter is the work
    number, so ``#66`` also brings the per-item ``#66.4``. Any trouble on the way
    (no roster, a broken session passport) — an empty list: the act view must
    never break ``show``.
    """
    try:
        from .. import acts

        m = re.search(r"^thread:\s*(\S+)", text, re.M)
        if not m:
            return []
        tdir = thread_dir(Path(root), m.group(1))
        if tdir is None:
            return []
        return acts.read_acts(tdir, ref=acts.make_ref(Path(wdir).name))
    except Exception:       # noqa: BLE001
        return []


def act_lines(rows: List[object]) -> List[str]:
    """Acts as journal lines, oldest first — the way the journal is read."""
    return ["- {0} — {1}".format(r.at.strftime(_STAMP_FMT), r.text)
            for r in reversed(rows)]


def journal_view(root: Path, wdir: Path, text: str,
                 rows: Optional[List[object]] = None) -> List[str]:
    """The work's ``## log`` as a VIEW over the acts of its thread's sessions.

    Merge: this work's **acts** plus those file lines that have no act twin. An
    old work has no acts and is read from the file entirely and forever; a new
    one is read from acts; a work that has both is not doubled.

    The sieve itself lives ONCE for everyone — :func:`tide.acts.sift_journal`;
    the board calls it too. What stays here is parsing our own line shape: this
    file's journal is written as ``- 2026-09-02 16:13 — text``, and the first
    line of a record is what the gesture is recognised by.

    Order is chronological, as in the file: the journal is read as the work's
    history.
    """
    entries = _journal_entries(text)
    rows = work_acts(root, wdir, text) if rows is None else rows
    if not rows:
        return [ln for _, block in entries for ln in block]
    from .. import acts
    prepared, last = [], datetime.min
    for i, (at, block) in enumerate(entries):
        last = at or last
        prepared.append((at, _journal_body(block[0]), (last, 0, i, block)))
    merged = list(acts.sift_journal(prepared, rows))
    for i, r in enumerate(reversed(rows)):       # oldest first, as in the file
        merged.append((r.at.replace(second=0, microsecond=0), 1, i,
                       ["- {0} — {1}".format(r.at.strftime(_STAMP_FMT), r.text)]))
    merged.sort(key=lambda x: (x[0], x[1], x[2]))
    return [ln for row in merged for ln in row[3]]


def _project_journal(root: Path, wdir: Path, text: str,
                     rows: Optional[List[object]] = None) -> str:
    """Replace the ``## log`` section in the text with its view over the acts."""
    view = journal_view(root, wdir, text, rows)
    lines = text.splitlines()
    found = _section(lines, JOURNAL_TITLE)
    if not view:
        return text
    head = ["## " + JOURNAL_TITLE]
    if not found:
        return "\n".join(lines + [""] + head + view) + "\n"
    return "\n".join(lines[:found[0]] + head + view + lines[found[1]:]) + "\n"


def show(root: Path, key: str) -> str:
    """The work.md as it is — plus the acceptance mark and the journal's view.

    Raw is nearly the whole rendering: ``## plan`` sits where it lives (after the
    description, before the checklist), a proposed item shows its own ``?`` and
    an item's description is already indented under its title. Two things are
    added. ``✓✓`` on an item that is both done and accepted — that second fact
    lives in the journal, and a reader shouldn't have to walk it line by line.
    And ``## log`` comes back as a VIEW (:func:`journal_view`): the work's
    acts from the sessions of its thread, plus the file's own older lines. The
    gesture is written in one place now, so the journal has to be read from it —
    the file's section stays where it is and keeps being written for the board.
    """
    wdir = _find(root, key)
    _, text = _read(wdir)
    rows = work_acts(root, wdir, text)
    return _mark_accepted(_project_journal(root, wdir, text, rows),
                          act_lines(rows)).rstrip("\n")


# --- CLI wiring --------------------------------------------------------------

def _root(args) -> Path:
    project = getattr(args, "project", None)
    if project:
        # same cross-project resolution as `candidate add --project`
        from .candidate import _resolve_target_root
        return _resolve_target_root(project)
    return paths.require_tide_root()


def _say_address(root: Path, name: str) -> None:
    """Where the work is headed: the thread and its plan step — right after the work is born."""
    text = (works_dir(root) / name / "work.md").read_text(encoding="utf-8")
    th = re.search(r"^thread:\s*(\S+)", text, re.M)
    if not th:
        return
    st = re.search(r"^step:\s*(\d+)\s*$", text, re.M)
    if not st:
        print("tide: thread {0} (from the authoring session)".format(th.group(1)))
        return
    title = plan_step_title(root, th.group(1), int(st.group(1)))
    print("tide: thread {0}, step {1}{2} (from the authoring session and its plan)".format(
        th.group(1), st.group(1), " «{0}»".format(title) if title else ""))


def _cmd_add(args) -> int:
    root = _root(args)
    if getattr(args, "cand", None):
        d, stem = new_work_from_candidate(
            root, " ".join(args.text), args.cand,
            deadline=args.deadline, for_project=args.for_project)
        print("tide: work created — {0}".format(d.name))
        print("tide: born from candidate {0} — it left the shelf for __dropped__ "
              "(recoverable), its text landed as a draft in ## plan".format(stem))
        _say_address(root, d.name)
        return 0
    d = new_work(root, " ".join(args.text),
                 deadline=args.deadline, for_project=args.for_project)
    print("tide: work created — {0}".format(d.name))
    print("tide: the checklist is empty — items are built in conversation: "
          "propose → the human's \"yes\" (the work's name is its title, not "
          "its first step)")
    _say_address(root, d.name)
    return 0


def _say_owner(name: str, owner: str) -> None:
    """Say out loud that the work got a thread: the human goes to look at its tab."""
    if owner:
        print("tide: {0} — responsible thread {1} (from the authoring session); "
              "the work shows in the thread's tab already".format(name, owner))


def _cmd_plan(args) -> int:
    # \n in a single shell argument is the practical way to pass a multi-line plan
    items_json = getattr(args, "items_json", None)
    if items_json:
        if args.text:
            raise WorkError("work: plan text or --items-json — one of the two")
        text = _plan_from_items_json(Path(items_json))
    elif not args.text:
        raise WorkError("work: plan — give the text or --items-json FILE")
    else:
        text = " ".join(args.text).replace("\\n", "\n")
    root = _root(args)
    name, replaced, owner = set_plan(root, args.key, text)
    if items_json:
        print(works_dir(root) / name / "work.md")  # machine output: the file path
        return 0
    print("tide: {0} — plan {1} (## plan); status untouched, the \"yes\" is the "
          "human's".format(name, "updated" if replaced else "proposed"))
    _say_owner(name, owner)
    return 0


def read_items_json(path: Path) -> List[Dict[str, object]]:
    """A JSON array ``{text, ref?, status?, done?}`` from the board → items.

    Shared parsing for ``work plan`` and ``agent-plan set-next``; errors are ValueError."""
    import json
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError("--items-json: cannot read {0} ({1})".format(path, exc)) from None
    except ValueError as exc:
        raise ValueError("--items-json: not JSON ({0})".format(exc)) from None
    if not isinstance(data, list):
        raise ValueError("--items-json: need a JSON array of objects")
    out: List[Dict[str, object]] = []
    for i, o in enumerate(data, 1):
        if not isinstance(o, dict):
            raise ValueError("--items-json: item {0} is not an object".format(i))
        text = o.get("text")
        if not isinstance(text, str) or not " ".join(text.split()):
            raise ValueError("--items-json: item {0} needs a non-empty text".format(i))
        ref, status, done = o.get("ref") or "", o.get("status") or "", o.get("done", False)
        if not isinstance(ref, str) or len(ref) > 80 or "\n" in ref:
            raise ValueError("--items-json: item {0} — ref must be a short string".format(i))
        if not isinstance(status, str):
            raise ValueError("--items-json: item {0} — status must be a string".format(i))
        if not isinstance(done, bool):
            raise ValueError("--items-json: item {0} — done must be true/false".format(i))
        out.append({"text": " ".join(text.split()), "ref": ref.strip(),
                    "status": " ".join(status.split()), "done": done})
    return out


def _plan_from_items_json(path: Path) -> str:
    """JSON items from the board → plan text as checkboxes "- [ ] text · link · status"."""
    try:
        its = read_items_json(path)
    except ValueError as exc:
        raise WorkError("work: " + str(exc)) from None
    if not its:
        raise WorkError("work: --items-json: empty array")
    return "\n".join("- [{0}] {1}{2}".format(
        "x" if it["done"] else " ", it["text"],
        "".join(" · " + str(it[k]) for k in ("ref", "status") if it.get(k))) for it in its)


def _unfold(texts: List[str]) -> List[str]:
    """``\\n`` typed in a shell argument becomes a real newline (as in `plan`)."""
    return [t.replace("\\n", "\n") for t in texts]


def _print_move(name: str, moved: Optional[str]) -> None:
    """Say a status move out loud — the gate must never move silently."""
    if moved == "review":
        print("tide: {0} — all items checked, no offers → review; done is set by "
              "the human — when they say the word, record it with tide work close "
              "--word (there is no board button: the board is a showcase)".format(name))
    elif moved == "taken":
        print("tide: {0} — something is undone → taken again (review lifted)".format(name))


def _cmd_propose(args) -> int:
    replace = getattr(args, "replace", False)
    name, first, last, reopened, owner = propose(_root(args), args.key,
                                                 _unfold(args.items),
                                                 replace=replace)
    print("tide: {0} — {1}".format(name, _proposal_words(first, last, replace)))
    print("tide: these are \"- [?]\" for now — they cannot be checked; they wait "
          "for the human's \"yes\" — record the word with tide work agree --word "
          "(the live board has a button too)")
    _say_owner(name, owner)
    if reopened:
        print("tide: {0} — the work is back in progress (review → taken): there "
              "is something to agree".format(name))
    return 0


def _cmd_agree(args) -> int:
    # two different answers of the human — "yes" and "no"; not mixed in one call
    if args.drop and (args.indexes or args.all):
        raise WorkError(
            "work: --drop is a separate gesture: drop first, then agree")
    if args.all and args.indexes:
        raise WorkError("work: --all or numbers — one or the other")
    if args.drop:
        name, nums, moved = drop_proposed(_root(args), args.key, args.drop,
                                          args.word)
        print("tide: {0} — dropped: {1} (the human's word is in the journal)".format(
            name, _steps_words(nums)))
        _print_move(name, moved)
        return 0
    name, nums, every, moved = agree(_root(args), args.key, args.indexes,
                                     args.word)
    print("tide: {0} — agreed: {1}{2}".format(
        name, _steps_words(nums), " (all offers)" if every else ""))
    print("tide: these are \"- [ ]\" now — they can be checked, but only with --proof")
    _print_move(name, moved)
    return 0


def _cmd_checklist(args) -> int:
    name = set_checklist(_root(args), args.key, _unfold(args.items),
                         force=args.force)
    print("tide: {0} — checklist agreed ({1} item(s))".format(
        name, len(args.items)))
    return 0


def _cmd_fix(args) -> int:
    name, first, last, reopened = add_fixes(_root(args), args.key,
                                            _unfold(args.items), args.word)
    print("tide: {0} — {1} (## fixes, agreed at once by the human's word)".format(
        name, _fix_words(first, last)))
    print("tide: numbering runs through — check them with --proof like other items")
    if reopened:
        print("tide: {0} — the work is back in progress (review → taken): there "
              "is something to finish".format(name))
    return 0


def _cmd_take(args) -> int:
    name, owner = take(_root(args), args.key, by=args.by, word=args.word,
                       thread=getattr(args, "thread", None))
    print("tide: {0} — taken (open → taken)".format(name))
    if owner:
        print("tide: responsible thread — {0}".format(owner))
    return 0


def _cmd_dispatch(args) -> int:
    name, who = dispatch(_root(args), args.key, args.to)
    print("tide: {0} — builder dispatched: {1} (trace in the journal; status "
          "untouched)".format(name, who))
    return 0


def _cmd_thread(args) -> int:
    val = "" if args.clear else (args.set or "")
    name = set_thread(_root(args), args.key, val, source="the human's hand (CLI)")
    print("tide: {0} — {1}".format(
        name, "thread cleared" if not val else "responsible thread → {0}".format(val)))
    return 0


def _cmd_step(args) -> int:
    if args.set is None and not args.clear:
        raise WorkError("work: give the step number (--set N) or --clear")
    name, step, title = set_step(_root(args), args.key,
                                 None if args.clear else args.set,
                                 word=getattr(args, "word", None))
    if step is None:
        print("tide: {0} — step cleared".format(name))
    else:
        print("tide: {0} — plan step {1}{2}".format(
            name, step, " «{0}»".format(title) if title else ""))
    return 0


def _cmd_drop(args) -> int:
    if args.index is None:
        raise WorkError(
            'work: nothing to drop — give the item number; put a number for N '
            'below, numbers are shown by tide work show {0}. Drop like this: '
            'tide work drop {0} N --word "their word"'.format(args.key))
    index = _item_number(args.index, args.key)
    name, title, moved = drop_item(_root(args), args.key, index, args.word)
    print("tide: {0} — item {1} «{2}» dropped (the human's word is in the journal)".format(
        name, index, title))
    print("tide: numbers below shifted by one — the cursor and acceptances moved "
          "along, the journal of past gestures is untouched")
    _print_move(name, moved)
    return 0


def _cmd_at(args) -> int:
    if args.index is None and not args.clear:
        raise WorkError("work: give the item number or --clear")
    name, item = at(_root(args), args.key,
                    None if args.clear else args.index)
    print("tide: {0} — {1}".format(
        name, "cursor cleared" if not item
        else "cursor on item {0} «{1}»".format(args.index, item)))
    return 0


def _cmd_check(args) -> int:
    if args.index is None:
        raise WorkError(
            'work: nothing to check — give the item number; put a number for N '
            'below, numbers are shown by tide work show {0}. Check like this: '
            'tide work check {0} N --proof "what was verified"'.format(args.key))
    index = _item_number(args.index, args.key)
    if not (args.proof or "").strip():
        raise WorkError(
            "work: a check without proof is no gesture — item {0} stays as it was. "
            "A proof is one line about what was actually verified (not \"done it\"): "
            "tide work check {1} {0} --proof \"what was verified\"".format(
                index, args.key))
    name, reviewed = check(_root(args), args.key, index, args.proof)
    print("tide: {0} — item {1} checked".format(name, index))
    _print_move(name, "review" if reviewed else None)
    return 0


def _cmd_uncheck(args) -> int:
    name = uncheck(_root(args), args.key, args.index, reason=args.reason)
    print("tide: {0} — item {1} unchecked".format(name, args.index))
    return 0


def _cmd_close(args) -> int:
    name, accepted = close(_root(args), args.key, args.word)
    print("tide: {0} — closed (the human's word is in the journal)".format(name))
    if accepted:
        print("tide: the same word accepted the done work — {0} item(s); in show "
              "they carry {1}".format(accepted, ACCEPTED_MARK))
    return 0


def _cmd_title(args) -> int:
    name, old, new, was_done = set_title(_root(args), args.key,
                                         " ".join(args.title), args.word)
    print("tide: {0} — renamed: «{1}» (was: «{2}»)".format(
        name, new, _clip(old, _TITLE_IN_JOURNAL)))
    if len(new) > TITLE_MAX:
        print("tide: the title is long ({0} chars) — a board card is read at "
              "a glance, shorter is better".format(len(new)))
    if was_done:
        print("tide: {0} is closed — renamed after the fact; in history it "
              "stays under its old name".format(name))
    return 0


def _cmd_reopen(args) -> int:
    name, st = reopen(_root(args), args.key, word=args.word)
    print("tide: {0} — reopened (status: {1})".format(name, st))
    return 0


def _cmd_list(args) -> int:
    print(render_list(_root(args)))
    return 0


def _cmd_show(args) -> int:
    root = _root(args)
    text = show(root, args.key)
    print(text)
    th = re.search(r"^thread:\s*(\S+)", text, re.M)
    st = re.search(r"^step:\s*(\d+)\s*$", text, re.M)
    if th and st:
        # the field carries a number, humans live by names: read the step name from the plan
        title = plan_step_title(root, th.group(1), int(st.group(1)))
        print("\ntide: headed to — thread {0}, step {1}{2}".format(
            th.group(1), st.group(1), " «{0}»".format(title) if title else ""))
    elif th:
        print("\ntide: headed to — thread {0}, step not set "
              "(tide work step {1} --set N)".format(th.group(1), args.key))
    if ACCEPTED_MARK in text:
        print("\ntide: {0} — item done AND accepted by the human; \"- [x]\" without "
              "the mark — done, not accepted yet".format(ACCEPTED_MARK))
    return 0


def register(subparsers) -> None:
    """Add the ``work`` command group to *subparsers* (called by cli.py)."""
    p = subparsers.add_parser(
        "work",
        help="works: add/plan/propose/agree/drop/fix/take/step/check/uncheck/"
             "close/reopen/title/list/show")
    wsub = p.add_subparsers(dest="work_cmd")

    def _common(sp):
        sp.add_argument(
            "--project",
            help="target ANOTHER rostered project's works (by roster name)")

    ap = wsub.add_parser("add", help="add a work (mirrors the board's form)")
    ap.add_argument("text", nargs="+", help="what to do — one line")
    ap.add_argument("--deadline", help="YYYY-MM-DD (one deadline per work)")
    ap.add_argument("--for", dest="for_project",
                    help="the 'project:' field — where the world changes")
    ap.add_argument("--cand", metavar="KEY",
                    help="born from a candidate (NN / NN-slug / slug): its text "
                         "lands as a draft in '## plan', the candidate leaves "
                         "the shelf for __dropped__; the work's name still comes "
                         "FROM THE ARGUMENT")
    _common(ap)
    ap.set_defaults(func=_cmd_add, _cmd="work add")

    pp = wsub.add_parser(
        "plan", help="propose the work's plan as text (the '## plan' section; "
                     "does not move status)")
    pp.add_argument("key")
    pp.add_argument("text", nargs="*",
                    help="the plan text; \\n in the argument is a line break")
    pp.add_argument("--items-json", metavar="FILE",
                    help="instead of text: JSON array {text, ref?, status?, done?} "
                         "→ plan as checkboxes")
    _common(pp)
    pp.set_defaults(func=_cmd_plan, _cmd="work plan")

    op = wsub.add_parser(
        "propose", help="propose checklist items as '- [?]' — they wait for the "
                        "human's yes")
    op.add_argument("key")
    op.add_argument("items", nargs="+",
                    help="items, one per argument; \\n inside an item ends the "
                         "title, the rest is the description")
    op.add_argument("--replace", action="store_true",
                    help="drop the previous '- [?]' and propose these (agreed "
                         "items are left alone)")
    _common(op)
    op.set_defaults(func=_cmd_propose, _cmd="work propose")

    gp = wsub.add_parser(
        "agree", help="the human's yes, in words: '- [?]' → '- [ ]' "
                      "(--drop is the no)")
    gp.add_argument("key")
    gp.add_argument("indexes", nargs="*", type=int, metavar="N",
                    help="item numbers; without them, every proposed item at once")
    gp.add_argument("--all", action="store_true",
                    help="explicitly: agree to every '- [?]'")
    gp.add_argument("--drop", nargs="+", type=int, metavar="N",
                    help="drop proposed items N (with their descriptions)")
    # NOT argparse-required on purpose: this is the human's SIGNATURE, and a
    # person meets it in their first hour. argparse would answer "the following
    # arguments are required: --word" — the parser's words, no hint of the next
    # gesture. The body says what happened, what stayed as it was, and what to
    # type. The refusal itself is unchanged.
    gp.add_argument("--word",
                    help="the human's word, verbatim (goes to the journal)")
    _common(gp)
    gp.set_defaults(func=_cmd_agree, _cmd="work agree")

    xp = wsub.add_parser(
        "drop", help="drop an AGREED item N — only with the human's word "
                     "(a proposed '- [?]' is dropped via agree --drop)")
    xp.add_argument("key")
    xp.add_argument("index", nargs="?", help="item number (from 1)")  # str: see check

    # NOT argparse-required on purpose: this is the human's SIGNATURE, and a
    # person meets it in their first hour. argparse would answer "the following
    # arguments are required: index, --word" — the parser's words, no hint of the next
    # gesture. The body says what happened, what stayed as it was, and what to
    # type. The refusal itself is unchanged.
    xp.add_argument("--word",
                    help="the human's word, verbatim (goes to the journal)")
    _common(xp)
    xp.set_defaults(func=_cmd_drop, _cmd="work drop")

    kp = wsub.add_parser(
        "checklist",
        help="gesture 1: replace the checklist with AGREED items (+journal)")
    kp.add_argument("key")
    kp.add_argument("items", nargs="+",
                    help="items, one per argument; \\n inside an item ends the "
                         "title, the rest is the description")
    kp.add_argument("--force", action="store_true",
                    help="replace despite checked items (the human's word)")
    _common(kp)
    kp.set_defaults(func=_cmd_checklist, _cmd="work checklist")

    fp = wsub.add_parser(
        "fix", help="what the human adds at acceptance: items into '## fixes', "
                    "agreed by their word right away")
    fp.add_argument("key")
    fp.add_argument("items", nargs="+",
                    help="items, one per argument; \\n inside an item ends the "
                         "title, the rest is the description")
    # NOT argparse-required on purpose: this is the human's SIGNATURE, and a
    # person meets it in their first hour. argparse would answer "the following
    # arguments are required: --word" — the parser's words, no hint of the next
    # gesture. The body says what happened, what stayed as it was, and what to
    # type. The refusal itself is unchanged.
    fp.add_argument("--word",
                    help="what the human added, verbatim (goes to the journal)")
    _common(fp)
    fp.set_defaults(func=_cmd_fix, _cmd="work fix")

    tp = wsub.add_parser("take", help="take the work: open → taken "
                                      "(+thread, +journal)")
    tp.add_argument("key", help="NN, NN-slug or the work's slug")
    tp.add_argument("--by", help="who takes it (into taken-by and the journal)")
    tp.add_argument("--word", help="the human's word you're taking it on")
    tp.add_argument("--thread", help="the owning thread, explicitly (otherwise "
                    "auto, from the calling session)")
    _common(tp)
    tp.set_defaults(func=_cmd_take, _cmd="work take")

    dp = wsub.add_parser(
        "dispatch", help="mark that a builder was sent out: a line in the "
                         "journal (status unchanged; call it again and you get "
                         "one more line)")
    dp.add_argument("key")
    # NOT argparse-required on purpose: this is the human's SIGNATURE, and a
    # person meets it in their first hour. argparse would answer "the following
    # arguments are required: --to" — the parser's words, no hint of the next
    # gesture. The body says what happened, what stayed as it was, and what to
    # type. The refusal itself is unchanged.
    dp.add_argument("--to", metavar="NAME",
                    help="who was sent out to build")
    _common(dp)
    dp.set_defaults(func=_cmd_dispatch, _cmd="work dispatch")

    hp = wsub.add_parser(
        "thread", help="the work's owning thread: attach / change / clear")
    hp.add_argument("key")
    hp.add_argument("--set", help="the thread's slug (NN-@slug) or an address "
                                  "proj/NN-@slug")
    hp.add_argument("--clear", action="store_true", help="clear the thread")
    _common(hp)
    hp.set_defaults(func=_cmd_thread, _cmd="work thread")

    stp = wsub.add_parser(
        "step", help="the thread's plan step this work heads for (usually "
                     "arrives with the thread — by hand only when it stayed "
                     "silent)")
    stp.add_argument("key")
    stp.add_argument("--set", type=int, metavar="N", help="step number (from 1)")
    stp.add_argument("--clear", action="store_true", help="clear the step")
    stp.add_argument("--word", help="the human's word, if they set the step "
                                    "(goes to the journal)")
    _common(stp)
    stp.set_defaults(func=_cmd_step, _cmd="work step")

    atp = wsub.add_parser(
        "at", help="cursor: which item the doer is on right now (the board "
                   "underlines it). Clears itself when the item is checked")
    atp.add_argument("key")
    atp.add_argument("index", type=int, nargs="?",
                     help="item number (from 1); without it, use --clear")
    atp.add_argument("--clear", action="store_true", help="clear the cursor")
    _common(atp)
    atp.set_defaults(func=_cmd_at, _cmd="work at")

    cp = wsub.add_parser(
        "check", help="check item N with proof (all checked → review on its own)")
    cp.add_argument("key")
    # index and --proof are NOT argparse-required, on purpose. A check without
    # proof is the single most common first-hour mistake, and argparse answers it
    # with "the following arguments are required: index, --proof" — the parser's
    # words, not tide's, and no hint of what to do next. Accepting them as missing
    # lets :func:`_cmd_check` say why the gesture exists and what to type.
    # Not type=int: a person pastes the hint before substituting, and argparse
    # answers "invalid int value: 'N'" — the parser's voice again, at the exact
    # moment the message was trying to teach. _cmd_check parses it and says what N is.
    cp.add_argument("index", nargs="?", help="item number (from 1)")
    cp.add_argument("--proof",
                    help="what exactly was done: a commit, a link, a file")
    _common(cp)
    cp.set_defaults(func=_cmd_check, _cmd="work check")

    up = wsub.add_parser("uncheck", help="uncheck item N (review → taken)")
    up.add_argument("key")
    up.add_argument("index", type=int)
    up.add_argument("--reason", help="why it was unchecked (goes to the journal)")
    _common(up)
    up.set_defaults(func=_cmd_uncheck, _cmd="work uncheck")

    dp = wsub.add_parser(
        "close", help="close it: done is set ONLY with the human's word (the "
                      "same word accepts everything done)")
    dp.add_argument("key")
    # NOT argparse-required on purpose: this is the human's SIGNATURE, and a
    # person meets it in their first hour. argparse would answer "the following
    # arguments are required: --word" — the parser's words, no hint of the next
    # gesture. The body says what happened, what stayed as it was, and what to
    # type. The refusal itself is unchanged.
    dp.add_argument("--word",
                    help="the human's word that closes and accepts it (goes to "
                         "the journal)")
    _common(dp)
    dp.set_defaults(func=_cmd_close, _cmd="work close")

    np = wsub.add_parser(
        "title", help="rename the work: the H1 changes ONLY with the human's word")
    np.add_argument("key")
    np.add_argument("title", nargs="+", help="the new title — short, one line")
    # NOT argparse-required on purpose: this is the human's SIGNATURE, and a
    # person meets it in their first hour. argparse would answer "the following
    # arguments are required: --word" — the parser's words, no hint of the next
    # gesture. The body says what happened, what stayed as it was, and what to
    # type. The refusal itself is unchanged.
    np.add_argument("--word",
                    help="the human's word, verbatim (goes to the journal)")
    _common(np)
    np.set_defaults(func=_cmd_title, _cmd="work title")

    rp = wsub.add_parser("reopen", help="open a closed work again: done → open")
    rp.add_argument("key")
    rp.add_argument("--word", help="the human's word (goes to the journal)")
    _common(rp)
    rp.set_defaults(func=_cmd_reopen, _cmd="work reopen")

    lp = wsub.add_parser("list", help="the works board as text (live + closed)")
    _common(lp)
    lp.set_defaults(func=_cmd_list, _cmd="work list")

    sp = wsub.add_parser("show", help="the work's card as it is (the file is "
                                      "the truth)")
    sp.add_argument("key")
    _common(sp)
    sp.set_defaults(func=_cmd_show, _cmd="work show")
