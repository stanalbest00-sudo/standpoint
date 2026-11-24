# Standpoint Seychelles

Website for **Standpoint Seychelles**, an independent, non-partisan civic education platform.

It is a plain static site (HTML + CSS + a little JavaScript). There is no build step, so you can edit any page directly.

## Pages

| File | Page |
|---|---|
| `index.html` | Home |
| `learn.html` | Learning hub, FAQ and quiz |
| `visuals.html` | Visual explainers (separation of powers, how a law is made, voting) |
| `about.html` | About the organisation |
| `get-involved.html` | Volunteer and contact |
| `404.html` | "Page not found" |

Styles are in `assets/css/style.css` (colours are at the top), and scripts are in `assets/js/main.js`.

## Media

| Path | Used for |
|---|---|
| `assets/frames/lg`, `assets/frames/sm` | Home page scroll-driven intro (181 frames from the intro video, desktop and phone sizes) |
| `assets/video/standpoint-intro.mp4` | Full intro video with sound ("Watch video" button) |
| `assets/img/logo-sm.webp`, `logo.webp` | Header and footer logo |
| `assets/img/icon-32.png`, `icon-180.png` | Browser tab and phone home-screen icons |
| `assets/img/hero-wide.webp`, `hero-tall.webp` | Still intro shown when animations are off |
| `assets/img/flag-banner.webp` | About page banner and image |
| `assets/img/og-image.jpg` | Preview image when the link is shared |

To replace the intro video, regenerate the frames with ffmpeg:

```sh
ffmpeg -i new-video.mp4 -vf "fps=12,scale=1280:-2" -c:v libwebp -quality 62 assets/frames/lg/f%03d.webp
ffmpeg -i new-video.mp4 -vf "fps=12,scale=720:-2"  -c:v libwebp -quality 60 assets/frames/sm/f%03d.webp
```

and update `FRAMES` in `assets/js/main.js` to the new frame count.

Motion follows a few rules: only opacity/transform/blur are animated, durations stay short with ease-out curves,
hover effects only run on devices with a mouse, and everything falls back to still images for visitors who
have "reduce motion" turned on.
The header and footer are repeated on every page, so if you change the menu, change it in each file.

## Preview locally

```sh
python3 -m http.server 8000
# open http://localhost:8000
```

## Going live (GitHub Pages)

1. In the repository on GitHub, go to **Settings → Pages** and set **Source** to **GitHub Actions**.
2. Merge changes into `main`. The workflow in `.github/workflows/pages.yml` publishes the site automatically.
3. The site appears at `https://<owner>.github.io/standpoint/`.

### Custom domain (e.g. standpoint.sc)

In **Settings → Pages → Custom domain**, enter the domain. Then, at your domain registrar, add a `CNAME` record pointing `www` to `<owner>.github.io`
(or the four GitHub Pages `A` records for the bare domain). Turn on **Enforce HTTPS** once the domain is verified.

## Before launch: checklist

- [ ] Replace the placeholder email `hello@standpoint.sc` in `get-involved.html`.
- [ ] Add social media links to the footer.
- [ ] Have someone review all facts against the Constitution and Electoral Commission sources.
