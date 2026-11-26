import React from 'react';
import {Composition} from 'remotion';
import {Edit} from './Edit';
import w0 from './words/v0.json';
import w1 from './words/v1.json';
import w2 from './words/v2.json';
import w3 from './words/v3.json';
import w4 from './words/v4.json';
import {scenes0, hook0} from './scenes/v0';
import {EditPro} from './EditPro';
import w6 from './words/v6.json';
import {icons6, KEYS6} from './scenes/v6';
import w7 from './words/v7.json';
const KEYS7 = ['testosterone','important','women','men','death','alzheimer\'s','dementia','heart','attacks','strokes','fractures','prostate','cancer','checked','free','estrogen','protein','study','studies','seven','prevented','dilates','arteries','stress','smoke','alcohol','diabetes','overweight','inflammation','homocysteine','hormone','fda','suicidal','normal','amazing','energy','pain','happiest','dose','absorbed','metabolized','level','share'];
import w5 from './words/v5.json';
import {scenes5, hook5} from './scenes/v5';

export const FPS = 30;
// id -> [file, words, duration seconds]
export const VIDEOS: Record<string, {file: string; words: any[]; dur: number; scenes?: any[]; hook?: any}> = {
  v0: {file: 'v0.mp4', words: w0, dur: 94.533, scenes: scenes0, hook: hook0},
  v1: {file: 'v1.mp4', words: w1, dur: 104.867},
  v2: {file: 'v2.mp4', words: w2, dur: 139.9},
  v3: {file: 'v3.mp4', words: w3, dur: 68.133},
  v4: {file: 'v4.mp4', words: w4, dur: 148.333},
  v5: {file: 'v5.mp4', words: w5, dur: 118.243, scenes: scenes5, hook: hook5},
};
export const Root: React.FC = () => (
  <>
    {Object.entries(VIDEOS).map(([id, v]) => (
      <Composition key={id} id={id} component={Edit} durationInFrames={Math.round(v.dur * FPS)} fps={FPS} width={1080} height={1920}
        defaultProps={{file: v.file, words: v.words, dur: v.dur, scenes: v.scenes ?? [], hook: v.hook}} />
    ))}
    <Composition id="v6" component={EditPro as any} durationInFrames={1981} fps={FPS} width={1080} height={1920}
      defaultProps={{file: 'v6.mp4', person: 'person6.webm', words: w6, dur: 66.025, icons: [] /* icons6 disabled: user preferred captions only */, keys: KEYS6}} />
    <Composition id="v7" component={EditPro as any} durationInFrames={3910} fps={FPS} width={1080} height={1920}
      defaultProps={{file: 'v7.mp4', person: 'person6.webm', words: w7, dur: 130.308, icons: [], keys: KEYS7}} />
  </>
);
