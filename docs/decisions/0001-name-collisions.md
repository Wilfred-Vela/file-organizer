# 0001: Handle name collisions by renaming with a numeric suffix

- Status: accepted
- Date: 2026-11-21

## Context

When a file moves into a category folder, a file with the same name may already
be there (e.g. `Images/photo.jpg` from an earlier run, and a new `photo.jpg` at
the top level). On macOS and Linux, `os.rename` silently replaces the
destination, so doing nothing special would destroy user data.

## Decision (Y-statement)

In the context of **moving files into category folders that may already contain
a file with the same name**,
facing **the risk of silently destroying user data and the need for every file
to end up organized**,
we decided for **renaming the incoming file with a numeric suffix
(`photo (1).jpg`, `photo (2).jpg`, ...)**
and neglected **overwriting the existing file, skipping the incoming file and
leaving it in place, and asking the user interactively for each clash**,
to achieve **no data loss and a fully organized folder in a single
non-interactive run**,
accepting that **duplicate copies of the same file can accumulate and that the
renamed file's name no longer matches its original exactly**.

## Alternatives considered

| Option | Why not chosen |
|--------|----------------|
| Overwrite (`os.replace`) | Simplest, but permanently deletes a user file. Violates the safety rule. |
| Skip and leave in place | Safe, but defeats the purpose: the folder stays cluttered, and re-running never fixes it. |
| Prompt per clash | Safe and precise, but breaks one-command, unattended use and complicates testing. |
| Rename with suffix (chosen) | Safe and finishes the job. The `(n)` pattern matches what browsers and Finder already do, so users recognize it. |

## Consequences

- `unique_destination()` in `organize.py` probes `name`, `name (1)`, ... until
  it finds a free path.
- There is a small window between the existence check and the rename where
  another process could create the same name. This is acceptable for a
  single-user desktop tool.
- Tests `test_R5_never_overwrites_existing_file` and
  `test_R5_repeated_collisions_get_increasing_numbers` cover this behavior.
