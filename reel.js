// Israel Coffee Shop · 60s cinematic reel
// Every frame is a pure function of time t, so the same code plays live in the
// browser and renders frame-perfect video via render.mjs.
import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

const params = new URLSearchParams(location.search);
const RENDER = params.has('render');
const W = +params.get('w') || 1080;
const H = +params.get('h') || 1920;
const DURATION = 60;
if (RENDER) document.body.classList.add('render');

// ---------------------------------------------------------------- math
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, t) => a + (b - a) * t;
const range = (t, a, b) => clamp((t - a) / (b - a));
const smooth = (t) => t * t * (3 - 2 * t);
const easeInOut = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
const easeOut = (t) => 1 - Math.pow(1 - t, 3);
const easeIn = (t) => t * t * t;
const fract = (x) => x - Math.floor(x);
const bump = (t, c, w) => Math.exp(-(((t - c) / w) ** 2));
const V = (x, y, z) => new THREE.Vector3(x, y, z);
function rng(seed) {
  return () => {
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// ---------------------------------------------------------------- renderer
const stage = document.getElementById('stage');
const canvas = document.getElementById('gl');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(45, W / H, 0.02, 120);
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;

const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));
const bloom = new UnrealBloomPass(new THREE.Vector2(W, H), 0.45, 0.6, 0.9);
composer.addPass(bloom);
composer.addPass(new OutputPass());

let stageScale = 1;
function resize() {
  let w = W, h = H;
  if (!RENDER) {
    stageScale = Math.min(innerWidth / W, innerHeight / H);
    w = Math.floor(W * stageScale);
    h = Math.floor(H * stageScale);
  }
  stage.style.width = w + 'px';
  stage.style.height = h + 'px';
  renderer.setPixelRatio(RENDER ? 1 : Math.min(devicePixelRatio, 2));
  renderer.setSize(w, h, false);
  composer.setPixelRatio(renderer.getPixelRatio());
  composer.setSize(w, h);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}

// ---------------------------------------------------------------- textures
function canvasTex(w, h, draw, { srgb = true, repeat } = {}) {
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  const ctx = c.getContext('2d');
  draw(ctx, w, h);
  const tex = new THREE.CanvasTexture(c);
  if (srgb) tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 8;
  if (repeat) { tex.wrapS = tex.wrapT = THREE.RepeatWrapping; tex.repeat.set(...repeat); }
  tex.ctx = ctx;
  return tex;
}

const softDot = canvasTex(128, 128, (g, w) => {
  const r = g.createRadialGradient(w / 2, w / 2, 0, w / 2, w / 2, w / 2);
  r.addColorStop(0, 'rgba(255,255,255,1)');
  r.addColorStop(0.35, 'rgba(255,255,255,.55)');
  r.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = r; g.fillRect(0, 0, w, w);
});

const bokehTex = canvasTex(128, 128, (g, w) => {
  const r = g.createRadialGradient(w / 2, w / 2, 0, w / 2, w / 2, w / 2);
  r.addColorStop(0, 'rgba(255,255,255,.55)');
  r.addColorStop(0.78, 'rgba(255,255,255,.7)');
  r.addColorStop(0.9, 'rgba(255,255,255,.35)');
  r.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = r; g.fillRect(0, 0, w, w);
});

const steamTex = canvasTex(128, 128, (g, w) => {
  const R = rng(7);
  for (let i = 0; i < 26; i++) {
    const x = w / 2 + (R() - 0.5) * w * 0.4, y = w / 2 + (R() - 0.5) * w * 0.4, rr = w * (0.12 + R() * 0.22);
    const r = g.createRadialGradient(x, y, 0, x, y, rr);
    r.addColorStop(0, 'rgba(255,255,255,.18)');
    r.addColorStop(1, 'rgba(255,255,255,0)');
    g.fillStyle = r; g.fillRect(0, 0, w, w);
  }
});

function woodTex(seed, base = [92, 58, 34], repeat = [1, 1]) {
  return canvasTex(1024, 512, (g, w, h) => {
    const R = rng(seed);
    g.fillStyle = `rgb(${base})`; g.fillRect(0, 0, w, h);
    const planks = 5;
    for (let p = 0; p < planks; p++) {
      const y0 = (p / planks) * h, ph = h / planks, tone = (R() - 0.5) * 26;
      for (let y = 0; y < ph; y++) {
        const k = Math.sin(y * 0.35 + R() * 0.4) * 10 + Math.sin(y * 0.07 + p) * 14 + tone;
        g.fillStyle = `rgba(${base[0] + k},${base[1] + k * 0.7},${base[2] + k * 0.5},.55)`;
        g.fillRect(0, y0 + y, w, 1);
      }
      for (let i = 0; i < 70; i++) {
        g.strokeStyle = `rgba(30,16,8,${0.05 + R() * 0.12})`; g.lineWidth = 1 + R() * 2;
        const yy = y0 + R() * ph; g.beginPath(); g.moveTo(0, yy);
        for (let x = 0; x <= w; x += 32) g.lineTo(x, yy + Math.sin(x * 0.01 + i) * 3);
        g.stroke();
      }
      g.fillStyle = 'rgba(20,10,5,.6)'; g.fillRect(0, y0, w, 2);
    }
  }, { repeat });
}

function drawCrema(g, S = 512) {
  const c = S / 2;
  const r = g.createRadialGradient(c * 0.92, c * 0.92, 0, c, c, c);
  r.addColorStop(0, '#c9874a'); r.addColorStop(0.55, '#9a5a2a'); r.addColorStop(0.9, '#5a2d12'); r.addColorStop(1, '#2c1408');
  g.fillStyle = r; g.fillRect(0, 0, S, S);
  const R = rng(3);
  for (let i = 0; i < 900; i++) {
    const a = R() * Math.PI * 2, d = Math.sqrt(R()) * c;
    g.fillStyle = R() > 0.5 ? 'rgba(230,170,110,.10)' : 'rgba(60,25,8,.12)';
    g.beginPath(); g.arc(c + Math.cos(a) * d, c + Math.sin(a) * d, 1 + R() * 5, 0, Math.PI * 2); g.fill();
  }
  // tiger striping swirl
  g.strokeStyle = 'rgba(240,190,130,.10)'; g.lineWidth = 6;
  for (let k = 0; k < 7; k++) { g.beginPath(); g.arc(c, c, 40 + k * 30, k, k + 2.2); g.stroke(); }
}

// Latte art: blob that blooms (rosetta rings) then gets pulled through into a heart
function drawLatte(g, pb, pp, time, fromX, toX, S = 512) {
  drawCrema(g, S);
  const c = S / 2;
  if (pb > 0) {
    const R = 190 * easeOut(pb), m = easeInOut(pp);
    const cx = c - 28 + 34 * m, cy = c;
    const shape = (scale) => {
      g.beginPath();
      for (let i = 0; i <= 160; i++) {
        const s = (i / 160) * Math.PI * 2;
        const wob = 1 + 0.04 * Math.sin(6 * s + time * 7) * (1 - m);
        const hx = (16 * Math.sin(s) ** 3) / 17;
        const hy = (13 * Math.cos(s) - 5 * Math.cos(2 * s) - 2 * Math.cos(3 * s) - Math.cos(4 * s)) / 17 + 0.18;
        const x = lerp(Math.sin(s) * 0.82, hx, m) * wob * scale * R;
        const y = lerp(Math.cos(s) * 0.82, hy, m) * wob * scale * R;
        const px = cx - y, py = cy + x;
        i ? g.lineTo(px, py) : g.moveTo(px, py);
      }
      g.closePath();
    };
    g.filter = 'blur(2px)';
    g.fillStyle = '#f9f1e4'; shape(1); g.fill();
    g.strokeStyle = 'rgba(176,112,60,.75)';
    for (const k of [0.76, 0.54, 0.33]) { g.lineWidth = 9 * (0.6 + k * 0.6) * easeOut(pb); shape(k); g.stroke(); }
    if (pp > 0) {
      g.strokeStyle = '#f9f1e4'; g.lineCap = 'round'; g.lineWidth = 11;
      g.beginPath(); g.moveTo(fromX, cy); g.lineTo(lerp(fromX, toX, pp), cy); g.stroke();
    }
    g.filter = 'none';
  }
  const e = g.createRadialGradient(c, c, c * 0.78, c, c, c);
  e.addColorStop(0, 'rgba(40,18,6,0)'); e.addColorStop(1, 'rgba(40,18,6,.7)');
  g.fillStyle = e; g.fillRect(0, 0, S, S);
}

// ---------------------------------------------------------------- materials & props
const M = {
  bean: new THREE.MeshStandardMaterial({ color: 0x4a2a16, roughness: 0.36 }),
  ceramic: new THREE.MeshPhysicalMaterial({ color: 0xe8e1d6, roughness: 0.22, clearcoat: 1, clearcoatRoughness: 0.08 }),
  steel: new THREE.MeshStandardMaterial({ color: 0xdfe3e8, metalness: 1, roughness: 0.2 }),
  brushed: new THREE.MeshStandardMaterial({ color: 0xb9bec6, metalness: 1, roughness: 0.38 }),
  black: new THREE.MeshStandardMaterial({ color: 0x141416, roughness: 0.45, metalness: 0.2 }),
  espresso: new THREE.MeshPhysicalMaterial({ color: 0x3a1a0a, roughness: 0.12, clearcoat: 1, emissive: 0x120603 }),
  milk: new THREE.MeshPhysicalMaterial({ color: 0xfaf3e8, roughness: 0.25, clearcoat: 0.6, emissive: 0x2a2620 }),
  led: new THREE.MeshBasicMaterial({ color: new THREE.Color(0.4, 1.4, 4.0), toneMapped: false }),
  bulb: new THREE.MeshBasicMaterial({ color: new THREE.Color(5, 3.2, 1.6), toneMapped: false }),
};

function makeBeanGeo() {
  const g = new THREE.SphereGeometry(1, 28, 20);
  const p = g.attributes.position, v = new THREE.Vector3();
  for (let i = 0; i < p.count; i++) {
    v.fromBufferAttribute(p, i);
    let z = v.z * 0.46;
    if (v.z > 0) {
      const d = v.x - 0.13 * Math.sin(v.y * 3.2);
      z -= 0.3 * Math.exp(-(d * d) / 0.01) * v.z;
    }
    p.setXYZ(i, v.x * 0.64, v.y * 0.86, z);
  }
  g.computeVertexNormals();
  g.scale(0.1, 0.1, 0.1);
  return g;
}
const beanGeo = makeBeanGeo();

function beanField(n, seed, mat = M.bean) {
  const mesh = new THREE.InstancedMesh(beanGeo, mat, n);
  const R = rng(seed), col = new THREE.Color();
  for (let i = 0; i < n; i++) mesh.setColorAt(i, col.setHSL(0.06 + R() * 0.02, 0.55, 0.42 + R() * 0.2));
  mesh.castShadow = mesh.receiveShadow = true;
  return mesh;
}

const dummy = new THREE.Object3D();
const tmpQ = new THREE.Quaternion();

// cup inner wall radius at height y (matches lathe profile below)
function rIn(y) {
  if (y < 0.25) return lerp(0.28, 0.36, range(y, 0.06, 0.25));
  return lerp(0.36, 0.41, range(y, 0.25, 0.52));
}

function makeCup(surfaceTex) {
  const cup = new THREE.Group();
  const prof = [[0, 0], [0.3, 0], [0.33, 0.02], [0.4, 0.25], [0.45, 0.55], [0.47, 0.58], [0.44, 0.585], [0.41, 0.52], [0.36, 0.25], [0.28, 0.06], [0, 0.06]]
    .map(([x, y]) => new THREE.Vector2(x, y));
  const body = new THREE.Mesh(new THREE.LatheGeometry(prof, 72), M.ceramic);
  const handle = new THREE.Mesh(new THREE.TorusGeometry(0.15, 0.035, 16, 40, Math.PI * 1.25), M.ceramic);
  handle.position.set(0.47, 0.33, 0);
  handle.rotation.z = -Math.PI * 0.62;
  const sprof = [[0, 0], [0.55, 0], [0.74, 0.05], [0.79, 0.085], [0.76, 0.09], [0.6, 0.045], [0.34, 0.035], [0, 0.035]]
    .map(([x, y]) => new THREE.Vector2(x, y));
  const saucer = new THREE.Mesh(new THREE.LatheGeometry(sprof, 72), M.ceramic);
  const surf = new THREE.Mesh(new THREE.CircleGeometry(1, 72), new THREE.MeshPhysicalMaterial({ map: surfaceTex, roughness: 0.45, clearcoat: 0.25, clearcoatRoughness: 0.3 }));
  surf.rotation.x = -Math.PI / 2;
  const inner = new THREE.Group();
  inner.position.y = 0.035;
  inner.add(body, handle, surf);
  cup.add(saucer, inner);
  for (const m of [body, handle, saucer]) { m.castShadow = true; m.receiveShadow = true; }
  surf.receiveShadow = true;
  cup.setLevel = (y) => { surf.position.y = y; surf.scale.setScalar(rIn(y)); surf.visible = y > 0.065; };
  cup.levelWorld = () => inner.localToWorld(surf.position.clone());
  cup.setLevel(0.06);
  return cup;
}

function makeSteam(n, seed, { height = 1.1, spread = 0.07, size = 0.5 } = {}) {
  const group = new THREE.Group();
  const R = rng(seed), puffs = [];
  for (let i = 0; i < n; i++) {
    const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: steamTex, transparent: true, depthWrite: false, color: 0xfff4ea }));
    puffs.push({ sp, off: R(), speed: 0.18 + R() * 0.12, phase: R() * 10, dir: R() > 0.5 ? 1 : -1, drift: (R() - 0.5) * 0.2 });
    group.add(sp);
  }
  group.update = (t, intensity = 1) => {
    for (const p of puffs) {
      const ph = fract(t * p.speed + p.off);
      p.sp.position.set(Math.sin(ph * 5 + p.phase) * spread + p.drift * ph, ph * height, Math.cos(ph * 4 + p.phase) * spread * 0.6);
      p.sp.scale.setScalar((0.1 + ph * size));
      p.sp.material.opacity = Math.pow(Math.sin(ph * Math.PI), 1.5) * 0.32 * intensity;
      p.sp.material.rotation = p.phase + ph * 1.6 * p.dir;
    }
  };
  return group;
}

function makeBokeh(n, seed, box, colors, size = [0.15, 0.5], opacity = 0.35) {
  const g = new THREE.Group(), R = rng(seed);
  for (let i = 0; i < n; i++) {
    const s = new THREE.Sprite(new THREE.SpriteMaterial({
      map: bokehTex, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
      color: colors[Math.floor(R() * colors.length)], opacity: opacity * (0.4 + R() * 0.6),
    }));
    s.position.set(lerp(box[0], box[1], R()), lerp(box[2], box[3], R()), lerp(box[4], box[5], R()));
    s.scale.setScalar(lerp(size[0], size[1], R()));
    s.userData.ph = R() * 6;
    g.add(s);
  }
  g.update = (t) => g.children.forEach((s) => (s.material.opacity = s.userData.o ??= s.material.opacity, s.material.opacity = s.userData.o * (0.75 + 0.25 * Math.sin(t * 0.8 + s.userData.ph))));
  return g;
}

function points(n, seed, color, size, place) {
  const R = rng(seed), pos = new Float32Array(n * 3), base = [];
  for (let i = 0; i < n; i++) base.push(place(R));
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  const mat = new THREE.PointsMaterial({ color, size, map: softDot, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false });
  const pts = new THREE.Points(geo, mat);
  pts.frustumCulled = false;
  pts.base = base;
  pts.write = (fn) => { for (let i = 0; i < n; i++) { const v = fn(base[i], i); pos.set([v[0], v[1], v[2]], i * 3); } geo.attributes.position.needsUpdate = true; };
  return pts;
}

// ---------------------------------------------------------------- camera rig
function rig(posKeys, lookKeys) {
  const pc = new THREE.CatmullRomCurve3(posKeys.map((a) => V(...a)), false, 'centripetal');
  const lc = new THREE.CatmullRomCurve3(lookKeys.map((a) => V(...a)), false, 'centripetal');
  const lp = new THREE.Vector3();
  return (u, t, shake = 0.004) => {
    camera.position.copy(pc.getPoint(clamp(u)));
    camera.position.x += shake * (Math.sin(t * 1.3) + 0.5 * Math.sin(t * 2.9));
    camera.position.y += shake * (Math.sin(t * 1.7 + 1) + 0.5 * Math.sin(t * 3.3));
    camera.lookAt(lc.getPoint(clamp(u), lp));
  };
}

// ---------------------------------------------------------------- shots
// fonts must be loaded before any shot draws text into a canvas texture
await Promise.all(['700 italic 50px Poppins', '700 50px Poppins', '600 20px Poppins', '800 20px Poppins', '400 20px Poppins'].map((f) => document.fonts.load(f)));
const shots = [];
function shot(name, start, end, build) {
  const group = new THREE.Group();
  group.visible = false;
  scene.add(group);
  const s = { name, start, end, group, env: 1, exposure: 1, ...build(group) };
  shots.push(s);
  return s;
}

// Shared drifting dust, lit by bloom
const dust = points(900, 11, new THREE.Color(1.2, 0.95, 0.7), 0.012, (R) => [lerp(-8, 8, R()), lerp(-3, 4.5, R()), lerp(-4, 3, R()), R() * 6]);
dust.material.opacity = 0.55;
scene.add(dust);

// ---- 1. INTRO — a vortex of beans in the dark (0–9s)
shot('intro', 0, 9, (g) => {
  const N = 700, beans = beanField(N, 1), R = rng(2), data = [];
  for (let i = 0; i < N; i++) {
    data.push({ r: 0.45 + Math.pow(R(), 0.7) * 3.6, a: R() * Math.PI * 2, y: R() * 14 - 8, axis: V(R() - 0.5, R() - 0.5, R() - 0.5).normalize(), spin: (R() - 0.5) * 4, s: 0.8 + R() * 0.5 });
  }
  g.add(beans);
  g.add(new THREE.HemisphereLight(0x6f86b0, 0x1a0e06, 0.35));
  const key = new THREE.SpotLight(0xffb070, 260, 30, 0.7, 0.8, 1.6);
  key.position.set(2, 9, 3); g.add(key, key.target);
  const rim = new THREE.DirectionalLight(0x3d8ef0, 3.5); rim.position.set(-4, -1, -6); g.add(rim);
  const core = new THREE.PointLight(0xff9a4a, 14, 7, 1.6); g.add(core);
  const bokeh = makeBokeh(26, 5, [-6, 6, -6, 5, -9, -5], [0xffa860, 0x3d8ef0, 0xffd2a0], [0.4, 1.2], 0.25);
  g.add(bokeh);
  return {
    bg: new THREE.Color(0x060509), fog: new THREE.FogExp2(0x060509, 0.085), env: 0.25,
    update(lt) {
      for (let i = 0; i < N; i++) {
        const d = data[i];
        const a = d.a + lt * (0.9 / (0.5 + d.r * 0.35));
        let y = d.y - lt * 0.55; y = ((y + 8) % 14 + 14) % 14 - 8;
        dummy.position.set(Math.cos(a) * d.r, y, Math.sin(a) * d.r);
        dummy.quaternion.setFromAxisAngle(d.axis, d.spin * lt + i);
        dummy.scale.setScalar(d.s);
        dummy.updateMatrix(); beans.setMatrixAt(i, dummy.matrix);
      }
      beans.instanceMatrix.needsUpdate = true;
      const u = easeInOut(lt / 9);
      const R0 = lerp(6.2, 1.5, u), ang = 0.5 + lt * 0.22 + easeIn(range(lt, 7.8, 9)) * 2.2;
      const cy = lerp(3.4, -2.2, u);
      core.position.set(0, cy - 1, 0);
      camera.position.set(Math.sin(ang) * R0, cy, Math.cos(ang) * R0);
      camera.lookAt(0, cy - 0.7, 0);
      bokeh.update(lt);
    },
  };
});

// ---- 2. ROAST — slow-motion hero bean falls onto a glowing pile (9–19s)
shot('roast', 9, 19, (g) => {
  const mound = (r) => 0.95 * Math.pow(clamp(1 - r / 2.8), 1.6);
  const NP = 1100, pile = beanField(NP, 3), R = rng(4);
  for (let i = 0; i < NP; i++) {
    const r = Math.sqrt(R()) * 2.8, a = R() * Math.PI * 2;
    dummy.position.set(Math.cos(a) * r, mound(r) - R() * 0.06, Math.sin(a) * r);
    dummy.quaternion.setFromAxisAngle(V(R() - 0.5, R() - 0.5, R() - 0.5).normalize(), R() * 6);
    dummy.scale.setScalar(0.85 + R() * 0.4);
    dummy.updateMatrix(); pile.setMatrixAt(i, dummy.matrix);
  }
  g.add(pile);
  const NF = 160, fall = beanField(NF, 5), fd = [];
  for (let i = 0; i < NF; i++) { const r = Math.sqrt(R()) * 1.6; fd.push({ r, a: R() * 6.28, off: R(), axis: V(R(), R(), R()).normalize(), sp: 0.3 + R() * 0.2 }); }
  g.add(fall);
  const hero = new THREE.Mesh(beanGeo, M.bean); hero.castShadow = true; hero.scale.setScalar(1.15); g.add(hero);
  const floor = new THREE.Mesh(new THREE.CircleGeometry(12, 48), new THREE.MeshStandardMaterial({ color: 0x120a06, roughness: 0.6, metalness: 0.4 }));
  floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; g.add(floor);
  const embers = points(380, 6, new THREE.Color(3, 1.1, 0.3), 0.035, (R) => [Math.sqrt(R()) * 3, R() * 6.28, R(), 0.2 + R() * 0.4]);
  g.add(embers);
  g.add(new THREE.HemisphereLight(0x405070, 0x2a1206, 0.3));
  const key = new THREE.SpotLight(0xffc48a, 160, 20, 0.55, 0.7, 1.5);
  key.position.set(-2.5, 6, 2.5); key.castShadow = true; key.shadow.mapSize.set(1024, 1024); key.shadow.bias = -0.0005;
  g.add(key, key.target);
  const glow1 = new THREE.PointLight(0xff5a14, 26, 7, 1.6); glow1.position.set(1.8, 0.35, 1.6);
  const glow2 = new THREE.PointLight(0xff7a2a, 18, 7, 1.6); glow2.position.set(-2, 0.3, -1.2);
  const rim = new THREE.DirectionalLight(0x5a9cff, 2.6); rim.position.set(1, 2, -6);
  g.add(glow1, glow2, rim);
  const bokeh = makeBokeh(24, 9, [-5, 5, 0.5, 4, -7, -4], [0xff8a3a, 0xffc070], [0.3, 0.9], 0.3);
  g.add(bokeh);
  const heroPos = new THREE.Vector3();
  return {
    bg: new THREE.Color(0x0c0604), fog: new THREE.FogExp2(0x0c0604, 0.07), env: 0.35,
    update(lt) {
      for (let i = 0; i < NF; i++) {
        const d = fd[i], ph = fract(lt * d.sp + d.off);
        const y = lerp(4.5, mound(d.r), ph * ph);
        dummy.position.set(Math.cos(d.a) * d.r, y, Math.sin(d.a) * d.r);
        dummy.quaternion.setFromAxisAngle(d.axis, lt * 3 + i);
        dummy.scale.setScalar(ph > 0.97 ? 0 : 1);
        dummy.updateMatrix(); fall.setMatrixAt(i, dummy.matrix);
      }
      fall.instanceMatrix.needsUpdate = true;
      embers.write(([r, a, off, sp]) => {
        const ph = fract(lt * sp * 0.25 + off), aa = a + ph * 2;
        return [Math.cos(aa) * r * (1 + ph * 0.3), ph * 4.2, Math.sin(aa) * r * (1 + ph * 0.3)];
      });
      // hero bean: slow-mo fall + settle
      const fallU = easeOut(range(lt, 0, 8.2));
      heroPos.set(0.25 * Math.sin(lt * 0.4), lerp(3.4, mound(0.15) + 0.07, fallU), 0.15);
      hero.position.copy(heroPos);
      hero.quaternion.setFromAxisAngle(V(0.3, 1, 0.5).normalize(), (1 - Math.pow(1 - fallU, 2)) * 7);
      const pull = easeInOut(range(lt, 6.6, 10));
      const a = 0.4 + lt * 0.1, dist = lerp(0.62, 3.6, pull);
      camera.position.set(heroPos.x + Math.sin(a) * dist, heroPos.y + lerp(0.02, 1.4, pull), heroPos.z + Math.cos(a) * dist);
      camera.lookAt(heroPos.x, heroPos.y - pull * 0.25, heroPos.z);
      glow1.intensity = 26 + 6 * Math.sin(lt * 7) * Math.sin(lt * 3.1);
      bokeh.update(lt);
    },
  };
});

// ---- 3. ESPRESSO — machine, double-spout pour, rising crema (19–31s)
shot('espresso', 19, 31, (g) => {
  const box = (w, h, d, mat, x, y, z) => { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat); m.position.set(x, y, z); m.castShadow = m.receiveShadow = true; g.add(m); return m; };
  const cyl = (r, h, mat, x, y, z, seg = 48) => { const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, seg), mat); m.position.set(x, y, z); m.castShadow = true; g.add(m); return m; };
  const counter = new THREE.Mesh(new THREE.BoxGeometry(8, 0.2, 3), new THREE.MeshStandardMaterial({ map: woodTex(21, [70, 42, 24], [2, 1]), roughness: 0.45 }));
  counter.position.set(0, -0.1, 0); counter.receiveShadow = true; g.add(counter);
  box(1.8, 0.2, 1.3, M.brushed, 0, 0.1, 0);
  box(1.2, 0.05, 0.75, M.black, 0, 0.225, 0.25);
  box(1.8, 1.6, 0.6, M.brushed, 0, 1.0, -0.35);
  box(1.8, 0.4, 0.62, M.steel, 0, 1.6, 0.24);
  const ledStrip = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.02, 0.02), M.led); ledStrip.position.set(0, 1.39, 0.54); g.add(ledStrip);
  cyl(0.17, 0.14, M.steel, 0, 1.33, 0.3);
  cyl(0.18, 0.12, M.steel, 0, 1.2, 0.3);
  const handle = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.035, 0.7, 24), M.black);
  handle.rotation.x = Math.PI / 2 - 0.1; handle.position.set(0, 1.18, 0.75); handle.castShadow = true; g.add(handle);
  for (const x of [-0.05, 0.05]) cyl(0.022, 0.08, M.steel, x, 1.12, 0.3, 16);
  // pressure gauge with brand-blue needle
  const gaugeTex = canvasTex(256, 256, (c, w) => {
    c.fillStyle = '#f4f1ea'; c.beginPath(); c.arc(128, 128, 124, 0, 7); c.fill();
    c.strokeStyle = '#222'; c.lineWidth = 4;
    for (let i = 0; i <= 12; i++) { const a = Math.PI * 0.75 + (i / 12) * Math.PI * 1.5; c.beginPath(); c.moveTo(128 + Math.cos(a) * 100, 128 + Math.sin(a) * 100); c.lineTo(128 + Math.cos(a) * 115, 128 + Math.sin(a) * 115); c.stroke(); }
    c.fillStyle = '#222'; c.font = '600 26px Poppins'; c.textAlign = 'center'; c.fillText('BAR', 128, 190);
  });
  const gauge = new THREE.Mesh(new THREE.CylinderGeometry(0.15, 0.15, 0.04, 48), [M.steel, new THREE.MeshStandardMaterial({ map: gaugeTex, roughness: 0.3 }), M.steel]);
  gauge.rotation.x = Math.PI / 2; gauge.position.set(0.55, 0.95, -0.03); g.add(gauge);
  const needle = new THREE.Mesh(new THREE.BoxGeometry(0.008, 0.11, 0.01), new THREE.MeshBasicMaterial({ color: 0x3d8ef0 }));
  needle.geometry.translate(0, 0.05, 0); needle.position.set(0.55, 0.95, 0.0); g.add(needle);

  const cremaTex = canvasTex(512, 512, (c) => drawCrema(c));
  const cup = makeCup(cremaTex); cup.position.set(0, 0.25, 0.3); g.add(cup);
  const steam = makeSteam(26, 31, { height: 1.0, size: 0.45 }); g.add(steam);

  const streamGeo = new THREE.CylinderGeometry(1, 0.85, 1, 20, 1, true); streamGeo.translate(0, -0.5, 0);
  const streams = [-0.05, 0.05].map((x) => { const m = new THREE.Mesh(streamGeo, M.espresso); m.position.set(x, 1.08, 0.3); g.add(m); return m; });

  g.add(new THREE.HemisphereLight(0x8090b0, 0x2a1a10, 0.15));
  const key = new THREE.SpotLight(0xffd2a8, 32, 18, 0.6, 0.8, 1.5);
  key.position.set(-2.2, 3.8, 3.2); key.target.position.set(0, 0.6, 0.3); key.castShadow = true; key.shadow.mapSize.set(1024, 1024); key.shadow.bias = -0.0004;
  g.add(key, key.target);
  const rim = new THREE.SpotLight(0x9cc8ff, 30, 14, 0.5, 0.6, 1.5); rim.position.set(2.2, 2.4, -2.5); rim.target.position.set(0, 0.8, 0.3); g.add(rim, rim.target);
  const warm = new THREE.PointLight(0xff9050, 3, 4, 1.8); warm.position.set(0.9, 0.7, 1.2); g.add(warm);
  const bokeh = makeBokeh(30, 13, [-6, 6, 0, 4.5, -8, -4], [0xffb070, 0xffd8a8, 0x3d8ef0], [0.35, 1.1], 0.28);
  g.add(bokeh);

  const move = rig(
    [[0.45, 1.16, 1.15], [0.4, 1.02, 1.5], [0.35, 0.92, 2.1], [-0.8, 1.0, 2.3], [-1.6, 1.25, 2.8], [-0.7, 1.3, 3.5]],
    [[0, 1.12, 0.3], [0, 0.98, 0.3], [0, 0.6, 0.3], [0, 0.62, 0.3], [0, 0.85, 0.15], [0, 0.95, 0.1]]);
  const spoutY = 1.08, cupBase = 0.25 + 0.035;
  return {
    bg: new THREE.Color(0x0a090c), fog: new THREE.FogExp2(0x0a090c, 0.06), env: 0.4,
    update(lt) {
      const fill = easeOut(range(lt, 1.6, 9.8));
      const level = lerp(0.06, 0.4, fill);
      cup.setLevel(level);
      cremaTex.rotation = lt * 0.04; cremaTex.center.set(0.5, 0.5);
      const surfY = cupBase + level;
      const head = Math.max(surfY, spoutY - Math.max(0, lt - 1.2) * 3.2);
      const tail = lt < 9.2 ? spoutY : spoutY - (lt - 9.2) * 3.2;
      for (const [i, s] of streams.entries()) {
        const len = tail - head;
        s.visible = lt > 1.2 && len > 0.005;
        s.position.y = tail;
        const thin = 1 - 0.55 * range(lt, 7.5, 9.2);
        s.scale.set(0.011 * thin * (1 + 0.12 * Math.sin(lt * 31 + i * 2)), Math.max(len, 0.001), 0.011 * thin);
      }
      needle.rotation.z = -(lerp(-2.2, 0.4, smooth(range(lt, 0.8, 2.5))) + 0.03 * Math.sin(lt * 9));
      steam.position.set(0, surfY + 0.08, 0.3);
      steam.update(lt, smooth(range(lt, 3, 7)));
      // camera: close on spouts → crane down the stream → orbit reveal → dive into the cup
      move(easeInOut(range(lt, 0, 11.3)), lt);
      const dive = easeIn(range(lt, 11.3, 12));
      if (dive > 0) {
        const tgt = V(0, surfY, 0.3);
        camera.position.lerp(V(0, surfY + 0.25, 0.32), dive);
        camera.lookAt(tgt);
      }
      bokeh.update(lt);
    },
  };
});

// ---- 4. LATTE ART — top-down pour, rosetta blooms into a heart (31–41s)
shot('latte', 31, 41, (g) => {
  const table = new THREE.Mesh(new THREE.PlaneGeometry(10, 10), new THREE.MeshStandardMaterial({ map: woodTex(41, [96, 62, 38], [2, 2]), roughness: 0.55 }));
  table.rotation.x = -Math.PI / 2; table.receiveShadow = true; g.add(table);
  const S = 512, latteTex = canvasTex(S, S, (c) => drawCrema(c));
  const cup = makeCup(latteTex); cup.rotation.y = 0.5; g.add(cup);
  const steam = makeSteam(18, 44, { height: 0.8, size: 0.4 }); g.add(steam);
  // milk pitcher, pivoting about its pour lip
  const pivot = new THREE.Group(); g.add(pivot);
  const pprof = [[0.001, 0], [0.2, 0], [0.23, 0.03], [0.235, 0.35], [0.2, 0.5], [0.215, 0.56]].map(([x, y]) => new THREE.Vector2(x, y));
  const pitcher = new THREE.Mesh(new THREE.LatheGeometry(pprof, 48), new THREE.MeshStandardMaterial({ color: 0xe6e9ee, metalness: 1, roughness: 0.18, side: THREE.DoubleSide }));
  pitcher.position.set(0.215, -0.56, 0); pitcher.castShadow = true;
  const ph = new THREE.Mesh(new THREE.TorusGeometry(0.12, 0.025, 12, 24, Math.PI), M.steel); ph.rotation.z = -Math.PI / 2; ph.position.set(0.44, 0.3, 0); pitcher.add(ph);
  pivot.add(pitcher);
  const streamGeo = new THREE.CylinderGeometry(1, 1, 1, 16, 1, true);
  const stream = new THREE.Mesh(streamGeo, M.milk); g.add(stream);

  g.add(new THREE.HemisphereLight(0xb0c0e0, 0x3a2414, 0.2));
  const key = new THREE.SpotLight(0xffd8b0, 22, 14, 0.55, 0.9, 1.5);
  key.position.set(-2, 4, 1.2); key.castShadow = true; key.shadow.mapSize.set(1024, 1024); key.shadow.bias = -0.0004;
  g.add(key, key.target);
  const rim = new THREE.DirectionalLight(0x8fb8ff, 1.4); rim.position.set(3, 2, -3); g.add(rim);

  const cupBase = 0.035;
  const lip = new THREE.Vector3(), contact = new THREE.Vector3(), dir = new THREE.Vector3();
  const pxOf = (x, r) => S / 2 + (x / r) * (S / 2);
  return {
    bg: new THREE.Color(0x120c08), fog: new THREE.Fog(0x120c08, 4, 9), env: 0.35,
    update(lt) {
      const level = lerp(0.38, 0.5, smooth(range(lt, 1.5, 7.5)));
      cup.setLevel(level);
      const surfY = cupBase + level, r = rIn(level);
      // choreography of the pour
      const pull = range(lt, 6.6, 8.0);
      const cx = lt < 6.6 ? -0.06 + 0.025 * Math.sin(lt * 13) * range(lt, 3.8, 4.4) : lerp(-0.2, 0.24, easeInOut(pull));
      const lipH = lt < 3.6 ? 0.42 : lt < 6.4 ? lerp(0.42, 0.11, smooth(range(lt, 3.6, 4.2))) : lerp(0.11, 0.2, smooth(range(lt, 6.4, 6.7)));
      const enter = easeOut(range(lt, 0.2, 1.4)), exit = easeInOut(range(lt, 8.1, 9.3));
      pivot.position.set(lerp(0.9, cx - 0.04, enter) + exit * 0.9, surfY + lipH + (1 - enter) * 0.8 + exit * 0.9, 0);
      pivot.rotation.z = lerp(0.2, lerp(1.0, 1.45, range(lt, 1.5, 8)), enter) * (1 - exit * 0.8);
      const pouring = lt > 1.45 && lt < 8.1;
      pitcher.updateMatrixWorld(true);
      pitcher.localToWorld(lip.set(-0.215, 0.56, 0));
      cup.updateMatrixWorld(true);
      contact.set(cx, surfY, 0);
      dir.subVectors(contact, lip);
      const len = dir.length();
      stream.visible = pouring;
      stream.position.copy(lip).addScaledVector(dir, 0.5);
      stream.quaternion.setFromUnitVectors(V(0, 1, 0), dir.normalize());
      const th = 0.018 * smooth(range(lt, 1.45, 1.7)) * (1 - smooth(range(lt, 7.8, 8.1))) * (lt > 6.5 ? 0.7 : 1);
      stream.scale.set(th, len, th);
      // the art itself, in the cup's rotated texture space
      const ca = Math.cos(-cup.rotation.y), sa = Math.sin(-cup.rotation.y);
      const local = (x) => ca * x; // contact z = 0 so only x matters along the rotated axis
      drawLatte(latteTex.ctx, range(lt, 1.6, 6.5), pull, lt, pxOf(local(-0.2), r), pxOf(local(0.24), r));
      latteTex.needsUpdate = true;
      steam.position.set(0, surfY + 0.05, 0);
      steam.update(lt, smooth(range(lt, 7, 9.5)) * 0.9);
      // overhead camera that spirals, then tilts to a hero 3/4
      const a = 0.6 + lt * 0.07, tilt = easeInOut(range(lt, 7.6, 10));
      const hgt = lerp(2.9, 2.2, smooth(range(lt, 0, 7)));
      const top = V(-0.15, surfY + hgt, 0.12), hero = V(-1.25, 0.95, 1.35);
      camera.position.copy(top.lerp(hero, tilt));
      camera.up.set(Math.sin(a), 0, -Math.cos(a)).lerp(V(0, 1, 0), tilt).normalize();
      camera.lookAt(0, lerp(surfY, 0.35, tilt), 0);
      void sa;
    },
  };
});

// ---- 5. THE RITUAL — follow-cam tracks the cup sliding down the bar (41–51s)
shot('counter', 41, 51, (g) => {
  const counter = new THREE.Mesh(new THREE.BoxGeometry(26, 1, 1.5), [
    new THREE.MeshStandardMaterial({ color: 0x2a1a10, roughness: 0.6 }), new THREE.MeshStandardMaterial({ color: 0x2a1a10 }),
    new THREE.MeshStandardMaterial({ map: woodTex(51, [108, 70, 42], [6, 1]), roughness: 0.32 }), new THREE.MeshStandardMaterial({ color: 0x1a100a }),
    new THREE.MeshStandardMaterial({ color: 0x22150c, roughness: 0.7 }), new THREE.MeshStandardMaterial({ color: 0x22150c })]);
  counter.position.set(0, 0.5, 0); counter.receiveShadow = true; g.add(counter);
  const brick = canvasTex(1024, 512, (c, w, h) => {
    c.fillStyle = '#1e1714'; c.fillRect(0, 0, w, h); const R = rng(52);
    for (let row = 0; row < 16; row++) for (let col = 0; col < 17; col++) {
      const x = col * 64 - (row % 2) * 32, y = row * 32, v = 30 + R() * 22;
      c.fillStyle = `rgb(${v + 22},${v + 4},${v - 4})`; c.fillRect(x + 2, y + 2, 60, 28);
    }
  }, { repeat: [5, 2] });
  const wall = new THREE.Mesh(new THREE.PlaneGeometry(32, 8), new THREE.MeshStandardMaterial({ map: brick, roughness: 0.9 }));
  wall.position.set(0, 3, -2.6); wall.receiveShadow = true; g.add(wall);
  // shelves with jars and house-blend bags (left of the sign)
  const shelfMat = new THREE.MeshStandardMaterial({ map: woodTex(53, [80, 50, 30]), roughness: 0.6 });
  const label = canvasTex(256, 320, (c, w, h) => {
    c.fillStyle = '#c9a678'; c.fillRect(0, 0, w, h);
    c.fillStyle = '#14151b'; c.fillRect(0, 90, w, 150);
    c.fillStyle = '#8fd0ff'; c.font = '800 40px Poppins'; c.textAlign = 'center'; c.fillText('ISRAEL', w / 2, 166);
    c.fillStyle = '#e8d2b4'; c.font = '600 20px Poppins'; c.fillText('HOUSE BLEND', w / 2, 212);
  });
  const bagMat = [0, 0, 0, 0, new THREE.MeshStandardMaterial({ map: label, roughness: 0.8 }), 0].map((m) => m || new THREE.MeshStandardMaterial({ color: 0xb8956a, roughness: 0.85 }));
  const R = rng(54);
  for (const y of [2.0, 2.75]) {
    const sh = new THREE.Mesh(new THREE.BoxGeometry(11, 0.06, 0.45), shelfMat); sh.position.set(-6.5, y, -2.35); sh.castShadow = true; g.add(sh);
    for (let x = -11.5; x < -1.4; x += 0.42 + R() * 0.2) {
      if (R() > 0.45) {
        const bag = new THREE.Mesh(new THREE.BoxGeometry(0.26, 0.38, 0.14), bagMat); bag.position.set(x, y + 0.22, -2.3); bag.castShadow = true; g.add(bag);
      } else {
        const hh = 0.25 + R() * 0.2;
        const jar = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.1, hh, 24), new THREE.MeshPhysicalMaterial({ color: new THREE.Color().setHSL(0.07 + R() * 0.04, 0.5, 0.25 + R() * 0.15), roughness: 0.1, clearcoat: 1 }));
        jar.position.set(x, y + 0.03 + hh / 2, -2.3); g.add(jar);
      }
    }
  }
  // neon sign
  const neon = canvasTex(1024, 640, (c, w) => {
    c.textAlign = 'center';
    const glow = (fn) => { for (const [b, col] of [[40, '#3d8ef0'], [18, '#8fd0ff'], [0, '#e8f6ff']]) { c.shadowBlur = b; c.shadowColor = '#3d8ef0'; c.fillStyle = col; fn(); } };
    glow(() => { c.font = '800 200px Poppins'; c.letterSpacing = '6px'; c.fillText('Israel', w / 2, 250); });
    glow(() => { c.font = '700 84px Poppins'; c.letterSpacing = '20px'; c.fillText('COFFEE SHOP', w / 2 + 10, 370); });
    c.shadowBlur = 24; c.shadowColor = '#ff9a4a'; c.fillStyle = '#ffd2a0'; c.font = '600 46px Poppins'; c.letterSpacing = '16px';
    c.fillText('— FRESH · DAILY —', w / 2 + 8, 470);
  });
  const sign = new THREE.Mesh(new THREE.PlaneGeometry(2.3, 1.44), new THREE.MeshBasicMaterial({ map: neon, transparent: true, toneMapped: false, color: new THREE.Color(1.1, 1.1, 1.1) }));
  sign.position.set(5.75, 2.5, -2.55); g.add(sign);
  const signLight = new THREE.PointLight(0x3d8ef0, 3, 6, 1.5); signLight.position.set(5.75, 2.4, -1.6); g.add(signLight);
  // laptop — the "digital" in the coffee house
  const lap = new THREE.Group();
  const screenTex = canvasTex(512, 320, (c, w, h) => {
    c.fillStyle = '#0b1020'; c.fillRect(0, 0, w, h); const R = rng(55);
    const cols = ['#8fd0ff', '#3d8ef0', '#e8d2b4', '#f0b43a', '#9ea3c2'];
    for (let i = 0; i < 16; i++) { let x = 24 + (i % 4 ? 30 : 0) + R() * 20; for (let k = 0; k < 3; k++) { const ww = 30 + R() * 90; c.fillStyle = cols[Math.floor(R() * 5)]; c.fillRect(x, 20 + i * 18, ww, 8); x += ww + 12; } }
  });
  const base = new THREE.Mesh(new THREE.BoxGeometry(0.9, 0.03, 0.6), M.brushed); base.position.y = 0.015;
  const scr = new THREE.Mesh(new THREE.BoxGeometry(0.9, 0.58, 0.02), [M.brushed, M.brushed, M.brushed, M.brushed, new THREE.MeshBasicMaterial({ map: screenTex, color: new THREE.Color(1.3, 1.3, 1.3), toneMapped: false }), M.brushed]);
  scr.geometry.translate(0, 0.29, 0); scr.position.set(0, 0.03, -0.3); scr.rotation.x = -0.25;
  lap.add(base, scr); lap.position.set(1.7, 1.0, -0.25); lap.rotation.y = -0.5; lap.traverse((m) => (m.castShadow = true)); g.add(lap);
  // background cups along the bar
  const latteDone = canvasTex(512, 512, (c) => drawLatte(c, 1, 1, 0, 256 + (-0.2 / 0.41) * 256, 256 + (0.24 / 0.41) * 256));
  for (const [x, z, ry] of [[-8.5, -0.2, 1], [-2.6, -0.45, 2.2], [7.6, -0.3, 0.3], [-11, -0.3, 3]]) {
    const c = makeCup(latteDone); c.setLevel(0.5); c.position.set(x, 1.0, z); c.rotation.y = ry; c.scale.setScalar(0.92); g.add(c);
  }
  const hero = makeCup(latteDone); hero.setLevel(0.5); hero.rotation.y = 0.5; g.add(hero);
  const steam = makeSteam(20, 57, { height: 0.9, size: 0.42 }); g.add(steam);
  // pendant lamps + fairy lights
  for (const x of [-6.5, -3.25, 0, 3.25, 6.5]) {
    const cord = new THREE.Mesh(new THREE.CylinderGeometry(0.006, 0.006, 2.5), M.black); cord.position.set(x, 3.9, -0.15);
    const shade = new THREE.Mesh(new THREE.ConeGeometry(0.26, 0.32, 40, 1, true), new THREE.MeshStandardMaterial({ color: 0x15161a, metalness: 0.7, roughness: 0.35, side: THREE.DoubleSide }));
    shade.position.set(x, 2.58, -0.15);
    const bulb = new THREE.Mesh(new THREE.SphereGeometry(0.075, 20, 14), M.bulb); bulb.position.set(x, 2.43, -0.15);
    const pl = new THREE.PointLight(0xffb36b, 2.2, 5, 1.6); pl.position.set(x, 2.3, -0.15);
    g.add(cord, shade, bulb, pl);
  }
  const fairy = new THREE.InstancedMesh(new THREE.SphereGeometry(0.025, 8, 6), new THREE.MeshBasicMaterial({ color: new THREE.Color(4, 2.6, 1.2), toneMapped: false }), 90);
  for (let i = 0; i < 90; i++) { const x = -13 + i * 0.3, sag = 0.18 * Math.cos(((x % 3) / 3) * Math.PI * 2); dummy.position.set(x, 3.55 + sag, -2.5); dummy.scale.setScalar(1); dummy.quaternion.identity(); dummy.updateMatrix(); fairy.setMatrixAt(i, dummy.matrix); }
  g.add(fairy);
  const key = new THREE.SpotLight(0xffd0a0, 16, 12, 0.45, 0.8, 1.5); key.castShadow = true; key.shadow.mapSize.set(1024, 1024); key.shadow.bias = -0.0004;
  g.add(key, key.target);
  g.add(new THREE.HemisphereLight(0x7088b0, 0x2a180c, 0.15));
  const fg = makeBokeh(16, 58, [-8, 9, 0.6, 2.2, 2.0, 2.6], [0xffb070, 0xffe0b0], [0.25, 0.6], 0.22);
  const bg = makeBokeh(30, 59, [-10, 10, 1.5, 4, -2.4, -2.2], [0xffb070, 0x3d8ef0], [0.12, 0.35], 0.3);
  g.add(fg, bg);
  const xAt = (t) => lerp(-5.6, 4.7, easeInOut(range(t, 0.2, 8.6)));
  return {
    bg: new THREE.Color(0x0b0807), fog: new THREE.FogExp2(0x0b0807, 0.05), env: 0.3,
    update(lt) {
      const x = xAt(lt), wob = Math.sin(lt * 2.2) * 0.012 * (1 - range(lt, 7.5, 8.6));
      hero.position.set(x, 1.0, 0.05 + wob);
      hero.rotation.y = 0.5 + (x + 5.6) * 0.08;
      steam.position.set(x, 1.0 + 0.6, 0.05);
      steam.update(lt + 3, 1);
      key.position.set(x - 1.2, 3.4, 1.6); key.target.position.set(x, 1, 0);
      // follow-cam with a little lag, then a slow push-in at the hero sign
      const cx = xAt(lt - 0.35), push = easeInOut(range(lt, 7.8, 10));
      camera.position.set(cx - 0.75 + 0.15 * Math.sin(lt * 0.5) + push * 0.55, 1.62 - push * 0.08, lerp(2.8, 2.15, push));
      camera.lookAt(cx + 0.25 + push * 0.15, lerp(1.45, 1.6, push), 0);
      fg.update(lt); bg.update(lt);
    },
  };
});

// ---- 6. OUTRO — the brand cube assembles, with coffee orbiting it (51–60s)
shot('outro', 51, 60, (g) => {
  const face = (c0, c1, kind) => canvasTex(512, 512, (c, w) => {
    const gr = c.createLinearGradient(0, 0, w, w); gr.addColorStop(0, c0); gr.addColorStop(1, c1);
    c.fillStyle = gr; c.fillRect(0, 0, w, w);
    c.strokeStyle = 'rgba(223,241,255,.85)'; c.lineWidth = 12; c.lineJoin = 'round';
    c.strokeRect(64, 64, w - 128, w - 128);
    c.strokeStyle = 'rgba(223,241,255,.35)'; c.lineWidth = 6;
    if (kind === 'top') c.strokeRect(150, 150, w - 300, w - 300);
    c.fillStyle = 'rgba(11,22,48,.25)'; c.fillRect(0, 0, w, 16); c.fillRect(0, 0, 16, w);
  });
  const mat = (tex) => new THREE.MeshStandardMaterial({ map: tex, emissiveMap: tex, emissive: 0xffffff, emissiveIntensity: 0.35, roughness: 0.3, metalness: 0.15 });
  const top = mat(face('#8fd0ff', '#3d8ef0', 'top')), left = mat(face('#2a6fd6', '#123a85')), right = mat(face('#3f8cf2', '#1a4fa8'));
  const dark = new THREE.MeshStandardMaterial({ color: 0x0b1630, roughness: 0.4 });
  // isometric orientation: the (1,1,1) diagonal faces the camera, +Y up on screen
  const iso = new THREE.Quaternion().setFromUnitVectors(V(1, 1, 1).normalize(), V(0, 0, 1));
  const yUp = V(0, 1, 0).applyQuaternion(iso);
  iso.premultiply(new THREE.Quaternion().setFromAxisAngle(V(0, 0, 1), Math.atan2(yUp.x, yUp.y)));
  const xIsLeft = V(1, 0, 0).applyQuaternion(iso).x < 0;
  const cube = new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1), [xIsLeft ? left : right, dark, top, dark, xIsLeft ? right : left, dark]);
  g.add(cube);
  const glow = new THREE.Sprite(new THREE.SpriteMaterial({ map: softDot, color: 0x2a6fd6, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, opacity: 0.6 }));
  glow.position.set(0, 0.9, -1.5); glow.scale.setScalar(5); g.add(glow);
  const rings = [0, 1].map(() => { const r = new THREE.Mesh(new THREE.TorusGeometry(1.15, 0.008, 8, 160), new THREE.MeshBasicMaterial({ color: new THREE.Color(0.5, 1.6, 4), toneMapped: false, transparent: true })); g.add(r); return r; });
  const orbit = beanField(28, 61); g.add(orbit);
  const sparks = points(500, 62, new THREE.Color(1.2, 2, 4), 0.025, (R) => [1.3 + R() * 2.2, R() * 6.28, (R() - 0.5) * 1.4, 0.05 + R() * 0.15]);
  g.add(sparks);
  const steam = makeSteam(18, 63, { height: 0.9, size: 0.38, spread: 0.05 }); g.add(steam);
  g.add(new THREE.HemisphereLight(0x8fb8ff, 0x0b1630, 0.6));
  const key = new THREE.DirectionalLight(0xffffff, 2.2); key.position.set(-2, 4, 5); g.add(key);
  const warm = new THREE.PointLight(0xffa060, 6, 6, 1.5); warm.position.set(1.6, -0.2, 1.5); g.add(warm);
  const spin = new THREE.Quaternion(), axis = V(0.3, 1, 0.2).normalize();
  return {
    bg: new THREE.Color(0x04060c), fog: new THREE.FogExp2(0x04060c, 0.05), env: 0.6,
    update(lt) {
      const e = easeOut(range(lt, 0, 3.2));
      const cy = 0.95 + 0.04 * Math.sin(lt * 1.3);
      cube.position.set(0, cy, lerp(-9, 0, e));
      spin.setFromAxisAngle(axis, Math.pow(1 - e, 2) * Math.PI * 6);
      cube.quaternion.copy(iso).multiply(spin);
      cube.scale.setScalar(lerp(0.4, 1, e));
      rings.forEach((r, i) => {
        const p = easeOut(range(lt, 2.4 + i * 0.35, 4.4 + i * 0.35));
        r.position.set(0, cy, -0.3); r.scale.setScalar(lerp(0.2, 1 + i * 0.18, p));
        r.material.opacity = p * (0.8 - i * 0.3) * (1 - 0.3 * range(lt, 6, 9));
      });
      const ob = easeOut(range(lt, 1.8, 4));
      for (let i = 0; i < 28; i++) {
        const a = (i / 28) * Math.PI * 2 + lt * 0.35;
        dummy.position.set(Math.cos(a) * 1.75 * ob, cy - 0.15 + Math.sin(a * 2 + lt) * 0.04 - Math.sin(a) * 0.12, Math.sin(a) * 1.75 * ob * 0.6);
        dummy.quaternion.setFromAxisAngle(axis, a * 3 + lt);
        dummy.scale.setScalar(ob * 1.1); dummy.updateMatrix(); orbit.setMatrixAt(i, dummy.matrix);
      }
      orbit.instanceMatrix.needsUpdate = true;
      sparks.write(([r, a, y, sp]) => { const aa = a + lt * sp * 2; return [Math.cos(aa) * r, cy + y, Math.sin(aa) * r * 0.5 - 0.5]; });
      sparks.material.opacity = smooth(range(lt, 1.5, 4));
      steam.position.set(0, cy + 0.8, 0); steam.update(lt, smooth(range(lt, 3, 5)));
      glow.material.opacity = 0.55 * e;
      camera.position.set(0.15 * Math.sin(lt * 0.3), 0.55 + 0.05 * lt / 9, lerp(6.4, 5.3, easeOut(lt / 9)));
      camera.lookAt(0, 0.5, 0);
    },
  };
});

// ---------------------------------------------------------------- captions
const CAPTIONS = [
  { t0: 1.0, t1: 8.3, pos: 'center', lines: [['kicker', 'Welcome to'], ['title', 'Israel Coffee Shop'], ['rule'], ['sub', 'Where great coffee meets great ideas']] },
  { t0: 10.3, t1: 18.2, pos: 'lower', lines: [['kicker', '01 — The Bean'], ['title', 'Hand-picked.'], ['title', 'Fresh roasted.']] },
  { t0: 20.4, t1: 30.4, pos: 'lower', lines: [['kicker', '02 — The Shot'], ['title', 'Pulled to perfection'], ['sub', 'Rich  ·  Bold  ·  Velvety']] },
  { t0: 32.0, t1: 40.3, pos: 'lower', lines: [['kicker', '03 — The Craft'], ['title', 'Every cup,'], ['title', 'a little art']] },
  { t0: 42.0, t1: 50.3, pos: 'lower', lines: [['kicker', '04 — The Ritual'], ['title', 'Your daily ritual'], ['sub', 'Great coffee · Fast Wi-Fi · Space to create']] },
  { t0: 53.6, t1: 59.4, pos: 'outro', lines: [['kicker', 'Your new favorite spot'], ['brand', 'Israel'], ['brand', 'Coffee Shop'], ['sub', 'Coffee · Community · Good Vibes'], ['cta', 'Visit us today']] },
];
const capRoot = document.getElementById('captions');
for (const cap of CAPTIONS) {
  cap.el = document.createElement('div');
  cap.el.className = 'cap ' + cap.pos;
  cap.words = [];
  cap.lines.forEach(([cls, text], li) => {
    const line = document.createElement('div');
    line.className = 'line ' + cls;
    if (cls === 'rule') { line.className = 'rule'; cap.words.push({ el: line, d: li * 0.18, rule: true }); }
    else (cls === 'cta' || cls === 'kicker' ? [text] : text.split(' ')).forEach((word, wi) => {
      const w = document.createElement('span'); w.className = 'w';
      const i = document.createElement('span'); i.className = 'wi'; i.textContent = word;
      w.append(i); line.append(w, ' ');
      cap.words.push({ el: i, d: li * 0.18 + wi * 0.08 });
    });
    cap.el.append(line);
  });
  capRoot.append(cap.el);
}
function updateCaptions(t) {
  for (const c of CAPTIONS) {
    const on = t > c.t0 - 0.1 && t < c.t1 + 0.1;
    c.el.style.opacity = on ? 1 : 0;
    if (!on) continue;
    const out = easeIn(range(t, c.t1 - 0.55, c.t1));
    c.el.style.filter = out > 0.01 ? `blur(${out * 10 * stageScale}px)` : 'none';
    c.el.style.opacity = 1 - out;
    const base = c.pos === 'center' ? 'translateY(-50%) ' : '';
    c.el.style.transform = base + `translateY(${-out * 4}cqh)`;
    for (const w of c.words) {
      const p = easeOut(range(t, c.t0 + w.d, c.t0 + w.d + 0.75));
      if (w.rule) w.el.style.transform = `scaleX(${p})`;
      else w.el.style.transform = `translateY(${(1 - p) * 110}%)`;
    }
  }
}

// ---------------------------------------------------------------- transitions & finishing
const $ = (id) => document.getElementById(id);
const fxBlack = $('black'), fxFlash = $('flash'), fxLeak = $('leak'), bug = $('bug'), grain = $('grain');
const grainTex = document.createElement('canvas'); grainTex.width = grainTex.height = 256;
{ const c = grainTex.getContext('2d'), d = c.createImageData(256, 256), R = rng(99); for (let i = 0; i < d.data.length; i += 4) { const v = R() * 255; d.data[i] = d.data[i + 1] = d.data[i + 2] = v; d.data[i + 3] = 255; } c.putImageData(d, 0, 0); }
grain.style.backgroundImage = `url(${grainTex.toDataURL()})`;

function updateFX(t) {
  let black = 1 - smooth(range(t, 0, 1.3));
  black = Math.max(black, smooth(range(t, 58.4, 60)), bump(t, 19, 0.36), bump(t, 51, 0.42));
  fxBlack.style.opacity = black;
  fxFlash.style.opacity = 0.95 * bump(t, 9, 0.16) + 0.5 * bump(t, 31, 0.1);
  const blur = (10 * bump(t, 9, 0.28) + 14 * bump(t, 31, 0.2) + 7 * bump(t, 41, 0.3)) * stageScale;
  canvas.style.filter = blur > 0.1 ? `blur(${blur}px)` : 'none';
  fxLeak.style.opacity = 0.9 * bump(t, 41, 0.55) + 0.45 * bump(t, 19.25, 0.4);
  fxLeak.style.transform = `translateX(${lerp(-70, 70, range(t, 40.2, 41.9))}%) scale(1.4)`;
  bug.style.opacity = 0.85 * smooth(range(t, 10, 11)) * (1 - smooth(range(t, 49.5, 50.5)));
  const f = Math.floor(t * 30);
  grain.style.backgroundPosition = `${(f * 73) % 256}px ${(f * 151) % 256}px`;
}

// ---------------------------------------------------------------- main
function renderAt(t) {
  t = clamp(t, 0, DURATION - 1e-4);
  const s = shots.find((x) => t >= x.start && t < x.end) || shots.at(-1);
  for (const x of shots) x.group.visible = x === s;
  scene.background = s.bg; scene.fog = s.fog; scene.environmentIntensity = s.env;
  renderer.toneMappingExposure = s.exposure;
  camera.up.set(0, 1, 0);
  s.update(t - s.start, t);
  dust.visible = s.name !== 'roast';
  dust.write(([x, y, z, ph]) => [x + Math.sin(t * 0.13 + ph) * 0.4, y + Math.sin(t * 0.21 + ph * 2) * 0.25, z + Math.cos(t * 0.11 + ph) * 0.4]);
  updateFX(t);
  updateCaptions(t);
  composer.render();
}

window.REEL = { duration: DURATION, renderAt, ready: false };
resize();
addEventListener('resize', () => { resize(); if (!playing) renderAt(time); });

// live player
let time = +params.get('t') || 0, playing = false, last = 0, idle;
const playBtn = $('play'), scrub = $('scrub'), tc = $('tc'), ui = $('ui'), hint = $('hint');
function setPlaying(p) { playing = p; playBtn.innerHTML = p ? '&#10074;&#10074;' : '&#9654;'; hint.style.display = p ? 'none' : ''; last = performance.now(); }
function loop(now) {
  if (playing) { time += (now - last) / 1000; if (time >= DURATION) time = 0; }
  last = now;
  renderAt(time);
  scrub.value = time; tc.textContent = `${Math.floor(time / 60)}:${String(Math.floor(time % 60)).padStart(2, '0')}`;
  requestAnimationFrame(loop);
}
if (!RENDER) {
  stage.addEventListener('click', (e) => { if (!ui.contains(e.target)) setPlaying(!playing); });
  playBtn.onclick = () => setPlaying(!playing);
  scrub.oninput = () => { time = +scrub.value; };
  addEventListener('keydown', (e) => { if (e.code === 'Space') { e.preventDefault(); setPlaying(!playing); } });
  stage.addEventListener('pointermove', () => { ui.classList.remove('hide'); clearTimeout(idle); idle = setTimeout(() => ui.classList.add('hide'), 2200); });
}

window.REEL.ready = true;
if (RENDER) renderAt(time); else requestAnimationFrame(loop);
