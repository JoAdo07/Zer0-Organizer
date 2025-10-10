#!/usr/bin/env python3
"""
Tidying files: Simple file renamer and organizer.

Features
- Rename: add prefix/suffix, prepend modified date, add sequential numbers
- Sort: move files into folders by extension or by category (Images, Docs, etc.)
- Safe by default: dry-run mode (use --commit to apply)
- Works on Windows/macOS/Linux (standard library only)

Usage examples
  Rename with prefix + date-stamp + numbering (preview only):
    python organizing_files.py rename --dir ./downloads --prefix IMG_ --datestamp --seq

  Actually apply changes:
    python organizing_files.py rename --dir ./downloads --prefix IMG_ --datestamp --seq --commit

  Sort by category (Images, Documents, etc.):
    python organizing_files.py sort --dir ./downloads --by category --commit

  Sort by extension folders (e.g., JPG, PDF):
    python organizing_files.py sort --dir ./downloads --by ext --commit

  Only include specific extensions:
    python organizing_files.py rename --dir . --ext .jpg .png --prefix OLD_ --commit
"""

import argparse
import datetime
import os
import sys
import fnmatch
from typing import List, Dict, Tuple, Optional

# ---------- Helpers ----------

CATEGORIES: Dict[str, set] = {
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".tiff", ".heic"},
    "Documents": {".pdf", ".doc", ".docx", ".txt", ".md", ".rtf", ".odt", ".ppt", ".pptx", ".xls", ".xlsx", ".csv"},
    "Audio": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"},
    "Video": {".mp4", ".mov", ".mkv", ".avi", ".webm"},
    "Archives": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"},
    "Code": {".py", ".js", ".ts", ".html", ".css", ".json", ".xml", ".yml", ".yaml", ".sh", ".bat", ".ps1",
             ".java", ".c", ".cpp", ".cs", ".go", ".rs", ".php", ".rb", ".kt"},
}

def collect_files(base_dir: str, recursive: bool, ext_filter: Optional[List[str]], exclude: Optional[List[str]]) -> List[str]:
    base_dir = os.path.abspath(base_dir)
    exts = {e.lower() for e in ext_filter} if ext_filter else None

    files: List[str] = []
    if recursive:
        for root, dirs, filenames in os.walk(base_dir):
            for name in filenames:
                path = os.path.join(root, name)
                if exts and os.path.splitext(name)[1].lower() not in exts:
                    continue
                if exclude and any(fnmatch.fnmatch(name, pat) for pat in exclude):
                    continue
                files.append(path)
    else:
        for entry in os.scandir(base_dir):
            if entry.is_file():
                if exts and os.path.splitext(entry.name)[1].lower() not in exts:
                    continue
                if exclude and any(fnmatch.fnmatch(entry.name, pat) for pat in exclude):
                    continue
                files.append(entry.path)
    return files

def unique_name(dirpath: str, base: str, ext: str) -> str:
    candidate = f"{base}{ext}"
    n = 1
    while os.path.exists(os.path.join(dirpath, candidate)):
        candidate = f"{base}_{n}{ext}"
        n += 1
    return candidate

def safe_move(src: str, dst_dir: str, new_name: Optional[str], dry_run: bool) -> Tuple[str, str]:
    os.makedirs(dst_dir, exist_ok=True)
    if new_name is None:
        new_name = os.path.basename(src)
    dst_path = os.path.join(dst_dir, new_name)
    dst_dir2 = os.path.dirname(dst_path)
    base, ext = os.path.splitext(os.path.basename(dst_path))
    final_name = unique_name(dst_dir2, base, ext)
    final_path = os.path.join(dst_dir2, final_name)

    action = f"{src} -> {final_path}"
    try:
        if dry_run:
            print(f"[DRY RUN] {action}")
        else:
            os.replace(src, final_path)
            print(f"[DONE] {action}")
    except Exception as e:
        print(f"[ERROR] Failed to move {src} to {final_path}: {e}")
    return src, final_path

def file_datestamp(path: str, datefmt: str) -> str:
    ts = os.path.getmtime(path)  # last modified time
    return datetime.datetime.fromtimestamp(ts).strftime(datefmt)

# ---------- Commands ----------

def cmd_rename(args: argparse.Namespace) -> None:
    files = collect_files(args.dir, args.recursive, args.ext, args.exclude)
    if not files:
        print("No files found.")
        return

    # Determine numbering width if sequential
    width = args.width
    if args.seq and width is None:
        width = max(2, len(str(len(files))))

    count = 0
    for idx, path in enumerate(sorted(files), start=args.start):
        dirpath = os.path.dirname(path)
        old_name = os.path.basename(path)
        stem, ext = os.path.splitext(old_name)

        # Build new base name
        new_base = stem
        if args.seq:
            new_base = f"{str(idx).zfill(width)}_{new_base}"
        if args.datestamp:
            ds = file_datestamp(path, args.datefmt)
            new_base = f"{ds}_{new_base}"
        if args.prefix:
            new_base = f"{args.prefix}{new_base}"
        if args.suffix:
            new_base = f"{new_base}{args.suffix}"

        new_name = f"{new_base}{ext}"
        if new_name == old_name:
            # Skip if no change
            continue

        safe_move(path, dirpath, new_name, dry_run=(not args.commit))
        count += 1

    print(f"{'(Preview) ' if not args.commit else ''}Renamed {count} file(s).")

def category_for_ext(ext: str) -> str:
    ext = ext.lower()
    for cat, exts in CATEGORIES.items():
        if ext in exts:
            return cat
    return "Others"

def cmd_sort(args: argparse.Namespace) -> None:
    files = collect_files(args.dir, args.recursive, args.ext, args.exclude)
    if not files:
        print("No files found.")
        return

    moved = 0
    for path in files:
        dirpath = os.path.abspath(args.dir)
        _, name = os.path.split(path)
        ext = os.path.splitext(name)[1]

        if args.by == "ext":
            sub = ext[1:].upper() if ext else "NOEXT"
        else:  # category
            sub = category_for_ext(ext)

        dst_dir = os.path.join(dirpath, sub)
        safe_move(path, dst_dir, name, dry_run=(not args.commit))
        moved += 1

    print(f"{'(Preview) ' if not args.commit else ''}Moved {moved} file(s).")

# ---------- CLI ----------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="organizing_files.py", description="Batch rename or organize files.")
    sub = p.add_subparsers(dest="cmd", required=True)

    # Common
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--dir", default=".", help="Target directory (default: current).")
    common.add_argument("-r", "--recursive", action="store_true", help="Include files in subfolders.")
    common.add_argument("--ext", nargs="*", help="Only process these extensions (e.g., .jpg .png).")
    common.add_argument("--exclude", nargs="*", help="Exclude files matching these patterns (e.g., *.bak *.tmp).")
    common.add_argument("--commit", action="store_true", help="Apply changes. Without this, it's a dry run.")

    # rename
    pr = sub.add_parser("rename", parents=[common], help="Batch rename files in place.")
    pr.add_argument("--prefix", default="", help="Prefix to add.")
    pr.add_argument("--suffix", default="", help="Suffix to add (before extension).")
    pr.add_argument("--datestamp", action="store_true", help="Prepend file modified date.")
    pr.add_argument("--datefmt", default="%Y-%m-%d", help="Date format (default: %%Y-%%m-%%d).")
    pr.add_argument("--seq", action="store_true", help="Add sequential numbering.")
    pr.add_argument("--start", type=int, default=1, help="Starting number (default: 1).")
    pr.add_argument("--width", type=int, default=None, help="Zero-pad width (auto if omitted).")
    pr.set_defaults(func=cmd_rename)

    # sort
    ps = sub.add_parser("sort", parents=[common], help="Move files into folders by extension or category.")
    ps.add_argument("--by", choices=["ext", "category"], default="category", help="Group by extension or category.")
    ps.set_defaults(func=cmd_sort)

    return p

def confirm_commit():
    resp = input("Are you sure you want to apply changes? Type 'yes' to continue: ")
    if resp.strip().lower() != "yes":
        print("Aborted by user.")
        sys.exit(0)

def main():
    parser = build_parser()
    args = parser.parse_args()
    if getattr(args, "commit", False):
        confirm_commit()
    args.func(args)

if __name__ == "__main__":
    main()