import React from 'react';
import {AbsoluteFill, spring, useCurrentFrame, useVideoConfig, interpolate} from 'remotion';
import * as L from 'lucide-react';

export type Item = {label: string; icon: string; tag?: string; red?: boolean};
export type Scene = {
  start: number; end: number;
  bg: 'grid' | 'teal' | 'red' | 'paper' | 'cream';
  title: string;
  kind: 'nodes' | 'cards' | 'bars' | 'pair';
  center?: {icon: string; label?: string};
  items: Item[];
  bars?: {label: string; sub?: string; h: number; color: string}[];
};

const MONO = '"JetBrains Mono", monospace';
const Icon: React.FC<{name: string; size: number; color: string; stroke?: number}> = ({name, size, color, stroke = 2.2}) => {
  const C = (L as any)[name] ?? L.Circle;
  return <C size={size} color={color} strokeWidth={stroke} />;
};

const useSp = (at: number, cfg = {damping: 13, stiffness: 190, mass: 0.6}) => {
  const frame = useCurrentFrame(); const {fps} = useVideoConfig();
  return spring({frame: frame - at, fps, config: cfg});
};

const Background: React.FC<{bg: Scene['bg']}> = ({bg}) => {
  const lines: React.ReactNode[] = [];
  if (bg === 'grid') {
    for (let i = -10; i <= 10; i++) lines.push(<line key={'v' + i} x1={540} y1={940} x2={540 + i * 300} y2={1920} stroke="#fff" strokeOpacity={0.22} strokeWidth={2} />);
    for (let k = 0; k < 12; k++) { const y = 940 + 14 * Math.pow(k + 1, 1.85); lines.push(<line key={'h' + k} x1={0} y1={y} x2={1080} y2={y} stroke="#fff" strokeOpacity={0.22} strokeWidth={2} />); }
  }
  const base = {grid: '#05070a', teal: '#17808f', red: '#6a0d12', paper: '#161616', cream: '#efe7d3'}[bg];
  return (
    <AbsoluteFill style={{background: base}}>
      {bg === 'grid' && (
        <svg width="1080" height="1920" style={{position: 'absolute'}}>
          <defs><pattern id="sq" width="54" height="54" patternUnits="userSpaceOnUse"><path d="M54 0H0V54" fill="none" stroke="#fff" strokeOpacity="0.07" strokeWidth="2" /></pattern></defs>
          <rect width="1080" height="940" fill="url(#sq)" />
          {lines}
        </svg>
      )}
      {bg === 'teal' && (
        <svg width="1080" height="1920" style={{position: 'absolute'}}>
          <defs><pattern id="g" width="48" height="48" patternUnits="userSpaceOnUse"><path d="M48 0H0V48" fill="none" stroke="#fff" strokeOpacity="0.16" strokeWidth="2" /></pattern>
            <linearGradient id="tg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#1b93a4" /><stop offset="1" stopColor="#0d4f5a" /></linearGradient></defs>
          <rect width="1080" height="1920" fill="url(#tg)" /><rect width="1080" height="1920" fill="url(#g)" />
        </svg>
      )}
      {bg === 'red' && <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 30%, #8d1319 0%, #5a0a0e 70%)'}} />}
      {(bg === 'paper' || bg === 'cream') && (
        <svg width="1080" height="1920" style={{position: 'absolute', opacity: bg === 'cream' ? 0.5 : 0.35}}>
          <filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="3" seed="4" /><feColorMatrix values="0 0 0 0 0.5  0 0 0 0 0.5  0 0 0 0 0.5  0 0 0 0.9 0" /></filter>
          <rect width="1080" height="1920" filter="url(#n)" />
        </svg>
      )}
    </AbsoluteFill>
  );
};

const fg = (bg: Scene['bg']) => (bg === 'cream' ? '#1b1b1b' : '#fff');

const NODE_POS: Record<number, [number, number][]> = {
  1: [[540, 380]],
  2: [[270, 520], [810, 520]],
  3: [[240, 500], [840, 500], [540, 900]],
  4: [[240, 500], [840, 500], [240, 880], [840, 880]],
};

const Nodes: React.FC<{s: Scene}> = ({s}) => {
  const frame = useCurrentFrame(); const {fps} = useVideoConfig();
  const t0 = s.start * fps;
  const cp = useSp(t0 + 6);
  const pos = NODE_POS[s.items.length];
  const C: [number, number] = [540, 700];
  const col = fg(s.bg);
  return (
    <AbsoluteFill>
      <svg width="1080" height="1920" style={{position: 'absolute'}}>
        {s.items.map((it, i) => {
          const p = interpolate(frame - (t0 + 12 + i * 6), [0, 14], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
          const [x, y] = pos[i];
          return <line key={i} x1={C[0]} y1={C[1]} x2={C[0] + (x - C[0]) * p} y2={C[1] + (y - C[1]) * p} stroke={col} strokeWidth={4} strokeOpacity={0.9} />;
        })}
      </svg>
      {s.items.map((it, i) => {
        const a = useSp(t0 + 20 + i * 6);
        const [x, y] = pos[i];
        const below = true;
        return (
          <div key={i} style={{position: 'absolute', left: x - 150, top: y - 56, width: 300, textAlign: 'center', transform: `scale(${a})`, opacity: a}}>
            <div style={{margin: '0 auto', width: 112, height: 112, borderRadius: 56, background: it.red ? '#e8392f' : s.bg === 'cream' ? '#1b1b1b' : '#d9d9d9',
              display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: it.red ? '0 0 40px rgba(232,57,47,.6)' : '0 0 30px rgba(255,255,255,.35)'}}>
              <Icon name={it.icon} size={56} color={it.red || s.bg === 'cream' ? '#fff' : '#111'} />
            </div>
            <div style={{fontFamily: MONO, fontWeight: 700, fontSize: 26, letterSpacing: 1, color: col, marginTop: 14, width: 230, margin: '14px auto 0', lineHeight: 1.15}}>{it.label}</div>
          </div>
        );
      })}
      {s.center && (
        <div style={{position: 'absolute', left: C[0] - 78, top: C[1] - 78, width: 156, height: 156, borderRadius: 78, background: s.bg === 'cream' ? '#1b1b1b' : '#fff',
          display: 'flex', alignItems: 'center', justifyContent: 'center', transform: `scale(${cp})`, boxShadow: '0 0 60px rgba(255,255,255,.45)'}}>
          <Icon name={s.center.icon} size={84} color={s.bg === 'cream' ? '#fff' : '#111'} />
        </div>
      )}
    </AbsoluteFill>
  );
};

const Cards: React.FC<{s: Scene}> = ({s}) => {
  const t0 = s.start * 30;
  const col = fg(s.bg);
  const n = s.items.length;
  const W = 420, H = 130, G = 32;
  return (
    <AbsoluteFill>
      {s.items.map((it, i) => {
        const a = useSp(t0 + 8 + i * 7);
        const cols = n === 1 ? 1 : 2;
        const r = Math.floor(i / cols), c = i % cols;
        const x0 = (1080 - (cols * W + (cols - 1) * G)) / 2;
        const x = x0 + c * (W + G), y = 430 + r * (H + 70);
        return (
          <div key={i} style={{position: 'absolute', left: x, top: y, width: W, height: H, transform: `scale(${a})`, opacity: a}}>
            <div style={{width: '100%', height: '100%', boxSizing: 'border-box', border: `3px solid ${col}`, borderRadius: 22, background: s.bg === 'cream' ? 'rgba(0,0,0,.04)' : 'rgba(255,255,255,.07)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 16, fontFamily: MONO, fontWeight: 800, fontSize: 31, color: col, textAlign: 'center', padding: '0 14px'}}>
              <Icon name={it.icon} size={38} color={col} /><span>{it.label}</span>
            </div>
            {it.tag && (
              <div style={{position: 'absolute', left: 36, bottom: -22, background: '#e8392f', color: '#fff', fontFamily: MONO, fontWeight: 800, fontSize: 22, padding: '8px 16px', borderRadius: 8, transform: 'rotate(-4deg)', whiteSpace: 'nowrap'}}>{it.tag}</div>
            )}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

const Bars: React.FC<{s: Scene}> = ({s}) => {
  const t0 = s.start * 30; const col = fg(s.bg);
  const bars = s.bars ?? [];
  return (
    <AbsoluteFill>
      {bars.map((b, i) => {
        const a = useSp(t0 + 10 + i * 10, {damping: 16, stiffness: 90, mass: 0.9});
        const x = 540 + (i - (bars.length - 1) / 2) * 330;
        const h = 400 * b.h * a;
        return (
          <React.Fragment key={i}>
            <div style={{position: 'absolute', left: x - 90, top: 800 - h, width: 180, height: h, borderRadius: '14px 14px 0 0', background: b.color, boxShadow: `0 0 40px ${b.color}66`}} />
            <div style={{position: 'absolute', left: x - 160, top: 820, width: 320, textAlign: 'center', fontFamily: MONO, fontWeight: 800, fontSize: 30, color: col, opacity: a}}>{b.label}</div>
            {b.sub && <div style={{position: 'absolute', left: x - 160, top: 862, width: 320, textAlign: 'center', fontFamily: MONO, fontWeight: 600, fontSize: 24, color: col, opacity: a * 0.75}}>{b.sub}</div>}
          </React.Fragment>
        );
      })}
    </AbsoluteFill>
  );
};

const Pair: React.FC<{s: Scene}> = ({s}) => {
  const frame = useCurrentFrame(); const t0 = s.start * 30; const col = fg(s.bg);
  const a = useSp(t0 + 8), b = useSp(t0 + 30);
  const p = interpolate(frame - (t0 + 16), [0, 16], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const [A, B] = s.items;
  const node = (it: Item, x: number, k: number) => (
    <div style={{position: 'absolute', left: x - 150, top: 500, width: 300, textAlign: 'center', transform: `scale(${k})`, opacity: k}}>
      <div style={{margin: '0 auto', width: 150, height: 150, borderRadius: 75, background: it.red ? '#e8392f' : '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: it.red ? '0 0 50px rgba(232,57,47,.6)' : '0 0 40px rgba(255,255,255,.4)'}}>
        <Icon name={it.icon} size={76} color={it.red ? '#fff' : '#111'} />
      </div>
      <div style={{fontFamily: MONO, fontWeight: 800, fontSize: 28, color: col, marginTop: 16}}>{it.label}</div>
    </div>
  );
  return (
    <AbsoluteFill>
      <svg width="1080" height="1920" style={{position: 'absolute'}}><line x1={400} y1={575} x2={400 + 280 * p} y2={575} stroke={col} strokeWidth={5} /></svg>
      {node(A, 250, a)}{node(B, 830, b)}
    </AbsoluteFill>
  );
};

export const SceneView: React.FC<{s: Scene}> = ({s}) => {
  const frame = useCurrentFrame(); const {fps} = useVideoConfig();
  const t0 = s.start * fps, t1 = s.end * fps;
  const op = Math.min(interpolate(frame, [t0, t0 + 5], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}), interpolate(frame, [t1 - 4, t1], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}));
  const settle = interpolate(frame, [t0, t0 + 8], [1.05, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const tp = Math.max(0, Math.floor((frame - t0 - 2) / 1.6));
  const title = s.title.slice(0, tp);
  return (
    <AbsoluteFill style={{opacity: op, transform: `scale(${settle})`}}>
      <Background bg={s.bg} />
      <div style={{position: 'absolute', top: 262, left: 0, right: 0, textAlign: 'center', fontFamily: MONO, fontWeight: 800, fontSize: 36, letterSpacing: 3, color: fg(s.bg)}}>{title}</div>
      {s.kind === 'nodes' && <Nodes s={s} />}
      {s.kind === 'cards' && <Cards s={s} />}
      {s.kind === 'bars' && <Bars s={s} />}
      {s.kind === 'pair' && <Pair s={s} />}
    </AbsoluteFill>
  );
};

export const Hook: React.FC<{start: number; end: number; lines: [string, string]}> = ({start, end, lines}) => {
  const frame = useCurrentFrame(); const {fps} = useVideoConfig();
  const sp = spring({frame: frame - start * fps, fps, config: {damping: 15, stiffness: 160, mass: 0.7}});
  const out = interpolate(frame, [end * fps - 6, end * fps], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const pts: string[] = ['0,0', '1080,0', '1080,330'];
  for (let i = 0; i <= 18; i++) pts.push(`${1080 - i * 60},${330 + (i % 2 ? -16 : 14)}`);
  return (
    <AbsoluteFill style={{transform: `translateY(${(1 - sp) * -360}px)`, opacity: out}}>
      <svg width="1080" height="400" style={{position: 'absolute', filter: 'drop-shadow(0 8px 14px rgba(0,0,0,.5))'}}>
        <polygon points={pts.join(' ')} fill="#151515" />
      </svg>
      <div style={{position: 'absolute', left: 54, top: 70, fontFamily: 'Poppins', fontWeight: 800, textTransform: 'uppercase', lineHeight: 1.08}}>
        <div style={{fontSize: 52, color: '#fff'}}>{lines[0]}</div>
        <div style={{fontSize: 76, color: '#FFD400', whiteSpace: 'nowrap'}}>{lines[1]}</div>
      </div>
    </AbsoluteFill>
  );
};

export const CtaPill: React.FC<{start: number}> = ({start}) => {
  const sp = useSp(start * 30, {damping: 13, stiffness: 150, mass: 0.7});
  return (
    <div style={{position: 'absolute', left: 250, top: 1590, transform: `scale(${sp})`, transformOrigin: '50% 50%', opacity: sp}}>
      <div style={{display: 'flex', alignItems: 'center', gap: 22, background: '#fff', borderRadius: 999, padding: '20px 44px 20px 24px', boxShadow: '0 10px 30px rgba(0,0,0,.4)'}}>
        <div style={{width: 84, height: 84, borderRadius: 42, background: '#e8392f', display: 'flex', alignItems: 'center', justifyContent: 'center'}}><L.Phone size={44} color="#fff" fill="#fff" /></div>
        <div style={{fontFamily: 'Poppins', fontWeight: 800, color: '#111', lineHeight: 1.05}}>
          <div style={{fontSize: 46}}>FREE CONSULT</div>
          <div style={{fontSize: 30, color: '#e8392f'}}>LINK BELOW ↓</div>
        </div>
      </div>
    </div>
  );
};
