"""U1 unit — slug: slugify + __…__-tolerant ref matching."""

from __future__ import annotations

from tide import slug


def test_slugify_lowercases_and_dashes_separators():
    assert slug.slugify("Hello World") == "hello-world"
    assert slug.slugify("a/b_c d") == "a-b-c-d"


def test_slugify_drops_unsafe_chars():
    assert slug.slugify("Café #1 (draft)!") == "caf-1-draft"


def test_slugify_collapses_and_trims_dashes():
    assert slug.slugify("--Foo   Bar--") == "foo-bar"
    assert slug.slugify("a   /   b") == "a-b"


def test_slugify_empty_and_none_safe():
    assert slug.slugify("") == ""
    assert slug.slugify(None) == ""


def test_slugify_transliterates_cyrillic():
    # a Russian-named thread must yield a real handle, not '' (which
    # threw "empty slug after slugify" at birth so the thread never started).
    assert slug.slugify("\u0447\u0430\u0439") == "chay"
    assert slug.slugify("\u041f\u0435\u0440\u0441\u043e\u043d\u0430\u043b") == "personal"
    health_and_finance = ("\u0417\u0434\u043e\u0440\u043e\u0432\u044c\u0435 \u0438 "
                          "\u0424\u0438\u043d\u0430\u043d\u0441\u044b")
    assert slug.slugify(health_and_finance) == "zdorove-i-finansy"
    # convention match: U+0446→c, U+0445→h, U+044F→ya (Russian "migration" /
    # "transitions" already on disk)
    assert slug.slugify("\u043c\u0438\u0433\u0440\u0430\u0446\u0438\u044f") == "migraciya"
    assert slug.slugify("\u043f\u0435\u0440\u0435\u0445\u043e\u0434\u044b") == "perehody"


def test_slugify_mixed_cyrillic_latin_survives():
    # a mixed name no longer loses its Cyrillic half to the [^a-z0-9-] strip.
    assert slug.slugify("\u0447\u0430\u0439-tea") == "chay-tea"
    # create/lookup stay in lock-step: a ref round-trips to its entry
    assert slug.ref_matches("\u0447\u0430\u0439", "07-chay") is True


def test_short_slug_passes_through_when_within_cap():
    assert slug.short_slug("fix the leak") == "fix-the-leak"
    assert slug.short_slug("") == ""


def test_short_slug_caps_long_text_on_word_boundary():
    long = "polish the settings screen with spring animations and haptics on slow devices"
    s = slug.short_slug(long, max_len=20)
    assert len(s) <= 20
    # trimmed back to a whole-word ('-') boundary, no trailing dash, no mid-word cut
    assert s == "polish-the-settings"


def test_short_slug_hard_cuts_a_single_overlong_word():
    s = slug.short_slug("a" * 100, max_len=10)
    assert s == "a" * 10


def test_strip_marker_one_layer():
    assert slug.strip_marker("__03-fix__") == "03-fix"
    assert slug.strip_marker("plain") == "plain"


def test_normalize_ref_strips_marker_then_slugifies():
    assert slug.normalize_ref("__Fix It__") == "fix-it"


def test_entry_slug_peels_num_goal_and_marker():
    assert slug.entry_slug("03-fix-bug") == "fix-bug"
    assert slug.entry_slug("07-@ship-it") == "ship-it"
    assert slug.entry_slug("__12-fix-bug__") == "fix-bug"
    assert slug.entry_slug("__09-@goal-x__/") == "goal-x"


def test_is_goal_and_is_closed_detect_markers():
    assert slug.is_goal_entry("07-@ship-it") is True
    assert slug.is_goal_entry("07-ship-it") is False
    assert slug.is_closed_entry("__12-fix__") is True
    assert slug.is_closed_entry("12-fix") is False


def test_is_entry_matches_open_and_closed_arcs_and_goals():
    assert slug.is_entry("03-fix-bug") is True       # open arc
    assert slug.is_entry("07-@ship-it") is True      # open goal
    assert slug.is_entry("__12-fix-bug__") is True   # closed arc
    assert slug.is_entry("__09-@goal-x__") is True   # closed goal
    assert slug.is_entry("candidates") is False      # not a NN- entry
    assert slug.is_entry("") is False


def test_ref_matches_marker_tolerant_both_sides():
    # bare ref against an open arc
    assert slug.ref_matches("fix-bug", "03-fix-bug") is True
    # __-wrapped ref against a closed goal entry
    assert slug.ref_matches("__fix-bug__", "__12-fix-bug__") is True
    # ref against a goal entry (@ stripped)
    assert slug.ref_matches("ship-it", "07-@ship-it") is True
    # non-match
    assert slug.ref_matches("fix-bug", "03-other") is False
