// Usage: node render.js spec.json outDir
// spec: {topic, avatar:"path", slides:[{photo:"local path", headline, highlight?, text?, author?, quote?}] x7}
// Assets must be local files (download with curl first). Output: outDir/slide1.jpg..slide7.jpg (1080x1350)
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const [specPath, outDir] = process.argv.slice(2);
const spec = JSON.parse(fs.readFileSync(specPath, 'utf8'));
const dir = path.dirname(path.resolve(specPath));
const abs = p => 'file://' + path.resolve(dir, p);
const esc = s => String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
const hl = (h, k) => { h = esc(h); if (!k) return h; const e = esc(k); const i = h.indexOf(e); return i < 0 ? h : h.slice(0,i)+`<span class="lime">${e}</span>`+h.slice(i+e.length); };
const fontFile = path.join(__dirname, 'Inter.woff2');
const css = `
@font-face{font-family:Inter;font-style:normal;font-weight:100 900;src:url('file://${fontFile}') format('woff2')}
*{box-sizing:border-box;margin:0;padding:0}
body{width:1080px;height:1350px;font-family:Inter,sans-serif}
.s{position:relative;width:1080px;height:1350px;overflow:hidden;background:#0B2C21;color:#F5F1E8}
.ph{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.sh{position:absolute;inset:0;background:linear-gradient(180deg,rgba(15,61,46,var(--top,.75)) 0%,rgba(15,61,46,.15) 20%,rgba(15,61,46,.1) 36%,rgba(15,61,46,.9) 62%,#0F3D2E 100%)}
.c{position:relative;height:100%;padding:96px 88px 88px;display:flex;flex-direction:column}
.top{display:flex;align-items:center;justify-content:space-between}
.me{display:flex;align-items:center;gap:34px}
.av{width:136px;height:136px;border-radius:50%;object-fit:cover;box-shadow:0 0 0 6px #0F3D2E,0 0 0 11px #C9F26B}
.nm{font-size:52px;font-weight:800;letter-spacing:-0.01em;line-height:1.1}
.hd{font-size:36px;font-weight:500;opacity:.8}
.pg{font-size:30px;font-weight:600;opacity:.8}
.body{flex:1;display:flex;flex-direction:column;justify-content:flex-end}
.lime{color:#C9F26B}
.tag{align-self:flex-start;background:#C9F26B;color:#0F3D2E;border-radius:999px;font-size:28px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:12px 26px;margin-bottom:40px}
.h1{font-size:112px;font-weight:900;line-height:1.02;letter-spacing:-0.035em}
.sub{font-size:48px;font-weight:500;line-height:1.36;opacity:.88;margin-top:40px;max-width:860px}
.num{font-size:150px;font-weight:900;line-height:.9;margin-bottom:28px;color:#C9F26B}
.h2{font-size:84px;font-weight:800;line-height:1.06;letter-spacing:-0.03em}
.q{font-size:72px;font-weight:800;line-height:1.1;letter-spacing:-0.025em}
.au{font-size:40px;font-weight:700;color:#C9F26B;margin-top:32px}
.tx{font-size:46px;font-weight:500;line-height:1.38;opacity:.88;margin-top:32px;max-width:860px}
.bar{width:120px;height:10px;background:#C9F26B;margin-bottom:40px}
.btn{align-self:flex-start;display:flex;align-items:center;gap:18px;background:#C9F26B;color:#0F3D2E;border-radius:999px;font-size:42px;font-weight:800;padding:26px 44px;margin-top:48px}
.bot{margin-top:56px;display:flex;justify-content:flex-end;align-items:center;gap:24px;font-size:32px;font-weight:700}
.ar{width:84px;height:84px;border-radius:50%;background:#C9F26B;display:flex;align-items:center;justify-content:center}
`;
const arrow = `<div class="ar"><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#0F3D2E" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg></div>`;
const bookmark = `<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#0F3D2E" stroke-width="2.6" stroke-linejoin="round"><path d="M6 3h12v18l-6-4-6 4z"/></svg>`;
function slide(s, i) {
  const n = i + 1;
  let body, bot;
  if (n === 1) {
    body = `<div class="tag">${esc(spec.topic)}</div><div class="h1">${hl(s.headline, s.highlight)}</div>${s.text?`<div class="sub">${esc(s.text)}</div>`:''}`;
    bot = `<span>Suring</span>${arrow}`;
  } else if (n === 7) {
    const [a, ...b] = String(s.headline).split('\n');
    body = `<div class="bar"></div><div class="h2">${esc(a)}${b.length?`<br><span class="lime">${esc(b.join(' '))}</span>`:''}</div>${s.text?`<div class="tx">${esc(s.text)}</div>`:''}<div class="btn">${bookmark}<span>Saqlab qo'ying</span></div>`;
    bot = `<span>Do'stingizga yuboring</span>`;
  } else {
    const num = `<div class="num">${String(n-1).padStart(2,'0')}</div>`;
    body = s.author ? `${num}<div class="q">${esc(s.headline)}</div><div class="au">${esc(s.author)}</div>`
                    : `${num}<div class="h2">${hl(s.headline, s.highlight)}</div>${s.text?`<div class="tx">${esc(s.text)}</div>`:''}`;
    bot = arrow;
  }
  const ph = s.photo ? `<img class="ph" src="${abs(s.photo)}">` : '';
  return `<!doctype html><html><head><meta charset="utf-8"><style>${css}</style></head><body><div class="s" style="--top:${s.topShade||.75}">${ph}<div class="sh"></div><div class="c">
  <div class="top"><div class="me"><img class="av" src="${abs(spec.avatar)}"><div><div class="nm">Rakhmatullo Numonov</div><div class="hd">@raxmatulloh_numonov</div></div></div><div class="pg">${n} / 7</div></div>
  <div class="body">${body}</div><div class="bot">${bot}</div></div></div></body></html>`;
}
(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1350 }, deviceScaleFactor: 1 });
  for (let i = 0; i < spec.slides.length; i++) {
    const f = path.join(outDir, `slide${i+1}.html`);
    fs.writeFileSync(f, slide(spec.slides[i], i));
    await p.goto('file://' + path.resolve(f));
    await p.evaluate(() => document.fonts.ready);
    await p.waitForFunction(() => [...document.images].every(im => im.complete && im.naturalWidth > 0), null, { timeout: 15000 });
    const over = await p.evaluate(() => { const c = document.querySelector('.c'); return c.scrollHeight > c.clientHeight + 2; });
    if (over) console.error(`WARN slide ${i+1}: text overflows`);
    await p.screenshot({ path: path.join(outDir, `slide${i+1}.jpg`), type: 'jpeg', quality: 92 });
    fs.unlinkSync(f);
  }
  await b.close();
  console.log('rendered', spec.slides.length);
})();
