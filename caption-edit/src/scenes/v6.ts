import words from '../words/v6.json';
import sides from './v6.sides.json';
const c = (s: string) => s.toLowerCase().replace(/[^a-z0-9']/g, '');
const T = (cue: string, near: number) => (words as any[]).find((x) => x.s >= near - 0.2 && c(x.w) === cue)?.s ?? near;

export type IconCue = {at: number; dur: number; icon: string; label?: string; side: 'L' | 'R'};
export const KEYS6 = ['hormetic', 'cold', 'plunges', 'showers', 'infrared', 'sauna', '130', '150', 'degrees', 'sweat', 'better', 'sweden', '10', 'years', 'longer', 'toxins', 'hearty', 'half', 'hour', 'week', 'marketplace', 'inexpensive', 'healthy', 'favorite', 'often', 'helpful'];
const raw6: IconCue[] = [
  {at: T('cold', 7.4), dur: 1.5, icon: 'Snowflake', side: 'L'},
  {at: T('plunges', 8.2), dur: 1.4, icon: 'Waves', side: 'R'},
  {at: T('showers', 9.0), dur: 1.8, icon: 'ShowerHead', side: 'L'},
  {at: T('infrared', 12.5), dur: 2.0, icon: 'Flame', label: 'INFRARED SAUNA', side: 'R'},
  {at: T('130', 23.4), dur: 2.2, icon: 'Thermometer', label: '130-150°F', side: 'L'},
  {at: T('sweat', 26.2), dur: 1.6, icon: 'Droplets', side: 'R'},
  {at: T('better', 29.2), dur: 1.7, icon: 'Smile', side: 'L'},
  {at: T('sweden', 31.7), dur: 1.9, icon: 'Globe', label: 'SWEDEN', side: 'R'},
  {at: T('10', 36.1), dur: 1.9, icon: 'HeartPulse', label: '+10 YEARS', side: 'L'},
  {at: T('toxins', 38.0), dur: 1.7, icon: 'FlaskConical', label: 'TOXINS OUT', side: 'R'},
  {at: T('hearty', 40.8), dur: 1.4, icon: 'Dumbbell', side: 'L'},
  {at: T('half', 45.0), dur: 1.6, icon: 'Clock', label: '30 MINUTES', side: 'R'},
  {at: T('twice', 46.5), dur: 1.7, icon: 'CalendarDays', label: '1-2x A WEEK', side: 'L'},
  {at: T('facebook', 48.6), dur: 1.4, icon: 'ShoppingBag', label: 'MARKETPLACE', side: 'R'},
  {at: T('inexpensive', 49.9), dur: 1.5, icon: 'Tag', label: 'INEXPENSIVE', side: 'L'},
  {at: T('office', 51.9), dur: 1.6, icon: 'Building2', label: 'OUR OFFICE', side: 'R'},
  {at: T('healthy', 57.0), dur: 1.2, icon: 'Heart', label: 'HEALTHY', side: 'L'},
  {at: T('favorite', 58.9), dur: 1.9, icon: 'Star', label: 'YOUR FAVORITE', side: 'L'},
  {at: T('put', 58.2), dur: 6.6, icon: 'MessageCircle', label: 'COMMENT BELOW', side: 'R'},
  {at: T('often', 61.9), dur: 2.0, icon: 'Repeat', label: 'HOW OFTEN', side: 'L'},
];

export const icons6: IconCue[] = raw6.map((c, i) => ({...c, side: (sides as string[])[i] as 'L' | 'R'}));
