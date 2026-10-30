// Renders the reel frame-by-frame in headless Chromium and pipes it to ffmpeg.
//   node render.mjs                      -> out/reel-1080x1920.mp4 (full 60s, 30fps)
//   node render.mjs --w 1920 --h 1080    -> landscape cut
//   node render.mjs --stills 2,14,25     -> JPEG stills only (quick preview)
//   node render.mjs --from 19 --to 31    -> render a time range
//   node render.mjs --page endcard.html --to 5 --out endcard.mp4   -> owners end card
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)('playwright');

const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
const W = +arg('w', 1080), H = +arg('h', 1920), FPS = +arg('fps', 30);
const FROM = +arg('from', 0), TO = +arg('to', 60);
const stills = arg('stills');
const PAGE = arg('page', 'index.html');
const root = path.dirname(new URL(import.meta.url).pathname);
const outDir = path.join(root, 'out');
fs.mkdirSync(outDir, { recursive: true });

const types = { '.html': 'text/html', '.js': 'text/javascript', '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.json': 'application/json', '.jpg': 'image/jpeg' };
const server = http.createServer((req, res) => {
  const file = path.join(root, decodeURIComponent(new URL(req.url, 'http://x').pathname));
  if (!file.startsWith(root) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) { res.writeHead(404).end(); return; }
  res.writeHead(200, { 'content-type': types[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
}).listen(0);
const port = server.address().port;

const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: W, height: H } });
page.on('console', (m) => m.type() === 'error' && console.error('[page]', m.text()));
page.on('pageerror', (e) => console.error('[page]', e.message));
await page.goto(`http://localhost:${port}/${PAGE}?render=1&w=${W}&h=${H}`);
await page.waitForFunction(() => window.REEL?.ready, null, { timeout: 120000 });
const stage = page.locator('#stage');

const frame = async (t) => {
  await page.evaluate((t) => window.REEL.renderAt(t), t);
  return stage.screenshot({ type: 'jpeg', quality: 93 });
};

if (stills) {
  for (const t of stills.split(',').map(Number)) {
    fs.writeFileSync(path.join(outDir, `still-${String(t).padStart(5, '0')}.jpg`), await frame(t));
    console.log('still', t);
  }
} else {
  const name = arg('out', `reel-${W}x${H}${FROM || TO !== 60 ? `-${FROM}-${TO}` : ''}.mp4`);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', path.join(outDir, name)], { stdio: ['pipe', 'inherit', 'inherit'] });
  const n = Math.round((TO - FROM) * FPS), t0 = Date.now();
  for (let i = 0; i < n; i++) {
    const buf = await frame(FROM + i / FPS);
    if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
    if (i % 30 === 0) console.log(`frame ${i}/${n}  ${((Date.now() - t0) / (i + 1)).toFixed(0)}ms/frame`);
  }
  ff.stdin.end();
  await new Promise((r) => ff.on('close', r));
  console.log('wrote', path.join(outDir, name));
}
await browser.close();
server.close();
