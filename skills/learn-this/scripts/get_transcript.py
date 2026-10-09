#!/usr/bin/env python3
"""
Fetch a YouTube video's transcript, trying multiple methods in order of
reliability. Designed to be run as: python3 get_transcript.py <url_or_id>

Exit codes / stdout contract (the calling model reads this, not just a human):
  - On success: prints the transcript as plain text, prefixed by a line
    "=== TRANSCRIPT (source: <method>) ===" so the caller knows which method
    worked, then exits 0.
  - On failure: prints "=== MANUAL_FALLBACK_NEEDED ===" followed by a short
    human-readable reason, then exits 1. This is the caller's signal to stop
    trying automated methods and ask the person to paste the transcript.

Why a fallback chain: YouTube aggressively rate-limits and IP-blocks
datacenter/cloud IPs (this is a known, common failure mode -- not a bug in
this script). A single method failing does not mean the transcript doesn't
exist; it may just mean this network path is blocked right now.
"""
import json
import re
import subprocess
import sys
import tempfile
import os


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


def try_youtube_transcript_api(video_id: str):
    """Primary method. Lightest weight, no video download. Most likely to
    work from a real residential/office network; most likely to be
    IP-blocked from cloud/datacenter sandboxes."""
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
        text = " ".join(snippet.text.strip() for snippet in fetched.snippets if snippet.text.strip())
        return text, None
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


def vtt_to_text(vtt_path: str) -> str:
    """Turn a WEBVTT caption file into deduplicated plain text. Auto-generated
    captions repeat overlapping lines across cues (rolling captions), so a
    naive join produces a lot of stutter -- this collapses consecutive
    duplicate lines."""
    with open(vtt_path, encoding="utf-8") as f:
        lines = f.readlines()
    out = []
    prev = None
    for line in lines:
        line = line.strip()
        if not line or "-->" in line or line.upper().startswith("WEBVTT") or line.isdigit():
            continue
        line = re.sub(r"<[^>]+>", "", line)  # strip inline timing/formatting tags
        if line and line != prev:
            out.append(line)
            prev = line
    return " ".join(out)


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
        text = vtt_to_text(os.path.join(tmp, vtt_files[0]))
        return text, None


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 get_transcript.py <youtube_url_or_video_id>", file=sys.stderr)
        sys.exit(2)

    try:
        video_id = extract_video_id(sys.argv[1])
    except ValueError as e:
        print("=== MANUAL_FALLBACK_NEEDED ===")
        print(str(e))
        sys.exit(1)

    text, err1 = try_youtube_transcript_api(video_id)
    if text:
        print("=== TRANSCRIPT (source: youtube_transcript_api) ===")
        print(text)
        sys.exit(0)

    text, err2 = try_yt_dlp(video_id)
    if text:
        print("=== TRANSCRIPT (source: yt-dlp) ===")
        print(text)
        sys.exit(0)

    print("=== MANUAL_FALLBACK_NEEDED ===")
    print(f"video_id={video_id}")
    print(f"youtube_transcript_api: {err1}")
    print(f"yt-dlp: {err2}")
    sys.exit(1)


if __name__ == "__main__":
    main()
