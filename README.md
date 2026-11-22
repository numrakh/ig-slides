# ig-slides

Daily Instagram carousel slides for @raxmatulloh_numonov, published with the Meta Graph API.

- `scripts/render.js` renders a 7-slide carousel (1080x1350 JPEG) from a JSON spec with Playwright.
- `scripts/ig_publish.py` publishes a carousel from public image URLs (reads `INSTAGRAM_ACCESS_TOKEN` from the environment; never commit the token).
- `slides/YYYY-MM-DD/slideN.jpg` are the published slides, served to Meta via raw.githubusercontent.com.

Font: Inter (SIL Open Font License).
