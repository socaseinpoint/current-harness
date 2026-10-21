"""tide.arc.work — "works": deterministic agent gestures over works/*/work.md.

The machine under test: open → taken → review → done, every verb journals,
done requires the human's word.
"""

from __future__ import annotations

import pytest

from tide import cli, paths
from tide.arc import work


@pytest.fixture
def in_project(tmp_project, monkeypatch):
    monkeypatch.chdir(tmp_project)
    return tmp_project


def _text(root, key="01"):
    return (work._find(root, key) / "work.md").read_text(encoding="utf-8")


def _view(root, key="01"):
    """The work journal the way it is read — a VIEW over the acts (what show prints).

    The raw ``work.md`` is no longer good for the journal:
    a gesture lands as an ACT in the session passport, and the file's ``## log``
    is not appended. What was written to the file before that day is read
    forever, so the view gathers both the file and the acts — and a gesture must
    be checked against it, not against the raw passport.
    """
    wdir = work._find(root, key)
    return "\n".join(work.journal_view(
        root, wdir, (wdir / "work.md").read_text(encoding="utf-8")))


def _acts_of(session):
    """A session's acts as text — what the verb actually wrote.

    Needed where the view from the card won't show the gesture: a work's acts
    are read through its ``thread:``, and if the card points at a thread that is
    not on disk (or its thread was cleared), they are invisible from the card,
    though written and intact.
    """
    return (session / "arc.md").read_text(encoding="utf-8")


def _old_journal(root, *lines, key="01"):
    """Append lines to the file's ``## log`` BY HAND — "a work written before 66".

    That is how every passport looked while the verb wrote the journal itself.
    The engine no longer does that, but must read such files forever — and this
    is the only way to set them up in a test.
    """
    f = work._find(root, key) / "work.md"
    text = f.read_text(encoding="utf-8").rstrip("\n")
    if "## log" not in text:
        text += "\n\n## log"
    f.write_text(text + "\n" + "\n".join(lines) + "\n", encoding="utf-8")


def _seed(item="x", key="01"):
    """The first checklist item by hand — what ``add`` used to put there itself.

    The work's name no longer becomes an item, and numbering in
    these tests counts from the first item, the way the human sees it on the board.
    """
    cli.main(["work", "checklist", key, item])


# --- add ---------------------------------------------------------------------

def test_add_creates_passport_with_empty_checklist(in_project):
    """the work's name is the title, not its first step.

    A name-twin item happened three times: nobody did it, the
    counter lied (0/6 instead of 0/5), and there was nothing to drop it with.
    """
    rc = cli.main(["work", "add", "ship referrals",
                   "--deadline", "2026-07-16", "--for", "myapp"])
    assert rc == 0
    d = work.works_dir(in_project) / "01-ship-referrals"
    assert d.is_dir()
    text = (d / "work.md").read_text(encoding="utf-8")
    assert "# ship referrals" in text
    assert "status: open" in text
    assert "project: myapp" in text
    assert "deadline: 2026-07-16" in text
    assert "## checklist" in text
    assert "- [ ] ship referrals" not in text
    assert work.all_items(text) == []


def test_add_rejects_bad_deadline(in_project, capsys):
    rc = cli.main(["work", "add", "x", "--deadline", "tomorrow"])
    assert rc == 1
    assert "bad deadline" in capsys.readouterr().err


# --- add --cand (a candidate births a work) ------------------------------------

def _shelf(root):
    return paths.candidates_dir(root)


def test_add_from_candidate_carries_the_text_and_clears_the_shelf(in_project, acting):
    """one verb instead of two gestures — else the shelf duplicates the table."""
    cli.main(["candidate", "add", "live remote", "engine mechanics: the birth verb"])
    assert (_shelf(in_project) / "01-live-remote.md").is_file()
    rc = cli.main(["work", "add", "The remote comes alive", "--cand", "01"])
    assert rc == 0
    text = _text(in_project)
    # the name comes from the argument, the candidate's long slug does not become the title
    assert "# The remote comes alive" in text
    assert "status: open" in text          # the agreement cycle is not bypassed
    assert "## plan" in text
    assert "engine mechanics: the birth verb" in text
    # the link is a passport field (decision 38, 02.09), not a gesture on the act feed:
    # an act lives in the calling session, and a board button may have no session at all
    assert "from-cand: 01" in text
    # off the shelf, but not off the disk
    assert not (_shelf(in_project) / "01-live-remote.md").exists()
    assert (_shelf(in_project) / "__dropped__" / "01-live-remote.md").is_file()


def test_add_from_candidate_takes_the_key_by_number_slug_or_both(in_project):
    for key in ("01", "01-one", "one"):
        cli.main(["candidate", "add", "one", "the idea body"])
        assert cli.main(["work", "add", "Work", "--cand", key]) == 0
        assert not list(_shelf(in_project).glob("*.md"))


def test_add_from_candidate_shouts_when_there_is_no_such_candidate(in_project, capsys):
    rc = cli.main(["work", "add", "Work", "--cand", "77"])
    assert rc == 1
    assert "no candidate" in capsys.readouterr().err
    assert not work.works_dir(in_project).exists()


def test_add_from_candidate_keeps_the_shelf_when_the_work_is_refused(in_project):
    """A bad deadline fails the gesture ENTIRELY: the candidate must not vanish."""
    cli.main(["candidate", "add", "one", "the idea body"])
    assert cli.main(["work", "add", "Work", "--cand", "01",
                     "--deadline", "tomorrow"]) == 1
    assert (_shelf(in_project) / "01-one.md").is_file()


def test_plain_add_still_touches_no_candidate(in_project):
    cli.main(["candidate", "add", "one", "the idea body"])
    assert cli.main(["work", "add", "Work"]) == 0
    assert (_shelf(in_project) / "01-one.md").is_file()
    assert "## plan" not in _text(in_project)


def test_plain_add_has_no_from_cand_field(in_project):
    """A work without a candidate has no ``from-cand:`` line at all, not an empty one."""
    cli.main(["work", "add", "Work"])
    text = _text(in_project)
    assert "from-cand" not in text


def test_from_cand_field_is_set_once_and_no_verb_touches_it(in_project, acting):
    """Decision 38: the field is set once at birth, like ``created:`` — neither
    ``take``, ``propose``/``agree``, ``check`` with proof, nor ``close`` touches it."""
    cli.main(["candidate", "add", "one", "the idea body"])
    cli.main(["work", "add", "Work", "--cand", "01"])
    assert "from-cand: 01" in _text(in_project)
    cli.main(["work", "take", "01", "--by", "builder"])
    cli.main(["work", "propose", "01", "item"])
    cli.main(["work", "agree", "01", "--word", "yes"])
    cli.main(["work", "check", "01", "1", "--proof", "done"])
    cli.main(["work", "close", "01", "--word", "done"])
    assert "from-cand: 01" in _text(in_project)


def test_candidate_gist_drops_the_header_not_the_prose(in_project):
    """The first line of an idea often looks like a key ("engine mechanics: …")."""
    text = ("# 07-ideya\n\nfrom: -\ndropped: 2026-08-01 14:25\n\n"
            "engine mechanics: the birth verb\nsecond line\n")
    assert work._candidate_gist(text) == (
        "engine mechanics: the birth verb\nsecond line")


# --- checklist ----------------------------------------------------------------

def test_checklist_replaces_raw_item_and_journals(in_project, acting):
    cli.main(["work", "add", "ship payouts"])
    rc = cli.main(["work", "checklist", "01", "bring up prod", "run the smoke"])
    assert rc == 0
    text = _text(in_project)
    assert "- [ ] bring up prod" in text
    assert "- [ ] run the smoke" in text
    assert "- [ ] ship payouts" not in text
    assert "checklist agreed: 2 item(s)" in _view(in_project)


def test_checklist_refuses_over_checked_progress_without_force(in_project, capsys):
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "take", "01"])
    cli.main(["work", "check", "01", "1", "--proof", "p"])
    assert cli.main(["work", "checklist", "01", "new"]) == 1
    assert "replacing erases progress" in capsys.readouterr().err
    assert cli.main(["work", "checklist", "01", "new", "--force"]) == 0
    assert "- [ ] new" in _text(in_project)


# --- plan (## plan) -----------------------------------------------------------

def test_plan_lands_between_description_and_checklist(in_project, acting):
    cli.main(["work", "add", "ship payouts"])
    rc = cli.main(["work", "plan", "01", "take a snapshot\\nrun the smoke"])
    assert rc == 0
    text = _text(in_project)
    assert "## plan" in text
    assert "take a snapshot\nrun the smoke" in text  # \n became a newline
    assert text.index("## plan") < text.index("## checklist")
    assert text.index("created:") < text.index("## plan")
    assert "plan proposed by the agent" in _view(in_project)


def test_plan_replaces_body_and_moves_no_status(in_project, acting):
    cli.main(["work", "add", "x"])
    cli.main(["work", "plan", "01", "first pass"])
    assert cli.main(["work", "plan", "01", "second pass"]) == 0
    text = _text(in_project)
    assert "second pass" in text
    assert "first pass" not in text
    assert text.count("## plan") == 1
    assert "status: open" in text  # a plan is the agent's word, not a status gesture
    assert "plan updated by the agent" in _view(in_project)


def test_plan_refuses_empty_and_closed(in_project, capsys):
    cli.main(["work", "add", "x"])
    assert cli.main(["work", "plan", "01", "  "]) == 1
    assert "empty plan" in capsys.readouterr().err
    cli.main(["work", "close", "01", "--word", "ok"])
    assert cli.main(["work", "plan", "01", "too late"]) == 1
    assert "tide work reopen first" in capsys.readouterr().err


# --- propose (- [?]) ----------------------------------------------------------

def test_propose_appends_question_items_with_real_numbers(in_project, acting, capsys):
    cli.main(["work", "add", "ship payouts"])  # gives item 1
    _seed("ship payouts")
    capsys.readouterr()
    rc = cli.main(["work", "propose", "01", "bring up prod", "run the smoke"])
    assert rc == 0
    assert "proposed items 2–3" in capsys.readouterr().out
    text = _text(in_project)
    assert "- [ ] ship payouts" in text
    assert "- [?] bring up prod" in text
    assert "- [?] run the smoke" in text
    assert "proposed items 2–3 (wait for the human's \"yes\")" in _view(in_project)
    assert "status: open" in text


def test_propose_hint_puts_the_verb_first_no_bare_button_promise(in_project, capsys):
    """Release panel, finding 2: the boxed board is read-only — there are no buttons.

    The hint after propose must lead to the command (tide work agree --word);
    the button is mentioned only as a live-board option, not as the first path.
    """
    cli.main(["work", "add", "x"])
    _seed()
    capsys.readouterr()
    cli.main(["work", "propose", "01", "step"])
    out = capsys.readouterr().out
    assert "tide work agree --word" in out
    assert "button on the board" not in out  # a promise of a button the box lacks
    assert "live board" in out


def test_review_hint_puts_close_word_first_no_bare_button_promise(in_project, capsys):
    """There is no "close" button on the board at all any more (word of 02.09) —
    and the hint never promises one in any form: one path, the human's word and the verb."""
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "take", "01"])
    capsys.readouterr()
    cli.main(["work", "check", "01", "1", "--proof", "p"])
    out = capsys.readouterr().out
    assert "→ review" in out
    assert "tide work close --word" in out
    assert "no board button" in out      # said plainly: there is no button


def test_propose_single_item_speaks_singular(in_project, acting):
    cli.main(["work", "add", "x"])
    _seed()
    assert cli.main(["work", "propose", "01", "finish the tail"]) == 0
    assert "proposed item 2 (waits for the human's \"yes\")" in _view(in_project)


def test_standing_offer_holds_review_back(in_project):
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "propose", "01", "maybe this too"])
    cli.main(["work", "take", "01"])
    cli.main(["work", "check", "01", "1", "--proof", "p"])
    text = _text(in_project)
    # the checklist is closed, the conversation is not: while a "- [?]" stands the work is not up for acceptance
    assert "status: taken" in text
    assert "- [?] maybe this too" in text
    assert "→ review" not in text
    # an offer still does not count as progress — the checklist has one item
    assert work.items(text) == [(True, "x")]


def test_check_refuses_a_proposed_item_and_keeps_the_file(in_project, capsys):
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "propose", "01", "not agreed yet"])
    cli.main(["work", "take", "01"])
    before = _text(in_project)
    assert cli.main(["work", "check", "01", "2", "--proof", "did it"]) == 1
    assert "item 2 is still an offer" in capsys.readouterr().err
    assert _text(in_project) == before  # a refusal does not touch the file


def test_every_hint_survives_a_verbatim_paste(in_project, capsys):
    """the teaching message must not send you back to argparse.

    The hints used to read `--word «their word»`, and guillemets are not shell
    quotes: pasting one split it into two words and produced
    `error: unrecognized arguments: word»`. `<N>` was worse — the shell reads it
    as a redirect before tide is even reached. Every command a message prints must
    paste and run as-is.
    """
    import re
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "propose", "01", "an offer"])
    cli.main(["work", "take", "01"])
    capsys.readouterr()
    argvs = [["work", "check", "01"], ["work", "check", "01", "1"],
             ["work", "close", "01"], ["work", "agree", "01", "2"],
             ["work", "agree", "01", "--drop", "2"], ["work", "fix", "01", "tail"],
             ["work", "title", "01", "name"], ["work", "dispatch", "01"],
             ["work", "drop", "01"], ["work", "drop", "01", "1"]]
    hints = []
    for argv in argvs:
        cli.main(argv)
        err = capsys.readouterr().err
        hints += [h.strip() for h in re.findall(r"tide work [^;.\n]*", err)]
    assert hints, "the messages stopped printing commands at all"
    for hint in hints:
        # shell metacharacters that mangle a paste: guillemets split on the space
        # inside them, <> redirect, () subshell.
        assert "«" not in hint and "»" not in hint, hint
        assert not re.search(r"[<>()]", hint), hint


def test_a_pasted_placeholder_number_is_answered_by_tide(in_project, capsys):
    # The hint prints a literal N. Pasted before substituting, argparse's
    # type=int would say "invalid int value: 'N'" — the parser's voice at exactly
    # the wrong moment. tide answers it instead.
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "take", "01"])
    capsys.readouterr()
    assert cli.main(["work", "check", "01", "N", "--proof", "p"]) == 1
    err = capsys.readouterr().err
    assert "is not an item number" in err
    assert "invalid int value" not in err
    assert cli.main(["work", "drop", "01", "N", "--word", "w"]) == 1
    assert "is not an item number" in capsys.readouterr().err


def test_the_human_gestures_never_answer_in_argparse(in_project, capsys):
    """the six SIGNATURE verbs answer in tide's words, not the parser's.

    A person meets these in their first hour: saying "yes" to a plan, closing a work
    with their word. `error: the following arguments are required: --word` is the
    worst first impression tide can make at the moment someone signs something.
    Each refusal must name the gesture, say what stayed as it was, and give the
    command with the key already filled in.
    """
    cli.main(["work", "add", "ship payouts"])
    _seed()
    cli.main(["work", "propose", "01", "one more offer"])
    cli.main(["work", "take", "01"])
    capsys.readouterr()
    cases = [
        (["work", "close", "01"],                    "done is set by the human", "stays open"),
        (["work", "agree", "01", "2"],               "the human agrees", "the items stay offers"),
        (["work", "agree", "01", "--drop", "2"],     "dropping an offer", "nothing dropped"),
        (["work", "fix", "01", "tail"],              "a fix carries the human's afterthought", "nothing added"),
        (["work", "title", "01", "new name"],        "the human renames a work", "the title stays as it was"),
        (["work", "dispatch", "01"],                 "who was dispatched", "nobody dispatched"),
        (["work", "drop", "01", "1"],                "only the human can drop an agreed item", "stays in place"),
    ]
    before = _text(in_project)
    for argv, whose, kept in cases:
        assert cli.main(argv) == 1, argv
        err = capsys.readouterr().err
        assert whose in err, (argv, err)
        assert kept in err, (argv, err)          # what stayed as it was
        assert "tide work" in err, (argv, err)   # the next gesture, spelled out
        assert "required:" not in err, (argv, err)   # never the parser's voice
    assert _text(in_project) == before   # seven refusals, file untouched


def test_drop_without_an_item_number_answers_in_tide_words(in_project, capsys):
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "take", "01"])
    before = _text(in_project)
    assert cli.main(["work", "drop", "01"]) == 1
    err = capsys.readouterr().err
    assert "give the item number" in err
    assert "tide work show 01" in err
    assert _text(in_project) == before


def test_a_blank_word_is_still_refused(in_project, capsys):
    # Relaxing argparse must NOT relax the requirement: whitespace is not a word.
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "take", "01"])
    before = _text(in_project)
    assert cli.main(["work", "close", "01", "--word", "   "]) == 1
    assert "done is set by the human" in capsys.readouterr().err
    assert _text(in_project) == before


def test_check_without_proof_answers_in_tide_words(in_project, capsys):
    # argparse used to answer this with "the following arguments are
    # required: --proof" — the parser's words, no hint of the next gesture, in the
    # first hour of a person's use. The engine must say why proof exists and what
    # to type.
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "take", "01"])
    before = _text(in_project)
    assert cli.main(["work", "check", "01", "1"]) == 1
    err = capsys.readouterr().err
    assert "a check without proof is no gesture" in err
    assert "tide work check 01 1 --proof" in err   # the next gesture, spelled out
    assert "required:" not in err                  # not argparse's voice
    assert _text(in_project) == before             # refusal never touches the file


def test_check_without_an_item_number_answers_in_tide_words(in_project, capsys):
    # `tide work check 01` is the other half of the same stumble.
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "take", "01"])
    before = _text(in_project)
    assert cli.main(["work", "check", "01"]) == 1
    err = capsys.readouterr().err
    assert "give the item number" in err
    assert "tide work show 01" in err              # where the numbers are
    assert _text(in_project) == before


def test_check_with_blank_proof_is_refused_too(in_project, capsys):
    # Whitespace is not a proof — and the message must be the same one.
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "take", "01"])
    assert cli.main(["work", "check", "01", "1", "--proof", "   "]) == 1
    assert "a check without proof is no gesture" in capsys.readouterr().err


def test_uncheck_refuses_a_proposed_item(in_project, capsys):
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "propose", "01", "not agreed yet"])
    cli.main(["work", "take", "01"])
    assert cli.main(["work", "uncheck", "01", "2"]) == 1
    assert "waiting for the human's \"yes\"" in capsys.readouterr().err


def test_checklist_agreement_replaces_proposals(in_project):
    cli.main(["work", "add", "x"])
    cli.main(["work", "propose", "01", "an offer"])
    assert cli.main(["work", "checklist", "01", "agreed"]) == 0
    text = _text(in_project)
    assert "- [ ] agreed" in text
    assert "[?]" not in text


# --- item descriptions (title + indented details) ------------------------------

def test_propose_splits_title_and_description(in_project):
    cli.main(["work", "add", "x"])
    rc = cli.main(["work", "propose", "01",
                   "Retrain the handoff ritual\\ndraft first — then curation"])
    assert rc == 0
    text = _text(in_project)
    assert "- [?] Retrain the handoff ritual\n  draft first — then curation\n" in text


def test_description_keeps_multiple_lines_under_one_item(in_project):
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "propose", "01", "Title\\nfirst\\nsecond", "Second item"])
    text = _text(in_project)
    assert "- [?] Title\n  first\n  second\n- [?] Second item\n" in text
    # a description is not an item: numbers count only "- [" lines
    assert [t for _, t in work.all_items(text)] == ["x", "Title", "Second item"]


def test_item_blocks_read_description_back(in_project):
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "propose", "01", "Title\\ndetails"])
    blocks = work.item_blocks(_text(in_project))
    assert blocks == [(" ", "x", ""), ("?", "Title", "details")]


def test_description_does_not_shift_item_numbers(in_project, acting, capsys):
    cli.main(["work", "add", "x"])
    cli.main(["work", "checklist", "01", "First\\ndetails of the first", "Second"])
    cli.main(["work", "take", "01"])
    capsys.readouterr()
    assert cli.main(["work", "check", "01", "2", "--proof", "commit abc"]) == 0
    text = _text(in_project)
    assert "- [ ] First\n  details of the first\n- [x] Second\n" in text
    # the gesture carries the item's TITLE, not its description
    assert "item 2 ✓ «Second»" in _view(in_project)


def test_check_keeps_description_and_autoreviews(in_project):
    cli.main(["work", "add", "x"])
    cli.main(["work", "checklist", "01", "Only one\\ndetails"])
    cli.main(["work", "take", "01"])
    assert cli.main(["work", "check", "01", "1", "--proof", "p"]) == 0
    text = _text(in_project)
    assert "- [x] Only one\n  details\n" in text
    assert "status: review" in text  # a description does not count as an undone item


def test_uncheck_by_index_survives_descriptions(in_project):
    cli.main(["work", "add", "x"])
    cli.main(["work", "checklist", "01", "First\\ndetails", "Second\\nmore details"])
    cli.main(["work", "take", "01"])
    cli.main(["work", "check", "01", "2", "--proof", "p"])
    assert cli.main(["work", "uncheck", "01", "2"]) == 0
    text = _text(in_project)
    assert "- [ ] Second\n  more details\n" in text


def test_item_without_title_is_refused(in_project, capsys):
    cli.main(["work", "add", "x"])
    assert cli.main(["work", "propose", "01", "\\nonly a description"]) == 1
    assert "item without a title" in capsys.readouterr().err


def test_show_prints_description_indented_under_title(in_project, capsys):
    cli.main(["work", "add", "x"])
    cli.main(["work", "propose", "01", "Title\\ndetails"])
    capsys.readouterr()
    assert cli.main(["work", "show", "01"]) == 0
    assert "- [?] Title\n  details" in capsys.readouterr().out


# --- propose --replace --------------------------------------------------------

def test_propose_replace_withdraws_old_offers_with_descriptions(in_project, acting,
                                                                capsys):
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "propose", "01", "Old\\nold details", "Also old"])
    capsys.readouterr()
    rc = cli.main(["work", "propose", "01", "--replace", "New\\nnew details"])
    assert rc == 0
    assert "offers replaced: item 2" in capsys.readouterr().out
    text = _text(in_project)
    assert "Old" not in text
    assert "old details" not in text
    assert "Also old" not in text
    assert "- [?] New\n  new details\n" in text
    assert "offers replaced: item 2 (waits for the human's \"yes\")" in _view(in_project)


def test_propose_replace_keeps_agreed_and_checked_items(in_project, acting):
    cli.main(["work", "add", "x"])
    cli.main(["work", "checklist", "01", "Agreed", "Second agreed"])
    cli.main(["work", "take", "01"])
    cli.main(["work", "check", "01", "1", "--proof", "p"])
    cli.main(["work", "propose", "01", "An offer"])
    assert cli.main(["work", "propose", "01", "--replace", "Now like this",
                     "And like this"]) == 0
    text = _text(in_project)
    assert "- [x] Agreed" in text
    assert "- [ ] Second agreed" in text
    assert "- [?] An offer" not in text
    assert "- [?] Now like this" in text
    assert "offers replaced: items 3–4" in _view(in_project)
    assert "status: taken" in text  # replacing offers is not a status gesture


def test_propose_without_replace_still_appends(in_project):
    cli.main(["work", "add", "x"])
    cli.main(["work", "propose", "01", "First offer"])
    assert cli.main(["work", "propose", "01", "Second offer"]) == 0
    text = _text(in_project)
    assert "- [?] First offer" in text
    assert "- [?] Second offer" in text


# --- agree (the human's word instead of a button) -------------------------------

def test_agree_flips_proposal_and_keeps_description(in_project, acting, capsys):
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "propose", "01", "Bring up prod\\nsmoke first"])
    capsys.readouterr()
    rc = cli.main(["work", "agree", "01", "2", "--word", "yes, let's do it"])
    assert rc == 0
    assert "agreed: item 2" in capsys.readouterr().out
    text = _text(in_project)
    assert "- [ ] Bring up prod\n  smoke first\n" in text
    assert "[?]" not in text
    assert "item 2 confirmed · word: «yes, let's do it»" in _view(in_project)
    assert "status: open" in text  # agreement is not a status gesture


def test_agree_refuses_without_word_and_keeps_the_file(in_project, capsys):
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "propose", "01", "an offer"])
    before = _text(in_project)
    assert cli.main(["work", "agree", "01", "2", "--word", "  "]) == 1
    assert "the human agrees" in capsys.readouterr().err
    assert _text(in_project) == before  # a refusal does not touch the file


def test_agree_refuses_agreed_and_checked_items(in_project, capsys):
    cli.main(["work", "add", "x"])
    cli.main(["work", "checklist", "01", "Agreed", "Second"])
    cli.main(["work", "take", "01"])
    cli.main(["work", "check", "01", "1", "--proof", "p"])
    assert cli.main(["work", "agree", "01", "1", "--word", "aha"]) == 1
    assert "item 1 is checked — it is no longer an offer" in capsys.readouterr().err
    assert cli.main(["work", "agree", "01", "2", "--word", "aha"]) == 1
    assert "item 2 is agreed — it is no longer an offer" in capsys.readouterr().err
    assert cli.main(["work", "agree", "01", "9", "--word", "aha"]) == 1
    assert "no item 9" in capsys.readouterr().err


def test_agree_without_numbers_takes_every_offer(in_project, acting):
    cli.main(["work", "add", "x"])
    cli.main(["work", "propose", "01", "First\\ndetails", "Second"])
    assert cli.main(["work", "agree", "01", "--word", "yes all correct"]) == 0
    text = _text(in_project)
    assert "- [ ] First\n  details\n- [ ] Second\n" in text
    assert "offers confirmed · word: «yes all correct»" in _view(in_project)


def test_agree_all_flag_matches_bare_call(in_project, acting, capsys):
    cli.main(["work", "add", "x"])
    cli.main(["work", "propose", "01", "First", "Second"])
    capsys.readouterr()
    assert cli.main(["work", "agree", "01", "--all", "--word", "yes"]) == 0
    assert "(all offers)" in capsys.readouterr().out
    text = _text(in_project)
    assert "[?]" not in text
    assert "offers confirmed · word: «yes»" in _view(in_project)


def test_agree_all_refuses_when_nothing_is_offered(in_project, capsys):
    cli.main(["work", "add", "x"])
    assert cli.main(["work", "agree", "01", "--word", "yes"]) == 1
    assert "no proposed items" in capsys.readouterr().err


def test_agree_takes_part_of_the_offer_and_leaves_the_rest(in_project, acting):
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "propose", "01", "First", "Second", "Third"])
    assert cli.main(["work", "agree", "01", "2", "4", "--word", "these two"]) == 0
    text = _text(in_project)
    assert "- [ ] First\n- [?] Second\n- [ ] Third\n" in text
    view = _view(in_project)
    assert "item 2 confirmed · word: «these two»" in view
    assert "item 4 confirmed · word: «these two»" in view


# --- agree --drop (the symmetric "no") ------------------------------------------

def test_agree_drop_removes_item_with_its_description(in_project, acting, capsys):
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "propose", "01", "Extra\\nextra details", "Needed"])
    capsys.readouterr()
    rc = cli.main(["work", "agree", "01", "--drop", "2", "--word", "not needed"])
    assert rc == 0
    assert "dropped: item 2" in capsys.readouterr().out
    text = _text(in_project)
    assert "Extra" not in text
    assert "extra details" not in text
    assert "- [?] Needed" in text
    assert "proposed item 2 dropped · word: «not needed»" in _view(in_project)


def test_agree_drop_renumbers_the_rest_for_the_next_gesture(in_project):
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "propose", "01", "First", "Second", "Third"])
    assert cli.main(["work", "agree", "01", "--drop", "2", "--word", "no"]) == 0
    assert [t for _, t in work.all_items(_text(in_project))] == [
        "x", "Second", "Third"]
    # "Second" slid to number 2 — agree by the NEW number
    assert cli.main(["work", "agree", "01", "2", "--word", "yes"]) == 0
    assert "- [ ] Second\n- [?] Third\n" in _text(in_project)


def test_agree_drop_several_keeps_the_numbers_the_human_saw(in_project, acting):
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "propose", "01", "First", "Second\\ndetails", "Third"])
    assert cli.main(["work", "agree", "01", "--drop", "2", "4",
                     "--word", "both miss"]) == 0
    text = _text(in_project)
    assert [t for _, t in work.all_items(text)] == ["x", "Second"]
    view = _view(in_project)
    assert "proposed item 2 dropped · word: «both miss»" in view
    assert "proposed item 4 dropped · word: «both miss»" in view


def test_agree_drop_refuses_agreed_item_and_mixed_call(in_project, capsys):
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "propose", "01", "An offer"])
    assert cli.main(["work", "agree", "01", "--drop", "1", "--word", "no"]) == 1
    assert "no longer an offer" in capsys.readouterr().err
    assert cli.main(["work", "agree", "01", "2", "--drop", "2",
                     "--word", "both"]) == 1
    assert "--drop is a separate gesture" in capsys.readouterr().err
    assert "- [?] An offer" in _text(in_project)


# --- review gate: a standing offer holds acceptance back -------------------------

def test_propose_pulls_a_reviewed_work_back_to_taken(in_project, acting, capsys):
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "take", "01"])
    cli.main(["work", "check", "01", "1", "--proof", "p"])
    assert "status: review" in _text(in_project)
    capsys.readouterr()
    assert cli.main(["work", "propose", "01", "and this too"]) == 0
    assert "the work is back in progress" in capsys.readouterr().out
    text = _text(in_project)
    assert "status: taken" in text
    assert ("items proposed — the work is back in progress (review → taken)"
            in _view(in_project))


def test_agree_of_last_offer_waits_for_the_proof(in_project, capsys):
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "take", "01"])
    cli.main(["work", "check", "01", "1", "--proof", "p"])   # → review
    cli.main(["work", "propose", "01", "Finish the tail"])     # → back to taken
    assert cli.main(["work", "agree", "01", "2", "--word", "yes, finish it"]) == 0
    text = _text(in_project)
    assert "- [ ] Finish the tail" in text
    assert "status: taken" in text  # agreed ≠ done
    capsys.readouterr()
    assert cli.main(["work", "check", "01", "2", "--proof", "commit abc"]) == 0
    assert "→ review" in capsys.readouterr().out
    assert "status: review" in _text(in_project)


def test_agree_pulls_back_a_work_left_in_review_with_offers(in_project, acting):
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "take", "01"])
    cli.main(["work", "check", "01", "1", "--proof", "p"])   # → review
    f = work._find(in_project, "01") / "work.md"
    # that is how an old work looked: the old engine let it into review with a standing "- [?]"
    f.write_text(_text(in_project).replace("- [x] x", "- [x] x\n- [?] Tail"),
                 encoding="utf-8")
    assert cli.main(["work", "agree", "01", "2", "--word", "yes"]) == 0
    text = _text(in_project)
    assert "status: taken" in text
    assert "checklist incomplete again → taken" in _view(in_project)


def test_drop_of_last_offer_closes_the_review_gate(in_project, acting, capsys):
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "take", "01"])
    cli.main(["work", "propose", "01", "Maybe this too"])
    cli.main(["work", "check", "01", "1", "--proof", "p"])
    assert "status: taken" in _text(in_project)  # the offer holds the gate
    capsys.readouterr()
    rc = cli.main(["work", "agree", "01", "--drop", "2", "--word", "no, enough"])
    assert rc == 0
    assert "→ review" in capsys.readouterr().out
    text = _text(in_project)
    assert "status: review" in text
    assert "all items checked → review" in _view(in_project)


def test_drop_of_one_of_two_offers_keeps_the_work_open(in_project):
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "take", "01"])
    cli.main(["work", "propose", "01", "First", "Second"])
    cli.main(["work", "check", "01", "1", "--proof", "p"])
    assert cli.main(["work", "agree", "01", "--drop", "2", "--word", "no"]) == 0
    assert "status: taken" in _text(in_project)  # the second offer still stands


# --- fix (the human's afterthought at acceptance) --------------------------------

def test_fix_refuses_without_word_and_keeps_the_file(in_project, capsys):
    cli.main(["work", "add", "x"])
    before = _text(in_project)
    assert cli.main(["work", "fix", "01", "and this too", "--word", "  "]) == 1
    assert "a fix carries the human's afterthought" in capsys.readouterr().err
    assert _text(in_project) == before  # a refusal does not touch the file


def test_fix_lands_agreed_in_its_own_section(in_project, acting, capsys):
    cli.main(["work", "add", "ship payouts"])
    _seed("ship payouts")
    capsys.readouterr()
    rc = cli.main(["work", "fix", "01", "Finish the tail\\nand the dashboard too",
                   "--word", "there's still a tail left"])
    assert rc == 0
    assert "fix 2 added" in capsys.readouterr().out
    text = _text(in_project)
    assert "## fixes" in text
    # the human's word = agreement: the item is "- [ ]" at once, no dotted line needed
    assert "- [ ] Finish the tail\n  and the dashboard too\n" in text
    assert "[?]" not in text
    assert "fix 2 added · word: «there's still a tail left»" in _view(in_project)
    # the section sits RIGHT AFTER the checklist — fix numbers continue it
    assert text.index("## checklist") < text.index("## fixes")


def test_fix_numbering_runs_through_both_sections(in_project, acting, capsys):
    cli.main(["work", "add", "x"])
    cli.main(["work", "checklist", "01", "First", "Second", "Third", "Fourth"])
    capsys.readouterr()
    assert cli.main(["work", "fix", "01", "Fifth is a fix",
                     "--word", "finish it"]) == 0
    assert "fix 5 added" in capsys.readouterr().out
    assert [t for _, t in work.all_items(_text(in_project))] == [
        "First", "Second", "Third", "Fourth", "Fifth is a fix"]
    # a check by the running number hits the fix, not the checklist
    cli.main(["work", "take", "01"])
    assert cli.main(["work", "check", "01", "5", "--proof", "commit abc"]) == 0
    text = _text(in_project)
    assert "- [x] Fifth is a fix" in text
    assert "item 5 ✓ «Fifth is a fix»" in _view(in_project)
    assert "- [ ] Fourth" in text  # the neighbouring number did not shift


def test_fix_span_speaks_plural(in_project, acting, capsys):
    cli.main(["work", "add", "x"])
    _seed()
    capsys.readouterr()
    assert cli.main(["work", "fix", "01", "One", "Two", "--word", "and this"]) == 0
    assert "fixes 2–3 added" in capsys.readouterr().out
    assert "fixes 2–3 added · word: «and this»" in _view(in_project)


def test_second_fix_appends_to_the_same_section(in_project, acting):
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "fix", "01", "First fix", "--word", "one"])
    assert cli.main(["work", "fix", "01", "Second fix", "--word", "two"]) == 0
    text = _text(in_project)
    assert text.count("## fixes") == 1
    assert "- [ ] First fix\n- [ ] Second fix\n" in text
    assert "fix 3 added · word: «two»" in _view(in_project)


def test_fix_pulls_a_reviewed_work_back_to_taken(in_project, acting, capsys):
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "take", "01"])
    cli.main(["work", "check", "01", "1", "--proof", "p"])
    assert "status: review" in _text(in_project)
    capsys.readouterr()
    assert cli.main(["work", "fix", "01", "This too",
                     "--word", "almost, but finish it"]) == 0
    assert "the work is back in progress" in capsys.readouterr().out
    text = _text(in_project)
    assert "status: taken" in text
    assert "a fix put it back in progress (review → taken)" in _view(in_project)


def test_review_waits_for_the_fixes_too(in_project, capsys):
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "take", "01"])
    cli.main(["work", "check", "01", "1", "--proof", "p"])       # → review
    cli.main(["work", "fix", "01", "Tail", "--word", "finish it"])  # → back
    assert "status: taken" in _text(in_project)  # the checklist is closed, the fix is not
    capsys.readouterr()
    assert cli.main(["work", "check", "01", "2", "--proof", "commit abc"]) == 0
    assert "→ review" in capsys.readouterr().out
    assert "status: review" in _text(in_project)


def test_uncheck_of_a_fix_falls_back_from_review(in_project):
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "take", "01"])
    cli.main(["work", "fix", "01", "Tail", "--word", "finish it"])
    cli.main(["work", "check", "01", "1", "--proof", "p"])
    cli.main(["work", "check", "01", "2", "--proof", "p"])
    assert "status: review" in _text(in_project)
    assert cli.main(["work", "uncheck", "01", "2", "--reason", "did not land"]) == 0
    text = _text(in_project)
    assert "- [ ] Tail" in text
    assert "status: taken" in text


def test_fix_refuses_a_closed_work(in_project, capsys):
    cli.main(["work", "add", "x"])
    cli.main(["work", "close", "01", "--word", "ok"])
    assert cli.main(["work", "fix", "01", "too late", "--word", "if only"]) == 1
    assert "tide work reopen first" in capsys.readouterr().err


def test_checklist_replacement_leaves_the_fixes_alone(in_project):
    cli.main(["work", "add", "x"])
    cli.main(["work", "fix", "01", "Afterthought", "--word", "this too"])
    assert cli.main(["work", "checklist", "01", "New step"]) == 0
    text = _text(in_project)
    assert "- [ ] New step" in text
    assert "- [ ] Afterthought" in text
    assert text.index("New step") < text.index("Afterthought")


def test_proposal_takes_its_number_before_the_fixes(in_project, acting, capsys):
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "fix", "01", "Afterthought", "--word", "this too"])
    capsys.readouterr()
    # the offer sits in the checklist — number 2, the fix moves to 3
    assert cli.main(["work", "propose", "01", "An offer"]) == 0
    assert "proposed item 2" in capsys.readouterr().out
    assert [t for _, t in work.all_items(_text(in_project))] == [
        "x", "An offer", "Afterthought"]
    assert cli.main(["work", "agree", "01", "2", "--word", "yes"]) == 0
    text = _text(in_project)
    assert "- [ ] An offer\n" in text
    assert "item 2 confirmed · word: «yes»" in _view(in_project)


def test_list_counts_both_blocks_as_one_progress(in_project, capsys):
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "fix", "01", "Afterthought", "--word", "this too"])
    cli.main(["work", "take", "01"])
    cli.main(["work", "check", "01", "1", "--proof", "p"])
    capsys.readouterr()
    cli.main(["work", "list"])
    assert "1/2" in capsys.readouterr().out


def test_show_prints_the_fixes_section(in_project, capsys):
    cli.main(["work", "add", "x"])
    cli.main(["work", "fix", "01", "Afterthought\\ndetails", "--word", "and this"])
    capsys.readouterr()
    assert cli.main(["work", "show", "01"]) == 0
    out = capsys.readouterr().out
    assert "## fixes" in out
    assert out.index("## checklist") < out.index("## fixes")
    assert "- [ ] Afterthought\n  details" in out


# --- take --------------------------------------------------------------------

def test_take_moves_open_to_taken_and_journals(in_project, acting):
    cli.main(["work", "add", "ship payouts"])
    rc = cli.main(["work", "take", "01", "--by", "myapp-agent",
                   "--word", "take the payouts"])
    assert rc == 0
    text = _text(in_project)
    assert "status: taken" in text
    assert "taken-by: myapp-agent" in text
    assert "taken-at: " in text
    assert ("taken (myapp-agent) · thread 01-@release · "
            "word: «take the payouts»" in _view(in_project))


def test_take_refuses_second_take_and_done(in_project, capsys):
    cli.main(["work", "add", "x"])
    cli.main(["work", "take", "01"])
    assert cli.main(["work", "take", "01"]) == 1
    assert "is already taken" in capsys.readouterr().err
    cli.main(["work", "close", "01", "--word", "close it"])
    assert cli.main(["work", "take", "01"]) == 1
    assert "tide work reopen first" in capsys.readouterr().err


# --- dispatch (builder dispatched) ----------------------------------------------

def test_dispatch_journals_the_builder_and_moves_no_status(in_project, acting,
                                                           capsys):
    """Candidates 179/180: dispatching a builder is no longer kept in someone's head."""
    cli.main(["work", "add", "x"])
    cli.main(["work", "take", "01"])
    capsys.readouterr()
    rc = cli.main(["work", "dispatch", "01", "--to", "04-pult"])
    assert rc == 0
    assert "builder dispatched: 04-pult" in capsys.readouterr().out
    assert "builder dispatched: 04-pult" in _view(in_project)
    assert "status: taken" in _text(in_project)  # an event, not a state


def test_dispatch_again_is_another_line_not_an_error(in_project, acting):
    """Workers get re-dispatched — each dispatch is its own fact with its own time."""
    cli.main(["work", "add", "x"])
    cli.main(["work", "take", "01"])
    assert cli.main(["work", "dispatch", "01", "--to", "first"]) == 0
    assert cli.main(["work", "dispatch", "01", "--to", "second"]) == 0
    view = _view(in_project)
    assert "builder dispatched: first" in view
    assert "builder dispatched: second" in view


def test_dispatch_refuses_a_work_nobody_took(in_project, capsys):
    """A dispatch on open is a hole in the cycle: no plan, no "yes" said."""
    cli.main(["work", "add", "x"])
    assert cli.main(["work", "dispatch", "01", "--to", "worker"]) == 1
    assert "builders go to a TAKEN" in capsys.readouterr().err
    assert "builder dispatched" not in _text(in_project)


def test_dispatch_refuses_review_and_done(in_project, capsys):
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "take", "01"])
    cli.main(["work", "check", "01", "1", "--proof", "p"])  # → review
    assert cli.main(["work", "dispatch", "01", "--to", "worker"]) == 1
    assert "builders go to a TAKEN" in capsys.readouterr().err
    cli.main(["work", "close", "01", "--word", "ok"])
    assert cli.main(["work", "dispatch", "01", "--to", "worker"]) == 1
    assert "tide work reopen first" in capsys.readouterr().err


def test_dispatch_wants_a_name(in_project, capsys):
    cli.main(["work", "add", "x"])
    cli.main(["work", "take", "01"])
    assert cli.main(["work", "dispatch", "01", "--to", "  "]) == 1
    assert "who was dispatched" in capsys.readouterr().err


# --- responsible thread -------------------------------------------------------

def test_take_records_explicit_thread(in_project, acting):
    cli.main(["work", "add", "x"])
    rc = cli.main(["work", "take", "01", "--thread", "19-@work"])
    assert rc == 0
    text = _text(in_project)
    assert "thread: 19-@work" in text
    # thread 19-@work is not on disk, the card's view will not find its acts —
    # read them where the verb wrote them: in the session passport
    assert "thread 19-@work" in _acts_of(acting)


def test_thread_verb_sets_and_clears(in_project, acting):
    cli.main(["work", "add", "x"])
    assert cli.main(["work", "thread", "01", "--set", "12-@news"]) == 0
    assert "thread: 12-@news" in _text(in_project)
    assert "responsible thread → 12-@news" in _acts_of(acting)
    assert cli.main(["work", "thread", "01", "--clear"]) == 0
    assert "thread:" not in _text(in_project)
    assert "thread cleared" in _acts_of(acting)


def test_take_auto_resolves_caller_thread(in_project, monkeypatch):
    # a session arc pinned to our sid → take stamps its thread with no flag
    sid = "auto-sid-abc"
    sess = work.paths.arcs_dir(in_project) / "09-@build" / "arcs" / "01-do"
    sess.mkdir(parents=True)
    (sess / "arc.md").write_text(
        "# do\n\ntitle: do\nclaude-session: {0}\n".format(sid),
        encoding="utf-8")
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", sid)
    cli.main(["work", "add", "y"])
    assert cli.main(["work", "take", "01"]) == 0
    assert "thread: 09-@build" in _text(in_project)


def test_thread_works_lists_only_the_live_ones_of_that_thread(in_project):
    cli.main(["work", "add", "ours live"])
    _seed()
    cli.main(["work", "add", "ours closed"])
    cli.main(["work", "add", "someone else's"])
    cli.main(["work", "thread", "01", "--set", "25-@sloy"])
    cli.main(["work", "thread", "02", "--set", "25-@sloy"])
    cli.main(["work", "thread", "03", "--set", "07-@drugaya"])
    cli.main(["work", "close", "02", "--word", "done"])

    recs = work.thread_works(in_project, "25-@sloy")
    assert [r["num"] for r in recs] == ["01"]
    assert recs[0]["title"] == "ours live"
    assert (recs[0]["status"], recs[0]["done"], recs[0]["total"]) == ("open", 0, 1)
    # closed ones are shown only when asked for
    assert [r["num"] for r in work.thread_works(in_project, "25-@sloy",
                                                live_only=False)] == ["01", "02"]


def test_thread_works_matches_a_cross_project_address(in_project):
    cli.main(["work", "add", "x"])
    cli.main(["work", "thread", "01", "--set", "proj/25-@sloy"])
    assert len(work.thread_works(in_project, "25-@sloy")) == 1


def test_thread_works_counts_progress_and_reads_the_cursor(in_project):
    cli.main(["work", "add", "x"])
    cli.main(["work", "checklist", "01", "one", "two", "three"])
    cli.main(["work", "thread", "01", "--set", "25-@sloy"])
    cli.main(["work", "take", "01", "--thread", "25-@sloy"])
    cli.main(["work", "check", "01", "1", "--proof", "p"])
    cli.main(["work", "at", "01", "2"])
    (rec,) = work.thread_works(in_project, "25-@sloy")
    assert (rec["status"], rec["done"], rec["total"], rec["at"]) == ("taken", 1, 3, 2)


def test_thread_works_skips_a_broken_card(in_project):
    cli.main(["work", "add", "alive"])
    cli.main(["work", "thread", "01", "--set", "25-@sloy"])
    broken = work.works_dir(in_project) / "02-bitaya"
    broken.mkdir()
    (broken / "work.md").write_text("# broken\n\nthread: 25-@sloy\n", encoding="utf-8")
    assert [r["num"] for r in work.thread_works(in_project, "25-@sloy")] == ["01"]


# --- thread and step: where a work is headed --------

PLAN = """# thread plan

## steps

- [x] 1. first | what is done | result: "already done"
- [>] 2. the work knows its step | plan-to-work link | result: "see where it goes"
- [ ] 3. stack map | lay it all out | result: "see it on one page"

## current step — 2 (the work knows its step)
"""


def _caller_in_thread(root, monkeypatch, thread="09-@build", plan=PLAN):
    """A session sitting in a thread with a plan — the agent writes from it."""
    sid = "sid-{0}".format(thread)
    tdir = work.paths.arcs_dir(root) / thread
    sess = tdir / "arcs" / "01-do"
    sess.mkdir(parents=True)
    (sess / "arc.md").write_text(
        "# do\n\ntitle: do\nclaude-session: {0}\n".format(sid), encoding="utf-8")
    if plan is not None:
        (tdir / "plan.md").write_text(plan, encoding="utf-8")
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", sid)
    return tdir


def test_add_stamps_the_callers_thread_and_its_current_step(in_project, monkeypatch,
                                                            capsys):
    """the work shows in the thread's tab RIGHT AWAY, not after the "yes"."""
    _caller_in_thread(in_project, monkeypatch)
    assert cli.main(["work", "add", "Work knows its step"]) == 0
    assert 'step 2 «the work knows its step»' in capsys.readouterr().out
    text = _text(in_project)
    assert "thread: 09-@build" in text
    assert "step: 2" in text
    assert text.index("thread:") < text.index("step:")  # the step reads next to the thread
    assert "responsible thread → 09-@build (authoring session)" in _view(in_project)
    assert "status: open" in text  # an address is not a status gesture


def test_plan_and_propose_stamp_the_thread_before_the_human_says_yes(
        in_project, monkeypatch, capsys):
    cli.main(["work", "add", "no thread"])          # created outside a thread session
    assert "thread:" not in _text(in_project)
    _caller_in_thread(in_project, monkeypatch)
    assert cli.main(["work", "plan", "01", "how I mean to do it"]) == 0
    assert "the work shows in the thread's tab already" in capsys.readouterr().out
    assert "thread: 09-@build" in _text(in_project)
    cli.main(["work", "add", "second"])
    cli.main(["work", "thread", "02", "--clear"])
    assert cli.main(["work", "propose", "02", "step"]) == 0
    assert "thread: 09-@build" in _text(in_project, "02")


def test_auto_thread_never_overwrites_an_explicit_one(in_project, monkeypatch):
    cli.main(["work", "add", "someone else's"])
    cli.main(["work", "thread", "01", "--set", "77-@drugaya"])
    _caller_in_thread(in_project, monkeypatch)
    cli.main(["work", "plan", "01", "plan"])
    cli.main(["work", "propose", "01", "step"])
    text = _text(in_project)
    assert "thread: 77-@drugaya" in text
    assert "09-@build" not in text


def test_step_stays_unset_when_the_plan_cannot_say(in_project, monkeypatch):
    """No guessing: no plan / no section / nothing marked [>] — no field."""
    _caller_in_thread(in_project, monkeypatch, thread="01-@bez-plana", plan=None)
    cli.main(["work", "add", "one"])
    assert "step:" not in _text(in_project)

    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID")
    _caller_in_thread(in_project, monkeypatch, thread="02-@bez-shagov",
                      plan="# plan\n\n## final\n\ntext\n")
    cli.main(["work", "add", "two"])
    assert "step:" not in _text(in_project, "02")

    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID")
    _caller_in_thread(in_project, monkeypatch, thread="03-@bez-tekushchego",
                      plan="# plan\n\n## steps\n\n- [ ] 1. future | x | y\n")
    cli.main(["work", "add", "three"])
    assert "step:" not in _text(in_project, "03")


def test_take_refreshes_the_step_from_the_plan(in_project, monkeypatch):
    tdir = _caller_in_thread(in_project, monkeypatch)
    cli.main(["work", "add", "work"])
    assert "step: 2" in _text(in_project)
    # while the work was being agreed, the plan stepped on
    (tdir / "plan.md").write_text(PLAN.replace("- [>] 2.", "- [x] 2.")
                                  .replace("- [ ] 3.", "- [>] 3."), encoding="utf-8")
    assert cli.main(["work", "take", "01"]) == 0
    assert "step: 3" in _text(in_project)


def test_step_follows_the_thread_and_leaves_with_it(in_project, monkeypatch):
    _caller_in_thread(in_project, monkeypatch)
    cli.main(["work", "add", "work"])
    assert cli.main(["work", "thread", "01", "--set", "77-@bez-plana"]) == 0
    text = _text(in_project)
    assert "step:" not in text  # the new thread has no plan — the old address is cleared
    # the gesture landed as an act in the calling session's passport; the card now
    # points at 77-@bez-plana, so read it where it was written
    sess = work.paths.arcs_dir(in_project) / "09-@build" / "arcs" / "01-do"
    assert "plan step cleared (not in the thread plan)" in _acts_of(sess)
    assert cli.main(["work", "thread", "01", "--set", "09-@build"]) == 0
    assert "step: 2" in _text(in_project)
    assert cli.main(["work", "thread", "01", "--clear"]) == 0
    assert "step:" not in _text(in_project)


def test_step_verb_sets_names_and_clears(in_project, monkeypatch, capsys):
    _caller_in_thread(in_project, monkeypatch)
    cli.main(["work", "add", "work"])
    capsys.readouterr()
    assert cli.main(["work", "step", "01", "--set", "3"]) == 0
    assert 'plan step 3 «stack map»' in capsys.readouterr().out
    text = _text(in_project)
    assert "step: 3" in text
    assert 'plan step → 3 «stack map» (by hand)' in _view(in_project)
    assert cli.main(["work", "step", "01", "--clear"]) == 0
    assert "step:" not in _text(in_project)


def test_step_refuses_a_work_without_a_thread(in_project, capsys):
    cli.main(["work", "add", "nobody's"])
    assert cli.main(["work", "step", "01", "--set", "1"]) == 1
    assert "a step is an address IN THE THREAD PLAN" in capsys.readouterr().err
    assert cli.main(["work", "step", "01"]) == 1
    assert "step number" in capsys.readouterr().err


def test_show_says_where_the_work_is_heading(in_project, monkeypatch, capsys):
    _caller_in_thread(in_project, monkeypatch)
    cli.main(["work", "add", "work"])
    capsys.readouterr()
    assert cli.main(["work", "show", "01"]) == 0
    out = capsys.readouterr().out
    assert "step: 2" in out
    assert 'headed to — thread 09-@build, step 2 «the work knows its step»' in out


def test_thread_works_carries_the_step(in_project, monkeypatch):
    _caller_in_thread(in_project, monkeypatch)
    cli.main(["work", "add", "work"])
    (rec,) = work.thread_works(in_project, "09-@build")
    assert rec["step"] == 2


def test_step_reads_a_cross_project_address(tmp_project, tmp_path, monkeypatch):
    """A neighbouring project's thread is found via the roster — the card's address is live."""
    from tests.conftest import build_tide_skeleton
    other = tmp_path / "neighbour"
    other.mkdir()
    build_tide_skeleton(other, name="neighbour")
    (work.paths.arcs_dir(other) / "26-@release").mkdir(parents=True)
    (work.paths.arcs_dir(other) / "26-@release" / "plan.md").write_text(
        PLAN, encoding="utf-8")
    (tmp_project / "roster.md").write_text(
        "# tide roster\nneighbour | {0}\n".format(other), encoding="utf-8")
    monkeypatch.chdir(tmp_project)
    cli.main(["work", "add", "work"])
    assert cli.main(["work", "thread", "01", "--set", "neighbour/26-@release"]) == 0
    assert "step: 2" in _text(tmp_project)


# --- drop (withdraw an agreed item by the human's word) -----------------------

def test_drop_removes_the_item_with_its_description_and_journals(in_project, acting,
                                                                 capsys):
    """there was NOTHING to drop a plain item with — only the human's word."""
    cli.main(["work", "add", "work"])
    cli.main(["work", "checklist", "01", "Extra\\nextra details", "Needed"])
    capsys.readouterr()
    rc = cli.main(["work", "drop", "01", "1", "--word", "this item is not needed"])
    assert rc == 0
    assert 'item 1 «Extra» dropped' in capsys.readouterr().out
    text = _text(in_project)
    assert "Extra" not in text
    assert "extra details" not in text
    assert [t for _, t in work.all_items(text)] == ["Needed"]
    assert ('item 1 «Extra» dropped · word: «this item is not needed»'
            in _view(in_project))


def test_drop_requires_the_human_word_and_keeps_the_file(in_project, capsys):
    cli.main(["work", "add", "work"])
    cli.main(["work", "checklist", "01", "Item"])
    before = _text(in_project)
    assert cli.main(["work", "drop", "01", "1", "--word", "  "]) == 1
    assert "only the human can drop an agreed item" in capsys.readouterr().err
    assert _text(in_project) == before


def test_drop_sends_a_proposal_and_a_checked_item_to_their_own_gestures(
        in_project, capsys):
    cli.main(["work", "add", "work"])
    cli.main(["work", "checklist", "01", "Done one"])
    cli.main(["work", "propose", "01", "Proposed one"])
    cli.main(["work", "take", "01"])
    cli.main(["work", "check", "01", "1", "--proof", "p"])
    assert cli.main(["work", "drop", "01", "2", "--word", "no"]) == 1
    assert "agree <key> --drop 2" in capsys.readouterr().err
    assert cli.main(["work", "drop", "01", "1", "--word", "no"]) == 1
    assert "tide work uncheck 1 first" in capsys.readouterr().err
    assert cli.main(["work", "drop", "01", "9", "--word", "no"]) == 1
    assert "no item 9" in capsys.readouterr().err


def test_drop_moves_the_cursor_and_the_acceptances_with_the_numbers(in_project,
                                                                    acting):
    """An item number is an address: live references follow it, history does not."""
    cli.main(["work", "add", "work"])
    cli.main(["work", "checklist", "01", "First", "Second", "Third"])
    cli.main(["work", "take", "01"])
    cli.main(["work", "check", "01", "3", "--proof", "p"])
    _hand_accepts(in_project, 3)
    cli.main(["work", "at", "01", "2"])
    assert cli.main(["work", "drop", "01", "1", "--word", "the first is extra"]) == 0
    text = _text(in_project)
    assert [t for _, t in work.all_items(text)] == ["Second", "Third"]
    assert "\nat: 1" in text                       # the cursor followed "Second"
    assert "item 2 accepted by hand" in text       # so did the acceptance of "Third"
    assert work.accepted_items(text) == [2]
    # the gesture's history is intact: "item 3 ✓" stays a narrative with its own text
    assert 'item 3 ✓ «Third»' in _view(in_project)


def test_drop_of_the_cursors_own_item_takes_the_cursor_off(in_project, acting):
    cli.main(["work", "add", "work"])
    cli.main(["work", "checklist", "01", "First", "Second"])
    cli.main(["work", "take", "01"])
    cli.main(["work", "at", "01", "1"])
    assert cli.main(["work", "drop", "01", "1", "--word", "not doing it"]) == 0
    assert "\nat:" not in _text(in_project)
    assert "cursor cleared: its item was dropped" in _view(in_project)


def test_drop_of_the_last_undone_item_closes_the_review_gate(in_project, capsys):
    cli.main(["work", "add", "work"])
    cli.main(["work", "checklist", "01", "Done one", "Unneeded"])
    cli.main(["work", "take", "01"])
    cli.main(["work", "check", "01", "1", "--proof", "p"])
    assert "status: taken" in _text(in_project)
    capsys.readouterr()
    assert cli.main(["work", "drop", "01", "2", "--word", "we don't need this"]) == 0
    assert "→ review" in capsys.readouterr().out
    assert "status: review" in _text(in_project)


def test_drop_refuses_a_closed_work(in_project, capsys):
    cli.main(["work", "add", "work"])
    cli.main(["work", "checklist", "01", "Item"])
    cli.main(["work", "close", "01", "--word", "ok"])
    assert cli.main(["work", "drop", "01", "1", "--word", "drop it"]) == 1
    assert "tide work reopen first" in capsys.readouterr().err


# --- check / uncheck ---------------------------------------------------------

def test_check_requires_proof_and_take(in_project, capsys):
    cli.main(["work", "add", "x"])
    # argparse enforces --proof presence; empty proof fails in logic
    assert cli.main(["work", "check", "01", "1", "--proof", "  "]) == 1
    assert "without proof" in capsys.readouterr().err
    assert cli.main(["work", "check", "01", "1", "--proof", "done"]) == 1
    assert "tide work take first" in capsys.readouterr().err


def test_check_marks_item_journals_proof_and_autoreviews(in_project, acting, capsys):
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "take", "01"])
    rc = cli.main(["work", "check", "01", "1", "--proof", "commit abc123"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "→ review" in out  # the last check announces the auto-move
    text = _text(in_project)
    assert "- [x] x" in text
    assert "status: review" in text
    view = _view(in_project)
    assert 'item 1 ✓ «x» · proof: commit abc123' in view
    assert "all items checked → review" in view


def test_check_no_review_while_items_remain(in_project):
    cli.main(["work", "add", "x"])
    cli.main(["work", "checklist", "01", "x", "second"])
    cli.main(["work", "take", "01"])
    cli.main(["work", "check", "01", "1", "--proof", "p"])
    assert "status: taken" in _text(in_project)


def test_check_double_and_missing_index_fail(in_project, capsys):
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "take", "01"])
    cli.main(["work", "check", "01", "1", "--proof", "p"])
    assert cli.main(["work", "check", "01", "1", "--proof", "p"]) == 1
    assert "is already checked" in capsys.readouterr().err
    assert cli.main(["work", "check", "01", "9", "--proof", "p"]) == 1
    assert "no item 9" in capsys.readouterr().err


def test_uncheck_falls_back_from_review_to_taken(in_project, acting):
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "take", "01"])
    cli.main(["work", "check", "01", "1", "--proof", "p"])
    rc = cli.main(["work", "uncheck", "01", "1", "--reason", "did not ship"])
    assert rc == 0
    text = _text(in_project)
    assert "- [ ] x" in text
    assert "status: taken" in text
    view = _view(in_project)
    assert "checklist incomplete again → taken" in view
    assert "did not ship" in view


# --- close / reopen ----------------------------------------------------------

def test_close_requires_word_and_journals_it(in_project, acting, capsys):
    cli.main(["work", "add", "x"])
    assert cli.main(["work", "close", "01", "--word", " "]) == 1
    assert "done is set by the human" in capsys.readouterr().err
    rc = cli.main(["work", "close", "01", "--word", "close it"])
    assert rc == 0
    assert "status: done" in _text(in_project)
    assert "closed on the human's word · word: «close it»" in _view(in_project)


def test_reopen_only_from_done(in_project, capsys):
    cli.main(["work", "add", "x"])
    assert cli.main(["work", "reopen", "01"]) == 1
    assert "is open anyway" in capsys.readouterr().err
    cli.main(["work", "close", "01", "--word", "ok"])
    assert cli.main(["work", "reopen", "01"]) == 0
    assert "status: open" in _text(in_project)


def test_reopen_gives_a_taken_work_back_to_its_taker(in_project, acting):
    """taken-by did not go anywhere — "open" would lie that the work is nobody's."""
    cli.main(["work", "add", "x"])
    cli.main(["work", "checklist", "01", "Step", "Tail"])
    cli.main(["work", "take", "01", "--by", "04-pult"])
    cli.main(["work", "check", "01", "1", "--proof", "commit abc"])
    cli.main(["work", "close", "01", "--word", "ok"])
    assert cli.main(["work", "reopen", "01"]) == 0
    text = _text(in_project)
    assert "status: taken" in text
    assert "taken-by: 04-pult" in text
    assert "- [x] Step" in text
    assert "reopened → taken (04-pult)" in _view(in_project)


def test_reopen_of_a_finished_work_lands_on_the_review_gate(in_project, acting,
                                                            capsys):
    """All checked and the human changed his mind about closing — the work belongs
    at the acceptance gate, not in the queue: nothing to do in it, it waits for the hand."""
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "take", "01", "--by", "04-pult"])
    cli.main(["work", "check", "01", "1", "--proof", "commit abc"])
    cli.main(["work", "close", "01", "--word", "ok"])
    capsys.readouterr()
    assert cli.main(["work", "reopen", "01", "--word", "hold on"]) == 0
    assert "status: review" in capsys.readouterr().out
    text = _text(in_project)
    assert "status: review" in text
    assert "taken-by: 04-pult" in text
    view = _view(in_project)
    assert "reopened → taken (04-pult) · word: «hold on»" in view
    assert "all items checked → review" in view


def test_reopen_of_a_work_nobody_took_goes_back_to_the_queue(in_project):
    cli.main(["work", "add", "x"])
    cli.main(["work", "close", "01", "--word", "ok"])
    assert cli.main(["work", "reopen", "01"]) == 0
    text = _text(in_project)
    assert "status: open" in text
    assert "taken-by:" not in text


# --- acceptance: an item has two facts — "done" and "accepted" ---------------

def _hand_accepts(root, index, key="01"):
    """The board hand: per-item acceptance — a journal line, the checklist untouched.

    The board button is gone (word of 02.09), but such lines live in real
    passports and are read as before: acceptance is derived from the file journal.
    """
    _old_journal(root, "- 2026-07-30 14:02 — item {0} accepted by hand".format(index),
                 key=key)


def _two_items(root):
    """A work with two agreed items, taken."""
    cli.main(["work", "add", "ship payouts"])
    cli.main(["work", "checklist", "01", "bring up prod", "run the smoke"])
    cli.main(["work", "take", "01"])


def test_close_accepts_everything_checked_by_the_same_word(in_project, acting,
                                                           capsys):
    _two_items(in_project)
    cli.main(["work", "check", "01", "1", "--proof", "commit abc"])
    capsys.readouterr()
    assert cli.main(["work", "close", "01", "--word", "accepted, close it"]) == 0
    assert "accepted the done work — 1 item(s)" in capsys.readouterr().out
    view = _view(in_project)
    assert work.ACCEPT_ALL_LINE in view
    # journal order: first the acceptance of the done work, then the closing itself
    assert view.index(work.ACCEPT_ALL_LINE) < view.index("closed on the human's word")
    # the checklist is not rewritten — acceptance lives as a journal record
    text = _text(in_project)
    assert "- [x] bring up prod\n" in text
    assert "- [ ] run the smoke\n" in text


def test_close_with_nothing_checked_accepts_nothing(in_project, acting, capsys):
    cli.main(["work", "add", "x"])
    capsys.readouterr()
    assert cli.main(["work", "close", "01", "--word", "not needed, close it"]) == 0
    out = capsys.readouterr().out
    view = _view(in_project)
    assert work.ACCEPT_ALL_LINE not in view  # nothing to accept — no record
    assert "accepted the done work" not in out
    assert "closed on the human's word · word: «not needed, close it»" in view


def test_show_marks_an_item_accepted_by_hand(in_project, capsys):
    _two_items(in_project)
    cli.main(["work", "check", "01", "1", "--proof", "commit abc"])
    _hand_accepts(in_project, 1)  # a board gesture, the agent has no such verb
    capsys.readouterr()
    assert cli.main(["work", "show", "01"]) == 0
    out = capsys.readouterr().out
    assert "- [x] bring up prod ✓✓" in out  # done AND accepted
    assert "- [ ] run the smoke\n" in out
    assert "✓✓ — item done AND accepted" in out  # the mark is explained
    # the file is untouched: ✓✓ is display only
    assert "✓✓" not in _text(in_project)


def test_show_marks_checked_items_of_a_closed_work(in_project, acting, capsys):
    _two_items(in_project)
    cli.main(["work", "check", "01", "1", "--proof", "commit abc"])
    cli.main(["work", "close", "01", "--word", "the rest is not needed"])
    capsys.readouterr()
    cli.main(["work", "show", "01"])
    out = capsys.readouterr().out
    assert "- [x] bring up prod ✓✓" in out
    assert "- [ ] run the smoke\n" in out  # nothing to accept for the undone one
    # mass acceptance is now ONLY an act — it is read together with it
    text = _text(in_project)
    rows = work.work_acts(in_project, work._find(in_project, "01"), text)
    assert work.accepted_items(text, work.act_lines(rows)) == [1]


def test_reopen_keeps_the_journal_but_the_mass_word_stops_speaking(in_project,
                                                                  acting, capsys):
    _two_items(in_project)
    cli.main(["work", "check", "01", "1", "--proof", "commit abc"])
    _hand_accepts(in_project, 1)
    cli.main(["work", "close", "01", "--word", "close it"])
    cli.main(["work", "reopen", "01", "--word", "bring it back, there is a tail"])
    cli.main(["work", "take", "01"])
    cli.main(["work", "check", "01", "2", "--proof", "commit def"])
    assert work.ACCEPT_ALL_LINE in _view(in_project)  # history is not rubbed out
    capsys.readouterr()
    cli.main(["work", "show", "01"])
    out = capsys.readouterr().out
    # item 1 is accepted by hand by number — its mark lives; item 2 was done after
    # the closing, and the old word does not speak for it
    assert "- [x] bring up prod ✓✓" in out
    assert "- [x] run the smoke\n" in out
    assert work.accepted_items(_text(in_project)) == [1]


def test_unchecked_item_wears_no_acceptance_mark(in_project, capsys):
    _two_items(in_project)
    cli.main(["work", "check", "01", "1", "--proof", "commit abc"])
    _hand_accepts(in_project, 1)
    cli.main(["work", "uncheck", "01", "1", "--reason", "did not ship"])
    capsys.readouterr()
    cli.main(["work", "show", "01"])
    out = capsys.readouterr().out
    assert "✓✓" not in out  # the two facts are shown together or not at all
    assert "- [ ] bring up prod\n" in out


# --- title (the work's name is the human's signature) -------------------------

def test_title_rewrites_h1_by_the_human_word(in_project, acting, capsys):
    cli.main(["work", "add", "ship payouts"])
    capsys.readouterr()
    rc = cli.main(["work", "title", "01", "ship payouts and referrals",
                   "--word", "name it more precisely"])
    assert rc == 0
    assert 'renamed: «ship payouts and referrals»' in capsys.readouterr().out
    text = _text(in_project)
    assert "# ship payouts and referrals\n" in text
    assert "# ship payouts\n" not in text
    assert ("renamed (was: ship payouts) · word: «name it more precisely»"
            in _view(in_project))
    assert "status: open" in text  # a name is not a status gesture
    # the folder slug is left alone: it is the address the board and the journal hold
    assert work._find(in_project, "01").name == "01-ship-payouts"


def test_title_refuses_without_word_and_keeps_the_file(in_project, capsys):
    cli.main(["work", "add", "ship payouts"])
    before = _text(in_project)
    assert cli.main(["work", "title", "01", "new name", "--word", "  "]) == 1
    assert "the human renames a work" in capsys.readouterr().err
    assert _text(in_project) == before  # a refusal leaves the file alone


def test_title_refuses_empty_and_the_same_name(in_project, capsys):
    cli.main(["work", "add", "ship payouts"])
    assert cli.main(["work", "title", "01", "   ", "--word", "go"]) == 1
    assert "empty title" in capsys.readouterr().err
    assert cli.main(["work", "title", "01", "ship", "payouts",
                     "--word", "go"]) == 1
    assert "is already named that" in capsys.readouterr().err


def test_title_warns_on_a_long_one_but_writes_it(in_project, capsys):
    cli.main(["work", "add", "x"])
    long = "ship payouts, referrals, and while at it sort out the account " \
           "leftovers and finish the smoke on prod"
    capsys.readouterr()
    assert cli.main(["work", "title", "01", long, "--word", "write it like that"]) == 0
    out = capsys.readouterr().out
    assert "the title is long ({0} chars)".format(len(long)) in out
    assert "# " + long + "\n" in _text(in_project)  # a warning, not a refusal


def test_title_renames_a_closed_work_and_says_so(in_project, capsys):
    cli.main(["work", "add", "ship payouts"])
    cli.main(["work", "close", "01", "--word", "close it"])
    capsys.readouterr()
    assert cli.main(["work", "title", "01", "payouts (first round)",
                     "--word", "rename it, there will be a second"]) == 0
    assert "is closed — renamed after the fact" in capsys.readouterr().out
    text = _text(in_project)
    assert "# payouts (first round)\n" in text
    assert "status: done" in text  # renaming does not reopen a closed work


def test_title_clips_the_old_name_in_the_journal(in_project, acting):
    old = "a very long work name that the human once typed into the form " \
          "field on the board"
    cli.main(["work", "add", old])
    assert cli.main(["work", "title", "01", "shorter", "--word", "ok"]) == 0
    view = _view(in_project)
    assert "(was: {0}…)".format(old[:59].rstrip()) in view
    assert old not in view


def test_list_shows_the_new_name(in_project, capsys):
    cli.main(["work", "add", "old name"])
    cli.main(["work", "title", "01", "new name", "--word", "rename it"])
    capsys.readouterr()
    cli.main(["work", "list"])
    out = capsys.readouterr().out
    assert "new name" in out
    assert "old name" not in out


# --- find / list / show ------------------------------------------------------

def test_find_by_nn_slug_and_ambiguity(in_project, capsys):
    cli.main(["work", "add", "alpha task"])
    cli.main(["work", "add", "beta task"])
    assert work._find(in_project, "alpha-task").name == "01-alpha-task"
    assert work._find(in_project, "02").name == "02-beta-task"
    with pytest.raises(work.WorkError):
        work._find(in_project, "nope")


def test_find_accepts_bare_number(in_project):
    """A newcomer's live run: add prints "01-…", the human types "1".

    A bare number equals the work number: 1 == 01. Numbers are unique, no collisions.
    """
    cli.main(["work", "add", "try the loop"])
    assert work._find(in_project, "1").name == "01-try-the-loop"
    assert work._find(in_project, "01").name == "01-try-the-loop"


def test_find_miss_hints_at_key_shape(in_project):
    cli.main(["work", "add", "x"])
    with pytest.raises(work.WorkError) as e:
        work._find(in_project, "99")
    assert "works are named 01, 02" in str(e.value)
    assert "tide work list" in str(e.value)


def test_list_orders_live_by_deadline_closed_last(in_project, capsys):
    cli.main(["work", "add", "late", "--deadline", "2026-08-01"])
    cli.main(["work", "add", "soon", "--deadline", "2026-07-01"])
    cli.main(["work", "add", "gone"])
    cli.main(["work", "close", "03", "--word", "ok"])
    capsys.readouterr()  # drop the add/close prints — we assert on list only
    cli.main(["work", "list"])
    out = capsys.readouterr().out.splitlines()
    assert out[0].startswith("02-soon")
    assert out[1].startswith("01-late")
    assert out[2].startswith("03-gone")
    assert "done" in out[2]


def test_list_marks_proposed_items_apart_from_agreed(in_project, capsys):
    cli.main(["work", "add", "x"])
    _seed()
    cli.main(["work", "propose", "01", "an offer"])
    capsys.readouterr()
    cli.main(["work", "list"])
    assert "0/1+1?" in capsys.readouterr().out


def test_show_prints_the_passport_verbatim_but_the_journal_as_a_view(in_project,
                                                                     capsys):
    """ the file is the truth about EVERYTHING but the journal; the journal is a view over the acts.

    ``show`` used to print the whole passport verbatim. The header, plan and
    checklist are still printed so — they live in the file; but ``## log`` became
    a projection, because the gesture is now written in one place (the session
    acts) and has to be read from there. Here there are no acts, and the view
    honestly degenerates into the same file — but it is assembled by
    :func:`work.journal_view`, not by a text slice.
    """
    cli.main(["work", "add", "x"])
    cli.main(["work", "plan", "01", "how I mean to do it"])
    cli.main(["work", "propose", "01", "an offer"])
    _old_journal(in_project, "- 2026-09-02 10:00 — an old journal line")
    capsys.readouterr()
    rc = cli.main(["work", "show", "01"])
    assert rc == 0
    out = capsys.readouterr().out

    text = _text(in_project)
    head, _, journal = text.partition("## log")
    assert head.strip() in out                       # everything before the journal — verbatim
    assert "kind: work" in out
    assert "## plan" in out
    assert out.index("## plan") < out.index("## checklist")
    assert "- [?] an offer" in out

    wdir = work._find(in_project, "01")
    assert work.work_acts(in_project, wdir, text) == []          # no acts
    assert (work.journal_view(in_project, wdir, text)
            == [ln for ln in journal.splitlines() if ln.strip()])
    assert "an old journal line" in _journal_of(out)


# --- cross-project ------------------------------------------------------------

def test_project_flag_targets_rostered_neighbour(tmp_project, tmp_path, monkeypatch):
    from tests.conftest import build_tide_skeleton
    other = tmp_path / "neighbour"
    other.mkdir()
    build_tide_skeleton(other, name="neighbour")
    home = tmp_project
    (home / "roster.md").write_text(
        "# tide roster\nneighbour | {0}\n".format(other), encoding="utf-8")
    monkeypatch.chdir(home)
    rc = cli.main(["work", "add", "neighbour work", "--project", "neighbour"])
    assert rc == 0
    f = work.works_dir(other) / "01-neighbour-work" / "work.md"
    assert f.is_file()
    # a fix goes by the same address as the other verbs
    assert cli.main(["work", "fix", "01", "Afterthought", "--word", "and this too",
                     "--project", "neighbour"]) == 0
    assert "## fixes" in f.read_text(encoding="utf-8")


# --- the work cursor  --------------------------------------

def test_at_marks_the_cursor_and_journals(in_project, acting, capsys):
    cli.main(["work", "add", "x"])
    cli.main(["work", "checklist", "01", "x", "second"])
    cli.main(["work", "take", "01"])
    rc = cli.main(["work", "at", "01", "2"])
    assert rc == 0
    assert 'cursor on item 2 «second»' in capsys.readouterr().out
    assert "at: 2" in _text(in_project)
    assert 'cursor on item 2 «second»' in _view(in_project)


def test_at_moves_and_clears(in_project, acting, capsys):
    cli.main(["work", "add", "x"])
    cli.main(["work", "checklist", "01", "x", "second"])
    cli.main(["work", "take", "01"])
    cli.main(["work", "at", "01", "1"])
    cli.main(["work", "at", "01", "2"])
    text = _text(in_project)
    assert "\nat: 2" in text and "\nat: 1" not in text  # one cursor, it moves
    assert cli.main(["work", "at", "01", "--clear"]) == 0
    assert "cursor cleared" in capsys.readouterr().out
    # "taken-at:" does not count — the cursor is read from the start of a line
    assert "\nat:" not in _text(in_project)
    assert "cursor cleared" in _view(in_project)


def test_at_refuses_missing_item_and_empty_call(in_project, capsys):
    cli.main(["work", "add", "x"])
    cli.main(["work", "take", "01"])
    assert cli.main(["work", "at", "01", "9"]) == 1
    assert "no item 9" in capsys.readouterr().err
    assert cli.main(["work", "at", "01"]) == 1
    assert "item number or --clear" in capsys.readouterr().err
    assert cli.main(["work", "at", "01", "--clear"]) == 1
    assert "no cursor is set anyway" in capsys.readouterr().err


def test_check_clears_the_cursor_of_its_own_item_only(in_project):
    cli.main(["work", "add", "x"])
    cli.main(["work", "checklist", "01", "x", "second"])
    cli.main(["work", "take", "01"])
    cli.main(["work", "at", "01", "2"])
    # a check of ANOTHER item leaves the cursor alone: there may be several workers
    cli.main(["work", "check", "01", "1", "--proof", "p"])
    assert "\nat: 2" in _text(in_project)
    # a check of ITS OWN item clears it: keeping "I am here" on a done item is a lie
    cli.main(["work", "check", "01", "2", "--proof", "p"])
    assert "\nat:" not in _text(in_project)


# --- the journal as a VIEW over the acts ---------------------

def _at(h, m):
    from datetime import datetime
    return datetime(2026, 9, 2, h, m)


@pytest.fixture
def acting(in_project, monkeypatch, tmp_path):
    """A thread with an ACCEPTED session: work verbs write both the file journal and an act.

    Returns the session folder itself — the acts land in its ``## context``.
    """
    from tide import fields
    from tide.arc import stream

    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "claude-home"))
    stream.new_thread(in_project, "release", goal="acts in one place")
    s = stream.new_session(in_project, "release", "stroyka")
    fields.set_field(s / "arc.md", "claude-session", "sid-66")
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "sid-66")
    return s


def _mute(monkeypatch):
    """A gesture WITHOUT a calling session — how the engine worked before acts (and how the board writes)."""
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)


def _journal_of(out):
    return out.partition("## log")[2]


def test_show_journal_glues_the_file_and_the_acts_without_doubling(
        in_project, acting, capsys):
    """Merge: the lines of the OLD file plus the acts — and none of them is lost."""
    work.new_work(in_project, "acts in one place", now=_at(10, 0))
    work.set_checklist(in_project, "01", ["Writer", "Reader"], now=_at(10, 5))
    work.set_thread(in_project, "01", "01-@release", now=_at(10, 10))
    _old_journal(in_project,                             # as written before 66
                 '- 2026-09-02 10:20 — taken (agent) on the word: «take it»')
    work.take(in_project, "01", word="take it", now=_at(10, 21))
    work.check(in_project, "01", 1, "module acts.py", now=_at(11, 0))

    capsys.readouterr()
    cli.main(["work", "show", "01"])
    journal = _journal_of(capsys.readouterr().out)

    assert journal.count("item 1 ✓") == 1               # the gesture is said once
    assert 'act: item 1 ✓ «Writer» · proof: module acts.py · #1.1' in journal
    assert 'taken (agent) on the word: «take it»' in journal   # old, from the file
    assert journal.index("taken (agent)") < journal.index("act: item 1")


def test_a_work_without_acts_is_read_from_its_file_whole(in_project, acting,
                                                         monkeypatch, capsys):
    """Old works have no acts — their journal is read from the file whole and forever."""
    _mute(monkeypatch)
    work.new_work(in_project, "old work", now=_at(9, 0))
    work.set_checklist(in_project, "01", ["Item"], now=_at(9, 10))
    _old_journal(in_project,
                 "- 2026-09-02 09:10 — checklist agreed: 1 item(s)",
                 '- 2026-09-02 09:20 — taken (agent) on the word: «yes»',
                 '- 2026-09-02 09:30 — item 1 ✓ «Item»: commit abc')

    capsys.readouterr()
    cli.main(["work", "show", "01"])
    journal = _journal_of(capsys.readouterr().out)
    for line in _journal_of(_text(in_project)).strip().splitlines():
        assert line in journal
    assert "act:" not in journal


def test_a_work_without_a_thread_keeps_its_file_journal(in_project, acting, capsys):
    """No thread — nowhere to look for acts, and the view honestly degenerates into the file.

    That is the PRICE of one place: the address of a work's acts is its
    ``thread:``, and a work whose thread was cleared no longer shows its gestures
    from the card (they are intact, but sit in the session passport). The old
    lines written to the file are read as they always were.
    """
    work.new_work(in_project, "no thread", now=_at(12, 0))
    _old_journal(in_project, "- 2026-09-02 12:05 — checklist agreed: 1 item(s)")
    work.set_thread(in_project, "01", None, now=_at(12, 6))
    capsys.readouterr()
    cli.main(["work", "show", "01"])
    out = _journal_of(capsys.readouterr().out)
    assert "checklist agreed" in out             # the file is read forever
    assert "thread cleared" not in out           # and a fresh gesture is only in the session


def test_accepted_items_sees_acceptance_that_came_as_an_act(in_project):
    """Acceptance is read as a UNION: the board hand writes to the file, close also as an act."""
    cli.main(["work", "add", "x"])
    _seed("bring up prod")
    cli.main(["work", "take", "01"])
    cli.main(["work", "check", "01", "1", "--proof", "commit abc"])
    cli.main(["work", "close", "01", "--word", "accepted"])

    bare = _text(in_project).partition("## log")[0] + "## log\n"
    assert work.accepted_items(bare) == []               # no acceptance in the file
    mass = "- 2026-09-02 12:00 — act: {0} · #1".format(work.ACCEPT_ALL_LINE)
    assert work.accepted_items(bare, [mass]) == [1]
    one = "- 2026-09-02 12:00 — act: item 1 accepted by hand · #1.1"
    assert work.accepted_items(bare, [one]) == [1]


def test_show_marks_an_item_accepted_through_the_acts(in_project, acting, capsys):
    """The full path: close from a session → act → ✓✓ on screen."""
    work.new_work(in_project, "work", now=_at(13, 0))
    work.set_checklist(in_project, "01", ["bring up prod"], now=_at(13, 5))
    work.take(in_project, "01", word="yes", now=_at(13, 10))
    work.check(in_project, "01", 1, "commit abc", now=_at(13, 20))
    work.close(in_project, "01", "accepted", now=_at(13, 30))

    ctx = (acting / "arc.md").read_text(encoding="utf-8")
    assert "act: {0} · #1".format(work.ACCEPT_ALL_LINE) in ctx
    capsys.readouterr()
    cli.main(["work", "show", "01"])
    assert "- [x] bring up prod ✓✓" in capsys.readouterr().out


def test_the_file_journal_is_not_written_any_more(in_project, acting):
    """Final of the journal rework: there is no second place to write — a gesture is an act only.

    Not a single line appears in ``work.md``: neither ``## log`` nor the record.
    The gesture is read through the view (:func:`work.journal_view`) — and there it is.
    """
    work.new_work(in_project, "work", now=_at(14, 0))
    work.set_checklist(in_project, "01", ["Item"], now=_at(14, 5))
    work.take(in_project, "01", word="yes", now=_at(14, 10))
    work.check(in_project, "01", 1, "commit abc", now=_at(14, 20))

    text = _text(in_project)
    assert "## log" not in text
    assert "commit abc" not in text
    assert 'item 1 ✓ «Item» · proof: commit abc' in _view(in_project)


def test_a_file_line_without_an_act_twin_survives_the_glue(in_project, acting,
                                                           monkeypatch, capsys):
    """The board hand has no session — its line lives only in the file, and it shows.

    A time boundary is not enough here: the human also writes acts into the
    passport by hand, and from that minute all further board work would vanish
    from the screen. So a newer line drops out of the view only if it HAS an act
    twin.
    """
    from tide import acts

    work.new_work(in_project, "work", now=_at(10, 0))
    work.set_checklist(in_project, "01", ["bring up prod"], now=_at(10, 5))
    work.take(in_project, "01", word="yes", now=_at(10, 20))
    work.check(in_project, "01", 1, "commit abc", now=_at(10, 30))
    acts.write_act(acting, "fix 5 added by word", ref="1", now=_at(11, 0))
    # the board hand had no session and wrote straight to the file — such lines are alive
    _old_journal(in_project, "- 2026-09-02 11:30 — item 1 accepted by hand")

    capsys.readouterr()
    cli.main(["work", "show", "01"])
    out = capsys.readouterr().out
    journal = _journal_of(out)
    assert "item 1 accepted by hand" in journal        # the hand is not lost
    assert "act: fix 5 added by word" in journal
    assert 'item 1 ✓ «bring up prod» · proof: commit abc' in journal
    assert "- [x] bring up prod ✓✓" in out


def test_a_twin_of_an_act_is_dropped_from_the_view(in_project, acting, capsys):
    """The same gesture, said both to the file and as an act, is read once.

    Twins were born while the verb wrote to both places; such ``work.md`` files
    are alive, and the sieve sorts them out by GESTURE — the same minute, the
    same start of text.
    """
    work.new_work(in_project, "work", now=_at(10, 0))
    work.set_checklist(in_project, "01", ["Item"], now=_at(10, 5))
    work.take(in_project, "01", word="yes", now=_at(10, 10))
    work.dispatch(in_project, "01", "builder B", now=_at(10, 20))
    _old_journal(in_project,     # the same dispatch, as the old verb wrote it
                 "- 2026-09-02 10:20 — builder dispatched: builder B")

    view = _view(in_project)
    assert view.count("builder dispatched: builder B") == 1
    assert "act: builder dispatched: builder B · #1" in view


# --- plan --items-json ----------------------------------------------

def test_plan_items_json_builds_checkbox_plan(in_project, acting, tmp_path, capsys):
    cli.main(["work", "add", "x"])
    f = tmp_path / "i.json"
    f.write_text('[{"text": "take a snapshot", "ref": "T-5", "status": "in progress"},'
                 ' {"text": "ready", "done": true}, {"text": "smoke"}]', encoding="utf-8")
    capsys.readouterr()
    assert cli.main(["work", "plan", "01", "--items-json", str(f)]) == 0
    out = capsys.readouterr().out.strip()
    assert out.endswith("work.md") and __import__("pathlib").Path(out).is_file()
    text = _text(in_project)
    assert "- [ ] take a snapshot · T-5 · in progress\n- [x] ready\n- [ ] smoke" in text
    assert text.index("## plan") < text.index("## checklist")
    assert "status: open" in text


def test_plan_items_json_errors(in_project, acting, tmp_path, capsys):
    cli.main(["work", "add", "x"])
    f = tmp_path / "i.json"
    f.write_text('[{"text": ""}]', encoding="utf-8")
    assert cli.main(["work", "plan", "01", "--items-json", str(f)]) == 1
    assert "text" in capsys.readouterr().err
    f.write_text("[]", encoding="utf-8")
    assert cli.main(["work", "plan", "01", "--items-json", str(f)]) == 1
    assert cli.main(["work", "plan", "01", "text", "--items-json", str(f)]) == 1
    assert "one of the two" in capsys.readouterr().err
    assert cli.main(["work", "plan", "01"]) == 1
