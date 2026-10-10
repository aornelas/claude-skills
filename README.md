# claude-skills

Skills I've built with [Claude](https://claude.com) for [Claude Code](https://claude.com/claude-code) and Claude.ai.

## Setup

Install `install-skill` once, then let it install everything else.

**1. Clone and bootstrap.** A skill can only run from a session that already knows about it, so `install-skill` needs one manual step to install itself:

```bash
git clone https://github.com/aornelas/claude-skills.git
python3 claude-skills/skills/install-skill/scripts/install_skill.py install-skill
```

That symlinks the skill into `~/.claude/skills`. (Prefer plain language? Open Claude Code in the clone and say "install the install-skill skill from this repo via a symlink.")

**2. Install any other skill by asking.** In a new Claude Code session, just say:

> install the learn-this skill

or `install all the skills`. It symlinks the skill from your clone into `~/.claude/skills` and reports exactly what it did.

**3. Update with `git pull`.** Installed skills are symlinks into your clone, so pulling is the only update step. New skills added to the repo need one "install the X skill" the first time.

`install-skill` only ever creates symlinks or refuses. It never overwrites a real file or directory, and it won't relink an existing symlink without `--force`.

## Skills

| Skill | What it does |
|---|---|
| [install-skill](skills/install-skill) | Symlinks a skill (or all of them) from this repo into `~/.claude/skills`, so installing is one sentence and updating is `git pull`. |
| [learn-this](skills/learn-this) | Takes a YouTube link and turns what the video teaches into a visual HTML report: thumbnail, a diagram of the mechanism, stills from the video, and a ready-to-paste prompt for applying it. |

Each skill is a self-contained folder under `skills/` with a `SKILL.md` and any scripts it needs.

## learn-this

Drop a YouTube URL into chat (or say "learn-this" with a link). The skill turns the video into a visual, self-contained HTML report:

1. Fetches the transcript with `scripts/get_transcript.py`, trying `youtube-transcript-api` and then `yt-dlp`. If YouTube blocks both (common from cloud IPs), it asks you to paste the transcript instead.
2. Pulls the video's thumbnail and details, and, when the video has slides, diagrams or demos, stills of the moments worth showing (`scripts/get_visuals.py`). Talking-head videos get no filler frames.
3. Identifies the underlying concept: the mechanism, why it works, what's actually new, and what has to be true for it to apply.
4. Writes the report: source card with the thumbnail, the core idea, a drawn diagram of the mechanism, the stills with deep links into the video, the application options that genuinely fit, and a self-contained prompt with a copy button. `scripts/finalize_report.py` inlines everything into a single `.html` file that opens anywhere and follows light or dark mode.

Requirements: Python 3, `ffmpeg`, and `pip install youtube-transcript-api yt-dlp` (if your `yt-dlp` is stale, the scripts fall back to `uvx yt-dlp`).

[![A learn-this report: Building secure agents for knowledge work](skills/learn-this/examples/preview.jpg)](https://aornelas.github.io/claude-skills/skills/learn-this/examples/building-secure-agents-for-knowledge-work-concept-notes.html)

Example reports, each produced by running the skill on a real video (click the preview above, or any link below, to open the live report). Each one is a single self-contained file in [`examples/`](skills/learn-this/examples), so you can also download it and open it locally:

- [Claude Chat vs Cowork vs Code](https://aornelas.github.io/claude-skills/skills/learn-this/examples/claude-chat-vs-cowork-vs-code-concept-notes.html): a product explainer with slides, so it includes stills from the video.
- [How the Claude Code team uses Claude Code](https://aornelas.github.io/claude-skills/skills/learn-this/examples/how-the-claude-code-team-uses-claude-code-concept-notes.html): a roundtable, so it relies on drawn diagrams.
- [Building secure agents for knowledge work](https://aornelas.github.io/claude-skills/skills/learn-this/examples/building-secure-agents-for-knowledge-work-concept-notes.html): an interview, same approach.

The thumbnails and stills belong to the videos' owners and are included only as commentary on those videos.

## License

MIT. See [LICENSE](LICENSE).
