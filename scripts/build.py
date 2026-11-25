#!/usr/bin/env python3
"""Build the Standpoint Seychelles site into _site/.

Page bodies live in src/pages/*.html. Content comes from src/data/*.json.
Tokens in page bodies:
  {{i:name}}            inline icon
  {{featured:VIDEO_ID}} large playable episode (home)
  {{recent:N}}          N newest published episodes as cards
  {{archive}}           every published episode, newest first (Watch page)
  {{broadcast-status}}  next confirmed live broadcast, or "Watch a replay"
  {{social-buttons}}    verified social profile buttons (or plain-text fallback)
  {{whatsapp-button}}   "Send us a question" button (opens a WhatsApp chat)
  {{whatsapp-band}}     full WhatsApp question section
  {{wa:number}} {{wa:link}} {{wa:invite}} {{wa:call}}  WhatsApp details from site.json
Usage: python3 scripts/build.py [output_dir]
"""
import datetime as dt
import html
import json
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "_site"
MAHE = dt.timezone(dt.timedelta(hours=4))  # Indian/Mahe, no daylight saving

site = json.loads((SRC / "data/site.json").read_text(encoding="utf-8"))
episodes = json.loads((SRC / "data/episodes.json").read_text(encoding="utf-8"))["episodes"]
broadcasts = json.loads((SRC / "data/broadcasts.json").read_text(encoding="utf-8"))["upcoming"]
SITE = site["site_url"]
WA = site["whatsapp"]
published = [e for e in episodes if e.get("status") == "published"]
published.sort(key=lambda e: (e["date"], e.get("episode") or 0), reverse=True)
by_id = {e["youtube_id"]: e for e in episodes}

NAV = [("index.html", "Home"), ("watch.html", "Watch"), ("our-work.html", "Our Work"),
       ("learn.html", "Learn"), ("visuals.html", "Visuals"), ("contact.html", "Contact")]
REDIRECTS = {"about.html": "our-work.html", "get-involved.html": "contact.html"}

P = {
    "scroll": ['M8 21h12a2 2 0 0 0 2-2v-2H10v2a2 2 0 1 1-4 0V5a2 2 0 1 0-4 0v3h4', 'M19 17V5a2 2 0 0 0-2-2H4'],
    "vote": ['m9 12 2 2 4-4', 'M5 7c0-1.1.9-2 2-2h10a2 2 0 0 1 2 2v12H5V7Z', 'M22 19H2'],
    "scale": ['m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z', 'm2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z', 'M7 21h10', 'M12 3v18', 'M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2'],
    "landmark": ['M3 22h18', 'M6 18v-7', 'M10 18v-7', 'M14 18v-7', 'M18 18v-7', 'M12 2l8 5H4z'],
    "flag": ['M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z', 'M4 22v-7'],
    "megaphone": ['m3 11 18-5v12L3 14v-3z', 'M11.6 16.8a3 3 0 1 1-5.8-1.6'],
    "home": ['M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z', 'M9 22V12h6v10'],
    "cap": ['M22 10 12 5 2 10l10 5 10-5Z', 'M6 12v5c3 3 9 3 12 0v-5'],
    "book": ['M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z', 'M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z'],
    "users": ['M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2', 'M9 3a4 4 0 1 0 0 8 4 4 0 0 0 0-8z', 'M22 21v-2a4 4 0 0 0-3-3.87', 'M16 3.13a4 4 0 0 1 0 7.75'],
    "eye": ['M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z', 'M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6z'],
    "flame": ['M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z'],
    "mountain": ['m8 3 4 8 5-5 5 15H2L8 3z'],
    "play": ['M6 3l14 9-14 9V3z'],
    "search": ['M11 3a8 8 0 1 0 0 16 8 8 0 0 0 0-16z', 'm21 21-4.3-4.3'],
    "mic": ['M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z', 'M19 10v2a7 7 0 0 1-14 0v-2', 'M12 19v3'],
    "calendar": ['M8 2v4', 'M16 2v4', 'M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z', 'M3 10h18'],
    "external": ['M15 3h6v6', 'M10 14 21 3', 'M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6'],
    "news": ['M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2Zm0 0a2 2 0 0 1-2-2v-9c0-1.1.9-2 2-2h2', 'M18 14h-8', 'M15 18h-5', 'M10 6h8v4h-8V6Z'],
    "youtube": ['M2.5 17a24.12 24.12 0 0 1 0-10 2 2 0 0 1 1.4-1.4 49.56 49.56 0 0 1 16.2 0A2 2 0 0 1 21.5 7a24.12 24.12 0 0 1 0 10 2 2 0 0 1-1.4 1.4 49.55 49.55 0 0 1-16.2 0A2 2 0 0 1 2.5 17', 'm10 15 5-3-5-3z'],
    "facebook": ['M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z'],
    "tiktok": ['M9 12a4 4 0 1 0 4 4V3c.5 2.5 2.5 4.5 5 5'],
    "whatsapp": ['M7.9 20A9 9 0 1 0 4 16.1L2 22Z', 'M9 10.5c.5 2 2 3.5 4 4l1.2-1.2 2 .9-.6 1.6c-3.8.2-7.3-3.3-7.1-7.1l1.6-.6.9 2z'],
}


def icon(name):
    return ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" '
            'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            + "".join(f'<path d="{d}"/>' for d in P[name]) + "</svg>")


esc = html.escape


def nice_date(iso):
    d = dt.date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%B %Y')}"


def lang_attr(e):
    return ' lang="crs"' if e.get("title_lang") == "crs" else ""


def player(e, eager=False):
    vid = e["youtube_id"]
    return (f'<div class="player" data-yt="{vid}">'
            f'<img src="assets/img/episodes/{vid}.webp" srcset="assets/img/episodes/{vid}-480.webp 480w, assets/img/episodes/{vid}.webp 960w" '
            f'sizes="(max-width: 760px) calc(100vw - 56px), (max-width: 860px) 100vw, 640px" width="960" height="540" alt=""'
            f'{" fetchpriority=\"high\"" if eager == "high" else ("" if eager else " loading=\"lazy\"")} decoding="async">'
            f'<button type="button" class="player-btn" aria-label="Play “{esc(e["title"])}” here">'
            f'<span class="player-icon">{icon("play")}</span></button></div>')


def yt_url(vid):
    return f"https://www.youtube.com/watch?v={vid}"


def meta(e):
    bits = []
    if e.get("episode"):
        bits.append(f"Episode {e['episode']}")
    bits.append(f'<time datetime="{e["date"]}">{nice_date(e["date"])}</time>')
    return " · ".join(bits)


def secondary(e):
    s = e.get("title_secondary")
    if not s:
        return ""
    lang = ' lang="crs"' if s.get("lang") == "crs" else ""
    return f'<p class="episode-alt"><span>{esc(s.get("kind", "Also titled").capitalize())}:</span> <span{lang}>{esc(s["text"])}</span></p>'


def related(e):
    out = []
    for r in e.get("related", []):
        parent = by_id.get(r["youtube_id"])
        if not parent:
            continue
        label = "Continues from" if r["relation"] == "part-1" else "Related"
        if parent.get("status") == "published":
            href, ext = f"watch.html#v-{parent['youtube_id']}", ""
        else:
            href, ext = yt_url(parent["youtube_id"]), ' target="_blank" rel="noopener"'
        out.append(f'<p class="episode-related">{label} <a href="{href}"{ext}{lang_attr(parent)}>{esc(parent["title"])}</a></p>')
    return "".join(out)


def watch_button(e, cls="btn btn-ghost btn-small"):
    return (f'<a class="{cls}" href="{yt_url(e["youtube_id"])}" target="_blank" rel="noopener" '
            f'data-watch="{e["youtube_id"]}">{icon("youtube")} Watch on YouTube</a>')


def episode_article(e, eager=False):
    summary = f'<p class="episode-summary">{esc(e["summary"])}</p>' if e.get("summary") else ""
    return (f'<article class="episode reveal" id="v-{e["youtube_id"]}" data-episode="{e["youtube_id"]}">'
            f'{player(e, eager)}<div class="episode-body"><p class="episode-meta">{meta(e)}</p>'
            f'<h3{lang_attr(e)}>{esc(e["title"])}</h3>{secondary(e)}{summary}{related(e)}'
            f'<div class="episode-actions">{watch_button(e)}</div></div></article>')


def featured(vid):
    e = by_id[vid]
    assert e.get("status") == "published", f"featured episode {vid} is not published"
    summary = f'<p class="featured-summary">{esc(e["summary"])}</p>' if e.get("summary") else ""
    return (f'<div class="featured" data-episode="{vid}">{player(e)}<div class="featured-body">'
            f'<p class="episode-meta">{meta(e)}</p><h3{lang_attr(e)}>{esc(e["title"])}</h3>{secondary(e)}{summary}'
            f'<div class="episode-actions">{watch_button(e, "btn btn-primary")}'
            f'<a class="btn btn-ghost" href="watch.html">More episodes</a></div></div></div>')


def recent(n):
    cards = []
    for e in published[:int(n)]:
        cards.append(f'<a class="card episode-card reveal" href="watch.html#v-{e["youtube_id"]}">'
                     f'<img src="assets/img/episodes/{e["youtube_id"]}-480.webp" srcset="assets/img/episodes/{e["youtube_id"]}-480.webp 480w, assets/img/episodes/{e["youtube_id"]}.webp 960w" sizes="(max-width: 760px) 100vw, 360px" width="960" height="540" alt="" loading="lazy" decoding="async">'
                     f'<span class="episode-meta">{meta(e)}</span><span class="episode-card-title"{lang_attr(e)}>{esc(e["title"])}</span></a>')
    return '<div class="grid grid-3">' + "".join(cards) + "</div>"


def archive():
    return '<div class="archive">' + "".join(episode_article(e, eager="high" if i == 0 else i < 2) for i, e in enumerate(published)) + "</div>"


def broadcast_status():
    now = dt.datetime.now(MAHE)
    items = []
    for b in broadcasts:
        start = dt.datetime.fromisoformat(b["start"]).replace(tzinfo=MAHE)
        end = dt.datetime.fromisoformat(b.get("end") or b["start"]).replace(tzinfo=MAHE)
        if end <= now or not b.get("live_url"):
            continue
        when = f'{start.day} {start.strftime("%B %Y")}, {start.strftime("%H:%M")} {site["timezone_label"]}'
        items.append(f'<div class="broadcast" data-ends="{end.isoformat()}"><p class="status-pill live">Next live broadcast</p>'
                     f'<h3>{esc(b["title"])}</h3><p><time datetime="{start.isoformat()}">{when}</time></p>'
                     f'<a class="btn btn-primary" href="{esc(b["live_url"])}" target="_blank" rel="noopener">Watch live</a></div>')
    replay = ('<div class="broadcast broadcast-replay"><p class="status-pill">Watch a replay</p>'
              '<p>Live times vary from week to week. The next broadcast time is announced on our pages; '
              'until then, every discussion below can be watched as a replay.</p></div>')
    # The replay note stays in the page; JS shows it again if every live item has ended.
    hidden = " hidden" if items else ""
    return "".join(items) + replay.replace('<div class="broadcast broadcast-replay"', f'<div class="broadcast broadcast-replay"{hidden}', 1)


def social_buttons():
    links = []
    for key in ("youtube", "facebook", "tiktok"):
        s = site["social"].get(key) or {}
        if s.get("verified") and s.get("url"):
            links.append(f'<a class="social-btn" href="{esc(s["url"])}" target="_blank" rel="noopener">'
                         f'{icon(key)}<span><strong>{esc(s["label"])}</strong><small>{esc(s["description"])}</small></span></a>')
    missing = [site["social"][k]["label"] for k in ("facebook", "tiktok") if not (site["social"].get(k) or {}).get("verified")]
    note = f'<p class="muted">Search “Standpoint Seychelles” on {" and ".join(missing)}.</p>' if missing else ""
    return '<div class="socials">' + "".join(links) + "</div>" + note


def whatsapp_button(cls="btn btn-whatsapp"):
    return (f'<a class="{cls}" href="{WA["link"]}" target="_blank" rel="noopener" '
            f'aria-label="{esc(WA["button_en"])} (opens a WhatsApp chat)">{icon("whatsapp")} {esc(WA["button_en"])}</a>')


def whatsapp_band():
    return (f'<div class="wa-band reveal"><div class="wa-copy"><span class="eyebrow">Take part</span>'
            f'<h2>Got a question for our next discussion?</h2>'
            f'<p class="wa-crs" lang="crs">{esc(WA["invite_crs"])}</p>'
            f'<p>Send it to us on WhatsApp at <a href="{WA["link"]}" target="_blank" rel="noopener">{esc(WA["number_display"])}</a>. '
            f'{esc(WA["call_note_en"])}</p></div><div class="wa-action">{whatsapp_button()}'
            f'<small>Opens a WhatsApp chat</small></div></div>')


TOKENS = [
    (r"\{\{featured:([\w-]+)\}\}", lambda m: featured(m.group(1))),
    (r"\{\{recent:(\d+)\}\}", lambda m: recent(m.group(1))),
    (r"\{\{archive\}\}", lambda m: archive()),
    (r"\{\{broadcast-status\}\}", lambda m: broadcast_status()),
    (r"\{\{social-buttons\}\}", lambda m: social_buttons()),
    (r"\{\{whatsapp-button\}\}", lambda m: whatsapp_button()),
    (r"\{\{whatsapp-band\}\}", lambda m: whatsapp_band()),
    (r"\{\{wa:number\}\}", lambda m: esc(WA["number_display"])),
    (r"\{\{wa:link\}\}", lambda m: WA["link"]),
    (r"\{\{wa:invite\}\}", lambda m: esc(WA["invite_crs"])),
    (r"\{\{wa:call\}\}", lambda m: esc(WA["call_note_en"])),
    (r"\{\{i:(\w+)\}\}", lambda m: icon(m.group(1))),
]


def jsonld():
    same = [s["url"] for s in site["social"].values() if s.get("verified")]
    data = {"@context": "https://schema.org", "@type": "Organization", "name": site["name"],
            "slogan": site["brand_line"], "url": SITE, "logo": SITE + "assets/img/icon-180.png",
            "areaServed": "Seychelles", "sameAs": same,
            "contactPoint": {"@type": "ContactPoint", "telephone": WA["number_display"].replace(" ", ""),
                             "contactType": "audience questions", "availableLanguage": ["English", "Seychellois Creole"]}}
    return '  <script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + "</script>\n"


def footer_socials():
    items = [f'<li><a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(s["label"])}</a></li>'
             for s in site["social"].values() if s.get("verified")]
    items.append(f'<li><a href="{WA["link"]}" target="_blank" rel="noopener">WhatsApp {esc(WA["number_display"])}</a></li>')
    return "\n            ".join(items)


def page(name, body):
    title = re.search(r"<!--title:(.*?)-->", body).group(1)
    desc = re.search(r"<!--desc:(.*?)-->", body).group(1)
    body = re.sub(r"<!--(title|desc):.*?-->\n", "", body)
    for pat, fn in TOKENS:
        body = re.sub(pat, fn, body)
    full = f"{site['name']} — {site['brand_line'].rstrip('.')}" if name == "index.html" else f"{title} · {site['name']}"
    url = SITE + ("" if name == "index.html" else name)
    nav = "\n".join(f'          <li><a href="{h}"{" aria-current=\"page\"" if h == name else ""}>{t}</a></li>' for h, t in NAV)
    base = f'  <base href="{SITE}">\n' if name == "404.html" else ""
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
{base}  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(full)}</title>
  <meta name="description" content="{esc(desc)}">
  <link rel="canonical" href="{url}">
  <meta property="og:url" content="{url}">
  <meta property="og:site_name" content="{site['name']}">
  <meta property="og:title" content="{esc(full)}">
  <meta property="og:description" content="{esc(desc)}">
  <meta property="og:type" content="website">
  <meta property="og:image" content="{SITE}assets/img/og-image.jpg">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="Standpoint Seychelles logo: Where Truth Ignites Transformation">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="theme-color" content="#070504">
  <link rel="icon" href="assets/img/icon-32.png" type="image/png" sizes="32x32">
  <link rel="apple-touch-icon" href="assets/img/icon-180.png">
  <script>document.documentElement.classList.add('js');if(!matchMedia('(prefers-reduced-motion: reduce)').matches)document.documentElement.classList.add('motion');</script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700&family=Montserrat:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="assets/css/style.css">
{jsonld() if name == "index.html" else ""}</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>
  <div class="flag-stripe" aria-hidden="true"></div>
  <header class="site-header">
    <div class="container">
      <nav class="nav" aria-label="Main">
        <a class="brand" href="index.html">
          <img src="assets/img/logo-sm.webp" width="193" height="200" alt="Standpoint Seychelles — home">
        </a>
        <button class="nav-toggle" aria-expanded="false" aria-controls="nav-links" aria-label="Menu">☰</button>
        <ul class="nav-links" id="nav-links">
{nav}
          <li class="nav-cta">{whatsapp_button("nav-wa")}</li>
        </ul>
      </nav>
    </div>
  </header>

  <main id="main">
{body}  </main>

  <footer class="site-footer">
    <div class="container">
      <div class="footer-grid">
        <div>
          <img class="footer-logo" src="assets/img/logo-sm.webp" width="193" height="200" alt="Standpoint Seychelles" loading="lazy">
          <p>{site['brand_line']}<br>Live podcasts, street interviews and youth forums on the decisions shaping Seychelles.</p>
        </div>
        <div>
          <h2 class="footer-title">Explore</h2>
          <ul>
            <li><a href="watch.html">Watch episodes</a></li>
            <li><a href="our-work.html">Our work</a></li>
            <li><a href="learn.html">Learn the basics</a></li>
            <li><a href="visuals.html">Visual explainers</a></li>
          </ul>
        </div>
        <div>
          <h2 class="footer-title">Follow &amp; contact</h2>
          <ul>
            {footer_socials()}
          </ul>
        </div>
      </div>
      <div class="footer-bottom">
        <span>© <span id="year">2026</span> {site['name']}</span>
        <span>Information is for education only and is not legal advice.</span>
      </div>
    </div>
  </footer>
  <script src="assets/js/main.js"></script>
</body>
</html>
'''


def redirect(old, new):
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Moved · {site["name"]}</title>'
            f'<link rel="canonical" href="{SITE}{new}"><meta name="robots" content="noindex">'
            f'<meta http-equiv="refresh" content="0; url={new}"></head>'
            f'<body><p>This page has moved to <a href="{new}">{new}</a>.</p></body></html>\n')


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    pages = sorted((SRC / "pages").glob("*.html"))
    for f in pages:
        (OUT / f.name).write_text(page(f.name, f.read_text(encoding="utf-8")), encoding="utf-8")
    for old, new in REDIRECTS.items():
        (OUT / old).write_text(redirect(old, new), encoding="utf-8")
    shutil.copytree(ROOT / "assets", OUT / "assets")
    (OUT / ".nojekyll").write_text("")
    urls = [SITE + ("" if f.name == "index.html" else f.name) for f in pages if f.name != "404.html"]
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                     + "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}sitemap.xml\n")
    print(f"built {len(pages)} pages, {len(published)} published episodes -> {OUT}")


if __name__ == "__main__":
    main()
