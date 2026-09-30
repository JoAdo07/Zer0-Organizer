# Zer0-Organizer
Organizing files of a company as not to get messy and making everyone stressful/ragebaiting.

- Rename: add prefix/suffix, date-stamp, sequential numbers
- Sort: move files into folders by extension or by category (Images, Documents, etc.)
- Safe by default: dry-run preview (use `--commit` to apply)
- Undo: every `--commit` run writes a journal, reversible with `undo`
- Cross-platform: Windows, macOS, Linux

## Quick start

1) Clone and run with Python 3 (standard library only, no dependencies)
```bash
python organizing_files.py --help
```

2) Preview, then apply, then undo if needed
```bash
python organizing_files.py sort --dir ./downloads --by category
python organizing_files.py sort --dir ./downloads --by category --commit
python organizing_files.py undo --commit
```

Journals live in `~/.zer0-organizer/` (one per run); pass `--journal PATH` to
override, and `undo` without `--commit` previews the reversal.