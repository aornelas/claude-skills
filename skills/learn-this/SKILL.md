---
name: learn-this
description: Extracts the transcript from a YouTube video and turns whatever it teaches into a visual, self-contained HTML report with the video thumbnail, diagrams, stills from the video, and a ready-to-paste prompt. Use this whenever the user shares a youtube.com or youtu.be URL together with intent to learn, understand, extract, or apply a concept or technique — e.g. "learn-this" followed by a video link, "watch this and tell me how I'd use it", "pull the concept out of this video", or any AI/engineering tutorial, talk, demo, or conference-clip link where the user wants to turn what's taught into something concrete (a new skill, an implementation plan, or a change to an existing workflow/architecture). Trigger even on a bare URL with minimal framing — a lone YouTube link dropped into chat is the primary use pattern for this skill, not the exception.
---

# learn-this

Turns a YouTube video into something the person can actually act on: not a summary, but a visual report that names the underlying concept, shows it (a drawn diagram, plus stills from the video when the video has something worth showing), sizes up how it applies to their situation, and hands them a prompt they can paste elsewhere to start building.

## Why this exists

Watching a video that teaches something useful and then actually doing something with it are two different activities, and the gap between them is usually just friction — re-watching to find the one part that mattered, figuring out how it maps onto your own setup, writing the first prompt from scratch. This skill exists to collapse that gap immediately after the video is watched, while the "I could use this for..." impulse is still fresh.

The output is an HTML report rather than a text file because the concept is easier to hold when you can see it: the source video's thumbnail, a diagram of the mechanism, the frames where the video itself showed the idea.

## Tools

Everything lives in `scripts/` and `assets/` next to this file:

| File | Purpose |
|---|---|
| `scripts/get_transcript.py` | Transcript, optionally with `[mm:ss]` timestamps |
| `scripts/get_visuals.py` | `info` (title, channel, length, date, thumbnail), `scan` (contact sheets to pick frames from), `frames` (extract chosen frames) |
| `scripts/finalize_report.py` | Inlines the CSS, JS and images so the report is one self-contained `.html` |
| `assets/report-skeleton.html` | Every report component, with placeholder content. Copy it and replace the content |
| `assets/report.css`, `assets/report.js` | The report's design system and the copy-prompt button. Referenced by name, never copied |

Needs `ffmpeg`, plus `yt-dlp` (or `uv`, which lets the scripts run the newest yt-dlp through `uvx` when the installed one is out of date; YouTube breaks old versions often). If frame extraction isn't possible, still produce the report: the thumbnail comes straight from YouTube and needs neither, and a drawn diagram does most of the work anyway.

## Step 1: Get the transcript

Run the bundled script with timestamps, so you can point at moments later:

```bash
python3 scripts/get_transcript.py "<the youtube url>" --timestamps
```

It tries two independent extraction methods in order (`youtube_transcript_api`, then `yt-dlp`), because they hit YouTube through different code paths and one succeeding where the other fails is common, not exceptional. Install whichever isn't already present first:

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

Then continue with whatever text they give you exactly as if the script had returned it. Without timestamps you can't link moments, so skip deep-linking in the report; frames can still be picked from the contact sheets in Step 5.

Auto-generated captions often mishear product names and jargon. Use the correct names in the report, and say so in a short note if it was noticeable.

## Step 2: Get the video's details and thumbnail

Make a scratch folder for this video's working files (call it `$WORK`), then:

```bash
python3 scripts/get_visuals.py info "<the youtube url>" --out "$WORK"
```

This saves `$WORK/thumb.jpg` and prints JSON with the title, channel, duration and upload date. Use these for the report's source card. Don't scrape the YouTube watch page yourself, and don't rely on web search for the title; this is faster and more reliable. (A quick web search is still fine if you want to know what kind of video it is: tutorial, talk, demo, interview.)

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

## Step 5: Choose the visuals

A visual report earns its place by showing the idea, so decide what to show before writing.

**Always draw one diagram of the mechanism** as inline SVG (a flow, a loop, a before/after, a layered stack). Draw what the video *describes*, even when the video never shows it; that's often the most useful picture in the report. Use a comparison table when the video contrasts options.

**Then look for stills from the video, but only the ones that carry information.** Run:

```bash
python3 scripts/get_visuals.py scan "<the youtube url>" --out "$WORK"
```

This downloads a temporary 720p working copy, samples 24 moments and tiles them into contact sheets (`$WORK/sheet_1.jpg`, `sheet_2.jpg`; four across, row-major, with the timestamp for each position printed). Open the sheets and decide what kind of video this is:

- **Slides, diagrams, screen recordings, UI demos, charts:** pick up to about six frames that show a concept, a diagram, a result, or a key claim. These are the report's best material. Choose frames where the visual is fully formed, not mid-animation.
- **Talking heads, interviews, panels:** there is nothing to extract. Don't fill the report with faces. At most use one wide establishing shot (who is talking, in what setting), and put the effort into the drawn diagram instead.

Extract the chosen moments, sized for a report:

```bash
python3 scripts/get_visuals.py frames "<the youtube url>" --out "$WORK" --times 03:24,04:19,05:14 --width 1000
```

Each frame needs a caption that says why the moment matters, and a timestamp chip that deep-links to it (`https://youtu.be/<id>?t=<seconds>`). Write alt text that describes what the frame shows. Keep it to stills for commentary: a handful of frames, never a long run of them, and never a stand-in for watching the video.

## Step 6: Write the report

Copy `assets/report-skeleton.html` to a draft file in `$WORK`, and replace its content. Keep its structure and component classes; they are the contract that keeps reports consistent across runs:

1. **Header:** kicker, title, a one-sentence deck.
2. **Source card with the thumbnail,** linking to the video, with channel, length and date as chips. The thumbnail always goes wherever the source is referenced.
3. **The idea:** the transferable mechanism in one or two sentences, as the highlighted callout.
4. **Stats strip** (optional): two to four real numbers or short facts from the video. Skip if there are none; never invent figures.
5. **The concept:** two to four short paragraphs for someone who has not watched it, with the diagram, the frames, and any comparison table. Say what's genuinely new versus familiar, and the preconditions.
6. **What you could do with it:** one to three cards, only for lenses that genuinely fit, each with a specific, concrete label (not just "New skill") and two to four sentences grounded in this video.
7. **Ready-to-use prompt:** a single, complete, self-contained prompt in second-person imperative that can be pasted into a fresh Claude conversation or Claude Code. It must not assume the reader watched the video, so restate any context inline. It goes in the copy-button block.
8. **Footer.**

In the draft, reference files by plain relative paths (`thumb.jpg`, `frames/...`, `report.css`, `report.js`); the finalize step inlines them. Write in your own words. Don't reproduce long stretches of the transcript, and quote at most a short phrase. Keep it scannable in about two minutes: the visuals and headings should carry the story, and paragraphs stay short.

Then build the single file and save it where the person asked, otherwise in the current directory as `<slugified-title>-concept-notes.html`:

```bash
python3 scripts/finalize_report.py "$WORK/draft.html" "<slugified-title>-concept-notes.html"
```

It fails loudly if any image is missing. Open the result in a browser to check it, in both light and dark if you can; the report follows the system theme.

When you're done, delete the working folder (it contains the downloaded video) and tell the person where the report is.

## A note on scope

This skill is deliberately not a transcription tool or a video summarizer — if someone just wants the transcript itself, or a plain recap of what happened, that's a much simpler task than this skill is built for. The point of `learn-this` is the leap from "here's what the video said" to "here's what you'd actually do about it," and Steps 3-4 are where that leap happens. Don't skip straight from transcript to report without genuinely thinking through them first — a prompt built on a shallow read of the transcript will sound plausible and be useless, however good it looks.
