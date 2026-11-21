#!/usr/bin/env python3
"""Sort the files at the top level of a folder into subfolders by file type.

Usage: python3 organize.py <folder>

Logic (categorize, plan_moves, organize, format_summary) is kept separate
from input/output (main) so it can be tested directly.
"""

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

NO_EXTENSION = "No Extension"
OTHER = "Other"

CATEGORIES = {
    "Images": "jpg jpeg png gif bmp tiff tif webp svg heic ico",
    "Documents": "pdf doc docx txt rtf odt md tex pages epub",
    "Spreadsheets": "xls xlsx csv ods numbers tsv",
    "Presentations": "ppt pptx odp key",
    "Audio": "mp3 wav flac aac ogg m4a wma aiff",
    "Videos": "mp4 mov avi mkv wmv flv webm m4v",
    "Archives": "zip tar gz bz2 xz 7z rar tgz dmg iso",
    "Code": "py js ts html css java c cpp h json xml yaml yml sh rb go rs",
}

EXTENSION_TO_CATEGORY = {
    "." + ext: category
    for category, exts in CATEGORIES.items()
    for ext in exts.split()
}


class InvalidFolderError(Exception):
    """Raised when the given path cannot be organized."""


@dataclass
class Result:
    moved: dict = field(default_factory=dict)    # category -> [new file names]
    skipped: list = field(default_factory=list)  # names left in place on purpose
    failed: list = field(default_factory=list)   # (name, error message)

    @property
    def total(self):
        return sum(len(names) for names in self.moved.values())


def categorize(filename):
    """Return the category folder name for a file name (R4, R5, R7)."""
    ext = os.path.splitext(filename)[1].lower()
    if ext in ("", "."):
        return NO_EXTENSION
    return EXTENSION_TO_CATEGORY.get(ext, OTHER)


def validate_folder(path):
    """Return the folder as a resolved Path, or raise InvalidFolderError (R9)."""
    folder = Path(path).expanduser()
    if not folder.exists():
        raise InvalidFolderError(f"Error: '{path}' does not exist.")
    if not folder.is_dir():
        raise InvalidFolderError(f"Error: '{path}' is not a folder.")
    return folder.resolve()


def _is_candidate(entry):
    """Regular, non-hidden, non-symlink files at the top level only (R3, R10)."""
    return (
        not entry.name.startswith(".")
        and not entry.is_symlink()
        and entry.is_file()
    )


def plan_moves(folder):
    """Return a sorted list of (source Path, category) for files to move."""
    folder = Path(folder)
    return [
        (entry, categorize(entry.name))
        for entry in sorted(folder.iterdir())
        if _is_candidate(entry)
    ]


def skipped_entries(folder):
    """Names of top-level files intentionally left alone (hidden or symlinks)."""
    return sorted(
        entry.name
        for entry in Path(folder).iterdir()
        if (entry.is_symlink() or entry.is_file()) and not _is_candidate(entry)
    )


def unique_destination(directory, name):
    """Return a path in directory for name that does not exist yet.

    photo.jpg -> photo.jpg, photo (1).jpg, photo (2).jpg, ...
    """
    candidate = directory / name
    stem, suffix = os.path.splitext(name)
    n = 1
    while candidate.exists() or candidate.is_symlink():
        candidate = directory / f"{stem} ({n}){suffix}"
        n += 1
    return candidate


def organize(folder):
    """Move top-level files of folder into category subfolders (R5, R6)."""
    folder = Path(folder)
    result = Result(skipped=skipped_entries(folder))
    for source, category in plan_moves(folder):
        target_dir = folder / category
        try:
            if target_dir.exists() and not target_dir.is_dir():
                raise OSError(f"'{category}' exists and is not a folder")
            target_dir.mkdir(exist_ok=True)
            destination = unique_destination(target_dir, source.name)
            os.rename(source, destination)
        except OSError as exc:
            result.failed.append((source.name, str(exc)))
            continue
        result.moved.setdefault(category, []).append(destination.name)
    return result


def format_summary(result):
    """Return a human-readable summary of an organize() result (R8)."""
    lines = []
    if result.total == 0:
        lines.append("No files to organize.")
    else:
        lines.append("Organized files:")
        for category in sorted(result.moved):
            lines.append(f"  {category}: {len(result.moved[category])}")
        lines.append(f"Total: {result.total}")
    if result.skipped:
        lines.append(f"Skipped: {len(result.skipped)} (hidden files or links)")
    if result.failed:
        lines.append(f"Failed: {len(result.failed)}")
        for name, message in result.failed:
            lines.append(f"  {name}: {message}")
    return "\n".join(lines)


USAGE = "usage: python3 organize.py <folder>"


def main(argv):
    if len(argv) != 1:
        print(USAGE, file=sys.stderr)
        return 2
    try:
        folder = validate_folder(argv[0])
    except InvalidFolderError as exc:
        print(exc, file=sys.stderr)
        print("Please provide the path to an existing folder.", file=sys.stderr)
        return 2
    result = organize(folder)
    print(format_summary(result))
    return 1 if result.failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
