"""« · » inside session names is not a list separator (shared splitter).

``tide thread layer --main`` (:func:`tide.arc.thread_layers.split_main`) splits
on « · » without breaking «role · NN».
"""

from __future__ import annotations

import re
from typing import List

# «·» inside a session's name is not a list separator: «project — thread · 04»,
# «designer · 01 · project-a-8» stay whole. «role · NN» with any continuation is
# a session name («from main · 04 12.10», «yes designer · 08 on ready-v3»): « · »
# after a latin role word before a 1–3 digit number is not a separator. A number
# («step 1 · step 2») and a date («· 12.10 …») still split, and so does a
# non-latin word before a number (e.g. a Russian verb: «<verb> · 10 tests»).
NAME_DOT = re.compile(r"\s·\s(?=\d{2}\b(?:\s·|\s*$|[,;:)]|\s*=|\s*\())"
                      r"|(?<=\b\d{2})\s·\s(?=[A-Za-z][\w.-]*-\d+\b)"
                      r"|(?<=[A-Za-z])\s·\s(?=\d{1,3}\b(?![.:]\d))"
                      # « · NN» before «→», a parenthesis, a comma or end of line —
                      # a session number whatever the word on the left («the thread · 04 → pair 14»)
                      r"|\s·\s(?=\d{1,3}(?:\s*→|\s*\(|,|\s*$))")
KEEP = "\x00"
# «project — thread · NN» with any tail: «proj — main · 02 via send»,
# «… · NN (manager-11)» — the session number follows a name of the form «X — Y»,
# and the « · » before it does not break the name, whatever follows.
DASH_NAME_DOT = re.compile(r"(?<=\S)(\s—\s[\w.@-]+)\s·\s(?=(?:\d{2}|NN)\b)")


def keep_name_dots(line: str) -> str:
    """Hide « · » inside session names so a ``split`` on « · » does not break them."""
    line = DASH_NAME_DOT.sub(lambda m: m.group(1) + KEEP, line)
    return NAME_DOT.sub(KEEP, line)


def split_dots(line: str) -> List[str]:
    """Split a line on « · », leaving «role · NN» session names whole; pieces as they are."""
    return [p.replace(KEEP, " · ") for p in keep_name_dots(line).split(" · ")]
