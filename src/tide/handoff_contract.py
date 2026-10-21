"""tide.handoff_contract — thread layer names and label parsing in a pulse note.

The ``## where we are`` layers of a thread goal (scaffold — :mod:`tide.arc.templates`,
writing — :mod:`tide.arc.thread_layers`) take their names and placeholders from here:
one place for everyone. Pulse labels ("Expectation: …", "Experience: …") are read by
:func:`pulse_labels`.

The module is pure: only data and a couple of functions, no disk.
"""

from __future__ import annotations

import re
from typing import Dict, Tuple
from tide.human import tr as _h, name_rx as _hn

# Canonical heading name of a thread layer, by key.
_LAYER_NAMES: Dict[str, str] = {
    "expectation": _h("user expectation"),
    "where": "where we are",
    "experience": "experience",
}


def name(key: str) -> str:
    """Canonical layer heading name by key (``KeyError`` if there is none)."""
    return _LAYER_NAMES[key]


# The ``## where we are`` layers of a thread goal (scaffold — :mod:`tide.arc.templates`):
# three seed blocks that live in the thread, not in a session. Subheading = block name.
THREAD_LAYERS: Tuple[Tuple[str, str], ...] = (
    ("expectation", _h("<what the user expects from the thread — in their words, dated>")),
    ("where", _h("<done · in progress · waiting on the user — one line each>")),
    ("experience", "<pitfalls, loops, «rejected» — accumulates from session to session>"),
)


# Labels in a pulse note: a manual handoff is written as the pulse
# «HANDOFF. Waiting on the user: … In flight: … Experience: … Decisions: …».
# Label → layer or block. Case does not matter, a note may hold any number of
# labels; a label's text runs up to the next label.
# ``(block, (label variants — regexes without the «:»))``.
_WHO = r"(?:the\s+)?(?:user|" + _hn() + r")"
PULSE_LABELS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("awaiting", (r"wait(?:s|ing)?\s+(?:on|for)\s+" + _WHO,
                  r"open\s+decisions(?:\s+(?:of|for)\s+" + _WHO + r")?")),
    ("inflight", (r"in[\s-]flight",)),
    ("experience", (r"experience", r"lessons?")),
    ("decisions", (r"(?:(?:session|" + _WHO + r")(?:'s)?\s+)?decisions?",)),
    # «Expectation:» without «user» is their word too (the label is often shortened)
    ("expectation", (r"(?:" + _WHO + r"(?:'s)?\s+)?expectations?",)),
    # «Map: <path> — why; <path> — why; …» — the entry map.
    ("entry_map", (r"(?:entry\s+)?map",)),
    # Open tails; «Not live:» is a caveat and goes in as a whole line.
    ("tails", (r"(?:open\s+)?(?:tails|loose\s+ends)", r"open")),
    ("unverified", (r"not\s+(?:verified\s+)?live", r"unverified")),
)

# Labels that feed no block but END the previous label's text —
# otherwise «In flight: nothing. Recipients: …» would carry the recipients into «in flight».
PULSE_STOP_LABELS: Tuple[str, ...] = (
    r"where\s+we\s+are", r"recipients", r"table", r"done", r"next", r"cursor",
    # «Never: …» — the user's rules, not «waiting on the user» items
    r"never", r"forbidden",
)


def _label_re():
    import re

    alts = []
    for key, pats in PULSE_LABELS:
        for i, p in enumerate(pats):
            alts.append(r"(?P<{0}_{1}>{2})".format(key, i, p))
    for i, p in enumerate(PULSE_STOP_LABELS):
        alts.append(r"(?P<stop_{0}>{1})".format(i, p))
    # A label stands at the start of the note or after a sentence end / dash / «·»
    # separator and is followed by «:»; a parenthesised note may sit in between
    # («USER DECISION (via …, 10-09):»).
    return re.compile(
        r"(?:^|(?<=[.;!?»)\]—·])\s+|(?<=\s—)\s)(?:{0})(?:\s*\([^()]*\))?\s*:\s*".format(
            "|".join(alts)), re.IGNORECASE)


_LABEL_RE = None


def pulse_labels(note: str) -> Dict[str, list]:
    """Pulse note → ``{block key: [text pieces]}`` by label.

    A piece is the text after a label up to the next label (any, stop labels
    included), without the trailing period. No labels — ``{}``. Pure, no disk.
    """
    global _LABEL_RE
    if _LABEL_RE is None:
        _LABEL_RE = _label_re()
    text = " ".join((note or "").split())
    hits = list(_LABEL_RE.finditer(text))
    out: Dict[str, list] = {}
    for i, m in enumerate(hits):
        group = next(g for g, v in m.groupdict().items() if v is not None)
        end = hits[i + 1].start() if i + 1 < len(hits) else len(text)
        piece = text[m.end():end].strip().rstrip(".;·").strip()
        if group.startswith("stop_") or not piece:
            continue
        out.setdefault(group.rsplit("_", 1)[0], []).append(piece)
    return out


# The «HANDOFF» label starts a pulse note (after the stamp); it is not a word in
# the text: «handoff of work 117 facts» is an ordinary pulse. The label is
# upper-case by convention, which is what tells it from the word.
PASS_RE = re.compile(r"^-?\s*(?:\d{4}-\d{2}-\d{2}T[\d:]+\s*[—-]\s*|\d{2}:\d{2}\s*[—-]\s*)?"
                     r"HANDOFF\b")


def is_pass_note(note: str) -> bool:
    """The pulse note is a handoff (the «HANDOFF» label at the start)."""
    return bool(PASS_RE.match((note or "").strip()))


__all__ = ["THREAD_LAYERS", "PULSE_LABELS", "PULSE_STOP_LABELS", "is_pass_note", "name",
           "pulse_labels"]
