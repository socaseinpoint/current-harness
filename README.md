# tide

**One seat for many projects. CLI + markdown + a board on localhost.**

You run several projects at once. Each has its own context, its own unfinished
lines, and between sessions all of it goes missing. tide holds the thread: all
state is plain markdown in each project's `.tide/` (you can `cat`, `grep` and
`diff` it), the commands are one binary `tide`, and the view from above is a
board in the browser.

## The living model

- **Control-home** — one folder you lead everything from: the project registry
  (`roster.md`) plus its own `.tide/` (tide runs itself the same way).
- **Projects** stay where they live; tide lays a `.tide/` layer on top and
  writes them into the roster (`tide adopt`).
- **Threads** — work runs in lines; a thread has a goal and a plan, and inside
  it live **sessions**: one sits down, works, hands off to the next. The thread
  doesn't break when the chat ends. `tide thread` prints the whole thing on one
  screen — goal, current step, decisions by state, what's moving, what's waiting
  on you, where the material of past sessions sits.
- **Works** — the human↔agent agreement on one card: free text, a checklist, a
  journal. The agent proposes items and checks them only with proof; "done" is
  set by the human alone, with a word.
- **Decisions** — what a thread concluded, one file per thread, on two separate
  axes: is it still **in force** (`accepted` · `superseded` · `dropped`), and was
  it **carried out** (a `done:` date, plus the `work:` that did it). They are not
  the same question — a decision can bind for years without anyone acting on it,
  which is exactly what went unnoticed here. `tide thread --check` finds the live
  promises with nobody carrying them.
- **The board** — `tide board`: a page on localhost with the streams of the
  home and every project, and the work cards. The inbox table (issues) and
  other surfaces are removable parts — see `tide plugins`.

An agent in a session doesn't have to remember commands — you speak in words,
it walks the `tide` verbs. Full list: `tide help`.

## Install

Needs **Python ≥ 3.12**. The main door is a clone and one command:

```bash
git clone https://github.com/socaseinpoint/current-harness && cd current-harness
./install.sh
```

`install.sh` puts `tide` on your PATH (through pipx if you have it, otherwise
its own venv + a symlink) and tells you the next gesture. The source stays with
you — that's not a side effect, that's the point: when it breaks, you fix it in
place (see below).

`tide init` and `tide install-hooks` wire five Claude Code hooks into
`.claude/settings.json` of the home (merge-safe, re-running changes nothing). There
is no uninstall verb yet: to unwire them, delete the `tide hook …` entries from
that file by hand.

Next: [QUICKSTART.md](QUICKSTART.md) — one pass from an empty folder to your
first closed work.

## A layer on top, not inside

The tide layer is external to your working repository. `.tide/` sits next to the
code and stays out of the project's history: the exclusion goes into
`.git/info/exclude`, a file git never commits, so your tooling does not ride
into a colleague's pull request. Your `.gitignore` is not touched, and `tide
adopt` makes no commit in a repo that already has one.

Running one thread as a team? `tide layer shared` commits `.tide/` with the
project. Committed it by accident already? `tide layer untrack` takes it out of
the index and leaves every file on disk — and says out loud that it does not
rewrite the commits that already carry it. `tide layer` says where you stand.

The package is impersonal too: skills speak in roles, not names, and no one
else's paths arrive in your project.

## The board, phone included

```bash
tide board --open
```

The server listens on localhost only; `tailscale serve` carries the board to
your phone — two commands, instructions in [docs/board.md](docs/board.md). Same
page: how to run the board as a launchd service so it lives on its own.

## Updates and repairs

- `tide self-update` — it tells you when a fresh release lands; on a clone
  that's `git pull` + reinstall, gated, with rollback.
- Broken? The source is already yours: fix it, run `./install.sh` (reinstall in
  place), and send the pain upstream.

## Machine-specific paths

The package carries no home paths, hosts or second-machine addresses (`tide verify --portable` enforces it).
Everything tied to one computer is read at run time.

## Development

```bash
python3.12 -m pytest -q     # the suite is cumulative and stays green
packaging/docker/run.sh     # a clean machine: clone → install → board, in docker
```

A small UNIX tool, deliberately so. MIT.
