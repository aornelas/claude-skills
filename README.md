# claude-skills

Skills I've built with [Claude](https://claude.com) for [Claude Code](https://claude.com/claude-code) and Claude.ai. Each skill is a self-contained folder under `skills/` with a `SKILL.md` and any scripts it needs.

## Skills

| Skill | What it does |
|---|---|
| [learn-this](skills/learn-this) | Takes a YouTube link, pulls the transcript, and turns what the video teaches into concept notes plus a ready-to-paste prompt for applying it (new skill, implementation plan, or rearchitecture). |

## Install

Copy a skill folder into your skills directory:

```bash
git clone https://github.com/aornelas/claude-skills.git
cp -R claude-skills/skills/learn-this ~/.claude/skills/
```

Or symlink it, so `git pull` is the only update step:

```bash
ln -s "$PWD/claude-skills/skills/learn-this" ~/.claude/skills/learn-this
```

## learn-this

Drop a YouTube URL into chat (or say "learn-this" with a link). The skill:

1. Fetches the transcript with `scripts/get_transcript.py`, trying `youtube-transcript-api` and then `yt-dlp`. If YouTube blocks both (common from cloud IPs), it asks you to paste the transcript instead.
2. Identifies the underlying concept: the mechanism, why it works, what's actually new, and what has to be true for it to apply.
3. Writes a short markdown document with a concept summary, the application paths that genuinely fit, and a self-contained prompt you can paste into a fresh session.

Requirements: Python 3, and `pip install youtube-transcript-api yt-dlp`.

Example outputs, each produced by running the skill on a real video:

- [Building secure agents for knowledge work](skills/learn-this/examples/building-secure-agents-for-knowledge-work-concept-notes.md)
- [Claude Chat vs Cowork vs Code](skills/learn-this/examples/claude-chat-vs-cowork-vs-code-concept-notes.md)
- [How the Claude Code team uses Claude Code](skills/learn-this/examples/how-the-claude-code-team-uses-claude-code-concept-notes.md)

## License

MIT. See [LICENSE](LICENSE).
