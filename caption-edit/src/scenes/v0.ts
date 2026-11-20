import type {Scene} from '../Scenes';
export const hook0 = {start: 0.4, end: 3.2, lines: ['Heard of', 'Intermittent Fasting?'] as [string, string]};
export const scenes0: Scene[] = [
  {start: 9.9, end: 14.3, bg: 'grid', title: 'THE BENEFITS', kind: 'nodes', center: {icon: 'User'}, items: [{label: 'HEALTHIER', icon: 'Heart'}, {label: 'WEIGHT LOSS', icon: 'Scale'}]},
  {start: 15.0, end: 19.4, bg: 'grid', title: 'AUTOPHAGY', kind: 'pair', items: [{label: 'BAD CELLS', icon: 'Bug', red: true}, {label: 'CLEARED OUT', icon: 'Sparkles'}]},
  {start: 27.0, end: 34.4, bg: 'grid', title: 'THE EATING WINDOW', kind: 'bars', items: [], bars: [{label: 'EAT', sub: '8-12 HOURS', h: 0.45, color: '#FFD400'}, {label: 'FAST', sub: 'REST OF THE DAY', h: 0.85, color: '#3b82f6'}]},
  {start: 37.0, end: 41.2, bg: 'teal', title: 'MAKES IT EASIER', kind: 'cards', items: [{label: 'HIGH PROTEIN', icon: 'Beef', tag: 'EASIER'}, {label: 'HIGH FAT', icon: 'Egg', tag: 'EASIER'}]},
  {start: 45.0, end: 50.6, bg: 'red', title: 'WHO SHOULD SKIP IT', kind: 'cards', items: [{label: 'HYPOGLYCEMIC', icon: 'Activity', tag: 'AVOID FASTING'}, {label: 'LOW BLOOD SUGAR', icon: 'Droplet'}]},
  {start: 53.0, end: 55.8, bg: 'cream', title: 'EAT INSTEAD', kind: 'cards', items: [{label: 'EVERY 2 HOURS', icon: 'Clock'}, {label: 'HIGH PROTEIN', icon: 'Beef'}, {label: 'HIGH FAT', icon: 'Egg'}]},
  {start: 58.0, end: 65.6, bg: 'grid', title: 'WHAT IT HELPS REVERSE', kind: 'nodes', center: {icon: 'HeartPulse'}, items: [{label: 'METABOLIC SYNDROME', icon: 'Flame'}, {label: 'INSULIN RESISTANCE', icon: 'Syringe'}, {label: 'DIABETES', icon: 'Stethoscope'}, {label: 'WEIGHT LOSS', icon: 'Scale'}]},
  {start: 66.8, end: 72.0, bg: 'paper', title: 'WORKS BETTER IN', kind: 'cards', items: [{label: 'MEN', icon: 'User', tag: 'OFTEN BETTER'}, {label: 'WOMEN', icon: 'User'}]},
  {start: 74.6, end: 80.3, bg: 'grid', title: 'GO SLOWLY IF YOU HAVE', kind: 'nodes', center: {icon: 'TriangleAlert'}, items: [{label: 'ADRENAL ISSUES', icon: 'Zap', red: true}, {label: 'HIGH STRESS', icon: 'Brain', red: true}]},
  {start: 81.6, end: 87.3, bg: 'cream', title: 'BEFORE A LONG FAST', kind: 'cards', items: [{label: 'REGULAR SLEEP', icon: 'Moon'}, {label: 'TOLERATE IF', icon: 'Timer'}]},
];
