// Rasterise an SVG logo to a transparent PNG: node svg2png.mjs in.svg out.png HEIGHT
import fs from 'node:fs';
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)('playwright');
const [, , src, out, h = '200'] = process.argv;
const svg = fs.readFileSync(src, 'utf8');
const b = await chromium.launch();
const p = await b.newPage();
await p.setContent(`<html><body style="margin:0;background:transparent">
<img id="i" style="height:${h}px;display:block" src="data:image/svg+xml;base64,${Buffer.from(svg).toString('base64')}"></body></html>`);
await p.locator('#i').screenshot({ path: out, omitBackground: true });
await b.close();
