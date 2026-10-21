---
tagline: "One-line pulse to the board"
summary: "Writes a ten-second tide offload line (current cursor plus next steps) into the session passport so the board always sees where work stands."
name: offload
description: Offload as you go — one tide offload command, 10 seconds, not a report. Appends a line to the context section of the CURRENT session arc's passport, moves the cursor, stamps offloaded-at. Use on "offload", "do an offload", "save progress", "/offload", when the context-watch Stop hook asks for it, and on your own — at the moment a decision is made or the work turns. The final handoff after offloads along the way is curation of what is already there, not a heavy dump.
---

# offload — offload as you go

One command, seconds. NOT a report, NOT a list, NOT a recap.

```bash
tide offload <session-slug> --cursor "<CURRENT ACTION, present tense>" \
  --next "<1–3 next steps separated by · >" "<what you decided/did — in plain words>"
```

**The form is board law (the human's word, 07.07):** the board shows it literally:
cursor → the "now" block, next → "next", note → a history line. So:
cursor is a present-tense verb ("wiring the board to the record form"), NOT meta
("role clarified"); next is concrete steps, not topics; note has no tech jargon
in the first words (the human reads it on the timeline).

## Rules (hard)

1. **One line each.** Cursor = "where I am". Note = "what I decided / what's
   next". Tempted to write a paragraph — cut it: the details already live in workspace.
2. **Your own session.** `<session-slug>` is the arc you are working in (the seed named
   it; if unsure — `tide status`, yours is the active one in the current thread).
3. **When:** made a decision · turned at a fork · finished a piece · the hook nudged.
   When the nudge comes, run its command right away and end the turn — don't argue.
4. This complements work in the arc, it does not replace it: work files go to workspace
   as you go (the [[tide-flow]] rule), offload is only the cursor plus a context line.
5. **`--summary` is a separate thing, not a note.** One line about the WHOLE arc:
   what it holds, for whoever is choosing which arc to open. `tide thread` prints
   it, `tide thread --check` catches it missing. Notes accumulate in
   `## context` (a log), the summary is rewritten (a showcase) — update it when
   the arc's contents change, not on every pulse.

```bash
tide offload <session-slug> --summary "<what this arc holds — one line>"
```

## Why

Offload quality drops as the session grows long — at the end you offload tired and
compressed. Lines written along the way turn the final handoff into curation of what
is ready: the seed is assembled from truth already on disk (the entry map), nothing
has to be remembered at the last moment.
