#!/usr/bin/env python3
"""Download the YouTube thumbnail for every published episode that lacks one.

Saves assets/img/episodes/<VIDEO_ID>.webp (960x540). Needs Pillow:
  pip install pillow && python3 scripts/fetch_thumbnails.py
"""
import io
import json
import pathlib
import urllib.request

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEST = ROOT / "assets/img/episodes"
DEST.mkdir(parents=True, exist_ok=True)
episodes = json.loads((ROOT / "src/data/episodes.json").read_text(encoding="utf-8"))["episodes"]

for e in episodes:
    vid = e["youtube_id"]
    target = DEST / f"{vid}.webp"
    if e.get("status") != "published" or target.exists():
        continue
    for quality in ("maxresdefault", "sddefault", "hqdefault"):
        try:
            data = urllib.request.urlopen(f"https://i.ytimg.com/vi/{vid}/{quality}.jpg", timeout=20).read()
        except Exception:
            continue
        img = Image.open(io.BytesIO(data)).convert("RGB")
        w, h = img.size
        if abs(w / h - 16 / 9) > 0.05:  # crop letterboxing on 4:3 thumbnails
            nh = int(w * 9 / 16)
            img = img.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
        img.resize((960, 540)).save(target, quality=78)
        img.resize((480, 270)).save(DEST / f"{vid}-480.webp", quality=74)
        print(f"saved {target.name} ({quality})")
        break
    else:
        print(f"could not fetch a thumbnail for {vid}")
