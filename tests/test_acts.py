"""tide.acts — the act: one line «what · proof · address» in a session passport.

 a single act writer + the double write from the work
verbs (the file log is written as before) — and a VIEW over them: ``tide work
show`` assembles the log from acts (see tests/test_work.py), ``tide thread``
shows the leading session's feed, a long proof moves to a file and the act
gets the path.

Assertions on the wording of work-verb log lines are kept to the parts this
module owns (the act grammar, the address, the user-given text), so the tests
do not depend on how tide.arc.work phrases its gestures.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from tide import acts, cli, fields
from tide.arc import stream, work


@pytest.fixture
def session(tmp_project):
    """A thread with one open session — the passport acts land in."""
    stream.new_thread(tmp_project, "release", goal="acts in one place")
    return stream.new_session(tmp_project, "release", "stroyka")


@pytest.fixture
def caller(tmp_project, session, monkeypatch):
    """The same session, but PINNED to the current chat — the act finds it itself."""
    fields.set_field(session / "arc.md", "claude-session", "sid-66")
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "sid-66")
    monkeypatch.chdir(tmp_project)
    return session


def _context(entry: Path) -> str:
    text = (entry / "arc.md").read_text(encoding="utf-8")
    return text.partition("## context")[2].split("\n## ", 1)[0]


# --- grammar ----------------------------------------------------------------

def test_act_line_is_what_proof_word_address(session):
    line = acts.write_act(
        session, "how-it-works page written",
        proof="200 after 40 s, commit e987384", word="give me the link", ref="66.4",
        now=datetime(2026, 9, 2, 16, 17, 32))
    assert line == (
        "- 2026-09-02T16:17:32 — act: how-it-works page written · "
        "proof: 200 after 40 s, commit e987384 · word: «give me the link» · #66.4")
    assert line[2:] in _context(session)


def test_empty_fields_are_not_written(session):
    line = acts.write_act(session, "decision 37 made")
    assert line.endswith("— act: decision 37 made")
    assert "proof" not in line and "#" not in line


def test_address_is_last_and_needs_no_hash(session):
    line = acts.write_act(session, "work taken", ref="66")
    assert line.endswith(" · #66")


def test_act_is_always_one_line(session):
    """A multi-line proof collapses — an act is one line by construction."""
    line = acts.write_act(session, "item 1 ✓ «done»",
                          proof="short for the human\n\n  and tech below", ref="66.1")
    assert "\n" not in line
    assert "proof: short for the human and tech below" in line
    assert len(_context(session).strip().splitlines()) == 1


def test_too_long_act_refuses_and_says_where_to_put_it(session):
    with pytest.raises(ValueError, match="Put long text in the thread as a file"):
        acts.write_act(session, "item 1 ✓", proof="x" * acts.ACT_MAX, ref="66.1")
    assert "act:" not in _context(session)  # nothing was written


def test_fit_proof_trims_the_tail_to_the_ceiling(session):
    short = acts.fit_proof("item 1 ✓", "y" * 500, ref="66.1")
    line = acts.write_act(session, "item 1 ✓", proof=short, ref="66.1")
    assert len(line) <= acts.ACT_MAX
    assert short.endswith("…")


# --- address -----------------------------------------------------------------

def test_make_ref_reads_the_work_dir_name():
    assert acts.make_ref("66-akty-v-odnom-meste") == "66"
    assert acts.make_ref("66-akty-v-odnom-meste", 4) == "66.4"
    assert acts.make_ref("07-x") == "7"
    assert acts.make_ref("works") == ""


# --- reading ----------------------------------------------------------------

def test_read_acts_is_newest_first(tmp_project, session):
    acts.write_act(session, "first", now=datetime(2026, 9, 2, 10, 0, 0))
    acts.write_act(session, "second", now=datetime(2026, 9, 2, 11, 0, 0))
    rows = acts.read_acts(session.parent.parent)
    assert [r.text.partition("act: ")[2] for r in rows] == ["second", "first"]
    assert rows[0].at > rows[1].at
    assert rows[0].session == session


def test_read_acts_gathers_every_session_of_the_thread(tmp_project, session):
    other = stream.new_session(tmp_project, "release", "razdacha")
    acts.write_act(session, "build", now=datetime(2026, 9, 2, 10, 0, 0))
    acts.write_act(other, "handout", now=datetime(2026, 9, 2, 12, 0, 0))
    rows = acts.read_acts(session.parent.parent)
    assert len(rows) == 2
    assert rows[0].session == other and rows[1].session == session


def test_read_acts_filters_by_address(session):
    acts.write_act(session, "work taken", ref="66", now=datetime(2026, 9, 2, 9, 0, 0))
    acts.write_act(session, "item 4 ✓", ref="66.4", now=datetime(2026, 9, 2, 9, 30, 0))
    acts.write_act(session, "another work", ref="65", now=datetime(2026, 9, 2, 9, 45, 0))
    acts.write_act(session, "no address", now=datetime(2026, 9, 2, 9, 50, 0))

    whole = acts.read_acts(session.parent.parent, ref="66")
    assert [r.ref for r in whole] == ["66.4", "66"]
    item = acts.read_acts(session.parent.parent, ref="#66.4")
    assert [r.ref for r in item] == ["66.4"]


def test_read_acts_of_a_thread_without_sessions_is_empty(tmp_project):
    stream.new_thread(tmp_project, "quiet", goal="nothing done")
    assert acts.read_acts(tmp_project / ".tide" / "arcs" / "01-@quiet") == []


# --- who writes------------------------------------------------------------

def test_caller_session_finds_the_pinned_session(tmp_project, caller):
    assert acts.caller_session(tmp_project) == caller


def test_caller_session_is_none_without_a_sid(tmp_project, session, monkeypatch):
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    assert acts.caller_session(tmp_project) is None


def test_caller_session_is_none_for_a_stranger_sid(tmp_project, session, monkeypatch):
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "sid-chuzhoy")
    assert acts.caller_session(tmp_project) is None


# --- double write from the work verbs -------------------------------------------

def _work(root, title="acts in one place"):
    cli.main(["work", "add", title])
    return work._find(root, "01")


def test_check_writes_the_act_and_nothing_else(tmp_project, caller):
    """End of the journal rework: a gesture has one place — the session passport, not work.md."""
    _work(tmp_project)
    cli.main(["work", "checklist", "01", "Single act writer"])
    cli.main(["work", "take", "01", "--word", "go"])
    cli.main(["work", "check", "01", "1", "--proof", "acts.py module + tests"])

    passport = (work._find(tmp_project, "01") / "work.md").read_text(encoding="utf-8")
    assert "## log" not in passport
    assert "acts.py module" not in passport

    act = [ln for ln in _context(caller).splitlines() if "Single act writer" in ln][0]
    assert "— act: " in act
    assert act.endswith(" · proof: acts.py module + tests · #1.1")


def test_the_human_word_gets_its_own_field_in_the_act(tmp_project, caller):
    _work(tmp_project)
    cli.main(["work", "take", "01", "--word", "taking it, plan agreed"])
    ctx = _context(caller)
    assert "word: «taking it, plan agreed»" in ctx
    assert ctx.rstrip().endswith("#1")


def test_dispatch_and_close_land_as_acts_with_the_work_address(tmp_project, caller):
    _work(tmp_project)
    cli.main(["work", "take", "01", "--word", "yes"])
    cli.main(["work", "dispatch", "01", "--to", "build worker"])
    cli.main(["work", "close", "01", "--word", "accepted"])
    lines = _context(caller).splitlines()
    sent = [ln for ln in lines if "build worker" in ln]
    assert len(sent) == 1 and "— act: " in sent[0] and sent[0].endswith(": build worker · #1")
    closed = [ln for ln in lines if "word: «accepted»" in ln]
    assert len(closed) == 1 and "— act: " in closed[0]
    assert closed[0].endswith(" · word: «accepted» · #1")


def test_a_long_proof_never_breaks_the_verb(tmp_project, caller):
    _work(tmp_project)
    cli.main(["work", "checklist", "01", "Long proof"])
    cli.main(["work", "take", "01", "--word", "yes"])
    cli.main(["work", "check", "01", "1", "--proof", "details " * 60])

    # long text does not fit in an act and is not cut: the full proof moves to a
    # file (below), while the act itself stays one line and keeps its address
    act = [ln for ln in _context(caller).splitlines() if "Long proof" in ln][0]
    assert len(act) <= acts.ACT_MAX and act.endswith("#1.1")
    assert "details details" in _spilled_text(caller)


# --- long proof: a file, not a truncation ------------------------------------

def _proofs(entry: Path):
    d = entry / "workspace" / acts.PROOFS_DIRNAME
    return sorted(d.glob("*.md")) if d.is_dir() else []


def _spilled_text(entry: Path) -> str:
    """Everything that moved into proof files, as one blob."""
    return "\n".join(f.read_text(encoding="utf-8") for f in _proofs(entry))


def test_a_long_proof_goes_to_a_file_and_the_act_carries_the_path(tmp_project, caller):
    """The human's word 09-02: one line, long text goes to a file. No cutting:
    the log became a VIEW over acts, and a truncation would be the only record."""
    _work(tmp_project)
    cli.main(["work", "checklist", "01", "Long proof"])
    cli.main(["work", "take", "01", "--word", "yes"])
    cli.main(["work", "check", "01", "1", "--proof",
              "page deployed, 200 after 40 s\n\n" + "tech " * 80])

    act = [ln for ln in _context(caller).splitlines() if "Long proof" in ln][0]
    assert len(act) <= acts.ACT_MAX and act.endswith("· #1.1")
    # the proof's first line — the one the author wrote FOR THE HUMAN — stays whole
    assert "proof: page deployed, 200 after 40 s · workspace/proofs/" in act

    files = _proofs(caller)
    assert len(files) == 1 and files[0].name.startswith("1.1-")
    assert str(files[0].relative_to(caller)) in act      # the path leads to the file
    assert "tech tech" in files[0].read_text(encoding="utf-8")  # nothing lost


def test_a_short_proof_writes_no_file(tmp_project, caller):
    _work(tmp_project)
    cli.main(["work", "checklist", "01", "Short proof"])
    cli.main(["work", "take", "01", "--word", "yes"])
    cli.main(["work", "check", "01", "1", "--proof", "commit e987384"])
    assert _proofs(caller) == []


def test_file_proof_never_cuts_the_path(session):
    """The proof's first line is cut, not the path: without it the record leads nowhere."""
    got = acts.file_proof("item 4 ✓ «page»", "z" * 400,
                          "workspace/proofs/66.4-20260902-195413.md", ref="66.4")
    assert got.endswith("· workspace/proofs/66.4-20260902-195413.md")
    assert "…" in got
    assert len(acts.write_act(session, "item 4 ✓ «page»",
                              proof=got, ref="66.4")) <= acts.ACT_MAX


# --- the thread's leading session ----------------------------------------------------

@pytest.fixture
def no_transcripts(tmp_path, monkeypatch):
    """No claude chats on disk — so `head_session` falls back to the passport stamp."""
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "claude-home"))


def test_head_session_is_the_newest_accepted_one(tmp_project, session, no_transcripts):
    fields.set_field(session / "arc.md", "claude-session", "sid-a")
    later = stream.new_session(tmp_project, "release", "razdacha")
    fields.set_field(later / "arc.md", "claude-session", "sid-b")
    assert acts.head_session(session.parent.parent) == later


def test_a_session_with_a_real_chat_leads_over_a_bare_stamp(tmp_project, session,
                                                            no_transcripts, tmp_path):
    """A ghost: raising an offer stamps the sid BEFORE the session ever speaks."""
    fields.set_field(session / "arc.md", "claude-session", "sid-a")
    ghost = stream.new_session(tmp_project, "release", "prizrak")
    fields.set_field(ghost / "arc.md", "claude-session", "sid-ghost")
    chats = tmp_path / "claude-home" / "projects" / str(tmp_project).replace(
        "/", "-").replace(".", "-")
    chats.mkdir(parents=True)
    (chats / "sid-a.jsonl").write_text("{}\n", encoding="utf-8")
    assert acts.head_session(session.parent.parent) == session


def test_a_dismissed_session_does_not_lead(tmp_project, session, no_transcripts):
    fields.set_field(session / "arc.md", "claude-session", "sid-a")
    left = stream.new_session(tmp_project, "release", "otpushchennaya")
    fields.set_field(left / "arc.md", "claude-session", "sid-b")
    fields.set_field(left / "arc.md", "dismissed", "2026-09-02T20:00")
    assert acts.head_session(session.parent.parent) == session


def test_a_thread_without_sessions_has_no_head(tmp_project):
    stream.new_thread(tmp_project, "quiet", goal="nothing done")
    assert acts.head_session(tmp_project / ".tide" / "arcs" / "01-@quiet") is None


# --- act feed on the thread screen --------------------------------------------

def test_thread_screen_shows_the_acts_of_the_leading_session(tmp_project, caller,
                                                             no_transcripts):
    from tide.arc import thread_screen

    _work(tmp_project)
    cli.main(["work", "take", "01", "--word", "taking it"])
    cli.main(["work", "dispatch", "01", "--to", "builder B"])
    out = thread_screen.render(tmp_project, "release")

    block = out.partition("\nacts · ")[2].partition("\n\n")[0]
    # three gestures, not two: «responsible thread → …» became an act too — before
    # the end of that rework it lived ONLY as a file line and would have vanished
    # once its entry was cancelled
    assert block.startswith("3 from {0}".format(caller.name))
    rows = [ln.strip() for ln in block.splitlines()[1:]]
    assert " act: " in rows[0] and rows[0].endswith(": builder B · #1")  # newest first
    assert "word: «taking it»" in rows[1]
    assert "01-@release" in rows[2]
    assert out.index("acts · ") < out.index("where to look")


def test_a_long_act_keeps_its_address_on_the_screen(tmp_project, caller,
                                                    no_transcripts):
    from tide.arc import thread_screen

    _work(tmp_project)
    cli.main(["work", "checklist", "01", "Screen item"])
    cli.main(["work", "take", "01", "--word", "yes"])
    cli.main(["work", "check", "01", "1", "--proof", "detail " * 20])
    row = [ln for ln in thread_screen.render(tmp_project, "release").splitlines()
           if "Screen item" in ln][0]
    assert row.rstrip().endswith("· #1.1")     # the address is cut last
    assert "…" in row


def test_a_thread_without_acts_says_nothing_about_them(tmp_project, session):
    from tide.arc import thread_screen

    assert "acts · " not in thread_screen.render(tmp_project, "release")


def test_no_caller_session_means_no_act_and_no_failure(tmp_project, session, monkeypatch):
    """A verb called from a script or another machine — no act, and no failure.

    The price of a single place is stated out loud: without a session the
    gesture is recorded NOWHERE. The verb still does its job in full — status,
    checklist, passport — and returns 0; only the feed stays silent.
    """
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.chdir(tmp_project)
    _work(tmp_project)
    assert cli.main(["work", "take", "01", "--word", "yes"]) == 0
    assert cli.main(["work", "dispatch", "01", "--to", "worker"]) == 0

    passport = (work._find(tmp_project, "01") / "work.md").read_text(encoding="utf-8")
    assert "status: taken" in passport                  # the work is done
    assert "worker" not in passport                     # but the gesture is not recorded
    assert "act:" not in _context(session)
