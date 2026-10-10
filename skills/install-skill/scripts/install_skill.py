#!/usr/bin/env python3
"""
install_skill.py
-----------------
Symlinks a skill (or every skill in this repo) into the local Claude skills
folder, so Claude Code discovers it, and `git pull` in the repo is the only
"update" step there ever is — no copying, no reinstalling, no drift between
what's on disk and what's in git.

Usage:
    # Install one skill by name
    python install_skill.py learn-this

    # Install every skill in the repo (first-time machine setup)
    python install_skill.py --all

    # See what's installed vs. available, without changing anything
    python install_skill.py --list

    # Re-point an existing symlink that points somewhere unexpected
    python install_skill.py learn-this --force

Target directory defaults to ~/.claude/skills. Override with --target-dir if
your Claude config lives elsewhere (e.g. CLAUDE_CONFIG_DIR is set).
"""

import argparse
import os
import sys
from pathlib import Path


def repo_root_from_script() -> Path:
    """This script lives at <repo>/skills/install-skill/scripts/install_skill.py."""
    return Path(__file__).resolve().parents[3]


def list_available_skills(repo_root: Path):
    """Every subdirectory of skills/ that has a SKILL.md, sorted by name."""
    skills_dir = repo_root / "skills"
    if not skills_dir.is_dir():
        return []
    return sorted(
        p.name for p in skills_dir.iterdir()
        if p.is_dir() and (p / "SKILL.md").is_file()
    )


def install_one(name: str, repo_root: Path, target_dir: Path, force: bool):
    """Symlink one skill. Returns (status, message).

    status is one of: 'installed', 'already_installed', 'relinked',
    'conflict', 'not_found', 'error'.
    """
    source = repo_root / "skills" / name
    if not source.is_dir() or not (source / "SKILL.md").is_file():
        return "not_found", f"No skill named '{name}' in {repo_root}/skills (expected a SKILL.md there)."

    target = target_dir / name

    if target.is_symlink():
        current_target = os.readlink(target)
        if target.resolve() == source.resolve():
            return "already_installed", f"{name} — already installed and up to date (symlink -> {source})."
        if not force:
            return "conflict", (
                f"{name} — already a symlink, but pointing at {current_target}, not {source}. "
                f"Re-run with --force to relink, or remove it manually first."
            )
        target.unlink()
        os.symlink(source, target, target_is_directory=True)
        return "relinked", f"{name} — relinked (was -> {current_target}, now -> {source})."

    if target.exists():
        return "conflict", (
            f"{name} — {target} already exists as a real file/directory, not a symlink. "
            f"Not touching it. Remove or rename it manually if you want the repo-linked version instead."
        )

    target_dir.mkdir(parents=True, exist_ok=True)
    try:
        os.symlink(source, target, target_is_directory=True)
    except OSError as e:
        return "error", f"{name} — failed to create symlink: {e}"

    return "installed", f"{name} — installed (-> {source})."


def status_of(name: str, repo_root: Path, target_dir: Path) -> str:
    """One-line status for --list, without changing anything."""
    source = repo_root / "skills" / name
    target = target_dir / name
    if not target.exists() and not target.is_symlink():
        return "not installed"
    if target.is_symlink():
        if target.resolve() == source.resolve():
            return "installed (linked to this repo)"
        return f"installed, but linked elsewhere -> {os.readlink(target)}"
    return "present, but NOT a symlink (real copy — will drift from the repo)"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("name", nargs="?", help="Skill name to install (folder name under skills/). Omit if using --all or --list.")
    parser.add_argument("--all", action="store_true", help="Install every skill found under skills/ in this repo.")
    parser.add_argument("--list", action="store_true", help="List available skills and their install status; changes nothing.")
    parser.add_argument("--force", action="store_true", help="Relink if the target already exists as a symlink pointing somewhere else. Never overwrites a real (non-symlink) file or directory.")
    parser.add_argument("--target-dir", default=None, help="Where to install symlinks (default: ~/.claude/skills, or $CLAUDE_SKILLS_DIR if set).")
    parser.add_argument("--repo-root", default=None, help="Path to the skills repo root (default: derived from this script's own location).")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve() if args.repo_root else repo_root_from_script()
    if args.target_dir:
        target_dir = Path(args.target_dir).expanduser().resolve()
    elif os.environ.get("CLAUDE_SKILLS_DIR"):
        target_dir = Path(os.environ["CLAUDE_SKILLS_DIR"]).expanduser().resolve()
    else:
        target_dir = Path.home() / ".claude" / "skills"

    available = list_available_skills(repo_root)
    if not available:
        print(f"❌  No skills found under {repo_root}/skills — is --repo-root correct?", file=sys.stderr)
        sys.exit(1)

    if args.list:
        print(f"Repo   : {repo_root}")
        print(f"Target : {target_dir}\n")
        width = max(len(n) for n in available)
        for name in available:
            print(f"  {name.ljust(width)}  {status_of(name, repo_root, target_dir)}")
        return

    if not args.name and not args.all:
        print("Specify a skill name, or pass --all to install every skill. Available skills:")
        for name in available:
            print(f"  {name}")
        sys.exit(1)

    if args.name and args.name not in available:
        print(f"❌  '{args.name}' is not a known skill. Available: {', '.join(available)}", file=sys.stderr)
        sys.exit(1)

    targets = available if args.all else [args.name]

    results = {"installed": [], "relinked": [], "already_installed": [], "conflict": [], "not_found": [], "error": []}
    icons = {
        "installed": "✅", "relinked": "🔁", "already_installed": "⏭️ ",
        "conflict": "⚠️ ", "not_found": "❌", "error": "❌",
    }

    for name in targets:
        status, message = install_one(name, repo_root, target_dir, args.force)
        results[status].append(name)
        print(f"{icons[status]} {message}")

    if args.all:
        total = len(targets)
        print(f"\n{'─'*40}")
        print(f"📄  Skills processed  : {total}")
        print(f"✅  Installed         : {len(results['installed'])}")
        print(f"🔁  Relinked          : {len(results['relinked'])}")
        print(f"⏭️   Already installed : {len(results['already_installed'])}")
        print(f"⚠️   Conflicts         : {len(results['conflict'])}"
              + (f"  → {results['conflict']}" if results['conflict'] else ""))
        print(f"❌  Errors            : {len(results['error']) + len(results['not_found'])}")

    if results["conflict"] or results["error"] or results["not_found"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
