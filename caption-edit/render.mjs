import {bundle} from '@remotion/bundler';
import {renderMedia, renderStill, selectComposition} from '@remotion/renderer';
import path from 'node:path';
const args = process.argv.slice(2);
const id = args.indexOf('--id') >= 0 ? args[args.indexOf('--id') + 1] : 'v0';
const still = args.indexOf('--still') >= 0 ? Number(args[args.indexOf('--still') + 1]) : null;
const entry = path.resolve('src/index.ts');
const serveUrl = await bundle({entryPoint: entry, webpackOverride: (c) => ({...c, module: {...c.module, rules: [...(c.module?.rules ?? []).filter(r => !(r.test && r.test.toString().includes('css'))), {test: /\.css$/, use: ['style-loader','css-loader']}, {test: /\.woff2$/, type: 'asset/resource'}]}})});
const browserExecutable = '/opt/pw-browsers/chromium';
const chromiumOptions = {gl: 'swangle', disableWebSecurity: true};
const comp = await selectComposition({serveUrl, id, browserExecutable, chromiumOptions});
if (still !== null) {
  await renderStill({composition: comp, serveUrl, output: `out/${id}-still-${still}.png`, frame: still, browserExecutable, chromiumOptions});
} else {
  await renderMedia({composition: comp, serveUrl, codec: 'h264', outputLocation: `out/${id}-captioned.mp4`, browserExecutable, chromiumOptions, crf: 18, concurrency: 4,
    onProgress: ({renderedFrames}) => { if (renderedFrames % 100 === 0) console.log('frames', renderedFrames); }});
}
console.log('\ndone');
