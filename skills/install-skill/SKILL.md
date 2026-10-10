---
name: install-skill
description: "Symlinks a skill (or every skill) from this skills repo into ~/.claude/skills, so Claude Code can discover and run it, and a later `git pull` is the only update step there ever is. Use this whenever the user asks to install, add, set up, sync, or update any skill from this repo — even if they just say \"install the X skill\" or \"add a skill\" without naming this skill explicitly — and whenever someone is setting up a new machine and wants every skill at once (\"install all the skills\", \"set up my machine\"). Also the skill to reach for on the very first bootstrap: before install-skill itself is symlinked in, run its bundled script once directly, or ask Claude Code in plain language to do it. That's the one time this doesn't need to already be \"installed\" to work."
triggers: ["install skill", "install the skill", "install-skill", "add a skill", "sync my skills", "install all the skills", "set up my machine"]
---

# install-skill

Symlink a skill from this repo into the local Claude skills folder
(`~/.claude/skills` by default), so it's discoverable and runnable, while
the repo stays the one and only copy. There is nothing to reinstall after a
`git pull`: the symlink always resolves to whatever's currently in the repo.

Without this, getting a skill into `~/.claude/skills` is a manual `ln -s`
that nobody remembers the exact form of, or a copy that quietly drifts from
the repo. This gives you one consistent phrase ("install the X skill") and
safety checks so it can't clobber anything.

## The bootstrap problem (read this first)

A skill can only be invoked from a session that already discovers it, so
`install-skill` can't install itself the first time.

The fix is to **run the bundled script once, by hand or by asking Claude Code
directly in plain language**, no skill required:

```bash
git clone https://github.com/aornelas/claude-skills.git
python3 claude-skills/skills/install-skill/scripts/install_skill.py install-skill
```

Or tell Claude Code: "install the install-skill skill from this repo via a
symlink, so git pull keeps it updated." Claude Code has local filesystem
access and can run the same script itself.

Once `install-skill` is symlinked into `~/.claude/skills`, everything after
that, including re-installing `install-skill` after an update, goes through
this skill for consistency and the safety checks below.

(Sandboxed or cloud sessions generally can't reach `~/.claude/skills`, a
protected home-directory path. This only works from a session with direct
local filesystem access, i.e. Claude Code running on your machine.)

## Workflow

1. **Make sure the repo is current.** `git pull` in the clone before
   installing anything, so the symlink points at the latest version from the
   start.
2. **Run the bundled script** for what the user asked for:

   ```bash
   # One named skill
   python skills/install-skill/scripts/install_skill.py <skill-name>

   # Every skill in the repo: first-time machine setup
   python skills/install-skill/scripts/install_skill.py --all

   # Just check status, changes nothing
   python skills/install-skill/scripts/install_skill.py --list
   ```

   Run it from anywhere inside the repo clone. The script locates the repo
   root from its own file path, so it doesn't matter what directory the
   shell is currently in.
3. **Read the result back plainly.** The script reports one of five
   outcomes per skill: installed, already installed (no-op), relinked,
   conflict, or not found. Conflicts are the case worth explaining clearly:
   - If `~/.claude/skills/<name>` is a real file or directory (not a
     symlink), the script **never touches it**. Tell the user to remove or
     rename it manually if they want the repo-linked version instead.
   - If it's a symlink pointing somewhere else (a stale or manual install),
     the script reports the conflict and stops. Re-run with `--force` to
     relink it, once you've confirmed with the user that's what they want.
4. **Confirm and move on.** Once installed, tell the user they're done. No
   further steps, and `git pull` alone keeps every symlinked skill current
   from then on. New skills only need installing once; a session started
   afterwards will pick them up.

## Notes

- This uses `os.symlink`, which needs a Unix-like filesystem (macOS/Linux).
  On Windows, symlinks need elevated permissions or Developer Mode, so flag
  this rather than assuming it'll just work.
- `--target-dir` (or the `CLAUDE_SKILLS_DIR` env var) overrides the default
  `~/.claude/skills`, for anyone with a non-default Claude config location.
- The script only ever creates symlinks or refuses. It never deletes or
  overwrites a real file/directory, and never relinks an existing symlink
  without `--force`. Destructive-by-accident isn't a risk here by design.
- Skills installed this way always point at the clone they were installed
  from. If you move or delete the clone, re-run the install from the new
  location with `--force`.
