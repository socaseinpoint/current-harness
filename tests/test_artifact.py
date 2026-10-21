"""tide.arc.artifact — "artifacts": things the agent puts on the human's desk.

The machine under test: new → taken, the flag decides the kind, every verb
journals, taken requires the human's word.
"""

from __future__ import annotations

import pytest

from tide import cli
from tide.arc import artifact


@pytest.fixture
def in_project(tmp_project, monkeypatch):
    monkeypatch.chdir(tmp_project)
    return tmp_project


def _text(root, key="01"):
    return (artifact._find(root, key) / "artifact.md").read_text(encoding="utf-8")


# --- add ---------------------------------------------------------------------

def test_add_text_creates_passport_on_the_desk(in_project):
    rc = cli.main(["artifact", "add", "Release note for a colleague — send",
                   "--text", "Hey, we shipped: check prod"])
    assert rc == 0
    d = artifact.artifacts_dir(in_project) / "01-release-note-for-a-colleague-send"
    assert d.is_dir()
    text = (d / "artifact.md").read_text(encoding="utf-8")
    assert "# Release note for a colleague — send" in text
    assert "kind: message" in text
    assert "status: new" in text
    assert "## content" in text
    assert "Hey, we shipped: check prod" in text
    assert "handed over by the agent" in text


def test_add_cmd_and_file_take_their_kind_from_the_flag(in_project):
    cli.main(["artifact", "add", "run the migration", "--cmd", "tide doctor"])
    cli.main(["artifact", "add", "look at the plan", "--file", "/tmp/plan.md"])
    first, second = _text(in_project, "01"), _text(in_project, "02")
    assert "kind: command" in first
    assert artifact.content_of(first) == "tide doctor"
    assert "kind: file" in second
    assert artifact.content_of(second) == "/tmp/plan.md"  # the path as is


def test_add_says_when_the_file_is_not_there(in_project, capsys):
    cli.main(["artifact", "add", "look at the plan", "--file", "/nope/plan.md"])
    assert "no file at this path" in capsys.readouterr().out


def test_add_requires_exactly_one_source(in_project, capsys):
    assert cli.main(["artifact", "add", "something"]) == 1
    assert "what are you handing over" in capsys.readouterr().err
    assert cli.main(["artifact", "add", "something", "--text", "a", "--cmd", "b"]) == 1
    err = capsys.readouterr().err
    assert "exactly one source" in err
    assert "--text, --cmd" in err


def test_add_refuses_empty_caption_and_empty_content(in_project, capsys):
    assert cli.main(["artifact", "add", "  ", "--text", "something to hand over"]) == 1
    assert "empty caption" in capsys.readouterr().err
    assert cli.main(["artifact", "add", "a caption", "--text", "  "]) == 1
    assert "empty content" in capsys.readouterr().err


def test_add_unfolds_newlines_in_text_but_not_in_cmd(in_project):
    cli.main(["artifact", "add", "letter", "--text", "first\\nsecond"])
    cli.main(["artifact", "add", "command", "--cmd", "printf 'a\\nb'"])
    assert artifact.content_of(_text(in_project, "01")) == "first\nsecond"
    assert artifact.content_of(_text(in_project, "02")) == "printf 'a\\nb'"


def test_add_numbers_its_own_sequence(in_project):
    cli.main(["work", "add", "work one"])
    cli.main(["work", "add", "work two"])
    cli.main(["artifact", "add", "first thing", "--text", "x"])
    assert (artifact.artifacts_dir(in_project) / "01-first-thing").is_dir()


def test_add_stamps_caller_thread_into_from_arc(in_project, monkeypatch):
    # a session arc pinned to our sid → from-arc names its thread, no flag needed
    sid = "artifact-sid-abc"
    sess = artifact.paths.arcs_dir(in_project) / "09-@build" / "arcs" / "01-do"
    sess.mkdir(parents=True)
    (sess / "arc.md").write_text(
        "# do\n\ntitle: do\nclaude-session: {0}\n".format(sid), encoding="utf-8")
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", sid)
    cli.main(["artifact", "add", "thing", "--text", "x"])
    text = _text(in_project)
    assert "from-arc: 09-@build" in text
    assert "handed over by the agent (09-@build)" in text


def test_add_without_a_session_leaves_from_arc_empty(in_project):
    cli.main(["artifact", "add", "thing", "--text", "x"])
    text = _text(in_project)
    assert "from-arc: \n" in text
    assert "— handed over by the agent\n" in text  # no empty parens


def test_add_resolves_work_number_and_refuses_a_dangling_one(in_project, capsys):
    cli.main(["work", "add", "issues desk"])
    assert cli.main(["artifact", "add", "thing", "--text", "x", "--work", "01"]) == 0
    assert "work: 01" in _text(in_project)
    assert cli.main(["artifact", "add", "thing", "--text", "x", "--work", "77"]) == 1
    err = capsys.readouterr().err
    assert "work:" in err and "'77'" in err


def test_add_warns_on_a_long_caption(in_project, capsys):
    cli.main(["artifact", "add", "x" * 90, "--text", "x"])
    assert "long caption" in capsys.readouterr().out


# --- taken / reopen -----------------------------------------------------------

def test_taken_requires_the_human_word(in_project, capsys):
    cli.main(["artifact", "add", "thing", "--text", "x"])
    assert cli.main(["artifact", "taken", "01", "--word", "  "]) == 1
    assert "only the human takes it" in capsys.readouterr().err
    assert "status: new" in _text(in_project)


def test_taken_moves_status_and_journals_the_word(in_project, capsys):
    cli.main(["artifact", "add", "thing", "--text", "x"])
    capsys.readouterr()
    rc = cli.main(["artifact", "taken", "01", "--word", "took it, sent to the colleague"])
    assert rc == 0
    assert "taken" in capsys.readouterr().out
    text = _text(in_project)
    assert "status: taken" in text
    assert "taken with the word: \"took it, sent to the colleague\"" in text


def test_taken_twice_is_refused(in_project, capsys):
    cli.main(["artifact", "add", "thing", "--text", "x"])
    cli.main(["artifact", "taken", "01", "--word", "ok"])
    assert cli.main(["artifact", "taken", "01", "--word", "ok"]) == 1
    assert "already taken" in capsys.readouterr().err


def test_reopen_puts_it_back_and_refuses_a_live_one(in_project, capsys):
    cli.main(["artifact", "add", "thing", "--text", "x"])
    assert cli.main(["artifact", "reopen", "01"]) == 1
    assert "already on the desk" in capsys.readouterr().err
    cli.main(["artifact", "taken", "01", "--word", "ok"])
    assert cli.main(["artifact", "reopen", "01", "--word", "changed my mind"]) == 0
    text = _text(in_project)
    assert "status: new" in text
    assert "back on the desk by the word: \"changed my mind\"" in text


# --- list / show --------------------------------------------------------------

def test_list_shows_live_newest_first_and_counts_taken(in_project, capsys):
    cli.main(["artifact", "add", "first thing", "--text", "a"])
    cli.main(["artifact", "add", "second thing", "--cmd", "tide doctor"])
    cli.main(["artifact", "add", "third thing", "--text", "c"])
    cli.main(["artifact", "taken", "01", "--word", "ok"])
    capsys.readouterr()
    assert cli.main(["artifact", "list"]) == 0
    out = capsys.readouterr().out
    assert out.index("03-third-thing") < out.index("02-second-thing")
    assert "command" in out
    assert "01-first-thing" not in out  # taken ones left the desk
    assert "taken: 1" in out


def test_list_on_an_empty_desk(in_project, capsys):
    assert cli.main(["artifact", "list"]) == 0
    assert "no artifacts" in capsys.readouterr().out
    cli.main(["artifact", "add", "thing", "--text", "x"])
    cli.main(["artifact", "taken", "01", "--word", "ok"])
    capsys.readouterr()
    cli.main(["artifact", "list"])
    out = capsys.readouterr().out
    assert "the desk is empty" in out
    assert "taken: 1" in out


def test_show_prints_the_file_as_it_is(in_project, capsys):
    cli.main(["artifact", "add", "thing", "--text", "first\\nsecond"])
    capsys.readouterr()
    assert cli.main(["artifact", "show", "01"]) == 0
    out = capsys.readouterr().out
    assert out.strip() == _text(in_project).strip()
    assert "first\nsecond" in out


def test_show_and_taken_refuse_an_unknown_key(in_project, capsys):
    assert cli.main(["artifact", "show", "77"]) == 1
    assert "no artifact" in capsys.readouterr().err


# --- the agent's question ------------------------------------------

def test_add_ask_puts_a_question_on_the_desk(in_project, capsys):
    rc = cli.main(["artifact", "add", "Where do we ship staging — k8s or compose?",
                   "--ask", "A colleague offers k8s.\\nWaiting for the word on what to build with."])
    assert rc == 0
    text = _text(in_project, "01")
    assert "kind: question" in text
    assert "status: new" in text
    # prose, as for a message: the line break is expanded
    assert artifact.content_of(text) == "A colleague offers k8s.\nWaiting for the word on what to build with."
    out = capsys.readouterr().out
    # the hint asks to ANSWER WITH A WORD, not to press a button (decision 06)
    assert "the human answers with a word in the session" in out
    assert "the human takes it" not in out


def test_ask_is_a_source_like_the_others(in_project, capsys):
    assert cli.main(["artifact", "add", "something"]) == 1
    assert "--ask \"question\"" in capsys.readouterr().err
    assert cli.main(["artifact", "add", "x", "--ask", "a", "--text", "b"]) == 1
    assert "exactly one source" in capsys.readouterr().err


def test_question_lives_the_same_two_states(in_project):
    cli.main(["artifact", "add", "I'll ask", "--ask", "this way or that?"])
    assert cli.main(["artifact", "taken", "01", "--word", "let's do it this way"]) == 0
    text = _text(in_project, "01")
    assert "status: taken" in text
    assert "let's do it this way" in text
