import {bundle} from '@remotion/bundler';
import {renderMedia, renderStill, selectComposition} from '@remotion/renderer';
import path from 'node:path';
const args = process.argv.slice(2);
const still = args.indexOf('--still') >= 0 ? Number(args[args.indexOf('--still') + 1]) : null;
const entry = path.resolve('src/index.ts');
const serveUrl = await bundle({entryPoint: entry, webpackOverride: (c) => ({...c, module: {...c.module, rules: [...(c.module?.rules ?? []).filter(r => !(r.test && r.test.toString().includes('css'))), {test: /\.css$/, use: ['style-loader','css-loader']}, {test: /\.woff2$/, type: 'asset/resource'}]}})});
const browserExecutable = '/opt/pw-browsers/chromium';
const chromiumOptions = {gl: 'swangle', disableWebSecurity: true};
const comp = await selectComposition({serveUrl, id: 'Edit', browserExecutable, chromiumOptions});
if (still !== null) {
  await renderStill({composition: comp, serveUrl, output: `out/still-${still}.png`, frame: still, browserExecutable, chromiumOptions});
} else {
  await renderMedia({composition: comp, serveUrl, codec: 'h264', outputLocation: 'out/captioned.mp4', browserExecutable, chromiumOptions, crf: 18, concurrency: 4,
    onProgress: ({progress}) => { if (Math.round(progress*100) % 10 === 0) process.stdout.write(`\r${Math.round(progress*100)}%`); }});
}
console.log('\ndone');
