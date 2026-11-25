import React, {useMemo} from 'react';
import {AbsoluteFill, OffthreadVideo, Img, staticFile, useCurrentFrame, useVideoConfig, spring, interpolate} from 'remotion';
import * as L from 'lucide-react';
import './fonts.css';
import type {IconCue} from './scenes/v6';

type W = {w: string; s: number; e: number};
type Props = {file: string; person: string; words: W[]; dur: number; icons: IconCue[]; keys: string[]};
const clean = (s: string) => s.toLowerCase().replace(/[^a-z0-9']/g, '');
const YEL = '#FFD400';

type Chunk = {top: W[]; bot: W[]; keyIdx: Set<number>; start: number; end: number};
function build(ws: W[], keys: Set<string>): Chunk[] {
  const out: Chunk[] = []; let cur: W[] = [];
  const flush = () => {
    if (!cur.length) return;
    const isKey = cur.map((x) => keys.has(clean(x.w)));
    const first = isKey.indexOf(true);
    let top: W[], bot: W[]; const ki = new Set<number>();
    if (first >= 0) { top = cur.slice(0, first); bot = cur.slice(first); bot.forEach((x, i) => { if (keys.has(clean(x.w))) ki.add(i); }); }
    else { const h = Math.ceil(cur.length / 2); top = cur.slice(0, h); bot = cur.slice(h); }
    if (!top.length) { top = [] }
    out.push({top, bot, keyIdx: ki, start: cur[0].s, end: cur[cur.length - 1].e}); cur = [];
  };
  ws.forEach((x) => {
    const p = cur[cur.length - 1];
    if (p && (cur.length >= 5 || /[.,?!]$/.test(p.w) || x.s - p.e > 0.4)) flush();
    cur.push(x);
  });
  flush(); return out;
}

const IconBehind: React.FC<{cue: IconCue}> = ({cue}) => {
  const frame = useCurrentFrame(); const {fps} = useVideoConfig();
  const t0 = cue.at * fps, t1 = (cue.at + cue.dur) * fps;
  if (frame < t0 - 1 || frame > t1 + 2) return null;
  const sp = spring({frame: frame - t0, fps, config: {damping: 11, stiffness: 170, mass: 0.7}});
  const fade = interpolate(frame, [t1 - 8, t1], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const drift = Math.sin((frame - t0) / 14) * 12, rot = Math.sin((frame - t0) / 22) * 3;
  const C = (L as any)[cue.icon] ?? L.Circle;
  const x = cue.side === 'L' ? 170 : 910, y = 600;
  return (
    <div style={{position: 'absolute', left: x - 160, top: y - 140 + drift, width: 320, textAlign: 'center', opacity: fade * Math.min(1, sp * 1.5),
      transform: `scale(${0.4 + 0.6 * sp}) rotate(${rot + (1 - sp) * (cue.side === 'L' ? -25 : 25)}deg)`}}>
      {cue.label && <div style={{position: 'absolute', left: 0, right: 0, top: -76, fontFamily: 'Poppins', fontWeight: 800, fontSize: 34, letterSpacing: 1, color: '#fff', textShadow: '0 4px 14px rgba(0,0,0,.85)'}}>{cue.label}</div>}
      <div style={{width: 260, height: 260, margin: '0 auto', borderRadius: 130, background: 'radial-gradient(circle at 35% 30%, rgba(255,212,0,.95), rgba(255,170,0,.9))',
        boxShadow: '0 0 90px rgba(255,200,0,.55), 0 22px 40px rgba(0,0,0,.45)', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
        <C size={146} color="#1a1204" strokeWidth={2.2} />
      </div>
    </div>
  );
};

export const EditPro: React.FC<Props> = ({file, person, words, icons, keys}) => {
  const frame = useCurrentFrame(); const {fps} = useVideoConfig(); const t = frame / fps;
  const chunks = useMemo(() => build(words, new Set(keys)), [words, keys]);
  let idx = -1; for (let i = 0; i < chunks.length; i++) if (chunks[i].start <= t + 0.02) idx = i;
  const ch = idx >= 0 ? chunks[idx] : null; const nx = chunks[idx + 1];
  const vis = ch && t <= Math.min(ch.end + 0.35, nx ? nx.start + 0.02 : 999);
  const creep = interpolate(frame, [0, 1981], [0, 0.03]);
  const word = (x: W, big: boolean, key: boolean, i: number) => {
    if (t < x.s - 0.02) return null;
    const p = spring({frame: frame - x.s * fps, fps, config: {damping: 12, stiffness: 260, mass: 0.5}});
    const bar = spring({frame: frame - x.s * fps - 4, fps, config: {damping: 18, stiffness: 120, mass: 0.8}});
    return (
      <span key={i} style={{position: 'relative', display: 'inline-block', fontWeight: 800, fontSize: big ? 100 : 60, lineHeight: 1.05, color: YEL,
        textShadow: '0 4px 16px rgba(0,0,0,.75), 0 2px 3px rgba(0,0,0,.6)' + (key ? ', 0 0 34px rgba(255,212,0,.35)' : ''),
        transform: `scale(${0.6 + 0.4 * p})`, opacity: Math.min(1, p * 1.6)}}>
        {x.w.replace(/[.,?!]$/, '')}
        {key && <span style={{position: 'absolute', left: 0, right: 0, bottom: -6, height: 9, borderRadius: 5, background: YEL, transformOrigin: 'left', transform: `scaleX(${Math.min(1, bar)})`, boxShadow: '0 3px 10px rgba(0,0,0,.5)'}} />}
      </span>
    );
  };
  return (
    <AbsoluteFill style={{backgroundColor: '#000'}}>
      {/* 1. full video (background, audio) */}
      <AbsoluteFill style={{transform: `scale(${1 + creep})`, transformOrigin: '50% 38%'}}>
        <OffthreadVideo src={staticFile(file)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
        {/* 2. icons, behind the person */}
        {icons.map((c, i) => <IconBehind key={i} cue={c} />)}
        {/* 3. person cut-out on top of the icons */}
        <AbsoluteFill><OffthreadVideo src={staticFile(person)} transparent muted style={{width: '100%', height: '100%', objectFit: 'cover'}} /></AbsoluteFill>
      </AbsoluteFill>
      <AbsoluteFill style={{background: 'linear-gradient(to top, rgba(0,0,0,0.42) 0%, rgba(0,0,0,0) 40%)'}} />
      <Img src={staticFile('logo-mix.png')} style={{position: 'absolute', left: 44, top: 78, width: 300, opacity: Math.min(1, frame / 12), filter: 'drop-shadow(0 2px 6px rgba(0,0,0,.55))'}} />
      {/* two-line captions */}
      {ch && vis && (
        <div style={{position: 'absolute', left: 50, right: 50, top: 1290, fontFamily: 'Poppins', textTransform: 'uppercase', textAlign: 'center'}}>
          <div style={{display: 'flex', justifyContent: 'center', gap: 20, minHeight: 70}}>{ch.top.map((x, i) => word(x, false, false, i))}</div>
          <div style={{display: 'flex', justifyContent: 'center', alignItems: 'baseline', gap: 18, marginTop: 4, flexWrap: 'nowrap'}}>
            {ch.bot.map((x, i) => word(x, ch.keyIdx.has(i), ch.keyIdx.has(i), i))}
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};
