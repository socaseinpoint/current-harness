"""Shared secret redactor.

Standard library only: the module can be copied next to other tools and checked by sha256, so it
imports nothing from tide. ``mask_secrets`` replaces tokens, keys, passwords, Bearer, ``token=``,
long hex/base64 strings and ssh keys with ``***``.
"""
from __future__ import annotations

import re

MASK = "***"

# --- secret masking ----------------------------------------------------------

_SECRET_PATTERNS = (
    # Authorization: Bearer / Basic
    re.compile(r"(?i)(\b(?:bearer|basic)\s+)([A-Za-z0-9._~+/=-]{8,})"),
    # user:pass@ in a URL
    re.compile(r"(://[^/\s:@]+:)([^@\s/]+)(@)"),
    # key=value / key: value, where the name looks like a secret
    re.compile(r"(?i)(\b[\w.-]*(?:token|secret|passw(?:or)?d|api[_-]?key|apikey|auth|"
               r"credential|private[_-]?key|access[_-]?key)[\w.-]*[\"']?\s*[=:]\s*[\"']?)"
               r"([^\s\"'&]{4,})"),
    # --token VALUE (flag with a space)
    re.compile(r"(?i)(--[\w-]*(?:token|secret|passw(?:or)?d|api[_-]?key|apikey|"
               r"credential|private[_-]?key|access[_-]?key)[\w-]*\s+[\"']?)([^\s\"'&]{4,})"),
)

_TOKEN_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}"),                 # OpenAI / Anthropic
    re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}"),  # GitHub
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"),          # Slack
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),                     # AWS
    re.compile(r"\blin_(?:api|oauth)_[A-Za-z0-9]{20,}"),     # issue-tracker token
    re.compile(r"\br8_[A-Za-z0-9]{20,}"),                    # Replicate
    re.compile(r"\bAIza[0-9A-Za-z_-]{30,}"),                 # Google
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"),  # JWT
    re.compile(r"(?<!\d)\d{8,10}:[A-Za-z0-9_-]{30,}"),            # chat bot token
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?(?:-----END [A-Z ]*PRIVATE KEY-----|$)",
               re.S),
    # long «random» string: hex ≥ 32 or base64-like ≥ 40 with digits
    re.compile(r"\b(?:ssh-(?:rsa|ed25519|dss)|ecdsa-sha2-nistp\d+)\s+AAAA[A-Za-z0-9+/=]{20,}"),  # public ssh key
    re.compile(r"\b[0-9a-fA-F]{32,}\b"),
    re.compile(r"(?<![\w/.-])(?=[A-Za-z0-9+/_-]*\d)(?=[A-Za-z0-9+/_-]*[A-Za-z])"
               r"[A-Za-z0-9+/_-]{40,}={0,2}"),
)


def mask_secrets(text: str) -> str:
    """Replace anything that looks like tokens/keys/passwords with ``***``."""
    out = text
    for pat in _SECRET_PATTERNS:
        if pat.groups == 3:
            out = pat.sub(lambda m: m.group(1) + MASK + m.group(3), out)
        else:
            out = pat.sub(lambda m: m.group(1) + MASK, out)
    for pat in _TOKEN_PATTERNS:
        out = pat.sub(MASK, out)
    return out

