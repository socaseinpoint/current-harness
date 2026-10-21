"""'## read first' in a thread plan.md: scaffold and advisory start gate."""

from __future__ import annotations

from tide import cli
from tide.arc import curate, plan_main, stream, templates


FILLED = ("- task: T-101, as a link\n"
          "- deliver: to the owner via tide offload\n"
          "- do not duplicate: board, topics\n")


def fill_main(tdir):
    """For other tests: the thread's read-first section is filled."""
    _fill(tdir)


def _fill(tdir, body=FILLED):
    (tdir / "plan.md").write_text(
        "# plan\n\n{0}\n{1}\n## steps\n\n- [ ] 1. a | b | c\n".format(plan_main.HEADING, body),
        encoding="utf-8")


def test_template_seeds_the_main_section_with_three_hints():
    text = templates.thread_plan_md("x")
    assert plan_main.HEADING in text
    assert plan_main.section(text) == ["- " + h for h in plan_main.HINTS]
    # advisory: a fresh thread is not stamped as «required»
    assert "plan-main: required" not in templates.thread_goal_md("x")


def test_new_thread_is_born_with_plan(tmp_project):
    t = stream.new_thread(tmp_project, "fresh", goal="goal")
    assert plan_main.read(t) is not None and plan_main.live_lines(t) == []
    assert plan_main.is_scaffold(t)
    assert "only hints" in plan_main.problem(t)
    curate.drop_thread(t)  # an untouched scaffold does not fill the thread — it is dropped


def _offload(tmp_project, monkeypatch, ref, *words):
    monkeypatch.chdir(tmp_project)
    return cli.main(["offload", ref, *words])


def test_offload_has_no_start_gate_the_pulse_always_lands(tmp_project, monkeypatch, capsys):
    t = stream.new_thread(tmp_project, "gated", goal="goal")
    s = stream.new_session(tmp_project, "gated", "one")
    assert _offload(tmp_project, monkeypatch, "gated/one", "start") == 0
    assert "start" in (s / "arc.md").read_text(encoding="utf-8").split("## context")[1]

    _fill(t)
    capsys.readouterr()
    assert _offload(tmp_project, monkeypatch, "gated/one", "second") == 0
    assert "read first" not in capsys.readouterr().err
