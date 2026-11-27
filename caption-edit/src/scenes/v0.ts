import type {Scene} from '../Scenes';
import words from '../words/v0.json';
const c = (s: string) => s.toLowerCase().replace(/[^a-z0-9']/g, '');
// time (s) he says `cue`, searching from `near`
const T = (cue: string, near: number) => (words as any[]).find((x) => x.s >= near - 0.2 && c(x.w) === cue)?.s ?? near;

export const hook0 = {start: 0.4, end: 3.2, lines: ['Heard of', 'Intermittent Fasting?'] as [string, string]};
export const scenes0: Scene[] = [
  {start: 12.9, end: 15.7, bg: 'grid', title: 'THE BENEFITS', kind: 'nodes', center: {icon: 'User'},
    items: [{label: 'HEALTHIER', icon: 'Heart', at: T('healthier', 13)}, {label: 'WEIGHT LOSS', icon: 'Scale', at: T('weight', 13.8)}]},
  {start: 15.9, end: 20.1, bg: 'grid', title: 'AUTOPHAGY', kind: 'pair',
    items: [{label: 'BAD CELLS', icon: 'Bug', red: true, at: T('bad', 17.5)}, {label: 'CLEARED OUT', icon: 'Sparkles', at: T('eaten', 19)}]},
  {start: 29.7, end: 34.6, bg: 'grid', title: 'THE EATING WINDOW', kind: 'bars', items: [],
    bars: [{label: 'EAT', sub: '8-12 HOURS', h: 0.45, color: '#FFD400', at: T('eight', 30)}, {label: 'FAST', sub: 'REST OF THE DAY', h: 0.85, color: '#3b82f6', at: T('other', 32.8)}]},
  {start: 36.4, end: 41.4, bg: 'teal', title: 'MAKES IT EASIER', kind: 'cards',
    items: [{label: 'HIGH PROTEIN', icon: 'Beef', tag: 'EASIER', at: T('protein', 36.8)}, {label: 'HIGH FAT', icon: 'Egg', tag: 'EASIER', at: T('fat', 39.8)}]},
  {start: 48.0, end: 52.8, bg: 'red', title: 'WHO SHOULD SKIP IT', kind: 'cards',
    items: [{label: 'HYPOGLYCEMIC', icon: 'Activity', tag: 'AVOID FASTING', at: T('hypoglycemic', 48.5)}, {label: 'LOW BLOOD SUGAR', icon: 'Droplet', at: T('low', 49.8)}]},
  {start: 53.3, end: 57.0, bg: 'cream', title: 'EAT INSTEAD', kind: 'cards',
    items: [{label: 'EVERY 2 HOURS', icon: 'Clock', at: T('every', 53.6)}, {label: 'HIGH PROTEIN', icon: 'Beef', at: T('protein', 54.5)}, {label: 'HIGH FAT', icon: 'Egg', at: T('fat', 55.1)}]},
  {start: 60.7, end: 66.4, bg: 'grid', title: 'WHAT IT HELPS REVERSE', kind: 'nodes', center: {icon: 'HeartPulse'},
    items: [{label: 'METABOLIC SYNDROME', icon: 'Flame', at: T('metabolic', 61)}, {label: 'INSULIN RESISTANCE', icon: 'Syringe', at: T('insulin', 62)}, {label: 'DIABETES', icon: 'Stethoscope', at: T('diabetes', 63)}, {label: 'WEIGHT LOSS', icon: 'Scale', at: T('weight', 65.2)}]},
  {start: 67.7, end: 71.2, bg: 'paper', title: 'WORKS BETTER IN', kind: 'cards',
    items: [{label: 'MEN', icon: 'User', tag: 'OFTEN BETTER', at: T('men', 68)}, {label: 'WOMEN', icon: 'User', at: T('women', 68.6)}]},
  {start: 73.8, end: 79.0, bg: 'grid', title: 'GO SLOWLY IF YOU HAVE', kind: 'nodes', center: {icon: 'TriangleAlert'},
    items: [{label: 'ADRENAL ISSUES', icon: 'Zap', red: true, at: T('adrenal', 74.1)}, {label: 'HIGH STRESS', icon: 'Brain', red: true, at: T('stressed', 75.8)}]},
  {start: 84.3, end: 88.0, bg: 'cream', title: 'BEFORE A LONG FAST', kind: 'cards',
    items: [{label: 'REGULAR SLEEP', icon: 'Moon', at: T('sleep', 84.6)}, {label: 'TOLERATE IF', icon: 'Timer', at: T('tolerate', 86.3)}]},
];
