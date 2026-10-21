"""tide.arc.artifact — "artifacts": what the agent puts on the human's desk.

An artifact is an arc-kind entity: a dir ``NN-<slug>/`` under
``.tide/arcs/artifacts/`` holding an ``artifact.md`` passport — a caption saying
what the thing is AND what to do with it, the thing itself, and a journal. A
message to send, a command to run, a file to look at: things the agent used to
type into the chat, where they drowned three turns later (the owner's word: "a tool
for getting things to the user"). The live
board renders these as "take" cards on the ISSUES desk; the CLI verbs here
are the AGENT's side of the same files.

The machine is two states — **new → taken**:

* ``add``    — put a thing on the desk. Exactly one of ``--text`` / ``--cmd`` /
  ``--file`` / ``--ask`` carries the content AND decides the kind (message /
  command / file / question); ``--file`` stores the path as given, nothing is
  copied. A ``question`` is the agent's "I have stopped and await your word" — answered
  by WORD in the session, never by a button (decision 06). ``from-arc``
  is resolved from the calling session (same address as ``work take``), so the
  human can always ask where a thing came from, and ``--work NN`` ties it to
  the work it came out of (resolved against the works dir — a dangling number
  would be a silent lie).
* ``taken``  — the human took it: REQUIRES ``--word`` (his word verbatim, into
  the journal). Taking is HIS gesture, exactly like closing a work — the agent
  may only record it.
* ``reopen`` — back onto the desk (changed one's mind).
* ``list`` / ``show`` — the desk as text; the file IS the truth.

Every verb appends a ``## log`` line — nothing sinks silently. All logic is
plain functions (argparse-free); :func:`register` wires the thin handlers.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from .. import io as _io, numbering, paths, slug
from . import stream

ARTIFACTS_DIRNAME = "artifacts"
_STAMP_FMT = "%Y-%m-%d %H:%M"
# created: carries the minute — a desk is read by "what is fresh here"
_CREATED_FMT = "%Y-%m-%dT%H:%M"
_STATUS_RE = re.compile(r"^status: .*$", re.M)
CONTENT_TITLE = "content"
NEW = "new"
TAKEN = "taken"
# the flag that carried the content also names the kind — one gesture, no --kind
# ``ask`` — the agent's QUESTION to the human. Waiting for a word
# was the one thing the agent could not put on the desk: it wrote the question in
# the chat and froze, and the human only found out by entering the session. A
# question is the same thing on the desk as a message or a command: it has a parent
# thread, it waits for a hand and leaves the desk once the human has answered. THE
# ANSWER STILL COMES AS A WORD IN THE SESSION (decision 06): the card is not an input
# field but a call and the road to it.
KIND_BY_SOURCE = (("text", "message"), ("cmd", "command"), ("file", "file"),
                  ("ask", "question"))
KINDS = tuple(kind for _, kind in KIND_BY_SOURCE)
# a card is read at a glance on the desk — longer is a warning, not a bar
CAPTION_MAX = 80


class ArtifactError(stream.StreamError):
    """A user-facing artifacts error (no content, unknown key, missing word …)."""


# --- paths / parsing ---------------------------------------------------------

def artifacts_dir(root: Path) -> Path:
    """``<project>/.tide/arcs/artifacts`` — the desk lives beside the works."""
    return paths.arcs_dir(root) / ARTIFACTS_DIRNAME


def _find(root: Path, key: str) -> Path:
    """Resolve an artifact dir by NN, NN-slug or slug; fail loud on 0 or 2+ hits."""
    adir = artifacts_dir(root)
    key = (key or "").strip().rstrip("/")
    if not key:
        raise ArtifactError("artifact: empty key")
    hits = []
    for p in sorted(adir.iterdir()) if adir.is_dir() else []:
        if not p.is_dir() or not (p / "artifact.md").is_file():
            continue
        num, _, rest = p.name.partition("-")
        if key in (p.name, num, rest):
            hits.append(p)
    if not hits:
        raise ArtifactError(
            "artifact: no artifact {0!r} in {1}".format(key, adir))
    if len(hits) > 1:
        raise ArtifactError(
            "artifact: key {0!r} is ambiguous: {1}".format(
                key, ", ".join(p.name for p in hits)))
    return hits[0]


def _read(adir: Path) -> Tuple[Path, str]:
    f = adir / "artifact.md"
    return f, f.read_text(encoding="utf-8")


def _status_of(text: str) -> str:
    m = re.search(r"^status:\s*(\S+)", text, re.M)
    if not m:
        raise ArtifactError("artifact: passport has no status field")
    return m.group(1)


def _set_status(text: str, new: str) -> str:
    return _STATUS_RE.sub("status: " + new, text, count=1)


def _journal(text: str, line: str) -> str:
    """Append a journal line, creating the (always-last) section when absent."""
    if re.search(r"^## log", text, re.M):
        return text.rstrip("\n") + "\n" + line + "\n"
    return text.rstrip("\n") + "\n\n## log\n" + line + "\n"


def _stamp(now: Optional[datetime]) -> str:
    return (now or datetime.now()).strftime(_STAMP_FMT)


def _head_caption(text: str) -> str:
    """The H1 — the caption the desk shows."""
    for ln in text.splitlines():
        if ln.startswith("# "):
            return ln[2:].strip()
    return ""


def content_of(text: str) -> str:
    """The ``## content`` body — the thing itself, as it was handed over."""
    lines = text.splitlines()
    try:
        head = next(i for i, ln in enumerate(lines)
                    if ln.startswith("## " + CONTENT_TITLE))
    except StopIteration:
        return ""
    end = head + 1
    while end < len(lines) and not lines[end].startswith("## "):
        end += 1
    return "\n".join(lines[head + 1:end]).strip("\n")


# --- verbs -------------------------------------------------------------------

def _caller_arc(root: Path) -> str:
    """The thread that put the thing on the desk — ``""`` when unresolvable.

    Same resolution as ``work take``: the session arc pinned to
    ``$CLAUDE_CODE_SESSION_ID``, as a bare thread slug at home and a
    ``<project>/<thread>`` address across projects. Imported lazily so the two
    entity modules stay independent at load time.
    """
    from .work import resolve_caller_thread

    return resolve_caller_thread(root) or ""


def _resolve_work(root: Path, key: Optional[str]) -> str:
    """The NN of the work an artifact came out of — resolved, not taken on trust.

    A number that names no work would point the human at nothing, so the key is
    looked up in the works dir and only its NN is stored (that is the address
    the board, the journal and the human already use).
    """
    key = (key or "").strip()
    if not key:
        return ""
    from .work import _find as _find_work

    return _find_work(root, key).name.partition("-")[0]


def new_artifact(
    root: Path,
    caption: str,
    kind: str,
    content: str,
    work: Optional[str] = None,
    from_arc: Optional[str] = None,
    now: Optional[datetime] = None,
) -> Path:
    """Create ``artifacts/NN-<slug>/artifact.md`` — a thing on the human's desk.

    *from_arc* defaults to the calling session's thread; pass ``""`` to record
    none. Returns the artifact dir.
    """
    title = " ".join((caption or "").split())
    if not title:
        raise ArtifactError(
            "artifact: empty caption — say what it is and what to do with it")
    body = (content or "").strip()
    if not body:
        raise ArtifactError("artifact: empty content — nothing to hand over")
    if kind not in KINDS:
        raise ArtifactError("artifact: unknown kind {0!r} (known: {1})".format(
            kind, ", ".join(KINDS)))
    origin = _caller_arc(root) if from_arc is None else from_arc.strip()
    num = _resolve_work(root, work)
    adir = artifacts_dir(root)
    adir.mkdir(parents=True, exist_ok=True)
    name = "{0}-{1}".format(numbering.next_num(adir),
                            slug.short_slug(title) or "artifact")
    d = adir / name
    d.mkdir()
    text = (
        "# {t}\n\nkind: {k}\nstatus: {s}\ncreated: {c}\nfrom-arc: {a}\n{w}"
        "\n## {sec}\n{body}\n"
    ).format(t=title, k=kind, s=NEW, c=(now or datetime.now()).strftime(_CREATED_FMT),
             a=origin, w="work: {0}\n".format(num) if num else "",
             sec=CONTENT_TITLE, body=body)
    text = _journal(text, "- {0} — handed over by the agent{1}".format(
        _stamp(now), " ({0})".format(origin) if origin else ""))
    _io.atomic_write(d / "artifact.md", text)
    return d


def mark_taken(
    root: Path,
    key: str,
    word: str,
    now: Optional[datetime] = None,
) -> Tuple[str, str]:
    """new → taken. The human's word is REQUIRED — the taking is HIS gesture.

    Returns ``(slug, caption)`` so the caller can name what left the desk.
    """
    if not (word or "").strip():
        raise ArtifactError(
            "artifact: only the human takes it — call with --word \"their word verbatim\"")
    adir = _find(root, key)
    f, text = _read(adir)
    if _status_of(text) == TAKEN:
        raise ArtifactError("artifact: {0} is already taken".format(adir.name))
    text = _set_status(text, TAKEN)
    text = _journal(text, "- {0} — taken with the word: \"{1}\"".format(
        _stamp(now), word.strip()))
    _io.atomic_write(f, text)
    return adir.name, _head_caption(text)


def reopen(
    root: Path,
    key: str,
    word: Optional[str] = None,
    now: Optional[datetime] = None,
) -> str:
    """taken → new: back onto the desk (changed one's mind)."""
    adir = _find(root, key)
    f, text = _read(adir)
    if _status_of(text) != TAKEN:
        raise ArtifactError("artifact: {0} is already on the desk".format(adir.name))
    text = _set_status(text, NEW)
    note = " by the word: \"{0}\"".format(word.strip()) if word and word.strip() else ""
    text = _journal(text, "- {0} — back on the desk{1}".format(_stamp(now), note))
    _io.atomic_write(f, text)
    return adir.name


# --- list / show -------------------------------------------------------------

def render_list(root: Path) -> str:
    """The desk as text: live artifacts newest first, taken ones counted below.

    Newest on top — the freshest thing is the one the human is most likely
    waiting on, and that is the order the board already reads in.
    """
    adir = artifacts_dir(root)
    live: List[Tuple[str, str, str]] = []
    taken = 0
    for p in sorted(adir.iterdir(), reverse=True) if adir.is_dir() else []:
        f = p / "artifact.md"
        if not p.is_dir() or not f.is_file():
            continue
        text = f.read_text(encoding="utf-8")
        if _status_of(text) == TAKEN:
            taken += 1
            continue
        m = re.search(r"^kind:\s*(\S+)", text, re.M)
        live.append((p.name, m.group(1) if m else "?",
                     _head_caption(text) or p.name))
    if not live and not taken:
        return "tide: no artifacts ({0})".format(adir)
    out = ["{0:<30} {1:<8} {2}".format(name, kind, caption)
           for name, kind, caption in live]
    if not live:
        out.append("tide: the desk is empty — everything taken")
    if taken:
        out.append("taken: {0}".format(taken))
    return "\n".join(out)


def show(root: Path, key: str) -> str:
    """The raw artifact.md — the file IS the truth."""
    _, text = _read(_find(root, key))
    return text.rstrip("\n")


# --- CLI wiring --------------------------------------------------------------

def _root(args) -> Path:
    project = getattr(args, "project", None)
    if project:
        # same cross-project resolution as `candidate add --project`
        from .candidate import _resolve_target_root
        return _resolve_target_root(project)
    return paths.require_tide_root()


def _source(args) -> Tuple[str, str]:
    """``(kind, content)`` from the one flag that was given — or a loud refusal.

    The flag IS the kind, so there is nothing to keep in sync; ``\\n`` typed in
    a ``--text`` argument becomes a real newline (as in ``work plan``), while a
    command and a path are taken byte for byte — a literal ``\\n`` inside them
    is theirs, not ours.
    """
    given = [(flag, kind, getattr(args, flag))
             for flag, kind in KIND_BY_SOURCE if getattr(args, flag) is not None]
    if not given:
        raise ArtifactError(
            "artifact: what are you handing over — --text \"message\", --cmd \"command\", "
            "--file <path> or --ask \"question\"")
    if len(given) > 1:
        raise ArtifactError(
            "artifact: exactly one source: --text | --cmd | --file | --ask "
            "(given: {0})".format(
                ", ".join("--" + flag for flag, _, _ in given)))
    flag, kind, value = given[0]
    # line breaks are expanded for prose (message, question); a command and a path
    # are taken byte for byte — a literal \\n inside them is theirs
    return kind, (value.replace("\\n", "\n")
                  if flag in ("text", "ask") else value)


def _cmd_add(args) -> int:
    root = _root(args)
    kind, content = _source(args)
    d = new_artifact(root, " ".join(args.caption), kind, content,
                     work=getattr(args, "work", None))
    print("tide: artifact on the desk — {0} ({1})".format(d.name, kind))
    num = d.name.partition("-")[0]
    if kind == "question":
        # a question is closed not by "taken" but by an ANSWER in the session (decision 06):
        # the hint must not send the human to press a button instead of talking
        print("tide: the human answers with a word in the session; the card leaves the desk "
              "with the gesture: tide artifact taken {0} --word \"their answer\"".format(num))
    else:
        print("tide: the human takes it — their gesture: tide artifact taken {0} "
              "--word \"their word\"".format(num))
    if kind == "file" and not Path(content.strip()).expanduser().exists():
        print("tide: no file at this path — the human will open nothing ({0})"
              .format(content.strip()))
    if len(" ".join(args.caption)) > CAPTION_MAX:
        print("tide: long caption — a card on the desk is read at a "
              "glance, shorter is better")
    return 0


def _cmd_taken(args) -> int:
    name, caption = mark_taken(_root(args), args.key, args.word)
    print("tide: {0} — taken (the human's word is in the log): {1}".format(name, caption))
    return 0


def _cmd_reopen(args) -> int:
    name = reopen(_root(args), args.key, word=args.word)
    print("tide: {0} — back on the desk".format(name))
    return 0


def _cmd_list(args) -> int:
    print(render_list(_root(args)))
    return 0


def _cmd_show(args) -> int:
    print(show(_root(args), args.key))
    return 0


def register(subparsers) -> None:
    """Add the ``artifact`` command group to *subparsers* (called by cli.py)."""
    p = subparsers.add_parser(
        "artifact", help="artifacts: what the agent puts on the human's table — "
                         "add/list/show/taken/reopen")
    asub = p.add_subparsers(dest="artifact_cmd")

    def _common(sp):
        sp.add_argument(
            "--project",
            help="target ANOTHER rostered project's artifacts (by roster name)")

    ap = asub.add_parser(
        "add", help="put a thing on the table: a message, a command or a file")
    ap.add_argument("caption", nargs="+",
                    help="the caption — what it is and what to do with it")
    ap.add_argument("--text", help="the message text; \\n in the argument is a "
                                   "line break")
    ap.add_argument("--cmd", help="a command to run, as is")
    ap.add_argument("--file", dest="file", help="a path to a file, as is")
    ap.add_argument("--ask", help="a question for the human: the agent has "
                                  "stopped and waits for a word (answered in "
                                  "the session, not with a button)")
    ap.add_argument("--work", help="NN of the work this thing came out of")
    _common(ap)
    ap.set_defaults(func=_cmd_add, _cmd="artifact add")

    tp = asub.add_parser(
        "taken", help="taken off the table: new → taken, ONLY with the human's word")
    tp.add_argument("key", help="NN, NN-slug or the artifact's slug")
    tp.add_argument("--word", required=True,
                    help="the human's word, verbatim (goes to the journal)")
    _common(tp)
    tp.set_defaults(func=_cmd_taken, _cmd="artifact taken")

    rp = asub.add_parser("reopen", help="put it back on the table: taken → new")
    rp.add_argument("key")
    rp.add_argument("--word", help="the human's word (goes to the journal)")
    _common(rp)
    rp.set_defaults(func=_cmd_reopen, _cmd="artifact reopen")

    lp = asub.add_parser("list", help="the table as text: live ones in full, "
                                      "taken ones as a count")
    _common(lp)
    lp.set_defaults(func=_cmd_list, _cmd="artifact list")

    sp = asub.add_parser("show", help="the artifact's card as it is (the file "
                                      "is the truth)")
    sp.add_argument("key")
    _common(sp)
    sp.set_defaults(func=_cmd_show, _cmd="artifact show")
