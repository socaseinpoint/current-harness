---
tagline: "How work lives inside an arc"
summary: "The tide working model for seeded sessions: orient via status and board, work inside the arc's workspace, drop candidates, close cleanly."
name: tide-flow
description: The tide working model for an agent in a tide session — "everything is an arc", and all work is DONE INSIDE the arc (in its `workspace/`), not scattered around. Covers how to orient on entry (status/board), how to work in an arc (input→workspace→output), how to drop a candidate (including into a sibling project from the roster), and how to close. Use whenever you do any work in a tide session, are unsure "where do files/progress go", work with arcs/candidates, or on "how does this all work here", "where do I put this", "tide flow", "/tide-flow".
---

# tide-flow

You are in a tide session. The start hook has already
given you the project's CANON.md, the active arc's passport and the roster. This skill
is about how to **do the work** here so it does not spill all over the place.

The CLI is your API. Commands are deterministic; `tide help` and `tide <cmd> --help`
are the source of truth on flags. This skill gives the MODEL, it does not duplicate the help.

## Two iron rules

### 1. Everything is an arc
Every unit of work lives as an arc (`NN-<slug>/` in `.tide/arcs/`). A thread
(`kind: thread`) is a container for the sessions of one line of work: sessions are linked
by **handoffs** (context transfer), not by empty re-entries. The thread law: the first
session is born together with the thread, every next one comes from a handoff (there is
no empty "+ new session" in the middle of a thread). (The "routine" entity was dissolved
by the canon on 17.07: anything recurring lives as a skill plus a project note, a run is
an ordinary session; if you meet an arc with `kind: routine`, it is legacy — convert it
into a note plus a skill, or ask the human.)
Don't start "work outside an arc": if there is no fitting arc, create one
(`tide arc new <slug>` / `tide arc new-session <slug> -p <thread>`) instead of writing into the void.

### 2. Work is DONE INSIDE the arc
This is the core of tide's value: the arc always shows what was done and how. The strict
semantics of the arc's three folders:

| Folder | What goes there | When |
|--------|-----------------|------|
| `input/` | what the arc started from — the seed, the spec, source material | on entry |
| `workspace/` | **ALL current work** — intermediate files, downloads, processed output, run logs, drafts, notes along the way | while working |
| `output/` | what the arc ENDED with — durable pointers to the final result only | on close |

Concretely: if the task goes to an external service, uploads an image, processes it,
calls an API, generates an artifact — **all of it goes into `<arc>/workspace/`**, not `/tmp`,
not the project root, not "somewhere nearby". Progress/events/decisions along the way also
go into workspace (as a note/log). You touch `output/` only when the arc is finishing.

Files for the human (images, PDFs, reports) go into your arc's `output/`.

Not sure which arc you are in → `tide status` (the board) shows the open arcs; the seed
named your active one. Arc path = `.tide/arcs/<NN-slug>/` (for a session —
`.tide/arcs/<NN-@thread>/arcs/<NN-slug>/`).

## Start gate — before the first work move

A session gets its passport floor AT BIRTH, by mechanics (14.07): the session name in
`title:` ("project — thread · NN", decision 09.10) and the thread's inherited live goal —
you no longer build it by hand.
Your part of the gate is to **bring the words to life for THIS session** and give the first
pulse, before the first edit/command on the task:

1. **A live goal** — not the thread slug, not a `<placeholder>`, but plain words for what
   this thread/session does. Slug-as-goal (`goal: main` on thread `01-@main`) =
   "there is no goal": the board treats such a goal as blind.
   ```bash
   tide arc set-goal <session> -p <thread> "<session goal>"
   tide arc set-goal <thread> "<goal in one line, ≤12 words>"   # if the thread has no goal yet
   ```
   Leave the title alone: tide named the session "project — thread · NN"
   (`proj — thread · 03`)
   and sets it again on every launch — do not pass `--title`.
   `set-goal` refuses an empty value / a slug / a placeholder (in `--title` too) — that
   is the gate. A thread without a goal is fine for a draft (signature C), but a session
   without live words is a blind spot on the board.
2. **The first `tide offload`** — right away, before any work (see below). Without the
   first pulse the board does not know the session is alive.

If you forget, the Stop hook catches it by session activity (even if you worked in another
repo) and sends you back with a command; for a blind goal it adds `tide arc set-goal`. But
closing the gate yourself on entry is cheaper than getting nudged.

## The work loop

1. **Orient** — `tide thread`. One screen for the whole thread. The FIRST block is
   the "main" one, the `## read first` section of plan.md: the essence, where we are
   heading, principles, ceiling, what not to do, what is burning, the measure. Read it
   in full and first — it is what the thread must not lose at a handoff; the rest of the
   screen you can skim. Then: the goal, the current plan step, decisions by state
   (what is signed and NOT done is visible at once),
   what is in progress, what waits for the human's hand, where past sessions' material lives.
   This is a fresh session's entry — don't ask the human to retell the thread, ask the machine.
   Next — the active arc's passport (`## cursor` is the resume point) and
   `tide status` if you need the whole stream. Don't start until you understand where the work is.
2. **Work in the arc** — all files/progress in `workspace/` (rule 2). As you go, update
   `## cursor`/`## context` in the passport so the next session can pick it up.
3. **Noticed something unrelated, or stumbled** — drop it as a candidate without getting distracted (see below).
4. **Close** — when done: put the durable result into `output/`, then
   `tide arc close <slug>` (the gate won't let you close with an empty output / placeholders).

## Offload as you go — `tide offload` (10 seconds, not a report)

The truth is written to disk the moment it is born, not at the end of the session. Made a
decision, turned at a fork, finished a piece — one command:

```bash
tide offload <session-slug> --cursor "<where I am — one line>" "<what I decided / what's next>"
```

Rule: one line each, no reports or lists. This appends to the passport's
`## context` and moves the cursor — the final handoff then becomes
curation of what is ready, not a heavy dump.

A separate flag — `--summary "<what this arc holds>"`: one line about the whole arc,
for whoever is choosing which arc to open. `tide thread` shows it,
and `tide thread --check` catches it missing. Rewrite it when the arc's contents
change: `## context` is a log (grows), `## summary` is a showcase (rewritten). If you
forget, the Stop hook reminds you by itself (workspace moved, the passport has been
still for >15 min): run its command and end the turn. Don't argue with the nudge and
don't postpone it — this is the "nothing sinks" law.

## Context full — offload

tide has no compaction: a full session is replaced by a fresh one. When the context hits
the threshold (`TIDE_CTX_LIMIT`, 200k by default), the Stop hook asks once for an offload:
run its `tide offload` command (cursor and next step) and end the turn.
Write what matters as pulses along the way — the fresh session reads them from disk.

A subagent does not offload: it writes its result into the arc's files and returns a short
answer.

## Candidates — don't lose ideas

A future task came up that does NOT belong to the current arc — don't do it now,
drop it into the backlog:

```bash
tide candidate add <slug> "<the full idea>"            # into the CURRENT project
tide candidate add <slug> "<idea>" --project <name>    # into a SIBLING project from the roster
```

The cross-project variant: you are working in project A and notice something that belongs to
project B (it is in the roster — see the Roster block in the seed) → drop the candidate
straight into B, it lands in its backlog marked `from: ↗ A`. Don't switch context, don't drag
someone else's work into your arc. Capture is cheap; only that project's orchestrator promotes
a candidate into an arc (`tide candidate promote`), locally.

**Friction is a candidate too** (decision 08, 31.07): not only an idea, but
any problem — a slowdown, a pitfall, a moment where the human boiled over — drops as a
candidate right away, with the whole situation: into the current project, or, if it is about
another roster project, `--project <its name>`. One rule for the worker and the orchestrator:
staying silent with a problem is not allowed; the review comes later, from the candidates.

**An unanswered question goes on the desk as a card, not into the scroll:** you asked the
human and they left or are silent — `tide artifact add "<caption>" --ask "<question>"` (into
another roster project — `--project <name>`). The question lands as a thing on the ISSUES desk
and waits for them there; they answer with a word in the session, and the answer takes the card away.

## Project notes — the human's cheat sheets (`.tide/notes/`)

A note is a "just remember" card on the board's shelf: a command/cheat sheet the
human pulls out in two clicks (canon 17.07: "four things on the shelf" — skill ·
work · candidate · note). The NOTES block on session entry shows you the index of the
current project's notes; read a body when needed, don't load them all.

Working with them means plain files, NO separate CLI:

- **Read**: `.tide/notes/<name>.md` — when the index says the answer is there
  (deploy command, removing a stub, access).
- **Extend/fix**: edit the file; learned something live (a new flag, a pitfall,
  the exact command) — write it in. Format: `# title`, `tags: …`, body (code
  indented 4 spaces or ```), a trailing `## log`.
- **The log is mandatory**: every gesture of yours is a line in `## log`:
  `- <ISO time> — <what you did> (agent, <session/arc>)`. Nothing sinks
  silently; the log survives any edit.
- **Creating a new one**: `NN-slug.md` with the next number + a "created" line in
  the log — when the human explicitly asks "write a note" OR you dug up a command
  they will want to pull out by hand (ask/tell them, don't breed notes quietly).
- **Delete only into the grave**: not rm, but a move to `notes/__dropped__/` with
  a line in the log — and only on the human's word.

## A new PROJECT ≠ a new thread (important)

"Let's start a project" from the human = a ROSTER project, not a thread. The levels differ:
- **A roster project** — a line in the control-home's `roster.md`; only it shows up
  in the "Pick a project" picker. Created with ONE command:
  `tide adopt <abs-path> [--name <name-in-roster>]` — git init + first commit +
  `.tide/` skeleton + a roster line, idempotent and worktree-ready.
- **A thread** (`NN-@slug` in `.tide/arcs/`) — a line of work INSIDE a project; it never
  shows up in the project picker.

Created a thread and reported "the project is ready" → the human opens the picker and
can't find the project. If unsure what the human meant, ask "a roster project
or a thread inside the current one?".

## Roles (briefly)
- **orchestrator** — drives the CLI: opens/closes arcs, merges the canon, promotes
  candidates. You know the commands, the human doesn't.
- **worker** — works ONE open arc; writes only to its `workspace/`/`output/` +
  its own candidate drops. Does not merge the canon, does not promote candidates.

The seed (and `TIDE_ROLE`) named your role.

## A skill broke or you got stuck? Report it (important)

tide skills (`tide-*`) are a living tool, and you are their main user. If a skill
in this group misbehaved, a command failed, the instructions did not match reality,
or you got stuck on unclear wording — **don't stay silent and don't fix it silently**.
Record the pain as a candidate:
`tide candidate add skill-<name>-<short> "<the same story>"`
(from another project — `--project <name from roster>`); it lands in the backlog marked
`from: ↗ <your project>`. Reporting is cheap; the more precise the repro, the
faster the fix.
