"""``tide hook ask-gate``: in an unattended session a question becomes a written note."""

from __future__ import annotations

import io
import json
from datetime import datetime, timedelta, timezone

import pytest

from tide.hooks import ask_gate

NOW = datetime(2026, 10, 9, 8, 0, 0, tzinfo=timezone.utc)


def _ts(minutes_ago: float) -> str:
    t = NOW - timedelta(minutes=minutes_ago)
    return t.strftime("%Y-%m-%dT%H:%M:%S.") + "{0:03d}Z".format(t.microsecond // 1000)


def _user(text, minutes_ago, kind="human", uid=None, content=None):
    rec = {"type": "user", "timestamp": _ts(minutes_ago), "origin": {"kind": kind},
           "uuid": uid or "u-{0}-{1}".format(kind, minutes_ago),
           "message": {"role": "user", "content": content if content is not None else text}}
    return rec


SPAWN = _user("You were started by tide in an unattended session.", 60, uid="spawn")


def _transcript(tmp_path, *records):
    path = tmp_path / "t.jsonl"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"type": "summary"}) + "\n")
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return path


@pytest.fixture
def proj(tmp_path):
    root = tmp_path / "proj"
    (root / ".tide").mkdir(parents=True)
    return root


@pytest.fixture
def unattended(monkeypatch, tmp_path):
    """An unattended session ($TIDE_UNATTENDED set)."""
    monkeypatch.setenv("TIDE_UNATTENDED", "1")
    monkeypatch.delenv("TIDE_ASK_GATE", raising=False)


def _payload(proj, transcript, tool="AskUserQuestion"):
    return {
        "tool_name": tool,
        "session_id": "claude-sid-1",
        "transcript_path": str(transcript),
        "cwd": str(proj),
        "tool_input": {"questions": [{
            "question": "Which option?", "header": "Choice", "multiSelect": False,
            "options": [{"label": "A", "description": "a"}, {"label": "B", "description": "b"}],
        }]},
    }


def _deny(payload):
    return ask_gate.deny_reason(payload, now=NOW)


# --- decision -----------------------------------------------------------------

def test_deny_when_unattended_without_live_human(unattended, proj, tmp_path):
    reason = _deny(_payload(proj, _transcript(tmp_path, SPAWN)))
    assert reason is not None
    assert reason.startswith("This is not a failure: no dialog here. This session is unattended")
    assert "in the last 10 min" in reason


def test_allow_with_live_human_two_minutes_ago(unattended, proj, tmp_path):
    t = _transcript(tmp_path, SPAWN, _user("yes, go ahead", 2))
    assert _deny(_payload(proj, t)) is None
    assert not (proj / ".tide" / "state" / "blocked-asks.jsonl").exists()


def test_allow_with_text_block_list(unattended, proj, tmp_path):
    rec = _user(None, 1, content=[{"type": "text", "text": "ok"}])
    assert _deny(_payload(proj, _transcript(tmp_path, SPAWN, rec))) is None


def test_deny_with_live_human_thirty_minutes_ago(unattended, proj, tmp_path):
    t = _transcript(tmp_path, SPAWN, _user("yes, go ahead", 30))
    assert _deny(_payload(proj, t)) is not None


def test_allow_when_attended(monkeypatch, proj, tmp_path):
    monkeypatch.delenv("TIDE_UNATTENDED", raising=False)
    assert _deny(_payload(proj, _transcript(tmp_path, SPAWN))) is None


def test_allow_when_switched_off(unattended, monkeypatch, proj, tmp_path):
    monkeypatch.setenv("TIDE_ASK_GATE", "off")
    assert _deny(_payload(proj, _transcript(tmp_path, SPAWN))) is None


def test_allow_other_tool(unattended, proj, tmp_path):
    assert _deny(_payload(proj, _transcript(tmp_path, SPAWN), tool="Bash")) is None


@pytest.mark.parametrize("rec", [
    _user("<task-notification>done</task-notification>", 1),
    _user("<system-reminder>x</system-reminder>", 1),
    _user("Another Claude session sent a message: hi", 1),
    _user("message from a neighbour", 1, kind="peer"),
    _user(None, 1, content=[{"type": "tool_result", "tool_use_id": "t", "content": "ok"}]),
])
def test_not_human_replies_do_not_count(unattended, proj, tmp_path, rec):
    assert _deny(_payload(proj, _transcript(tmp_path, SPAWN, rec))) is not None


def test_first_human_record_is_spawn_prompt(unattended, proj, tmp_path):
    fresh_spawn = _user("You were started by tide in an unattended session.", 1, uid="spawn")
    assert _deny(_payload(proj, _transcript(tmp_path, fresh_spawn))) is not None


def test_reads_only_tail(unattended, proj, tmp_path, monkeypatch):
    # Tail shorter than the file: a fresh message in the tail is seen, one sunk before the tail is not.
    pad = [{"type": "assistant", "message": {"content": "x" * 200}} for _ in range(50)]
    monkeypatch.setattr(ask_gate, "TAIL_BYTES", 2_000)
    in_tail = _transcript(tmp_path, SPAWN, *pad, _user("yes", 1))
    assert _deny(_payload(proj, in_tail)) is None
    sunk = _transcript(tmp_path, SPAWN, _user("yes", 1), *pad)
    assert _deny(_payload(proj, sunk)) is not None


# --- recording the question-----------------------------------------------------------

def test_blocked_ask_recorded(unattended, proj, tmp_path):
    reason = _deny(_payload(proj, _transcript(tmp_path, SPAWN)))
    path = proj / ".tide" / "state" / "blocked-asks.jsonl"
    assert path.is_file()
    assert "The question was recorded: {0}.".format(path) in reason
    rows = [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1
    row = rows[0]
    assert set(row) == {"id", "ts", "project", "claude_session",
                        "cwd", "questions", "answered"}
    assert len(row["id"]) == 36
    assert row["ts"] == "2026-10-09T08:00:00Z"
    assert row["project"] == "proj"
    assert row["claude_session"] == "claude-sid-1"
    assert row["cwd"] == str(proj)
    assert row["questions"] == [{"question": "Which option?", "header": "Choice",
                                 "options": ["A", "B"]}]
    assert row["answered"] is None


def test_not_recorded_outside_tide_project(unattended, tmp_path):
    bare = tmp_path / "bare"
    bare.mkdir()
    reason = _deny(_payload(bare, _transcript(tmp_path, SPAWN)))
    assert reason.endswith("The question was recorded: not recorded.")


# --- CLI wrapper -------------------------------------------------------------

def _run(monkeypatch, capsys, stdin: str):
    monkeypatch.setattr("sys.stdin", io.StringIO(stdin))
    rc = ask_gate.cmd_ask_gate(None)
    return rc, capsys.readouterr().out


def test_cli_deny_prints_pretooluse_json(unattended, monkeypatch, capsys, proj, tmp_path):
    rc, out = _run(monkeypatch, capsys,
                   json.dumps(_payload(proj, _transcript(tmp_path, SPAWN))))
    assert rc == 0
    spec = json.loads(out)["hookSpecificOutput"]
    assert spec["hookEventName"] == "PreToolUse"
    assert spec["permissionDecision"] == "deny"
    assert spec["permissionDecisionReason"].startswith(
        "This is not a failure: no dialog here.")


@pytest.mark.parametrize("stdin", ["", "{ not json", "[1, 2]", '"str"'])
def test_cli_broken_input_passes(unattended, monkeypatch, capsys, stdin):
    rc, out = _run(monkeypatch, capsys, stdin)
    assert rc == 0 and out == ""


def test_cli_other_tool_passes_silently(unattended, monkeypatch, capsys, proj, tmp_path):
    rc, out = _run(monkeypatch, capsys,
                   json.dumps(_payload(proj, _transcript(tmp_path, SPAWN), tool="Edit")))
    assert rc == 0 and out == ""


def test_cli_exception_fails_open(unattended, monkeypatch, capsys, proj, tmp_path):
    def boom(*a, **k):
        raise RuntimeError("boom")
    monkeypatch.setattr(ask_gate, "deny_reason", boom)
    rc, out = _run(monkeypatch, capsys,
                   json.dumps(_payload(proj, _transcript(tmp_path, SPAWN))))
    assert rc == 0 and out == ""


def test_merge_hooks_wires_ask_gate():
    from tide import harness

    data: dict = {}
    harness.merge_hooks(data)
    cmds = [h["command"] for g in data["hooks"]["PreToolUse"] for h in g["hooks"]]
    assert cmds.count(harness.ASK_GATE_CMD) == 1
    assert harness.merge_hooks(data) == []
