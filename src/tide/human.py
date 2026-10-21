"""tide.human — what tide calls the human it works for.

The name is not baked into the package. It lives in
``<control-home>/.tide/canon/config`` (the same ``key=value`` as the other keys):

    human_name=Anna          # how texts address the human
    human_actor=anna         # latin id used in machine keys and file names

No key — the neutral default "user". No ``human_actor`` — it is derived from an
ASCII ``human_name`` (lowercased, letters and digits only), else ``human``.

Texts in the code are written with the neutral word; :func:`tr` substitutes the
configured name on output ("the user" / "user" → "Anna"), :func:`name_rx` gives a
pattern for regexes. The config is cached by mtime, so a name change is picked up
without a restart; module-level constants are fixed at import time.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Optional, Tuple

NAME_KEY = "human_name"
ACTOR_KEY = "human_actor"

DEFAULT_NAME = "user"
DEFAULT_ACTOR = "human"

_cache: Dict[Tuple[str, int, int], Tuple[str, str]] = {}


def _config_file() -> Optional[Path]:
    try:
        from . import paths

        return paths.canon_config(paths.control_home())
    except Exception:  # noqa: BLE001 — the name matters less than a live session
        return None


def _load() -> Tuple[str, str]:
    path = _config_file()
    if path is None:
        return DEFAULT_NAME, DEFAULT_ACTOR
    try:
        st = path.stat()
    except OSError:
        return DEFAULT_NAME, DEFAULT_ACTOR
    key = (str(path), st.st_mtime_ns, st.st_size)
    hit = _cache.get(key)
    if hit is not None:
        return hit
    vals: Dict[str, str] = {}
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            k, sep, v = line.strip().partition("=")
            if sep and not k.startswith("#") and v.strip():
                vals[k.strip()] = v.strip()
    except (OSError, ValueError):
        pass
    nom = vals.get(NAME_KEY) or ""
    actor_id = vals.get(ACTOR_KEY) or (re.sub(r"[^a-z0-9]+", "", nom.lower())
                                       if nom and nom.isascii() else "") \
        or DEFAULT_ACTOR
    _cache.clear()
    _cache[key] = (nom or DEFAULT_NAME, actor_id)
    return _cache[key]


def name() -> str:
    """The configured name of the human (default ``user``)."""
    return _load()[0]


def actor() -> str:
    """The human's latin id for machine keys and file names (default ``human``)."""
    return _load()[1]


def is_default() -> bool:
    return _load()[0] == DEFAULT_NAME


def name_rx() -> str:
    """Case-insensitive pattern for the human's name: ``(?i:anna)``."""
    return "(?i:{0})".format(re.escape(name().lower()))


def poss_rx() -> str:
    """Possessive («the user's decision» / «Anna's decision») — ``(?i:user|anna)'s``."""
    alts = sorted({DEFAULT_NAME, name().lower()}, key=len, reverse=True)
    return "(?i:{0})'s".format("|".join(re.escape(a) for a in alts))


# the neutral word in code texts: «the user» or a bare «user» («user expectation»)
_NEUTRAL_RX = re.compile(r"(?<![\w])(?:the\s+)?user(?![\w])", re.IGNORECASE)


def tr(text: str) -> str:
    """Substitute the configured name for the neutral «the user» / «user» in *text*."""
    if not text or is_default():
        return text
    who = name()
    return _NEUTRAL_RX.sub(lambda _m: who, text)


__all__ = ["ACTOR_KEY", "DEFAULT_ACTOR", "DEFAULT_NAME", "NAME_KEY", "actor",
           "is_default", "name", "name_rx", "poss_rx", "tr"]
