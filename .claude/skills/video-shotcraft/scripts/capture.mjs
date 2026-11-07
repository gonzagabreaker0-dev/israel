// Records a smooth, eased scroll through a web page as video.
//   node capture.mjs <url> <out.webm> [--w 1080] [--h 1920] [--dur 8] [--scale 1]
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
const { chromium } = createRequire(import.meta.url)('playwright');

const [url, out] = process.argv.slice(2);
if (!url || !out) { console.error('usage: node capture.mjs <url> <out.webm> [--w 1080 --h 1920 --dur 8]'); process.exit(1); }
const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? +process.argv[i + 1] : d; };
const W = arg('w', 1080), H = arg('h', 1920), DUR = arg('dur', 8);

const dir = fs.mkdtempSync(path.join(path.dirname(path.resolve(out)), '.cap-'));
const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: W, height: H }, recordVideo: { dir, size: { width: W, height: H } } });
const page = await ctx.newPage();
await page.goto(url, { waitUntil: 'networkidle' });
await page.waitForTimeout(800);
await page.evaluate(async (dur) => {
  const max = document.documentElement.scrollHeight - innerHeight;
  const ease = (p) => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2);
  const t0 = performance.now();
  await new Promise((done) => {
    const step = () => {
      const p = Math.min(1, (performance.now() - t0) / (dur * 1000));
      scrollTo(0, ease(p) * max);
      p < 1 ? requestAnimationFrame(step) : done();
    };
    requestAnimationFrame(step);
  });
}, DUR - 1.5);
await page.waitForTimeout(700);
const video = page.video();
await ctx.close();
await browser.close();
fs.renameSync(await video.path(), out);
fs.rmSync(dir, { recursive: true, force: true });
console.log(out);
