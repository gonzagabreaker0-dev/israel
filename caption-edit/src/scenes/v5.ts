import type {Scene} from '../Scenes';
import words from '../words/v5.json';
const c = (s: string) => s.toLowerCase().replace(/[^a-z0-9']/g, '');
const T = (cue: string, near: number) => (words as any[]).find((x) => x.s >= near - 0.2 && c(x.w) === cue)?.s ?? near;

export const hook5 = {start: 0.4, end: 3.6, lines: ['Start your day', 'With Gratitude'] as [string, string]};
export const scenes5: Scene[] = [
  {start: 20.7, end: 28.9, bg: 'grid', title: 'AT HOME', kind: 'nodes', center: {icon: 'Heart'}, items: [
    {label: 'ROOF OVER YOUR HEAD', icon: 'House', at: T('roof', 21)}, {label: 'WARM BED', icon: 'BedDouble', at: T('bed', 22.9)},
    {label: 'SOMEONE SPECIAL', icon: 'UserRound', at: T('person', 24.3)}, {label: 'FAMILY', icon: 'Users', at: T('family', 27.5)}]},
  {start: 29.0, end: 34.9, bg: 'grid', title: 'EVERYDAY BLESSINGS', kind: 'nodes', center: {icon: 'Heart'}, items: [
    {label: 'PEOPLE WHO LOVE YOU', icon: 'HandHeart', at: T('love', 29.3)}, {label: 'FOOD ON YOUR TABLE', icon: 'Utensils', at: T('food', 30.3)}, {label: 'YOUR CAR', icon: 'Car', at: T('car', 33.4)}]},
  {start: 35.1, end: 41.4, bg: 'grid', title: 'AND THE ABILITY TO GIVE', kind: 'nodes', center: {icon: 'Heart'}, items: [
    {label: 'YOUR WORK', icon: 'Briefcase', at: T('work', 35.4)}, {label: 'MONEY IN THE BANK', icon: 'Banknote', at: T('money', 37.7)}, {label: 'HELPING OTHERS', icon: 'HandHelping', at: T('things', 40)}]},
  {start: 45.2, end: 47.2, bg: 'cream', title: 'YOUR TURN', kind: 'cards', items: [{label: 'COMMENT BELOW', icon: 'MessageCircle', at: T('below', 45.4)}]},
  {start: 48.3, end: 58.7, bg: 'teal', title: 'MORNING PRAYER', kind: 'cards', items: [
    {label: 'HAND ON HEART', icon: 'HandHeart', at: T('heart', 48.8)}, {label: 'SAY A PRAYER', icon: 'Sparkles', at: T('prayer', 51)}, {label: 'THANK GOD', icon: 'Sun', at: T('god', 54)}]},
  {start: 60.0, end: 69.0, bg: 'grid', title: 'PRAY FOR OTHERS TO BE', kind: 'nodes', center: {icon: 'Users'}, items: [
    {label: 'HEALTHY', icon: 'HeartPulse', at: T('healthy', 62.5)}, {label: 'HAPPY', icon: 'Smile', at: T('happy', 64.4)}, {label: 'FIND GOD', icon: 'Sun', at: T('god', 67.4)}]},
  {start: 73.0, end: 76.6, bg: 'cream', title: 'GRATITUDE HABIT', kind: 'pair', items: [
    {label: 'WRITE IT DOWN', icon: 'PenLine', at: T('write', 73.1)}, {label: 'SAY IT OUT LOUD', icon: 'Volume2', at: T('loud', 75)}]},
  {start: 77.0, end: 80.6, bg: 'teal', title: 'MOVE YOUR BODY', kind: 'cards', items: [{label: 'MOVE IN THE MORNING', icon: 'Activity', at: T('move', 76.9)}]},
  {start: 81.8, end: 88.7, bg: 'red', title: 'MORNING MINDSET', kind: 'cards', items: [
    {label: 'NEGATIVE SELF-TALK', icon: 'Frown', tag: 'SKIP IT', at: T('negative', 82.3)}, {label: 'YOUR PHONE', icon: 'Smartphone', tag: 'SKIP IT', at: T('phone', 84)}, {label: 'POSITIVE WORDS', icon: 'Smile', at: T('positive', 84.5)}]},
  {start: 94.9, end: 100.7, bg: 'grid', title: 'CHANGE YOUR FOCUS', kind: 'pair', items: [
    {label: 'EXPECTATIONS', icon: 'Target', red: true, at: T('expectations', 95.4)}, {label: 'APPRECIATION', icon: 'Sparkles', at: T('appreciations', 99)}]},
  {start: 101.9, end: 104.5, bg: 'cream', title: 'AS TONY ROBBINS SAYS', kind: 'cards', items: [{label: 'GRATITUDE > EXPECTATION', icon: 'Quote', at: T('robbins', 102.2)}]},
  {start: 105.2, end: 112.9, bg: 'grid', title: 'HAPPINESS IS A CHOICE', kind: 'cards', items: [
    {label: 'UNHAPPY', icon: 'Frown', tag: 'NOT WITH GRATITUDE', at: T('unhappy', 105.4)}, {label: 'GRATITUDE', icon: 'Heart', at: T('gratitude', 107.2)}, {label: 'CHOOSE HAPPY', icon: 'Smile', at: T('happiness', 108.5)}]},
  {start: 113.9, end: 116.9, bg: 'cream', title: 'COMING UP', kind: 'cards', items: [{label: 'THANKSGIVING NEXT WEEK', icon: 'Gift', at: T('thanksgiving', 114)}]},
];
