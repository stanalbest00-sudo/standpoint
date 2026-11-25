#!/usr/bin/env python3
"""Site checks. Run before every deploy (the GitHub workflow does this).

  python3 scripts/check.py

Fails (exit 1) if content data is invalid, if re-running an import would change
or overwrite anything, or if the built pages contain a broken link, a replay
button pointing at the wrong video, an unpublished episode, or an unverified
social link.
"""
import copy
import datetime as dt
import html.parser
import importlib.util
import json
import pathlib
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
errors = []


def fail(msg):
    errors.append(msg)


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


site = load("src/data/site.json")
store = load("src/data/episodes.json")
broadcasts = load("src/data/broadcasts.json")["upcoming"]
eps = store["episodes"]

# ── 1. Data ──────────────────────────────────────────────
ids = [e.get("youtube_id") for e in eps]
for vid in {i for i in ids if ids.count(i) > 1}:
    fail(f"duplicate episode record for video {vid}")
today = dt.date.today()
published = {}
for e in eps:
    vid = e.get("youtube_id", "")
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", vid or ""):
        fail(f"invalid YouTube ID {vid!r}")
    if e.get("status") not in ("published", "review"):
        fail(f"{vid}: status must be 'published' or 'review'")
    if e.get("status") == "published":
        published[vid] = e
        for field in ("title", "date"):
            if not e.get(field):
                fail(f"{vid}: published episode is missing {field}")
        try:
            if dt.date.fromisoformat(e["date"]) > today:
                fail(f"{vid}: published date {e['date']} is in the future")
        except (KeyError, ValueError):
            fail(f"{vid}: date must be YYYY-MM-DD")
        if not all((ROOT / f"assets/img/episodes/{vid}{sfx}.webp").exists() for sfx in ("", "-480")):
            fail(f"{vid}: missing thumbnail assets/img/episodes/{vid}.webp (run scripts/fetch_thumbnails.py)")
review = {e["youtube_id"] for e in eps if e.get("status") == "review"}

# ── 2. Imports are idempotent and never overwrite edits ──
spec = importlib.util.spec_from_file_location("importer", ROOT / "scripts/import_content.py")
importer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(importer)
for batch_file in sorted((ROOT / "content/imports").glob("*.json")):
    batch = json.loads(batch_file.read_text(encoding="utf-8"))
    trial = copy.deepcopy(store)
    added, filled, _, _ = importer.merge(trial, batch)
    if added or filled:
        fail(f"{batch_file.name}: re-running would add {len(added)} records and fill {len(filled)} fields; run the import and commit")
    if json.dumps(trial, sort_keys=True) != json.dumps(store, sort_keys=True):
        fail(f"{batch_file.name}: re-running the import would change episodes.json")
    edited = copy.deepcopy(store)
    if edited["episodes"]:
        target = edited["episodes"][0]
        target["title"] = "EDITOR CHANGED THIS"
        target["summary"] = "Editor summary"
        importer.merge(edited, batch)
        if target["title"] != "EDITOR CHANGED THIS" or target["summary"] != "Editor summary":
            fail(f"{batch_file.name}: import overwrote an editor's change")

# ── 3. Build and inspect the output ──────────────────────
out = pathlib.Path(tempfile.mkdtemp()) / "site"
subprocess.run([sys.executable, str(ROOT / "scripts/build.py"), str(out)], check=True, stdout=subprocess.DEVNULL)


class Links(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs, self.ids = [], set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        for k in ("href", "src"):
            if a.get(k):
                self.refs.append(a[k])


pages = {p.name: p.read_text(encoding="utf-8") for p in out.glob("*.html")}
parsed = {}
for name, text in pages.items():
    p = Links()
    p.feed(text)
    parsed[name] = p

verified_social = {s["url"] for s in site["social"].values() if s.get("verified")}
for name, text in pages.items():
    if name == "404.html":
        continue
    for ref in parsed[name].refs:
        if ref.startswith(("http://", "https://", "mailto:", "tel:", "data:")):
            continue
        path, _, frag = ref.partition("#")
        path = path.split("?")[0] or name
        if not (out / path).exists():
            fail(f"{name}: broken link {ref}")
        elif frag and path.endswith(".html") and frag not in parsed.get(path, Links()).ids:
            fail(f"{name}: link {ref} points to a missing anchor")
    # Replay buttons and players inside an episode block must use that episode's ID.
    for m in re.finditer(r'data-episode="([\w-]+)"(.*?)(?=data-episode="|</main>)', text, re.S):
        vid, block = m.group(1), m.group(2)
        if vid not in published:
            fail(f"{name}: episode block for unpublished video {vid}")
        for other in re.findall(r'youtube\.com/watch\?v=([\w-]{11})', block):
            if other != vid and other not in review | set(published):
                fail(f"{name}: unknown video {other} inside episode {vid}")
        for other in re.findall(r'data-(?:yt|watch)="([\w-]+)"', block):
            if other != vid:
                fail(f"{name}: player/button for {other} inside episode {vid}")
    # Review records may only appear as a 'continues from' link on YouTube.
    for vid in review:
        for m in re.finditer(re.escape(vid), text):
            ctx = text[max(0, m.start() - 200):m.start()]
            if 'class="episode-related"' not in ctx:
                fail(f"{name}: unpublished video {vid} appears on the page")
    for url in re.findall(r'https://(?:www\.)?(?:facebook|tiktok|instagram)\.com[^"\s<]*', text):
        if html.unescape(url) not in verified_social:
            fail(f"{name}: unverified social link {url}")
    for url in re.findall(r'https://wa\.me/[^"\s<]*', text):
        if url != site["whatsapp"]["link"]:
            fail(f"{name}: WhatsApp link {url} differs from site.json")
    if "Watch live" in text and not broadcasts:
        fail(f"{name}: says 'Watch live' but no broadcast is confirmed")

for vid in published:
    if f'data-yt="{vid}"' not in pages.get("watch.html", ""):
        fail(f"watch.html: published episode {vid} has no player")

if errors:
    print("FAILED")
    for e in errors:
        print(" -", e)
    sys.exit(1)
print(f"OK: {len(published)} published, {len(review)} in review, {len(pages)} pages checked, imports idempotent")
