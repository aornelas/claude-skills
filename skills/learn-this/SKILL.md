---
name: learn-this
description: Extracts the transcript from a YouTube video and turns whatever it teaches into an actionable, ready-to-paste prompt. Use this whenever the user shares a youtube.com or youtu.be URL together with intent to learn, understand, extract, or apply a concept or technique — e.g. "learn-this" followed by a video link, "watch this and tell me how I'd use it", "pull the concept out of this video", or any AI/engineering tutorial, talk, demo, or conference-clip link where the user wants to turn what's taught into something concrete (a new skill, an implementation plan, or a change to an existing workflow/architecture). Trigger even on a bare URL with minimal framing — a lone YouTube link dropped into chat is the primary use pattern for this skill, not the exception.
---

# learn-this

Turns a YouTube video into something the person can actually act on: not a summary, but a working document that names the underlying concept, sizes up how it applies to their situation, and hands them a prompt they can paste elsewhere to start building.

## Why this exists

Watching a video that teaches something useful and then actually doing something with it are two different activities, and the gap between them is usually just friction — re-watching to find the one part that mattered, figuring out how it maps onto your own setup, writing the first prompt from scratch. This skill exists to collapse that gap immediately after the video is watched, while the "I could use this for..." impulse is still fresh.

## Step 1: Get the transcript

Run the bundled script:

```bash
python3 scripts/get_transcript.py "<the youtube url>"
```

The script tries two independent extraction methods in order (`youtube_transcript_api`, then `yt-dlp`), because they hit YouTube through different code paths and one succeeding where the other fails is common, not exceptional. Install whichever isn't already present before running:

```bash
pip install youtube-transcript-api yt-dlp --break-system-packages -q
```

**Read the script's own output contract** — it prints one of two things:
- `=== TRANSCRIPT (source: ...) ===` followed by the transcript text. Proceed to Step 2.
- `=== MANUAL_FALLBACK_NEEDED ===` followed by the specific errors from each method.

### If it falls back to manual

This is expected often enough that it's worth explaining plainly rather than treating it as broken: YouTube actively blocks requests from cloud/datacenter IP ranges (the kind most sandboxes and hosted environments run on), regardless of which library is doing the asking. It's a YouTube-side anti-scraping measure, not a bug in the extraction method. Running from a real residential or office network (e.g. Claude Code on a personal machine) usually works fine; running from a shared cloud sandbox often doesn't.

When you hit this, don't retry the same command hoping it'll pass — tell the person in one plain sentence what happened, and ask them to either:
- Paste the transcript directly (YouTube: the "..." menu under the video → **Show transcript** → select all → copy), or
- Point you to a transcript/subtitle file if they have one.

Then continue with whatever text they give you exactly as if the script had returned it.

## Step 2: Get light context on the video

Before reading the transcript, do a quick web search for the video title or ID to pick up the title, channel, and what kind of video this is (tutorial, conference talk, product demo, casual walkthrough). Don't try to fetch the YouTube watch page directly for this — it's subject to the same rate-limiting as Step 1 and a search is faster and more reliable for metadata alone.

## Step 3: Find the actual concept, not just the summary

Read the transcript like a practitioner looking for something to steal, not like someone writing a book report. Push past "what happens in the video" to:

- **The underlying mechanism or pattern** — if the video is framed around a specific tool or product, ask what the general technique underneath it is, since that's usually the transferable part.
- **Why it works** — what problem does it actually solve, and what would break without it?
- **What's genuinely new here** — vs. a known pattern wearing new branding. Say so if it's the latter; that's still useful to know.
- **Preconditions** — what has to already be true (tools, data, access, prior setup) for this to apply at all.

If the video covers several distinct ideas, pick the 1-3 most substantial ones rather than cataloging everything mentioned. A shorter, sharper set of concepts is more useful than an exhaustive list.

## Step 4: Size up application paths

For each concept identified, consider these three lenses, but only write up the ones that genuinely fit — forcing all three onto a concept that only supports one produces filler the person will have to mentally discard:

- **New skill** — is this a self-contained, repeatable procedure worth packaging so it can be invoked again later, rather than re-derived from scratch each time?
- **Implementation plan** — is this a scoped feature or change to build inside something that already exists?
- **Rearchitecture** — does this concept challenge an assumption baked into an existing system, such that the honest recommendation is redesigning a piece of it rather than bolting something on?

Ground every suggestion in a specific detail from the transcript. If you genuinely don't know enough about the person's own setup to say which lens fits best, say that plainly rather than inventing a plausible-sounding specific to fill the space — a direct "this would depend on X, which I don't know" is more useful than a confident guess that's wrong.

## Step 5: Write the output document

Produce a single markdown file with this structure — it's a fixed contract so the output is predictable across runs, not a suggestion to riff on:

```markdown
# [Video Title] — Concept Notes

**Source:** [URL] · [Channel] · [length/date if known]

## Concept Summary
[2-4 paragraphs. What's actually being taught, the mechanism behind it, why it works.
Written for someone who has NOT watched the video.]

## Application Options

### [Lens name]: [specific, concrete label — not "New skill" alone, but what the skill would do]
[2-4 sentences, specific to this transcript, not generic advice.]

(repeat only for lenses that genuinely apply — 1 to 3 sections total)

## Ready-to-Use Prompt

> [A single, complete, self-contained prompt in second-person imperative that the
> person can paste into a fresh Claude conversation (or Claude Code) to start
> actually applying the concept. It must not assume the reader watched the video —
> restate whatever context is needed inline.]
```

This is a plain markdown file. Save it to `<slugified-title>-concept-notes.md` in the current working directory (or wherever the user asks) and present it. Keep the whole document tight enough to read in under two minutes; this is meant to be acted on, not archived.

## A note on scope

This skill is deliberately not a transcription tool or a video summarizer — if someone just wants the transcript itself, or a plain recap of what happened, that's a much simpler task than this skill is built for. The point of `learn-this` is the leap from "here's what the video said" to "here's what you'd actually do about it," and steps 3-5 are where that leap happens. Don't skip straight from transcript to prompt without genuinely thinking through steps 3 and 4 first — a prompt built on a shallow read of the transcript will sound plausible and be useless.
