"""tide.arc.thread_layers — the three thread layers at session exit.

The ``## where we are`` layers of a thread's goal file — "human expectation",
"where we are", "experience" — are the main entry point into a thread: without them
the "human expectation" block is empty whatever the seed builder does.
Old-style threads have no layer scaffold at all.

* :func:`empty_layers` / :func:`exit_warning` — which layers are empty; a warning,
  NOT a block: a thread with empty layers is still better handed off than stuck.
* :func:`write_layers` / ``tide thread layer <thread> --expect … --where … --exp …`` —
  write the layers with a command instead of editing the file by hand.
* :func:`write_main` / ``tide thread layer <thread> --main "task · whom to deliver to ·
  whom not to duplicate" [--replace]`` — the "read first" section in the thread's
  ``plan.md`` (read by the seed builder via :mod:`tide.arc.plan_main`).
* :func:`seed_skeleton` — seeds an empty scaffold of the missing layers into an old
  thread's goal file, touching nothing else (``tide thread layers --seed-skeleton <thread>``).
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .. import fields, handoff_contract as contract, io as _io, \
    name_dots as _name_dots, paths, resolve
from . import plan_main as _plan_main, stream as _stream
from .stream import StreamError

WHERE_HEAD = "## where we are"


class LayersError(StreamError):
    """No such thread / not a thread."""


def _where_span(lines: List[str]) -> "tuple[int, int]":
    """``(body start, end)`` of the ``## where we are`` section; ``(-1, -1)`` — none."""
    for i, ln in enumerate(lines):
        if ln.strip().lower() == WHERE_HEAD:
            end = next((j for j in range(i + 1, len(lines))
                        if lines[j].startswith("## ")), len(lines))
            return i + 1, end
    return -1, -1


def _layer_heads(body: List[str]) -> List[str]:
    return [ln[4:].strip().lower() for ln in body if ln.startswith("### ")]


def empty_layers(thread_dir: Path) -> List[str]:
    """Names of the contract layers (:data:`contract.THREAD_LAYERS`) that have no live
    lines — no subheading, or only ``<…>`` placeholders under it."""
    try:
        lines = _stream.passport_path(Path(thread_dir)).read_text(
            encoding="utf-8").splitlines()
    except OSError:
        lines = []
    start, end = _where_span(lines)
    live = set()
    head = ""
    for ln in (lines[start:end] if start >= 0 else []):
        if ln.startswith("### "):
            head = ln[4:].strip().lower()
        elif ln.strip() and not ln.strip().startswith("<") and head:
            live.add(head)
    return [contract.name(key) for key, _ph in contract.THREAD_LAYERS
            if not any(h.startswith(contract.name(key).lower()) for h in live)]


# ``tide thread layer`` flags → contract layer key.
LAYER_FLAGS = (("expect", "expectation"), ("where", "where"), ("exp", "experience"))


def layer_cmd(thread: str) -> str:
    """The ready command that writes a thread's
    layers: ``tide thread layer <thread> --expect "…" --where "…" --exp "…"``."""
    return ('tide thread layer {0} --expect "<what the human expects — in their words, '
            'each quote with its message number>" '
            '--where "<done · in progress · waiting on the human>" --exp "<pitfalls, rejected>"'
            .format(thread))


def main_cmd(thread: str) -> str:
    """The command that writes a thread's "read first" into plan.md."""
    return ('tide thread layer {0} --main "<task> · <whom and over which channel to deliver> · '
            '<whom not to duplicate>"'.format(thread))


def exit_warning(thread_dir: Path) -> Optional[str]:
    """Handoff warning when the thread's layers are empty (None — all filled)."""
    empty = empty_layers(thread_dir)
    if not empty:
        return None
    goal = _stream.passport_path(Path(thread_dir))
    from .. import slug as _slug
    name = _slug.entry_slug(Path(thread_dir).name)
    main = ""
    if not _plan_main.live_lines(Path(thread_dir)):
        main = ("\nThe thread's \"read first\" ({0}) is empty too — the seed reads it first:\n  {1}"
                .format(Path(thread_dir) / _plan_main.PLAN_FILE, main_cmd(name)))
    return (("tide: thread layers are empty — {0} ({1}, ## where we are). The new session "
            "will not learn them from the seed: write them before the handoff in the human's "
            "words — with a command (no hand edits needed, the head is allowed to run it):\n"
            "  {2}{4}\nThe command seeds the layer scaffold itself (scaffold only — tide "
            "thread layers --seed-skeleton {3}). Not stopping the handoff.").format(
                ", ".join("\"{0}\"".format(n) for n in empty), goal,
                layer_cmd(name), Path(thread_dir).name, main))


def split_main(values) -> List[str]:
    """``--main`` values (the flag can repeat) → "read first" lines: each is further
    split on " · ", whitespace collapses, empties and repeats drop. A session name
    "role · NN" ("main · 05", "designer · 09") is not torn apart — the same
    splitter as the seed's (:func:`tide.name_dots.split_dots`)."""
    out: List[str] = []
    for v in values or []:
        for part in _name_dots.split_dots(" ".join(str(v or "").split())):
            part = part.strip().strip("·").strip()
            if part and part not in out:
                out.append(part)
    return out


def write_main(thread_dir: Path, items: List[str], *, replace: bool = False) -> List[str]:
    """Write lines into the "## read first" section of the thread's ``plan.md`` (F61).

    The format is what the seed builder reads (:func:`tide.arc.plan_main.live_lines`):
    a heading prefixed ``## read first`` with ``- text`` lines under it. No plan.md —
    it is created from the thread scaffold (:func:`tide.arc.templates.thread_plan_md`);
    no section — it goes after the plan's ``# …`` heading. Without *replace* lines are
    appended to the end of the section (``<…>`` hints go, live lines and repeats stay
    as they were); with *replace* the section body is replaced whole. Returns the
    written lines."""
    items = split_main(items)
    if not items:
        return []
    plan = Path(thread_dir) / _plan_main.PLAN_FILE
    if not plan.is_file():
        from . import templates
        from .. import slug as _slug
        _io.atomic_write(plan, templates.thread_plan_md(
            _slug.entry_slug(Path(thread_dir).name)))
    lines = plan.read_text(encoding="utf-8").splitlines()
    head = next((i for i, ln in enumerate(lines) if ln.startswith(_plan_main.PREFIX)), -1)
    if head < 0:
        at = next((i + 1 for i, ln in enumerate(lines) if ln.startswith("# ")), 0)
        lines = lines[:at] + [""] * bool(at) + [_plan_main.HEADING, ""] + lines[at:]
        head = at + bool(at)
    stop = next((j for j in range(head + 1, len(lines)) if lines[j].startswith("## ")),
                len(lines))
    body = [] if replace else [ln for ln in lines[head + 1:stop]
                               if not ln.strip().lstrip("-* ").startswith("<")]
    while body and not body[-1].strip():
        body.pop()
    while body and not body[0].strip():
        body.pop(0)
    have = {ln.strip().lstrip("-* ").strip() for ln in body}
    added = [it for it in items if replace or it not in have]
    body += ["- {0}".format(it) for it in added]
    tail = [""] if stop < len(lines) else []
    lines = lines[:head + 1] + body + tail + lines[stop:]
    _io.atomic_write(plan, "\n".join(lines).rstrip("\n") + "\n")
    return added


# F65: layers that ``tide thread layer`` REPLACES whole (the old text goes to the log).
# "Where we are" is a snapshot of the position: appended to, it piled up
# contradictions (different counts in one seed). Expectation and experience are
# feeds and get appended.
REPLACE_KEYS = ("where",)
JOURNAL_HEAD = "## layer log"
# the layer log is a separate file next to the goal file (<thread>-goal-log.md),
# not inside it: the goal is read at start, a log there is noise.
LOG_SUFFIX = "-log"
PLACEHOLDER_HEAD = "<thread: the work-line this thread carries>"


def goal_log_path(goal_path: Path) -> Path:
    """``main-goal.md`` → ``main-goal-log.md`` next to it."""
    goal_path = Path(goal_path)
    return goal_path.with_name(goal_path.stem + LOG_SUFFIX + goal_path.suffix)


def _log_text(goal_path: Path, entries: List[str], old_text: str = "") -> str:
    """Log file text: header + new entries on top + earlier entries."""
    head = ["# layer log — {0}".format(Path(goal_path).name), "",
            "Earlier layer lines of the thread's goal file (replaced \"where we are\" and "
            "lines moved out on tidy-up). The seed builder does not read it; new entries "
            "go on top.", ""]
    rest = old_text.splitlines()
    while rest and not rest[0].startswith("### "):
        rest = rest[1:]  # old header
    body = list(entries) + rest
    while body and not body[-1].strip():
        body.pop()
    return "\n".join(head + body) + "\n"


def _journal(goal_path: Path, name: str, stamp: str, old: List[str]) -> None:
    """Earlier layer lines → the layer log file next to the goal file (:func:`goal_log_path`).
    The newest entry goes on top."""
    log = goal_log_path(goal_path)
    entry = ["### {0} — replaced {1}".format(name, stamp)] + old + [""]
    try:
        prev = log.read_text(encoding="utf-8")
    except OSError:
        prev = ""
    _io.atomic_write(log, _log_text(goal_path, entry, prev))


def split_journal(text: str) -> "tuple[str, List[str]]":
    """Goal file → (text without the ``## layer log`` section, section lines without heading)."""
    lines = text.splitlines()
    at = next((i for i, ln in enumerate(lines) if ln.strip().lower() == JOURNAL_HEAD), -1)
    if at < 0:
        return text, []
    stop = next((j for j in range(at + 1, len(lines))
                 if lines[j].startswith("## ")), len(lines))
    body = lines[at + 1:stop]
    while body and not body[0].strip():
        body = body[1:]
    kept = lines[:at] + lines[stop:]
    while kept and not kept[-1].strip():
        kept.pop()
    return "\n".join(kept) + "\n", body


def tidy_goal(goal_path: Path, *, dry_run: bool = True) -> Dict[str, object]:
    """Tidy a thread's goal file: the "layer log" section moves to the log file next to it;
    the placeholder heading ``<thread: …>`` becomes the thread's ``goal:`` if that is real.
    *dry_run* — report only. Before writing, a copy ``<goal>.bak-soc181`` is kept next to it."""
    goal_path = Path(goal_path)
    text = goal_path.read_text(encoding="utf-8")
    rest, journal = split_journal(text)
    goal = (fields.read_field(goal_path, "goal") or "").strip()
    real_goal = goal if goal and not goal.startswith("<") else ""
    placeholder = PLACEHOLDER_HEAD in text
    new = rest
    if placeholder and real_goal:
        new = new.replace(PLACEHOLDER_HEAD, real_goal, 1)
    jchars = len("\n".join(journal))
    rep: Dict[str, object] = {
        "goal": str(goal_path), "chars": len(text), "journal_chars": jchars,
        "journal_lines": len([ln for ln in journal if ln.strip()]),
        "placeholder": placeholder, "placeholder_fix": bool(placeholder and real_goal),
        "log": str(goal_log_path(goal_path)), "after_chars": len(new),
        "changed": new != text, "applied": False}
    if dry_run or new == text:
        return rep
    bak = goal_path.with_name(goal_path.name + ".bak-soc181")
    if not bak.exists():
        _io.atomic_write(bak, text)
    if journal:
        log = goal_log_path(goal_path)
        try:
            prev = log.read_text(encoding="utf-8")
        except OSError:
            prev = ""
        _io.atomic_write(log, _log_text(goal_path, journal + [""], prev))
    _io.atomic_write(goal_path, new)
    rep["applied"] = True
    rep["backup"] = str(bak)
    return rep


def goal_files(home: Path) -> List[Path]:
    """Goal files of open threads across all roster projects (``.tide/arcs/NN-@thread/*-goal.md``)."""
    from .. import roster as _roster
    out: List[Path] = []
    for e in _roster.read_roster(Path(home)):
        arcs = Path(e.get("path", "")).expanduser() / ".tide" / "arcs"
        if not arcs.is_dir():
            continue
        for d in sorted(arcs.iterdir()):
            if d.is_dir() and "-@" in d.name and not d.name.startswith("__"):
                out += sorted(d.glob("*-goal.md"))
    return out


# a layer stamp is the time of writing, not the time of the words. Text that already
# starts with its own date ("09.10 (from chat) — …") gets no stamp: the joined
# "09.10 19:22 — 09.10 …" read as the time of the words. For "tg N" references the
# time of the words comes from an external log (the ``tg_times`` argument). The write
# time of the expectation layer is the goal file's ``expect-written:`` field (read by
# :func:`freshness`).
EXPECT_AT_FIELD = "expect-written"
_LEAD_DATE = re.compile(r"^[(\[]?\s*(?:\d{1,2}\.\d{1,2}(?:\.\d{2,4})?|\d{4}-\d{2}-\d{2})(?![\d.])")
_TG_REF = re.compile(r"\b(tg)[ :]*(\d{3,6})\b"
                     r"(?P<date>\s*,\s*\d{1,2}\.\d{1,2}(?:\.\d{2,4})?(?![\d.]))?"
                     r"(?P<time>\s*,?\s*~?\d{1,2}:\d{2})?", re.I)


def tg_refs(text: str) -> List[int]:
    """Numbers of "tg N" refs in *text* that have no time yet ("tg 3573, 18:50" has one)."""
    return [int(m.group(2)) for m in _TG_REF.finditer(text or "") if not m.group("time")]


def stamp_line(text: str, now: datetime, times: Optional[Dict[int, datetime]] = None) -> str:
    """A layer line ``- DD.MM HH:MM — text`` (F81). Text that starts with a date gets
    no stamp. Otherwise the stamp is the time of the first "tg N" quote from *times*
    (external log), or *now* if there is none. Other "tg N" refs with a known time get
    ``, DD.MM HH:MM``."""
    times = times or {}
    lead = bool(_LEAD_DATE.match(text))
    first = None
    if not lead:
        first = next((times[int(m.group(2))] for m in _TG_REF.finditer(text)
                      if not m.group("time") and int(m.group(2)) in times), None)

    def _sub(m):
        at = times.get(int(m.group(2)))
        if m.group("time") or at is None or at == first:
            return m.group(0)
        return "{0} {1}, {2}".format(m.group(1), m.group(2), at.strftime("%d.%m %H:%M"))

    text = _TG_REF.sub(_sub, text)
    if lead:
        return "- " + text
    return "- {0} — {1}".format((first or now).strftime("%d.%m %H:%M"), text)


def write_layers(goal_path: Path, values: Dict[str, str], *,
                 now: Optional[datetime] = None,
                 tg_times: Optional[Dict[int, datetime]] = None) -> List[str]:
    """Write lines into the ``## where we are`` layers of a thread's goal file.

    *values* — ``{contract layer key: text}`` (``expectation`` / ``where`` /
    ``experience``). No scaffold — it is seeded (:func:`seed_skeleton`). A line
    ``- DD.MM HH:MM — text`` goes to the end of the layer, the layer's ``<…>``
    placeholder goes, live lines stay — except "where we are" (:data:`REPLACE_KEYS`,
    F65): its body is replaced by one new line and the earlier lines go to the
    layer log with the replacement date. Exactly the sections read by
    :func:`empty_layers` and the seed builder. Returns the names of the layers written."""
    goal_path = Path(goal_path)
    values = {k: " ".join(str(v or "").split()) for k, v in values.items()}
    values = {k: v for k, v in values.items() if v}
    if not values:
        return []
    seed_skeleton(goal_path)
    lines = goal_path.read_text(encoding="utf-8").splitlines()
    now = now or datetime.now()
    stamp = now.strftime("%d.%m %H:%M")
    done: List[str] = []
    for key, _ph in contract.THREAD_LAYERS:
        if key not in values:
            continue
        want = contract.name(key).lower()
        start, end = _where_span(lines)
        head = next((i for i in range(start, end) if lines[i].startswith("### ")
                     and lines[i][4:].strip().lower().startswith(want)), -1)
        if head < 0:
            continue
        stop = next((j for j in range(head + 1, end) if lines[j].startswith("### ")), end)
        body = [ln for ln in lines[head + 1:stop] if not ln.strip().startswith("<")]
        while body and not body[-1].strip():
            body.pop()
        while body and not body[0].strip():
            body.pop(0)
        old = []
        if key in REPLACE_KEYS:  # F65: "where we are" is a snapshot, not a feed
            old, body = [ln for ln in body if ln.strip()], []
        if key in REPLACE_KEYS:  # snapshot: the stamp is always the write time
            body.append("- {0} — {1}".format(stamp, values[key]))
        else:
            body.append(stamp_line(values[key], now, tg_times))
        tail = [""] if stop < len(lines) else []
        lines = lines[:head + 1] + body + tail + lines[stop:]
        if old:
            _journal(goal_path, contract.name(key), stamp, old)
        done.append(contract.name(key))
    _io.atomic_write(goal_path, "\n".join(lines).rstrip("\n") + "\n")
    if "expectation" in values:
        fields.set_field(goal_path, EXPECT_AT_FIELD, now.isoformat(timespec="seconds"))
    return done


# --- F66: layer freshness against the HANDOFF -----------------------------------

_STAMP_RE = re.compile(r"^\s*[-*]\s*(\d{2})\.(\d{2})\s+(\d{2}):(\d{2})\s+—")
_PULSE_RE = re.compile(r"^-\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?)\S*\s+—\s+(.*)$")


def _layer_lines(goal: Path, want: str) -> List[str]:
    try:
        lines = goal.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    start, end = _where_span(lines)
    out: List[str] = []
    head = ""
    for ln in (lines[start:end] if start >= 0 else []):
        if ln.startswith("### "):
            head = ln[4:].strip().lower()
        elif head.startswith(want) and ln.strip() and not ln.strip().startswith("<"):
            out.append(ln)
    return out


def _mtime(path: Path) -> Optional[datetime]:
    try:
        return datetime.fromtimestamp(Path(path).stat().st_mtime)
    except OSError:
        return None


def _pulses(thread_dir: Path):
    """``(time, note)`` of pulses of all the thread's sessions (``arcs/*/arc.md`` → ``## context``)."""
    for arc in sorted((Path(thread_dir) / "arcs").glob("*/arc.md")):
        try:
            text = arc.read_text(encoding="utf-8")
        except OSError:
            continue
        section = ""
        for ln in text.splitlines():
            if ln.startswith("## "):
                section = ln.strip().lower()
                continue
            m = _PULSE_RE.match(ln.strip()) if section == "## context" else None
            if m:
                try:
                    yield datetime.fromisoformat(m.group(1)), m.group(2)
                except ValueError:
                    continue


def freshness(thread_dir: Path) -> Dict[str, object]:
    """Freshness of the expectation layer and of "read first" against the thread's pulses.

    * ``expect`` — ``empty`` | ``stale`` (the layer was edited before the newest pulse
      carrying the expectation label) | ``fresh``; the layer time is the newest
      ``DD.MM HH:MM`` stamp of its lines, or the goal file's mtime if there are none;
    * ``main`` — ``empty`` | ``stale`` (plan.md was edited before the last HANDOFF)
      | ``fresh``;
    * ``expect_at`` / ``expect_pulse_at`` / ``main_at`` / ``pass_at`` — the times."""
    thread_dir = Path(thread_dir)
    goal = _stream.passport_path(thread_dir)
    expect_pulse = pass_at = None
    for at, note in _pulses(thread_dir):
        if "expectation" in contract.pulse_labels(note):
            expect_pulse = max(expect_pulse or at, at)
        if contract.is_pass_note(note):
            pass_at = max(pass_at or at, at)
    lines = _layer_lines(goal, contract.name("expectation").lower())
    expect_at = None
    year = (expect_pulse or datetime.now()).year
    for ln in lines:
        m = _STAMP_RE.match(ln)
        if m:
            try:
                at = datetime(year, int(m.group(2)), int(m.group(1)),
                              int(m.group(3)), int(m.group(4)))
            except ValueError:
                continue
            expect_at = max(expect_at or at, at)
    written = (fields.read_field(goal, EXPECT_AT_FIELD) or "").strip() if lines else ""
    try:
        w_at = datetime.fromisoformat(written) if written else None
    except ValueError:
        w_at = None
    if w_at is not None:  # F81: lines carry the time of the words, not of writing
        expect_at = max(expect_at or w_at, w_at)
    if lines and expect_at is None:
        expect_at = _mtime(goal)
    if not lines:
        expect = "empty"
    elif expect_pulse and (expect_at is None or expect_at < expect_pulse.replace(
            second=0, microsecond=0)):
        expect = "stale"
    else:
        expect = "fresh"
    main_at = _mtime(thread_dir / _plan_main.PLAN_FILE)
    if not _plan_main.live_lines(thread_dir):
        main = "empty"
    elif pass_at and (main_at is None or main_at < pass_at):
        main = "stale"
    else:
        main = "fresh"
    return {"expect": expect, "expect_at": expect_at, "expect_pulse_at": expect_pulse,
            "main": main, "main_at": main_at, "pass_at": pass_at}


def cmd_layer(args) -> int:
    """``tide thread layer <thread> --expect "…" --where "…" --exp "…" --main "…"``."""
    target = (getattr(args, "target", None) or "").strip()
    values = {key: getattr(args, "layer_" + flag, None) or ""
              for flag, key in LAYER_FLAGS}
    main = split_main(getattr(args, "layer_main", None) or [])
    if not target or not (main or any(v.strip() for v in values.values())):
        raise LayersError("thread layer: name the thread and at least one layer — " +
                          layer_cmd(target or "<thread>") + "  (or " +
                          main_cmd(target or "<thread>") + ")")
    entry = thread_entry(paths.require_tide_root(), target)
    if any(v.strip() for v in values.values()):
        goal = _stream.passport_path(entry)
        done = write_layers(goal, values)
        print("tide: {0} — written: {1}".format(goal, ", ".join(done) or "nothing"))
    if main:
        replace = bool(getattr(args, "layer_replace", False))
        added = write_main(entry, main, replace=replace)
        print("tide: {0} — \"read first\" {1}: {2}".format(
            entry / _plan_main.PLAN_FILE, "replaced" if replace else "appended",
            "; ".join(added) or "nothing new (lines already there)"))
        problem = _plan_main.problem(entry)
        if problem:
            print("tide: \"read first\": " + problem)
    empty = empty_layers(entry)
    print("tide: thread layers of {0}: {1}".format(
        entry.name, "empty — " + ", ".join(empty) if empty else "filled"))
    return 0


def seed_skeleton(goal_path: Path) -> List[str]:
    """Seed the scaffold of missing layers into a thread's goal file; return the names added.

    No ``## where we are`` section — it is appended at the end. If present, the missing
    ``### <layer>`` headings with placeholders go to its end. Nothing else is touched:
    filled layers, old placeholders and other sections stay as they were.
    """
    goal_path = Path(goal_path)
    text = goal_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    start, end = _where_span(lines)
    have = _layer_heads(lines[start:end]) if start >= 0 else []
    missing = [(contract.name(k), ph) for k, ph in contract.THREAD_LAYERS
               if not any(h.startswith(contract.name(k).lower()) for h in have)]
    if not missing:
        return []
    add: List[str] = []
    for name, ph in missing:
        add += ["### {0}".format(name), ph, ""]
    add = add[:-1]  # no trailing blank line
    if start < 0:
        body = text.rstrip("\n") + "\n\n" + WHERE_HEAD + "\n" + "\n".join(add) + "\n"
    else:
        while end > start and not lines[end - 1].strip():
            end -= 1  # land after the last live line of the section
        tail = lines[end:]
        while tail and not tail[0].strip():
            tail = tail[1:]
        head = lines[:end] + ([""] if end > start else [])
        body = "\n".join(head + add + ([""] + tail if tail else [])) + "\n"
    _io.atomic_write(goal_path, body)
    return [n for n, _ph in missing]


def thread_entry(root: Path, ref: str) -> Path:
    """An open thread of the project by name (``31-@main``, ``main``)."""
    entry = resolve.open_top_entry(Path(root), ref)
    if entry is None or not _stream.is_thread(entry):
        raise LayersError("thread layers: no open thread {0!r} in {1}".format(
            ref, paths.arcs_dir(Path(root))))
    return entry


def cmd_goal_tidy(args) -> int:
    """``tide thread goal-tidy <thread | goal file path> [--dry-run]`` and
    ``tide thread goal-tidy --all --dry-run`` — a report over all roster threads:
    the layer log moves to ``<thread>-goal-log.md`` next to it, the heading placeholder
    becomes ``goal:``."""
    dry = bool(getattr(args, "goal_dry", False))
    target = (getattr(args, "target", None) or "").strip()
    if getattr(args, "every", False):
        if not dry:
            raise LayersError("thread goal-tidy --all — only with --dry-run: for real, one "
                              "thread at a time (tide thread goal-tidy <thread>)")
        goals = goal_files(paths.control_home())
    elif target:
        p = Path(target).expanduser()
        goals = [p] if p.suffix == ".md" and p.is_file() else [
            _stream.passport_path(thread_entry(paths.require_tide_root(), target))]
    else:
        raise LayersError("thread goal-tidy: name a thread or a goal file (or --all --dry-run)")
    reps = [tidy_goal(g, dry_run=dry) for g in goals]
    if getattr(args, "as_json", False):
        import json as _json
        print(_json.dumps(reps, ensure_ascii=False, indent=1))
        return 0
    for r in reps:
        print("{0} · {1} chars · layer log: {2} lines, {3} chars{4}{5}".format(
            r["goal"], r["chars"], r["journal_lines"], r["journal_chars"],
            " · heading placeholder" + (" → goal" if r["placeholder_fix"] else " (goal empty)")
            if r["placeholder"] else "",
            "" if dry else (" · applied, backup {0}".format(r.get("backup"))
                            if r["applied"] else " · nothing to change")))
    if dry:
        print("tide: --dry-run — nothing written ({0} goal files)".format(len(reps)))
    return 0


def cmd_layers(args) -> int:
    """``tide thread layers <thread> [--seed-skeleton]``."""
    target = (getattr(args, "target", None) or "").strip()
    if not target:
        raise LayersError("thread layers: name the thread — tide thread layers <thread>")
    entry = thread_entry(paths.require_tide_root(), target)
    goal = _stream.passport_path(entry)
    if getattr(args, "seed_skeleton", False):
        added = seed_skeleton(goal)
        print("tide: {0} — {1}".format(goal, "scaffold seeded: " + ", ".join(added)
                                       if added else "the three-layer scaffold is already there"))
    empty = empty_layers(entry)
    print("tide: thread layers of {0}: {1}".format(
        entry.name, "empty — " + ", ".join(empty) if empty else "filled"))
    return 0


__all__ = ["JOURNAL_HEAD", "LAYER_FLAGS", "LayersError", "cmd_goal_tidy", "cmd_layer",
           "cmd_layers", "empty_layers", "goal_files", "goal_log_path", "split_journal",
           "tidy_goal",
           "exit_warning", "freshness", "layer_cmd", "main_cmd", "seed_skeleton", "split_main",
           "thread_entry", "write_layers", "write_main"]
