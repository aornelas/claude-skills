#!/usr/bin/env python3
"""
Pull the visual material for a learn-this report out of a YouTube video:
the thumbnail, basic metadata, and still frames at chosen moments.

Usage:
    python3 get_visuals.py info   <url> --out DIR
    python3 get_visuals.py scan   <url> --out DIR [--count 24]
    python3 get_visuals.py frames <url> --out DIR --times 02:15,10:40 [--width 1280]

Subcommands (all write into DIR; the video is downloaded once and cached there):

  info    Writes DIR/thumb.jpg and prints one JSON object with id, title,
          channel, duration_seconds, duration_text, upload_date and url.

  scan    Samples COUNT evenly spaced frames and tiles them into contact
          sheets (DIR/sheet_1.jpg, sheet_2.jpg, ...), 12 frames per sheet in
          a 4x3 grid, row-major order, each frame stamped with its timestamp
          where the local ffmpeg supports text. Prints which timestamps are
          on which sheet. Look at the sheets to decide which moments are
          worth showing (slides, diagrams, UI, demos -- not talking heads).

  frames  Extracts a full-size JPEG at each requested time into
          DIR/frame_<mmss>.jpg and prints the path with its timestamp.
          Times are mm:ss, h:mm:ss, or plain seconds, comma separated.

Requires ffmpeg on PATH, plus yt-dlp (or uv, which lets it run the newest yt-dlp via
uvx when the installed one is out of date). Nothing is uploaded anywhere; the video
file is a temporary working copy you can delete when the report is done.
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys
import urllib.request

FONT_CANDIDATES = [
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
]


def die(msg: str):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def require(tool: str):
    if subprocess.run(["which", tool], capture_output=True).returncode != 0:
        die(f"{tool} is not installed (try: brew install {tool}  or  pip install {tool})")


def video_id(url: str) -> str:
    m = re.search(r"(?:v=|/videos/|embed/|youtu\.be/|/shorts/|/live/)([0-9A-Za-z_-]{11})", url)
    if m:
        return m.group(1)
    if re.fullmatch(r"[0-9A-Za-z_-]{11}", url.strip()):
        return url.strip()
    die(f"could not find a video ID in: {url}")


def parse_time(text: str) -> float:
    seconds = 0.0
    for part in text.strip().split(":"):
        seconds = seconds * 60 + float(part)
    return seconds


def fmt_time(seconds: float) -> str:
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def stamp_name(seconds: float) -> str:
    seconds = int(seconds)
    return f"{seconds // 60:02d}{seconds % 60:02d}" if seconds < 3600 else f"{seconds // 3600}h{(seconds % 3600) // 60:02d}{seconds % 60:02d}"


def run_ytdlp(args, timeout=None):
    """Run yt-dlp, retrying through `uvx yt-dlp` (always the newest release)
    when the installed one fails. YouTube changes often enough that an old
    yt-dlp failing with errors like "page needs to be reloaded" is common,
    and a stale install on an old Python can't upgrade itself."""
    extra = []
    for rt in ("node", "deno", "bun"):
        if subprocess.run(["which", rt], capture_output=True).returncode == 0:
            extra = ["--js-runtimes", rt]
            break
    launchers = []
    if subprocess.run(["which", "yt-dlp"], capture_output=True).returncode == 0:
        launchers.append(["yt-dlp"])
    if subprocess.run(["which", "uvx"], capture_output=True).returncode == 0:
        launchers.append(["uvx", "yt-dlp"])
    if not launchers:
        die("yt-dlp is not installed (try: pip install yt-dlp, or install uv and use uvx)")
    last = None
    for launcher in launchers:
        last = subprocess.run(launcher + extra + ["--no-warnings"] + args,
                              capture_output=True, text=True, timeout=timeout)
        if last.returncode == 0:
            return last
    return last


def fetch(url: str, dest: str) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read()
        if len(data) < 2000:  # YouTube serves a tiny placeholder for missing sizes
            return False
        with open(dest, "wb") as f:
            f.write(data)
        return True
    except Exception:
        return False


def cmd_info(args):
    vid = video_id(args.url)
    os.makedirs(args.out, exist_ok=True)
    thumb = os.path.join(args.out, "thumb.jpg")
    for name in ("maxresdefault", "sddefault", "hqdefault"):
        if fetch(f"https://i.ytimg.com/vi/{vid}/{name}.jpg", thumb):
            break
    else:
        print("WARNING: could not download a thumbnail", file=sys.stderr)

    info = {"id": vid, "url": f"https://www.youtube.com/watch?v={vid}", "thumbnail": thumb}
    meta = None
    r = run_ytdlp(["--skip-download", "--dump-single-json", info["url"]], timeout=120)
    if r is not None and r.returncode == 0:
        try:
            meta = json.loads(r.stdout)
        except ValueError:
            meta = None
    if meta:
        info["title"] = meta.get("title")
        info["channel"] = meta.get("channel") or meta.get("uploader")
        info["duration_seconds"] = meta.get("duration")
        info["duration_text"] = fmt_time(meta["duration"]) if meta.get("duration") else None
        ud = meta.get("upload_date")
        info["upload_date"] = f"{ud[:4]}-{ud[4:6]}-{ud[6:]}" if ud and len(ud) == 8 else None
    else:
        # oEmbed gives title and channel even when yt-dlp is blocked
        try:
            oembed = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json"
            with urllib.request.urlopen(oembed, timeout=15) as r:
                o = json.loads(r.read())
            info["title"] = o.get("title")
            info["channel"] = o.get("author_name")
        except Exception:
            pass
    print(json.dumps(info, indent=2, ensure_ascii=False))


def ensure_video(url: str, out: str) -> str:
    """Download a 720p-or-smaller, video-only copy once; reuse it afterwards."""
    os.makedirs(out, exist_ok=True)
    existing = [p for p in glob.glob(os.path.join(out, "video.*")) if not p.endswith((".part", ".ytdl"))]
    if existing:
        return existing[0]
    r = run_ytdlp(["-f", "bv*[height<=720]/b[height<=720]/bv*/b",
                   "-o", os.path.join(out, "video.%(ext)s"), url])
    found = [p for p in glob.glob(os.path.join(out, "video.*")) if not p.endswith((".part", ".ytdl"))]
    if r.returncode != 0 or not found:
        tail = r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "unknown error"
        die(f"could not download the video: {tail}")
    return found[0]


def duration_of(path: str) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", path],
        capture_output=True, text=True,
    )
    try:
        return float(r.stdout.strip())
    except ValueError:
        die("could not read the video duration")


def extract(video: str, t: float, dest: str, width: int, label: str = None) -> bool:
    """Grab one frame at t seconds. If label is given, try to stamp it on."""
    vf = f"scale='min({width},iw)':-2"
    attempts = []
    if label:
        font = next((f for f in FONT_CANDIDATES if os.path.exists(f)), None)
        if font:
            text = label.replace(":", "\\:")
            attempts.append(
                f"{vf},drawtext=fontfile='{font}':text='{text}':fontcolor=white:fontsize=22:"
                "box=1:boxcolor=black@0.6:boxborderw=6:x=8:y=8"
            )
    attempts.append(vf)
    for filt in attempts:
        r = subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", video,
             "-frames:v", "1", "-vf", filt, "-q:v", "3", dest],
            capture_output=True, text=True,
        )
        if r.returncode == 0 and os.path.exists(dest):
            return True
    return False


def cmd_scan(args):
    require("ffmpeg")
    video = ensure_video(args.url, args.out)
    dur = duration_of(video)
    count = max(2, args.count)
    lo, hi = dur * 0.02, dur * 0.98
    times = [lo + (hi - lo) * i / (count - 1) for i in range(count)]
    tmp = os.path.join(args.out, "cand")
    os.makedirs(tmp, exist_ok=True)
    for old in glob.glob(os.path.join(tmp, "*.jpg")):
        os.remove(old)
    kept = []
    for i, t in enumerate(times, 1):
        dest = os.path.join(tmp, f"c_{i:03d}.jpg")
        if extract(video, t, dest, 480, label=fmt_time(t)):
            kept.append((i, t, dest))
    per_sheet = 12
    for s in range(0, len(kept), per_sheet):
        group = kept[s:s + per_sheet]
        n = s // per_sheet + 1
        sheet = os.path.join(args.out, f"sheet_{n}.jpg")
        # tile needs a numbered sequence, so link this group's frames as 1..k
        seq = os.path.join(tmp, f"seq{n}")
        os.makedirs(seq, exist_ok=True)
        for j, (_, _, path) in enumerate(group, 1):
            link = os.path.join(seq, f"s_{j:02d}.jpg")
            if os.path.lexists(link):
                os.remove(link)
            os.symlink(os.path.abspath(path), link)
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(seq, "s_%02d.jpg"),
             "-vf", "tile=4x3:padding=4:margin=4:color=black", "-frames:v", "1", "-q:v", "3", sheet],
            capture_output=True, text=True,
        )
        print(f"{sheet}  (row-major, 4 across): " + "  ".join(fmt_time(t) for _, t, _ in group))
    print(f"video_duration={fmt_time(dur)}  cached_video={video}")


def cmd_frames(args):
    require("ffmpeg")
    video = ensure_video(args.url, args.out)
    dur = duration_of(video)
    for raw in args.times.split(","):
        raw = raw.strip()
        if not raw:
            continue
        t = parse_time(raw)
        if t < 0 or t > dur:
            print(f"SKIPPED {raw}: outside the video (length {fmt_time(dur)})")
            continue
        dest = os.path.join(args.out, f"frame_{stamp_name(t)}.jpg")
        if extract(video, t, dest, args.width):
            print(f"{dest}  {fmt_time(t)}")
        else:
            print(f"FAILED {raw}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("info", "scan", "frames"):
        sp = sub.add_parser(name)
        sp.add_argument("url")
        sp.add_argument("--out", required=True)
        if name == "scan":
            sp.add_argument("--count", type=int, default=24)
        if name == "frames":
            sp.add_argument("--times", required=True)
            sp.add_argument("--width", type=int, default=1280)
    args = p.parse_args()
    {"info": cmd_info, "scan": cmd_scan, "frames": cmd_frames}[args.cmd](args)


if __name__ == "__main__":
    main()
