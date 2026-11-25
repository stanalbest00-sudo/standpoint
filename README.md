# Standpoint Seychelles

Website for **Standpoint Seychelles** — *Where Truth Ignites Transformation.*
Live at https://stanalbest00-sudo.github.io/standpoint/

A small static site: page text in `src/pages`, content in `src/data`, and a Python
build script (standard library only) that turns them into the published pages.
Every push to `main` is checked, built and deployed by `.github/workflows/pages.yml`.

## Where things live

| Path | What it holds |
|---|---|
| `src/pages/*.html` | Page text: Home, Watch, Our Work, Learn, Visuals, Contact, 404 |
| `src/data/site.json` | **Central links**: YouTube, Facebook, TikTok, WhatsApp. Buttons appear only when `"verified": true` |
| `src/data/episodes.json` | Episode archive, one record per YouTube video ID |
| `src/data/broadcasts.json` | Confirmed upcoming live broadcasts (empty = the site says "Watch a replay") |
| `content/imports/` | Content handovers, imported with `scripts/import_content.py` |
| `content/EDITORIAL-REVIEW.md` | Items waiting for a decision before they go public |
| `assets/` | Styles, scripts, logo, intro video and frames, episode thumbnails |
| `scripts/` | `build.py`, `check.py`, `import_content.py`, `fetch_thumbnails.py` |

`about.html` and `get-involved.html` are kept as redirects to `our-work.html` and `contact.html`.

## Everyday tasks

**Preview locally**

```sh
python3 scripts/build.py && python3 -m http.server 8000 -d _site
# open http://localhost:8000
```

**Publish an episode.** Add a record to `src/data/episodes.json` (or flip a `review`
record to `"status": "published"`), then fetch its thumbnail and run the checks:

```json
{
  "youtube_id": "2zFrmKl5qFM",
  "episode": 17,
  "title": "50 Years Later: Are Seychellois Politically Mature?",
  "title_lang": "en",
  "title_secondary": {"text": "50an apre: Eski Seselwa i politikman matir?", "lang": "crs", "kind": "campaign title"},
  "date": "2026-08-03",
  "summary": "One or two sentences, approved for publication.",
  "status": "published"
}
```

```sh
pip install pillow && python3 scripts/fetch_thumbnails.py
python3 scripts/check.py
```

Keep published titles in their original language (`"title_lang": "crs"` for Kreol).
Add an approved translation as `title_secondary`. Link Part 2 to Part 1 with
`"related": [{"youtube_id": "...", "relation": "part-1"}]`.

**Announce a live broadcast.** Add it to `src/data/broadcasts.json` with the approved
start and end time in Seychelles time and the live link. The site shows "Watch live"
until the end time, then falls back to "Watch a replay".

**Import a content batch.** Put the batch JSON in `content/imports/` and run
`python3 scripts/import_content.py content/imports/<file>.json`. Records are matched on
YouTube video ID, existing values are never overwritten, and re-running a batch changes
nothing. Add `"locked_fields": ["summary"]` to a record to protect a field, or set
`"editorial_updated": "YYYY-MM-DD"` to protect the whole record from older batches.

**Change a social link.** Edit `src/data/site.json` only; the homepage, Watch page,
Contact page and footer all read from it. Record how you verified the link in `evidence`.

## Checks

`python3 scripts/check.py` runs on every pull request and before every deploy. It fails if:
an episode record is duplicated or incomplete, a thumbnail is missing, re-running an import
would change data or overwrite an edit, a replay button or player points at a different video
than its episode, an unpublished episode appears on a page, an internal link or anchor is broken,
an unverified social link appears, the WhatsApp link differs from `site.json`, or the site says
"Watch live" without a confirmed broadcast.

## Design

Palette: black, deep maroon, fiery orange and metallic gold, with white for readable
content areas (tokens at the top of `assets/css/style.css`). Fonts: Cinzel and Montserrat.
Motion is limited to opacity, transform and blur, and everything falls back to still images
for visitors who turn on "reduce motion".

To replace the home page intro video, regenerate the frames and update `FRAMES` in
`assets/js/main.js`:

```sh
ffmpeg -i new-video.mp4 -vf "fps=12,scale=1280:-2" -c:v libwebp -quality 62 assets/frames/lg/f%03d.webp
ffmpeg -i new-video.mp4 -vf "fps=12,scale=720:-2"  -c:v libwebp -quality 60 assets/frames/sm/f%03d.webp
```

## Going live and custom domain

GitHub Pages is set to deploy from GitHub Actions. For a custom domain, add it in
**Settings → Pages → Custom domain**, add the DNS record at your registrar, and update
`site_url` in `src/data/site.json`.
