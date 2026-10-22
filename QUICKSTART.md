# tide — the first hour


Already installed and lost? `tide quickstart` prints this route in your terminal,
`tide quickstart --open` opens the page.

One pass: install → home → project → board → your first closed work.
Every step says what you'll see. Needs Python ≥ 3.12; step 6 needs
[Claude Code](https://claude.com/claude-code) (tide's own machinery works without it).

The commands are spelled out here so you feel the cycle by hand. In real work an
agent in a session walks them — you speak in words.

---

## 1. Install

```bash
git clone https://github.com/socaseinpoint/current-harness && cd current-harness
./install.sh
```

**You'll see:** `✓ tide <version>` and a hint for the next gesture. If PATH
didn't pick it up, the script prints one line to add to your shell profile —
and that's the only thing here you ever "configure".

## 2. Unfold a home

The home (control-home) is one folder you lead every project from:

```bash
mkdir ~/harness-home && cd ~/harness-home
tide init --git
```

**You'll see** a list of what was created:

```
tide: tide control-home ready at ~/harness-home
  + canon/CANON.md
  + state/strictness
  + .tide/
  + roster.md
  + .tide/plugins (core only)
  + README.md
  + git repo (birth commit)
  + Claude hooks → …/.claude/settings.json (5)
  + skills → …/skills: offload, tide-flow, tide-work
```

Hooks and skills landed on their own — an agent opened in this home knows how to
offload from day one. A fresh home gets the core only;
removable parts live in `tide plugins`.

Now tell the shell where the home is — otherwise the next step will create a
project but won't write it into the roster. It isn't an error, just one skipped
line in the middle of an otherwise successful run:

```
  · roster  no control-home — set $TIDE_HOME or run 'tide init' somewhere
```

Miss that line and the project never shows up on the board.

```bash
export TIDE_HOME=~/harness-home
```

Put the same line in your shell profile so `tide` finds the home from any folder
and in later sessions.

## 3. Adopt a project

A project is any folder with code, old or new:

```bash
mkdir -p ~/code/myapp && cd ~/code/myapp   # or step into a project you already have
tide adopt --goal "a small web app — trying tide"
```

**You'll see** the adoption steps:

```
tide: adopted myapp at ~/code/myapp
  ✓ git     git init
  ✓ tide    scaffolded .tide/ (canon seeded with the goal)
  ✓ layer   .tide/ stays on this machine (.git/info/exclude, not .gitignore)
  ✓ readme  README.md generated from canon
  ✓ commit  empty first commit (worktree-ready; none of your files in it)
  ✓ roster  rostered → ~/harness-home
ready: next → tide board --open
```

The project is born speaking: its README and canon carry your goal, not template
filler. It's already in the home's roster.

Adopting a project that **already has commits** looks the same minus two lines:
no commit is written there, and your working tree is left exactly as it was. The
`layer` line is why — `.tide/` is how you run the work, not part of the project,
so it is excluded in `.git/info/exclude`, a file that never leaves this machine.
Want it committed with the project (a team on one thread)? `tide layer shared`.
Already committed it? `tide layer untrack`.

## 4. Open the board

```bash
tide board --open
```

**You'll see** in the browser (http://127.0.0.1:8765): the home's stream, myapp's
stream, a HEALTH line on each. The page re-reads `.tide/` every 30 seconds —
everything you do next shows up there without a restart. The port is a flag,
`--port`; for your phone and as a service — [docs/board.md](docs/board.md).

## 5. First work — all the way to closed

A work is an agreement card: the agent proposes steps, you say yes, the agent
checks items only with proof, and you close it. The `tide work …` commands always
work, out of the box. The removable `work` part adds the tide-work skill for the
agent and a works tab on the board — switch it on so the agent already knows this
cycle in step 6 (once per home):

```bash
tide plugins on work        # skill for the agent + a place on the board; the verbs work without it
```

Walk one work by hand to see the cycle:

```bash
cd ~/code/myapp
tide work add "the app says hello — check that it starts"
tide work propose 01 "start the app and see it answer"   # an agent gesture: a proposal
tide work agree 01 --word "yes"                          # your word
tide work take 01 --by "first session"
tide work check 01 1 --proof "started it — it answers"   # a check won't pass without proof
tide work close 01 --word "accepted"                     # done is set by the human alone
```

**You'll see** a short answer after each gesture — what happened and a hint for
the next one (usually two lines) — and on the board, a card that went
open → taken → review → done. `tide work show 01` prints the journal: every
gesture is a line, with the human's words in it.

## 6. A session

```bash
cd ~/code/myapp
claude
```

**You'll see** Claude start with the session-start hook's context already in it:
the project's canon, the live thread, the roster. From here you say what you
want ("add a work: …", "show me the status") and the agent walks the verbs from
step 5 itself.

---

Want to go deeper: `tide help` — every command; [README.md](README.md) — the
whole model; [docs/board.md](docs/board.md) — the board as a service and on your
phone. Broken? The source is yours: fix it and run `./install.sh`.
