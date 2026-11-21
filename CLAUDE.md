# CLAUDE.md

Guidance for working in this repo.

## Project

A command-line tool that sorts files in one folder into subfolders by type.
`problem.md` holds the requirements (R1–R10); `spec.md` holds the exact behavior.
Read both before changing anything.

## Hard constraints

- Python 3 standard library only. Nothing to install, no API keys, no logins.
- Runs with one command: `python3 organize.py <folder>`.
- Never touch files outside the target folder. Never overwrite a file.
- Tests use temporary folders only (`tempfile.TemporaryDirectory`), never real user folders.

## Layout

- `organize.py` — pure logic (`categorize`, `plan_moves`, `organize`, `format_summary`)
  kept separate from I/O (`main`, which parses args, prints, and returns an exit code).
- `tests/` — `unittest` tests. Every test name contains its requirement ID, e.g. `test_R7_...`.
- `docs/decisions/` — architecture decision records as Y-statements.

## Commands

- Run: `python3 organize.py <folder>`
- Test: `python3 -m unittest discover tests` (must pass with nothing skipped)

## Workflow

- Commit in small steps; messages say what changed and why.
- Never undo, amend, or force-push a commit.
- When behavior changes, update `spec.md` and the tests in the same change.
