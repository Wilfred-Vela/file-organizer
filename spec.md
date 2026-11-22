# Specification: File Organizer

Sorts the files at the top level of one folder into subfolders by file type.
Requirements R1–R11 come from `problem.md`; this document pins down the
behavior needed to implement and test each one.

## Command

```
python3 organize.py [--dry-run] <folder>
```

- Exit code `0` on success, `1` if any individual move failed, `2` on a usage
  error or invalid folder.
- Python 3 standard library only. No network, accounts, API keys, or installs.

## Requirements and behavior

| ID  | Behavior |
|-----|----------|
| R1  | Runs with the single command above using only the Python 3 standard library. No network access, configuration, or credentials. |
| R2  | Takes exactly one positional argument: the folder path. `~` is expanded. Missing or extra arguments, or any unknown `--` option, print usage and exit `2`. |
| R3  | Scans only the direct entries of the folder. Regular files are candidates. Hidden files (name starts with `.`, e.g. `.DS_Store`) and symbolic links are skipped and left in place. |
| R4  | The extension is the part after the last `.` in the name (via `os.path.splitext`), compared case-insensitively (`PHOTO.JPG` = `.jpg`). |
| R5  | Each file moves into a category folder inside the target folder, chosen by extension: `Images`, `Documents`, `Spreadsheets`, `Presentations`, `Audio`, `Videos`, `Archives`, `Code`. A file with an extension not in the table goes to `Other`. |
| R6  | A category folder is created only when at least one file goes into it; existing folders are reused. |
| R7  | Files with no extension (e.g. `README`, `Makefile`, `notes.`) go to `No Extension`. |
| R8  | After running, prints the number of files moved per category, the total, and the number skipped. If nothing was moved, says so. |
| R9  | If the path does not exist, or is not a directory, prints a message naming the path and the problem to stderr and exits `2` without changing anything. |
| R10 | Subfolders (including existing category folders) and their contents are never opened, moved, or modified. |
| R11 | `--dry-run` (before or after the folder) moves nothing and creates no folders. It prints `Dry run: nothing was moved.`, then one line per file, `name -> Category/new name`, using the same collision renames a real run would choose, then the per-category counts under `Would organize:` and the total. A file that would fail (e.g. the category name exists as a file) is listed under `Would fail:` and the exit code is `1`. Invalid paths are handled as in R9. |

## Safety rules

- Never reads, writes, or moves anything outside the target folder.
- Never overwrites a file. If `Images/photo.jpg` already exists, the incoming
  file is renamed `photo (1).jpg`, then `photo (2).jpg`, and so on
  (see `docs/decisions/0001-name-collisions.md`).
- If a single move fails (e.g. permissions), it is reported as skipped and the
  rest continue.

## Extension table

| Category      | Extensions |
|---------------|------------|
| Images        | jpg jpeg png gif bmp tiff tif webp svg heic ico |
| Documents     | pdf doc docx txt rtf odt md tex pages epub |
| Spreadsheets  | xls xlsx csv ods numbers tsv |
| Presentations | ppt pptx odp key |
| Audio         | mp3 wav flac aac ogg m4a wma aiff |
| Videos        | mp4 mov avi mkv wmv flv webm m4v |
| Archives      | zip tar gz bz2 xz 7z rar tgz dmg iso |
| Code          | py js ts html css java c cpp h json xml yaml yml sh rb go rs |

## Out of scope

Recursion into subfolders, undo, custom category configuration,
detecting type by file contents.
