# File Organizer

A small command-line tool that tidies a cluttered folder. It looks at the files
directly inside the folder you give it and moves each one into a subfolder
named after its type, based on its extension:

`Images`, `Documents`, `Spreadsheets`, `Presentations`, `Audio`, `Videos`,
`Archives`, `Code`, `Other` (unrecognized extensions), and `No Extension`.

- Only top-level files are moved; subfolders and their contents are left alone.
- Hidden files (like `.DS_Store`) and symbolic links are skipped.
- Existing files are never overwritten: a clash becomes `photo (1).jpg`.
- Nothing outside the chosen folder is touched.
- Prints a summary of how many files went into each folder.

Needs only Python 3 (standard library). Nothing to install, no accounts or API keys.

## Run it

```
python3 organize.py <folder>
```

Example:

```
$ python3 organize.py ~/Downloads
Organized files:
  Documents: 4
  Images: 12
Total: 16
```

Preview first without moving anything:

```
$ python3 organize.py --dry-run ~/Downloads
Dry run: nothing was moved.
  photo.jpg -> Images/photo.jpg
  report.pdf -> Documents/report (1).pdf
Would organize:
  Documents: 1
  Images: 1
Total: 2
```

Exit codes: `0` success, `1` some files could not be moved, `2` bad arguments
or the path is not an existing folder.

## Run the tests

```
python3 -m unittest discover tests
```

Tests create and clean up their own temporary folders.

## More

- `problem.md` — the problem and requirements R1–R11
- `spec.md` — exact behavior, including the full extension table
- `docs/decisions/` — design decisions
