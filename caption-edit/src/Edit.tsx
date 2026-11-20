import React, {useMemo} from 'react';
import {AbsoluteFill, OffthreadVideo, Img, staticFile, useCurrentFrame, useVideoConfig, spring, interpolate} from 'remotion';
import './fonts.css';

type W = {w: string; s: number; e: number};
type Props = {file: string; words: W[]; dur: number};
type Chunk = {words: W[]; start: number; end: number; key: number; icon?: string};

const clean = (s: string) => s.toLowerCase().replace(/[^a-z0-9']/g, '');
const STOP = new Set('a an and are as at be but by for from have has had i i\'m if in is it its it\'s of on or so that the their there they this to was we you your with all not about other than just also very can will do does'.split(' '));
const KEY = new Set(['intermittent','fasting','healthier','weight','autophagy','cells','eaten','rhythm','easiest','window','protein','fat','hypoglycemic','blood','sugar','worse','metabolic','syndrome','insulin','resistance','diabetes','men','women','adrenal','stressed','difficult','prolonged','fast','sleep','consult','free','definitely','effective','never','always','shouldn\'t','try','thyroid','tired','cold','constipation','hair','skin','sleep','hormonal','testosterone','stress','cortisol','mindset','picture','brain','refrigerator','happy','reverse','medications','effectiveness','supplements','therapy','pounds','months','visit','call','education','lifestyle','exercise','diet','symptoms','energy','weight']);
const ICONS: Record<string, string> = {
  intermittent: '⏳', fasting: '⏳', healthier: '💪', weight: '⚖️', autophagy: '🧬', cells: '🦠',
  window: '🕐', protein: '🥩', fat: '🥑', hypoglycemic: '🩸', sugar: '🩸', hours: '⏰',
  metabolic: '🔥', insulin: '💉', diabetes: '🩺', adrenal: '⚡', stressed: '😰', sleep: '😴',
  consult: '📞', never: '🚫', hope: '🙌', thyroid: '🦋', tired: '😴', cold: '🥶', hair: '💇', skin: '🧴', testosterone: '💪', cortisol: '😰', stress: '😰', mindset: '🧠', picture: '📸', brain: '🧠', refrigerator: '🧊', happy: '😊', medications: '💊', supplements: '💊', therapy: '🔴', pounds: '⚖️', diet: '🥗', exercise: '🏃', visit: '📞', reverse: '🔄', energy: '⚡', 'glp-1s': '💉', hormonal: '🧪',
};
const SIZE_KEY = 112, SIZE_NORM = 82;

const FIX: Record<string, string> = {barrett: 'Baird', beard: 'Baird', baird: 'Baird', barrett_: 'Baird'};
function normalize(raw: W[]): W[] {
  const out: W[] = [];
  for (let i = 0; i < raw.length; i++) {
    let x = {...raw[i]};
    const c = clean(x.w);
    if (FIX[c] && /^(john|dr)/i.test(clean(raw[i - 1]?.w ?? '')) ) x.w = x.w.replace(/[A-Za-z']+/, FIX[c]);
    // "GOP ones" -> "GLP-1s"
    if (c === 'gop' && clean(raw[i + 1]?.w ?? '') === 'ones') { x = {w: 'GLP-1s', s: x.s, e: raw[i + 1].e}; i++; }
    const prev = out[out.length - 1];
    // merge "3 a .m." / "1 %" / "502 -785 -7480" style splits
    if (prev && (/^[.%]/.test(x.w) || /^-\d/.test(x.w))) { prev.w = prev.w + x.w.replace(/^\s+/, ''); prev.e = x.e; continue; }
    out.push(x);
  }
  return out;
}
function buildChunks(raw: W[]): Chunk[] {
  const ws = normalize(raw);
  const out: Chunk[] = [];
  let cur: W[] = [];
  const flush = () => {
    if (!cur.length) return;
    let key = -1, best = -1;
    cur.forEach((x, i) => {
      const c = clean(x.w);
      const sc = KEY.has(c) ? 100 + c.length : STOP.has(c) ? -1 : c.length;
      if (sc > best) { best = sc; key = i; }
    });
    if (best < 7) key = -1; // no highlight unless a topic word or a long word
    let icon: string | undefined;
    for (const x of cur) { const c = clean(x.w); if (ICONS[c]) { icon = ICONS[c]; break; } }
    out.push({words: cur, start: cur[0].s, end: cur[cur.length - 1].e, key, icon});
    cur = [];
  };
  ws.forEach((x, i) => {
    const prev = cur[cur.length - 1];
    if (prev) {
      const gap = x.s - prev.e;
      const punct = /[.,?!]$/.test(prev.w);
      if (cur.length >= 3 || punct || gap > 0.4 || (cur.length >= 2 && KEY.has(clean(prev.w)))) flush();
    }
    cur.push(x);
  });
  flush();
  return out;
}

const ZOOM_LEVELS = [1.0, 1.13, 1.05, 1.18, 1.0, 1.1];

export const Edit: React.FC<Props> = ({file, words, dur}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const t = frame / fps;
  const chunks = useMemo(() => buildChunks(words), [words]);

  // active chunk: last chunk whose start <= t, kept until its end+0.3 or next start
  let idx = -1;
  for (let i = 0; i < chunks.length; i++) if (chunks[i].start <= t + 0.02) idx = i;
  const chunk = idx >= 0 ? chunks[idx] : null;
  const next = chunks[idx + 1];
  const visible = chunk && t <= Math.min(chunk.end + 0.35, next ? next.start + 0.02 : 999);

  // punch-in zoom: level changes every 2 chunks, springs in
  const level = idx >= 0 ? ZOOM_LEVELS[Math.floor(idx / 2) % ZOOM_LEVELS.length] : 1;
  const prevLevel = idx >= 2 ? ZOOM_LEVELS[Math.floor((idx - 2) / 2) % ZOOM_LEVELS.length] : 1;
  const stepStart = idx >= 0 ? chunks[Math.floor(idx / 2) * 2].start : 0;
  const sp = spring({frame: frame - stepStart * fps, fps, config: {damping: 18, stiffness: 220, mass: 0.6}});
  const creep = interpolate(frame, [0, durationInFrames], [0, 0.03]);
  const scale = (prevLevel + (level - prevLevel) * sp) + creep;

  const fadeIn = interpolate(frame, [0, 12], [0, 1], {extrapolateRight: 'clamp'});
  const ctaStart = (dur - 5.3) * fps;
  const cta = spring({frame: frame - ctaStart, fps, config: {damping: 14, stiffness: 140}});

  return (
    <AbsoluteFill style={{backgroundColor: '#000'}}>
      <AbsoluteFill style={{transform: `scale(${scale})`, transformOrigin: '50% 38%'}}>
        <OffthreadVideo src={staticFile(file)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
      </AbsoluteFill>
      {/* subtle bottom shade for caption legibility */}
      <AbsoluteFill style={{background: 'linear-gradient(to top, rgba(0,0,0,0.38) 0%, rgba(0,0,0,0) 45%)'}} />

      {/* logo, top-left */}
      <div style={{position: 'absolute', left: 48, top: 70, opacity: fadeIn, padding: '14px 22px', borderRadius: 22, background: 'rgba(0,0,0,0.38)', backdropFilter: 'blur(6px)'}}>
        <Img src={staticFile('logo-white.png')} style={{width: 330, display: 'block', filter: 'drop-shadow(0 2px 6px rgba(0,0,0,.6))'}} />
      </div>

      {/* icon pop */}
      {chunk && visible && chunk.icon && (() => {
        const a = spring({frame: frame - chunk.start * fps, fps, config: {damping: 10, stiffness: 200, mass: 0.6}});
        return (
          <div style={{position: 'absolute', right: 70, top: 120, textAlign: 'center', fontSize: 150, fontFamily: '"Noto Color Emoji"',
            transform: `scale(${a}) rotate(${(1 - a) * -20}deg)`, filter: 'drop-shadow(0 8px 14px rgba(0,0,0,.5))'}}>{chunk.icon}</div>
        );
      })()}

      {/* captions */}
      {chunk && visible && (
        <div style={{position: 'absolute', left: 60, right: 60, top: 1230, display: 'flex', flexWrap: 'wrap', justifyContent: 'center', alignItems: 'baseline', gap: '6px 26px', fontFamily: 'Poppins', textTransform: 'uppercase', textAlign: 'center'}}>
          {chunk.words.map((x, i) => {
            if (t < x.s - 0.02) return null;
            const isKey = i === chunk.key;
            const isBig = isKey && KEY.has(clean(x.w));
            const p = spring({frame: frame - x.s * fps, fps, config: {damping: 12, stiffness: 260, mass: 0.5}});
            return (
              <span key={i} style={{
                fontWeight: 800, fontSize: isBig ? SIZE_KEY : isKey ? 96 : SIZE_NORM, lineHeight: 1.05,
                color: isKey ? '#FFE600' : '#fff',
                WebkitTextStroke: `${isKey ? 10 : 8}px #000`, paintOrder: 'stroke fill',
                textShadow: '0 6px 0 rgba(0,0,0,.55)',
                display: 'inline-block', transform: `scale(${0.6 + 0.4 * p})`, opacity: Math.min(1, p * 1.6),
              }}>{x.w.replace(/[.,?!]$/, '')}</span>
            );
          })}
        </div>
      )}

      {/* end CTA */}
      {frame >= ctaStart && (
        <div style={{position: 'absolute', left: 0, right: 0, top: 1560, display: 'flex', justifyContent: 'center', transform: `scale(${cta})`, opacity: cta}}>
          <div style={{background: '#FFE600', color: '#111', fontFamily: 'Poppins', fontWeight: 800, fontSize: 54, padding: '26px 54px', borderRadius: 999, boxShadow: '0 10px 30px rgba(0,0,0,.45)'}}>
            📞 FREE CONSULT — CLICK BELOW
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};
