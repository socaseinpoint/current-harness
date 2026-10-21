"""offload as you go — tide offload + the offload-nudge Stop hook."""

from __future__ import annotations

import io
import json
import os
import time
from pathlib import Path

import pytest

from tide import cli, fields, offload
from tide.arc import stream

from tests.test_plan_main import fill_main


@pytest.fixture
def session(tmp_project):
    fill_main(stream.new_thread(tmp_project, "hygiene", goal="keep the seam clean"))
    return stream.new_session(tmp_project, "hygiene", "otliv")


# --- the offload write -------------------------------------------------------

def test_offload_appends_context_and_stamps(tmp_project, session):
    p1 = offload.offload(tmp_project, "otliv", note="picked the traffic light in doctor")
    p2 = offload.offload(tmp_project, "otliv", note="thresholds: soft defaults")
    assert p1 == p2 == session / "arc.md"
    text = p2.read_text(encoding="utf-8")
    ctx = text.partition("## context")[2]
    assert "picked the traffic light" in ctx and "thresholds: soft" in ctx
    assert ctx.index("picked") < ctx.index("thresholds")      # entries accrue in order
    assert "<session memory" not in text                    # placeholder dropped
    assert (fields.read_field(p2, "offloaded-at") or "").startswith("20")


def test_offload_cursor_replaces_section(tmp_project, session):
    offload.offload(tmp_project, "otliv", cursor="on substep 3, thresholds next")
    text = (session / "arc.md").read_text(encoding="utf-8")
    body = text.partition("## cursor — resume here")[2].partition("## ")[0]
    assert "substep 3" in body
    assert "<where this session left off" not in body


def _pulses(session):
    """The count `tide thread` shows for *session* — read by thread_screen itself."""
    from tide.arc import thread_screen
    rows = thread_screen.sessions(session.parent.parent)
    return next(int(s["pulses"] or 0) for s in rows if s["dir"] == session)


def test_cursor_only_offload_counts_as_a_pulse(tmp_project, session):
    # `tide offload <s> --cursor …` without a note used to leave
    # ## context empty, and `tide thread` said "0 pulses in ## context".
    before = _pulses(session)
    offload.offload(tmp_project, "otliv", cursor="fixing the pulse counter")
    assert _pulses(session) == before + 1
    ctx = (session / "arc.md").read_text(encoding="utf-8").partition("## context")[2]
    ctx = ctx.split("\n## ", 1)[0]
    assert "cursor → fixing the pulse counter" in ctx


def test_next_only_offload_counts_as_a_pulse(tmp_project, session, monkeypatch):
    monkeypatch.chdir(tmp_project)
    before = _pulses(session)
    assert cli.main(["offload", "otliv", "--next", "step one · step two"]) == 0
    assert _pulses(session) == before + 1
    assert "next → step one · step two" in (session / "arc.md").read_text(encoding="utf-8")


def test_offload_with_a_note_writes_one_line_not_two(tmp_project, session):
    before = _pulses(session)
    offload.offload(tmp_project, "otliv", note="decided so", cursor="doing this")
    assert _pulses(session) == before + 1
    assert "cursor →" not in (session / "arc.md").read_text(encoding="utf-8")


def test_offload_requires_something_to_write(tmp_project, session):
    with pytest.raises(offload.OffloadError, match="nothing to write"):
        offload.offload(tmp_project, "otliv")


def test_offload_unknown_session_lists_open(tmp_project, session):
    with pytest.raises(offload.OffloadError, match="no open session.*otliv"):
        offload.offload(tmp_project, "ghost", note="x")


# --- ambiguous slug across threads must RAISE, not corrupt a stranger ---

def _two_threads_same_session_slug(tmp_project):
    stream.new_thread(tmp_project, "alpha", goal="a-goal")
    a = stream.new_session(tmp_project, "alpha", "work")
    stream.new_thread(tmp_project, "beta", goal="b-goal")
    b = stream.new_session(tmp_project, "beta", "work")
    return a, b  # both dirs are '01-work', in different threads


def test_offload_ambiguous_slug_raises_with_thread_options(tmp_project):
    a, b = _two_threads_same_session_slug(tmp_project)
    with pytest.raises(offload.OffloadError, match="ambiguous"):
        offload.offload(tmp_project, "work", note="must not silently land anywhere")
    # neither passport was touched — no silent corruption
    assert "must not silently land" not in (a / "arc.md").read_text(encoding="utf-8")
    assert "must not silently land" not in (b / "arc.md").read_text(encoding="utf-8")


def test_offload_thread_qualified_resolves_the_right_session(tmp_project):
    a, b = _two_threads_same_session_slug(tmp_project)
    offload.offload(tmp_project, "beta/work", note="lands in beta only")
    assert "lands in beta only" in (b / "arc.md").read_text(encoding="utf-8")
    assert "lands in beta only" not in (a / "arc.md").read_text(encoding="utf-8")


def test_offload_single_slug_still_resolves_plainly(tmp_project, session):
    # a slug unique across all threads keeps working without qualification
    offload.offload(tmp_project, "otliv", note="plain")
    assert "plain" in (session / "arc.md").read_text(encoding="utf-8")


# --- words != disk guard: pulse says closed while the thread is open ---

def test_closure_word_warning_when_thread_open(tmp_project, session):
    warn = offload._closure_word_warning(session / "arc.md", "thread closed — everything merged into main")
    assert warn and "OPEN" in warn and "arc close" in warn


def test_closure_word_warning_silent_without_marker(tmp_project, session):
    assert offload._closure_word_warning(session / "arc.md", "cleaned up dead code") is None


# --- nudge fires on a BLIND session: work in a nested repo, arc workspace idle ---





def test_cli_offload_roundtrip(tmp_project, session, monkeypatch, capsys):
    monkeypatch.chdir(tmp_project)
    rc = cli.main(["offload", "otliv", "--cursor", "here", "decision", "made"])
    assert rc == 0
    assert "offloaded" in capsys.readouterr().out
    text = (session / "arc.md").read_text(encoding="utf-8")
    assert "decision made" in text














# --- the Stop-hook nudge -----------------------------------------------------

def _pin(session_dir: Path, claude_id: str) -> None:
    fields.set_field(session_dir / "arc.md", "claude-session", claude_id)


def _age(path: Path, seconds: int) -> None:
    old = time.time() - seconds
    os.utime(path, (old, old))












# --- start-gate add-on: nudge also flags a blind thread goal ----





# --- dissolved head stands down instead of pulsing -----------------

def _control_home_with_taken_offer(base, *, from_session, taker="successor"):
    """A fresh control-home where *from_session* offered a thread that was then taken."""
    from tests.conftest import build_tide_skeleton
    from tide import handoff_queue as hq

    home = base.parent / "ch-91"
    home.mkdir(exist_ok=True)
    build_tide_skeleton(home, name="ch", control_home=True)
    hq.offer(home, "handoff", arc="-", project="demo", seed="-", from_session=from_session)
    hq.take(home, "handoff", session=taker)
    return home














# --- install merge -----------------------------------------------------------



def test_find_session_matches_digit_leading_slug(tmp_project):
    # session '01-01-mvp' (slug '01-mvp') must resolve by ref '01-mvp'.
    stream.new_thread(tmp_project, "build", goal="g")
    sess = stream.new_session(tmp_project, "build", "01-mvp")
    assert offload.find_session(tmp_project, "01-mvp") == sess
    assert offload.find_session(tmp_project, sess.name) == sess


def test_offload_next_writes_section(tmp_project, session):
    # record form (board law 07.07): cursor = current action, next = 1-3 steps
    offload.offload(tmp_project, "otliv",
                    cursor="wiring the board to the record form",
                    next_steps="handoff timeline · traffic light · form into the skill")
    text = (session / "arc.md").read_text(encoding="utf-8")
    nxt = text.partition("## next")[2].partition("## ")[0]
    assert "handoff timeline" in nxt and "traffic light" in nxt


def test_cli_offload_next_flag(tmp_project, session, monkeypatch):
    monkeypatch.chdir(tmp_project)
    assert cli.main(["offload", "otliv", "--next", "step one · step two"]) == 0
    assert "step one" in (session / "arc.md").read_text(encoding="utf-8")








# --- later false hits -----------------------------------


def test_closure_warning_not_across_clause(tmp_project):
    # "start gate closed, planning the THREAD" — "thread" is in another clause (16.07)
    from tide.arc import stream
    from tide.offload import _closure_word_warning

    stream.new_thread(tmp_project, "demo2", goal="ship")
    s = stream.new_session(tmp_project, "demo2", "s1")
    assert _closure_word_warning(
        s / "arc.md", "start gate closed, planning the thread per law 47") is None
    assert _closure_word_warning(s / "arc.md", "thread closed, result in output")


def test_blind_goal_allows_slug_inside_real_words():
    # a real goal with the slug inside is NOT a stub
    from tide.placeholders import is_blind_goal

    assert is_blind_goal("start thread test-thread: check it", "test-thread") is False
    assert is_blind_goal("test-thread", "test-thread") is True
    assert is_blind_goal("debug_deck", "debug-deck") is True


def test_find_by_sid_falls_back_to_closed_sessions(tmp_project):
    # the arc was closed, the chat lives on — sid routing finds the closed passport
    from tide import fields
    from tide.arc import stream
    from tide.offload import find_session_by_claude_id

    stream.new_thread(tmp_project, "office", goal="world")
    s = stream.new_session(tmp_project, "office", "world")
    fields.set_field(s / "arc.md", "claude-session", "sid-closed-live")
    closed = s.parent / "__{0}__".format(s.name)
    s.rename(closed)  # arc closed, the chat (sid) lives on
    hit = find_session_by_claude_id(tmp_project, "sid-closed-live")
    assert hit == closed


# --- summary: the arc says in one line what it holds -------

def test_summary_replaces_the_template_placeholder(tmp_project, session):
    passport = offload.offload(tmp_project, "otliv",
                               summary="three daily reports and the thread map")
    text = passport.read_text(encoding="utf-8")
    body = text.partition(offload.SUMMARY_SECTION)[2].partition("\n## ")[0].strip()
    assert body == "three daily reports and the thread map"
    assert "a few plain sentences" not in text      # the placeholder is gone


def test_summary_is_rewritten_not_appended(tmp_project, session):
    offload.offload(tmp_project, "otliv", summary="first edit")
    passport = offload.offload(tmp_project, "otliv", summary="second edit")
    body = passport.read_text(encoding="utf-8").partition(
        offload.SUMMARY_SECTION)[2].partition("\n## ")[0].strip()
    assert body == "second edit"               # a showcase, not a journal


def test_summary_alone_is_enough_to_pulse(tmp_project, session):
    """A summary is a real pulse — it must not need a note to be accepted."""
    passport = offload.offload(tmp_project, "otliv", summary="what lives here")
    assert (fields.read_field(passport, "offloaded-at") or "").startswith("20")


def test_summary_does_not_disturb_cursor_or_context(tmp_project, session):
    offload.offload(tmp_project, "otliv", note="did one", cursor="doing two")
    passport = offload.offload(tmp_project, "otliv", summary="arc showcase")
    text = passport.read_text(encoding="utf-8")
    assert "did one" in text
    cursor = text.partition(offload.CURSOR_SECTION)[2].partition("\n## ")[0].strip()
    assert cursor == "doing two"


# --- --eta / --deliverable (passport: when it delivers and what the human gets) ------

def test_parse_eta_formats():
    from datetime import datetime
    now = datetime(2026, 10, 9, 15, 30).astimezone()
    today = offload.parse_eta("12:05", now=now)          # past → stays today (overdue)
    assert today.startswith("2026-10-09T12:05:00") and today[19] in "+-"
    assert offload.parse_eta("31.12 09:00", now=now).startswith("2026-12-31T09:00:00")
    assert offload.parse_eta("2026-10-10T18:00:00+03:00") == "2026-10-10T18:00:00+03:00"
    assert offload.parse_eta("2026-10-10T18:00")[19] in "+-"   # naive → local offset
    assert offload.parse_eta("-") == offload.parse_eta("none") == ""
    with pytest.raises(offload.OffloadError):
        offload.parse_eta("tomorrow")


def test_cli_offload_eta_and_deliverable_replace_and_clear(tmp_project, session, monkeypatch):
    monkeypatch.chdir(tmp_project)
    arc = session / "arc.md"
    assert cli.main(["offload", "otliv", "--eta", "18:00",
                     "--deliverable", "screenshot of the in-progress screen"]) == 0
    assert fields.read_field(arc, "eta").startswith(
        fields.read_field(arc, "offloaded-at")[:10] + "T18:00:00")
    assert fields.read_field(arc, "deliverable") == "screenshot of the in-progress screen"
    assert cli.main(["offload", "otliv", "--eta", "2026-10-10T09:30:00+03:00",
                     "--deliverable", "PR #171", "moved the deadline"]) == 0
    text = arc.read_text(encoding="utf-8")
    assert text.count("\neta: ") == 1 and text.count("\ndeliverable: ") == 1
    assert fields.read_field(arc, "eta") == "2026-10-10T09:30:00+03:00"
    assert fields.read_field(arc, "deliverable") == "PR #171"
    assert cli.main(["offload", "otliv", "--eta", "-", "--deliverable", "-"]) == 0
    assert fields.read_field(arc, "eta") is None
    assert fields.read_field(arc, "deliverable") is None


def test_offload_deliverable_is_cut_to_one_short_line(tmp_project, session):
    offload.offload(tmp_project, "otliv", deliverable="very " * 30)
    value = fields.read_field(session / "arc.md", "deliverable")
    assert len(value) <= offload.DELIVERABLE_MAX and value.endswith("…")
