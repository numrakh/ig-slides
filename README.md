# ig-slides

Daily Instagram carousel slides for @raxmatulloh_numonov, published with the Meta Graph API.

- `scripts/render.js` renders a 7-slide carousel (1080x1350 JPEG) from a JSON spec with Playwright.
- `scripts/ig_publish.py` publishes a carousel from public image URLs (reads `INSTAGRAM_ACCESS_TOKEN` from the environment; never commit the token).
- `scripts/threads_publish.py` publishes the same carousel to Threads (reads `THREADS_ACCESS_TOKEN`; drops hashtags, trims text to 500 chars; `--check`, `--dry-run`).
- `scripts/fb_publish.py` posts the same slides to the Facebook Page as one multi-photo post (reads `FACEBOOK_PAGE_TOKEN`, a system user token; gets the Page token at runtime; `--check`, `--dry-run`).
- `slides/YYYY-MM-DD/slideN.jpg` are the published slides, served to Meta via raw.githubusercontent.com.

Font: Inter (SIL Open Font License).
