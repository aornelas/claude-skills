#!/usr/bin/env python3
"""
Fetch a YouTube video's transcript, trying multiple methods in order of
reliability. Designed to be run as:

    python3 get_transcript.py <url_or_id> [--timestamps]

Exit codes / stdout contract (the calling model reads this, not just a human):
  - On success: prints the transcript as plain text, prefixed by a line
    "=== TRANSCRIPT (source: <method>) ===" so the caller knows which method
    worked, then exits 0.
  - With --timestamps, the text is grouped into ~20 second chunks, each line
    prefixed with "[mm:ss]" (or "[h:mm:ss]"). Use this when you need to point
    at moments in the video, for example to pick frames to show in a report.
  - On failure: prints "=== MANUAL_FALLBACK_NEEDED ===" followed by a short
    human-readable reason, then exits 1. This is the caller's signal to stop
    trying automated methods and ask the person to paste the transcript.

Why a fallback chain: YouTube aggressively rate-limits and IP-blocks
datacenter/cloud IPs (this is a known, common failure mode -- not a bug in
this script). A single method failing does not mean the transcript doesn't
exist; it may just mean this network path is blocked right now.
"""
import re
import subprocess
import sys
import tempfile
import os

CHUNK_SECONDS = 20


def extract_video_id(url_or_id: str) -> str:
    """Pull an 11-char YouTube video ID out of any common URL shape, or
    pass through if the input already looks like a bare ID."""
    url_or_id = url_or_id.strip()
    patterns = [
        r"(?:v=|/videos/|embed/|youtu\.be/|/shorts/|/live/)([0-9A-Za-z_-]{11})",
    ]
    for p in patterns:
        m = re.search(p, url_or_id)
        if m:
            return m.group(1)
    if re.fullmatch(r"[0-9A-Za-z_-]{11}", url_or_id):
        return url_or_id
    raise ValueError(f"Could not find an 11-character video ID in: {url_or_id}")


def fmt_time(seconds: float) -> str:
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def render(items, timestamps: bool) -> str:
    """items is a list of (start_seconds, text). Plain mode joins everything;
    timestamp mode groups into CHUNK_SECONDS chunks, one line each."""
    if not timestamps:
        return " ".join(t for _, t in items)
    lines = []
    chunk_start = None
    chunk_text = []
    for start, text in items:
        if chunk_start is None:
            chunk_start = start
        elif start - chunk_start >= CHUNK_SECONDS:
            lines.append(f"[{fmt_time(chunk_start)}] {' '.join(chunk_text)}")
            chunk_start = start
            chunk_text = []
        chunk_text.append(text)
    if chunk_text:
        lines.append(f"[{fmt_time(chunk_start)}] {' '.join(chunk_text)}")
    return "\n".join(lines)


def try_youtube_transcript_api(video_id: str):
    """Primary method. Lightest weight, no video download. Most likely to
    work from a real residential/office network; most likely to be
    IP-blocked from cloud/datacenter sandboxes. Returns (items, error)."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api._errors import (
            TranscriptsDisabled,
            NoTranscriptFound,
            VideoUnavailable,
            AgeRestricted,
            IpBlocked,
            RequestBlocked,
            CouldNotRetrieveTranscript,
        )
    except ImportError:
        return None, "youtube_transcript_api is not installed"

    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        # Prefer a manually created transcript over an auto-generated one,
        # and prefer English, but fall back to whatever exists.
        transcript = None
        try:
            transcript = transcript_list.find_manually_created_transcript(["en"])
        except NoTranscriptFound:
            try:
                transcript = transcript_list.find_generated_transcript(["en"])
            except NoTranscriptFound:
                # take the first available transcript in any language
                transcript = next(iter(transcript_list))
                if transcript.language_code != "en" and transcript.is_translatable:
                    try:
                        transcript = transcript.translate("en")
                    except Exception:
                        pass  # ship it in the original language rather than fail
        fetched = transcript.fetch()
        items = [(s.start, s.text.strip()) for s in fetched.snippets if s.text.strip()]
        return items, None
    except (IpBlocked, RequestBlocked) as e:
        return None, f"IP_BLOCKED: {e}"
    except (TranscriptsDisabled, NoTranscriptFound) as e:
        return None, f"NO_CAPTIONS: {e}"
    except (VideoUnavailable, AgeRestricted) as e:
        return None, f"VIDEO_UNAVAILABLE: {e}"
    except CouldNotRetrieveTranscript as e:
        return None, f"COULD_NOT_RETRIEVE: {e}"
    except Exception as e:
        return None, f"UNKNOWN_ERROR: {type(e).__name__}: {e}"


def parse_vtt_time(stamp: str) -> float:
    """'00:01:02.500' or '01:02.500' -> seconds."""
    seconds = 0.0
    for part in stamp.strip().split(":"):
        seconds = seconds * 60 + float(part)
    return seconds


def vtt_to_items(vtt_path: str):
    """Turn a WEBVTT caption file into deduplicated (start, text) items.
    Auto-generated captions repeat overlapping lines across cues (rolling
    captions), so a naive join produces a lot of stutter -- this collapses
    consecutive duplicate lines."""
    with open(vtt_path, encoding="utf-8") as f:
        lines = f.readlines()
    items = []
    prev = None
    cue_start = 0.0
    for line in lines:
        line = line.strip()
        if "-->" in line:
            try:
                cue_start = parse_vtt_time(line.split("-->")[0])
            except ValueError:
                pass
            continue
        if not line or line.upper().startswith("WEBVTT") or line.isdigit():
            continue
        line = re.sub(r"<[^>]+>", "", line)  # strip inline timing/formatting tags
        if line and line != prev:
            items.append((cue_start, line))
            prev = line
    return items


def try_yt_dlp(video_id: str):
    """Secondary method. Downloads only the caption track (not the video),
    via a different code path / request pattern than youtube_transcript_api,
    so it sometimes succeeds when the first method is blocked, and vice versa."""
    if subprocess.run(["which", "yt-dlp"], capture_output=True).returncode != 0:
        return None, "yt-dlp is not installed"

    with tempfile.TemporaryDirectory() as tmp:
        out_tmpl = os.path.join(tmp, "%(id)s.%(ext)s")
        cmd = [
            "yt-dlp", "--skip-download",
            "--write-auto-sub", "--write-sub", "--sub-lang", "en",
            "--sub-format", "vtt", "-o", out_tmpl,
            f"https://www.youtube.com/watch?v={video_id}",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        vtt_files = [f for f in os.listdir(tmp) if f.endswith(".vtt")]
        if not vtt_files:
            err = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "no captions found"
            return None, err
        return vtt_to_items(os.path.join(tmp, vtt_files[0])), None


def main():
    timestamps = "--timestamps" in sys.argv[1:]
    args = [a for a in sys.argv[1:] if a != "--timestamps"]
    if len(args) != 1:
        print("Usage: python3 get_transcript.py <youtube_url_or_video_id> [--timestamps]", file=sys.stderr)
        sys.exit(2)

    try:
        video_id = extract_video_id(args[0])
    except ValueError as e:
        print("=== MANUAL_FALLBACK_NEEDED ===")
        print(str(e))
        sys.exit(1)

    items, err1 = try_youtube_transcript_api(video_id)
    if items:
        print("=== TRANSCRIPT (source: youtube_transcript_api) ===")
        print(render(items, timestamps))
        sys.exit(0)

    items, err2 = try_yt_dlp(video_id)
    if items:
        print("=== TRANSCRIPT (source: yt-dlp) ===")
        print(render(items, timestamps))
        sys.exit(0)

    print("=== MANUAL_FALLBACK_NEEDED ===")
    print(f"video_id={video_id}")
    print(f"youtube_transcript_api: {err1}")
    print(f"yt-dlp: {err2}")
    sys.exit(1)


if __name__ == "__main__":
    main()
