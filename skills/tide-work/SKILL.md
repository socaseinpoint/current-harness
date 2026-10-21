---
tagline: "Checklist work-cycle from the board"
summary: "Take a work item, agree the plan by dictation, check items with proof and drive it to review; only the human marks it done."
plugin: work
name: tide-work
description: The cycle of a "work" from the tide board — take a work, agree the plan by dictation (plan/propose → the human's word → agree), check items with proof, drive it to review; only the human marks it done. The mechanics are the native tide work verbs (add/plan/propose/agree/checklist/take/dispatch/check/uncheck/fix/title/close/reopen/list/show) over .tide/arcs/works/NN-slug/work.md of your project. Triggers — "take a work", "take work X", "run it through a work", "check off a work item", "works from the board", "show works", "/tide-work".
---

# tide-work — how an agent handles a work

A work = an arc of `kind: work` in `.tide/arcs/works/NN-slug/work.md` of the project
where it was created — the current one by default (the control-home is itself a tide
project, its works live in its own `.tide/arcs/works/`): free text (a task or a
problem, no types) + `## plan` + `## checklist` + `## log`. The board is a projection
of these files: the boxed `tide board` shows the cards, the human's buttons live
on the live (interactive) board. Your mechanics are the **native `tide work …` verbs**
(the "work = a kind of arc" law: not a separate entity, but an arc with its own
state machine).

State machine: `open → taken → review → done`. The verbs move the status and
write the log themselves — don't edit work.md by hand. A work key: NN, NN-slug or slug.
The work lives in ANOTHER roster project → add `--project <name from roster>`
to any verb.

## gestures

**0. Look around.** `tide work list` / `tide work show <key>`.

**1. Lay it out and agree — by dictation.** You hang the plan and the steps; the human
says "yes" — not with a button on the card, but in words in the orchestrator's chat
(decision 06: the human answers only through the session). The format is the "card
frame" below.
```bash
tide work plan <key> "Problem: …\nWhere we are: …\nResult: …"
tide work propose <key> "Step title\ndescription" "Second step\ndescription"
tide work propose <key> --replace "…"   # changed your mind: drop the old [?], propose these
```
Proposed items land as `- [?]` (dashed on the board) and wait for the word.
The human reads the ISSUES desk and dictates: "ok / not ok / fix this". Record it
verbatim:
```bash
tide work agree <key> --word "<their word>"      # all pending [?] → regular items
tide work agree <key> 2 3 --word "…"             # only these
tide work agree <key> --drop 4 --word "…"        # "no": the item is removed with its description
```
Agreed → take it:
```bash
tide work take <key> --by <who-you-are> --word "<the word you took it on>"
```
Safety catches (you don't bypass them, you use them to get the word): `check`/`uncheck` on
a `- [?]` refuse; the work will NOT go to review while even one `[?]` is pending;
`propose` on a work in review sends it back to taken — the desk has a question again.
`tide work checklist <key> …` replaces the whole checklist with already agreed
items; it refuses over checked ones (`--force` only on the human's word).

**2. Work.** The world changes in the window of the project from `project:` (the roster
tells you its folder), not where the card lives. If the project has a skill, use it first.
`project:` is empty — ask the human.

**3. Set the cursor when you start an item.** The board shows where you are
right now ONLY from your words — it does not know by itself and is forbidden to guess
("the first unchecked one" has already lied to the human):
```bash
tide work at <key> <N>        # started item N
tide work at <key> --clear    # let go, not working on anything
```
Set it when an item STARTS, move it as you go. No need to clear it after yourself:
`check` on the same item clears the cursor. The cursor gates nothing — it is an
"I'm here" mark: the board underlines the item in cobalt and writes the line "agent
is doing: N · item". No cursor — no line at all, and the human sees only the count.

**4. Check by fact.** Only what is done, proof is mandatory (the verb won't let you
through without it):
```bash
tide work check <key> <N> --proof "what exactly was done: commit/link/file"
tide work uncheck <key> <N> --reason "why it rolled back"
```
**The doer checks** (the human's signature, 30.07): you did the item — you check it, with
proof (the verb won't let you through without it). An item that is human by nature — to see
with their own eyes, to run on their machine, something personal — is checked by the human:
with a click on the live board (their hand is its own proof, the log records "human's
hand"), or without it — by a word to you, and then you check it with the proof "human's
hand: <the word verbatim>". The checkmark is NOT acceptance: the human's authority gestures
are separate — the "yes" to the plan (`agree --word`) and closing (`close --word`; a button
on the live board).

**The proof starts with a short line** (the human's signature: "reading it is
very hard to take in; I want to click quickly and see what was actually
verified"). The first line is for the human: what was done, how it was verified, what is
left unverified. Up to ~120 chars, NO paths or line numbers. Then a blank line —
and below it the technical part for the record, as much as you like: files, functions, commands, numbers.
```bash
tide work check 33 3 --proof "What was done — one line, in plain language.
Verified by rendering on a narrow screen.

live_projection.py: _proof_split (~4860) splits on the blank line…"
```
That first line is the FACE of the item on the card: it sits under it as ordinary quiet
text and is visible WITHOUT a click (the word "proof" does not appear on the board at all —
the human's decision, 01.08). Only the technical part goes behind a click — folded into
"details". A one-blob proof will still be shown, cut at the first sentence, but the card
should not have to guess for you where the human part ends: whatever lands in the first
line is what the human reads when deciding whether to accept the work.

All agreed items checked → the verb moves the work to review BY ITSELF and says so —
tell the human in words: the work is ready to close.

**5. A remark at acceptance → a fix item IMMEDIATELY.** The human looks at the result and
adds ("number on the card", "smaller pills") — this is not chat, it is a new
item of the work. Hang it right away; their word is the agreement: there is no dashed
`[?]` here.
```bash
tide work fix <key> "Title\ndescription" --word "the remark verbatim"
```
The item lands in the `## fixes` section, numbered continuously with the checklist, and is
checked like any other — with proof. A fix on a work in review sends it back to taken: until
it is checked, the work is not ready.

**6. done is NOT your gesture.** The human closes it: they tell you in words — then
the gesture below (the live board also has a "close" button):
```bash
tide work close <key> --word "<their word verbatim>"   # the word goes into the log
tide work reopen <key>                                 # to open it back up
```

## the card frame (the human's signature, 30.07)

**The card is written for the human** (the human's signature, 01.08: "in the future all works
must be done in human language"). Everything the human sees on the card —
title, plan, steps with descriptions, proofs, questions — is in their language, in the words
they themselves use about this work. There are no file names, functions or line numbers
in what they read: nobody decides by those, they are for reporting. The technical part does
not disappear, it goes deeper — behind the proof's first line (gesture 4) and into the body
of descriptions; on top stays what the human decides by: done or not, good enough
or not. The ear test: read what you wrote out loud — would they understand without opening
the repository? No — rewrite it. The rules below are special cases of this one.

- **The title is the work's NAME** (the human's signature, 31.07): 2–4 words, punchy —
  a verb or a label ("Move to the new server", "Subagent hygiene", "Thread sees
  its works"). No colons or lists — a second head and phases go
  into the plan. A wall of text in the H1 hurts: the card becomes unreadable. Details live
  in the plan and step descriptions. Renaming — only with the human's word:
  `tide work title <key> "<new>" --word "…"`.
- **The plan is three lines: Problem → Where we are → Result**, Result last.
  Example: "Problem: the board can't be opened from a phone. Where we are: the server
  listens on localhost only. Result: the board opens from a phone in two gestures".
- **A step is "Title\ndescription"**: the first line is the action, like in a notebook;
  details below, as a separate paragraph.

## the ISSUES desk — where the human reads

The first tab of the live board: only what waits for their hand (agreements and works in
review), and **one target action on top**, the rest folded. Hence the
rule: don't hang several agreements at once — the extra ones get folded away, and the
human drowns. One proposal → a word → the next one.

## the responsible thread — the AGENT binds/unbinds it (not the human)

YOU manage thread ownership; the human does not do it by hand (their word, 17.07):
- **binding is automatic:** `tide work take` (1.0.43) records the responsible
  thread itself — the one whose session you are in (resolved via `$CLAUDE_CODE_SESSION_ID`
  → arc → thread). From another project — by address `proj/NN-@thread`.
- **unbinding is your gesture too:** stopped running the work (handed it off,
  released it) → `tide work thread <key> --clear`. To change the thread —
  `tide work thread <key> --set <NN-@thread>`.

The link is two-way on the live board: the LEADING agent and the "dive in →" button (back to
their session) live on the big card of the "work" tab and on the ISSUES desk card —
those are the two entries into the work's session from the board; there is no manual thread
picker (only the agent creates ownership). The compacts — in the thread details and on the
project shelf (the "works" tab, full row) — are read-only in current versions: name, state
and progress, no buttons on them, click → modal. There is no contention lock yet: if you take
a work already run by another thread, you simply overwrite it; be careful (the human put off a hard lock).

## rules

- **The world changes only under a work** (the human's signature, 31.07): a build worker is not
  dispatched without a taken card — the worker's assignment carries the work key and the line
  "friction → candidate right away"; a remark along the way = a `fix` in the same work; no card —
  create and agree one first. Reading, exploring, talking — fine without a
  card: they don't change the world.
- **Sent a builder — record it** : the orchestrator
  took a work, reported to the human and wrote "with the worker" in pulses, but never sent
  the message to the worker — for three hours the card looked alive, with no building going on.
  A dispatch queue does not live in your head:
  ```bash
  tide work dispatch <NN | NN-slug | slug> --to "<worker name>"
  ```
  A line lands in the work's log, the status does NOT move (a dispatch is an event, not a
  state), a repeat dispatch is just another line: the worker was re-sent,
  replaced, a second one added. Only a taken work can be dispatched: a dispatch on `open` is a
  hole in the cycle — there is no plan yet and no "yes" has been said.
- **Friction → candidate right away** (decision 08, 31.07): ran into
  a problem — a slowdown, a pitfall, a moment where the human boiled over — drop it in the
  same move, without waiting for the work to end and without digging into it on the spot:
  ```bash
  tide candidate add <slug> "<the whole situation: what you were doing, where you tripped, how it ended>"
  ```
  Friction about another roster project → `--project <name>`, the full situation in
  the text. One rule for the worker and the orchestrator:
  the review comes later, from the candidates; staying silent with a problem is not allowed.
- **A candidate that became a work leaves the shelf** (the human's word, 01.08: "if a candidate
  turns into a work, it must be thrown out right away so nothing is duplicated").
  Not two gestures resting on your memory, but one verb — create the work right from the candidate:
  ```bash
  tide work add "Name in 2–4 words" --cand <NN | NN-slug | slug>
  ```
  The candidate's text lands as a DRAFT in `## plan`, the candidate itself goes to `__dropped__`
  (the same path as the cross on the board: off the shelf, but not off the disk), the log says
  "born from candidate". The work's name still comes from the argument: a candidate slug is
  long and no good as a title. This bypasses nothing — the work is born `open`
  and goes through plan → propose → the human's "yes", like any other. If it was born without
  the verb — throw the candidate out by hand in the same move and name its number in the plan.
  A shelf duplicating the desk promises the human what is already in progress: on 01.08 such
  candidates were thrown out by hand after the fact.
- **Test the fence with a dummy, not with yourself** : to find
  out how the role gate will cut a command, ask the engine, not a live shell:
  ```bash
  tide hook role-gate --explain-file /tmp/probe.txt   # keep a dangerous line in a file
  tide hook role-gate --explain 'ls | head -3'        # inline — only for a harmless one
  ```
  It prints the verdict, which link was cut and by which rule, and executes nothing.
  Running probes through a real Bash is forbidden: that is how a worker tested the gate on 31.07 —
  `$(rm -rf .)` expanded for real, the tree survived by luck. The worker is not
  gated, nobody would catch it — this habit is all that holds.
- Adding items after agreement — only with a new `propose` and a new word;
  a remark at acceptance — a `fix` right away (also with a word).
- **One item per unit of result** (a fix, a step), not per worker. Two built,
  a third verified — that is ONE item; who built it and how it was verified lives in its
  proof: "done by so-and-so, verified end to end".
- The human's answers come ONLY from the session; there is no "yes" button on the card —
  don't wait for a click, ask in the chat. **You asked, and they left or are silent** — the
  question is not left to sink in the scroll, it lands as a thing on the desk:
  ```bash
  tide artifact add "<caption: what you are waiting for>" --ask "<the full question>" --work <NN>
  ```
  It lands as `kind: question` — the card waits for them on the ISSUES desk and leads into your
  session; they still answer with a word (not a button). The question card has no
  buttons at all (the human's word, 01.08): no star, no "answered ✓" — only the text and
  the way into the session. So YOU REMOVE IT once you hear the answer, right away:
  ```bash
  tide artifact taken <NN> --word "<their answer verbatim>"
  ```
  If you don't remove it, the desk will keep calling them to a question already answered, and
  the human will stop trusting it. From another project — `--project <name from roster>`. The
  same way you post a plan gate you are stuck on: the board should not have to guess who is
  waiting for what.
- Deadline today/overdue — tell the human right away, don't stay silent.
- Don't change the name, deadline or project without the human's word.
- The human has their own gestures on the live board (check, edit text by click, close/open,
  thread, deadline) — the file is always right; before your gesture take a fresh look with `show`.

## experience (collecting pitfalls — add here after a run)

- 2026-07-16, first run (a live product project): the agent checked an item but did NOT
  move `status` and did not write the log — the board showed neither "in progress" nor
  the "close" button, the orchestrator pushed the status by hand. The answer is mechanics:
  the `tide work` verbs (1.0.42) move the status and the log themselves; we no longer edit
  the file by hand.
- 2026-07-17, dogfood "work ↔ thread": the feature was built AS a work (07) —
  created with `tide work add`, laid out with `checklist`, taken with `take`, each item
  checked with `check --proof` as it got ready. It works: the plan is visible on the board,
  progress is live. Do big work this way — as a plan through the same cycle.
- 2026-07-30, the ISSUES desk: the human drowned in four agreement cards at
  once ("I'm being loaded with a pile of info, I'm drifting"). Hang agreements one at a time —
  the desk shows one action.
- 2026-07-30: a long work title = pain on the card. Keep the title short,
  the wall of text goes into the description and the plan.
- 2026-07-30: a worker's idle signal ≠ a report of what was done. Verify yourself — git
  log, files, verbs; "silent" does not mean "done".
- Half a day of the human's remarks along the way (number on the card,
  pills, a "copy" button) went past the work — done, but at acceptance there was no sign
  they had been added at all. NOT allowed anymore: every remark = a `fix`
  right away. When closing a work, reread the fixes as a lesson: what the plan missed.
- 2026-07-31: description-style titles ("X: phase 1 + Y") on cards are unreadable —
  the human cannot orient. Title = a name of 2–4 words, details go into the plan;
  three works were renamed on the human's word.
- 2026-07-31: a skill edit went out through a worker without a card — done and agreed
  by word, but invisible on the board. "Work without a work" = a hole in the single layer;
  the rule above is the answer. A mechanical lock (a hook on spawning without a taken work) —
  a follow-up idea.
- Testing the fence with your own hands is a bad idea. A worker
  typed probe lines into a live Bash, `$(rm -rf .)` executed, what saved us was that
  `rm` refused to delete `.`. The answer is the dummy in the engine (`tide hook role-gate
  --explain[-file]`): a verdict without execution. It also immediately found a hole
  nobody had found by hand: the gate did not treat a newline as a separator,
  and `ls` with `rm -rf x` on the second line went through whole.
