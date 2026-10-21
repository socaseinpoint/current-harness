"""tide.hooks — Claude Code hook wiring (install + runtime hooks).

Five hooks:
  session_start.py  — `tide hook session-start`: print who-am-I + role reminder +
                      warnings (canon drift, unmerged deltas).
  edit_gate.py      — `tide hook edit-gate` (PreToolUse): block project edits
                      until a worker arc is open; allow edits inside .tide/.
  ask_gate.py       — `tide hook ask-gate` (PreToolUse, AskUserQuestion): in an
                      unattended session ($TIDE_UNATTENDED) with no live human
                      reply for 10 min, deny the dialog and record the question.
  context_watch.py  — `tide hook context-watch` (Stop): context is full -> run
                      `tide offload` (one nudge per session).
  session_end.py    — `tide hook session-end` (SessionEnd): stamp `ended:` on the
                      session passport.
  install.py        — `tide install-hooks`: write the entries into
                      .claude/settings.json, MERGE-not-clobber existing hooks.

``cli.py`` wires the human ``install-hooks`` command and the internal ``hook``
dispatch group via :func:`tide.hooks.install.register` /
:func:`tide.hooks.install.register_hook_group`.
"""
