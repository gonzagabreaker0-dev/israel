// Render the overlay (captions, graphics, CTA) and composite it onto base.mp4 + audio.wav.
//   node shorts/render.mjs OUTDIR                 -> OUTDIR/final.mp4
//   node shorts/render.mjs OUTDIR --stills 3,12,40 -> OUTDIR/still-*.jpg (composited previews)
//   --workers 4   parallel browser pages
import fs from 'node:fs';
import path from 'node:path';
import { spawn, execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const fa = require('@fortawesome/free-solid-svg-icons');

const here = path.dirname(new URL(import.meta.url).pathname);
const out = path.resolve(process.argv[2]);
const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
const tl = JSON.parse(fs.readFileSync(path.join(out, 'timeline.json'), 'utf8'));
const { w: W, h: H, fps: FPS } = tl;
const N = Math.round(tl.duration * FPS);
const icons = {};
for (const k of Object.keys(fa)) if (k.startsWith('fa') && fa[k]?.icon) icons[k] = fa[k].icon;

const browser = await chromium.launch();
async function openPage() {
  const page = await browser.newPage({ viewport: { width: W, height: H } });
  page.on('pageerror', (e) => console.error('[page]', e.message));
  await page.goto('file://' + path.join(here, 'overlay.html'));
  await page.evaluate(([t, i]) => window.OVL.init(t, i), [tl, icons]);
  return page;
}
const shot = async (page, t) => {
  await page.evaluate((t) => window.OVL.renderAt(t), t);
  return page.locator('#stage').screenshot({ type: 'png', omitBackground: true });
};

const stills = arg('stills');
if (stills) {
  const page = await openPage();
  for (const t of stills.split(',').map(Number)) {
    const png = path.join(out, `ov-${t}.png`);
    fs.writeFileSync(png, await shot(page, t));
    execFileSync('ffmpeg', ['-y', '-v', 'error', '-ss', String(t), '-i', path.join(out, 'base.mp4'), '-i', png,
      '-filter_complex', '[0:v][1:v]overlay=0:0,scale=540:-1', '-frames:v', '1', '-q:v', '3', path.join(out, `still-${t}.jpg`)]);
    console.log('still', t);
  }
  await browser.close();
  process.exit(0);
}

// ---- parallel overlay render into alpha .mov chunks ----
const WORKERS = +arg('workers', 4);
const per = Math.ceil(N / WORKERS);
const t0 = Date.now();
let done = 0;
await Promise.all(Array.from({ length: WORKERS }, async (_, k) => {
  const a = k * per, b = Math.min(N, a + per);
  if (a >= b) return;
  const page = await openPage();
  const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'png', '-i', '-',
    '-c:v', 'qtrle', '-pix_fmt', 'argb', path.join(out, `ov${k}.mov`)], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let f = a; f < b; f++) {
    const buf = await shot(page, f / FPS);
    if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
    if (++done % 150 === 0) console.log(`${done}/${N} frames, ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  ff.stdin.end();
  await new Promise((r) => ff.on('close', r));
  await page.close();
}));
await browser.close();

const list = path.join(out, 'ov.txt');
fs.writeFileSync(list, Array.from({ length: WORKERS }, (_, k) => `file 'ov${k}.mov'`).filter((_, k) => k * per < N).join('\n'));
execFileSync('ffmpeg', ['-y', '-v', 'error', '-i', path.join(out, 'base.mp4'), '-f', 'concat', '-safe', '0', '-i', list,
  '-i', path.join(out, 'audio.wav'),
  '-filter_complex', '[0:v][1:v]overlay=0:0:eof_action=pass,format=yuv420p[v]', '-map', '[v]', '-map', '2:a',
  '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-profile:v', 'high', '-r', String(FPS),
  '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-shortest', path.join(out, 'final.mp4')], { stdio: 'inherit' });
console.log('done', path.join(out, 'final.mp4'), `${((Date.now() - t0) / 1000).toFixed(0)}s`);
