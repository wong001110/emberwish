/** Pure domain state: rendering speed never determines burn progress. */
export const DURATIONS = [5, 15, 30] as const;
export const MAX_WISH = 160;
export const MAX_STATE_BYTES = 16_384;
export type Duration = typeof DURATIONS[number];
export type RitualStatus = 'idle' | 'burning' | 'completed' | 'extinguished';
export interface Ritual {
  status: RitualStatus;
  startedAt: number | null;
  endedAt: number | null;
  durationMs: number;
  wish: string;
}
export interface AppState {
  version: 1;
  wishDraft: string;
  durationMinutes: Duration;
  soundEnabled: boolean;
  reduceMotion: boolean;
  pinned: boolean;
  view: 'expanded' | 'compact';
  ritual: Ritual;
}
export const cleanWish = (text: string): string => Array.from(text.replace(/[\u0000-\u0008\u000b-\u001f\u007f]/g, '')).slice(0, MAX_WISH).join('');
export function defaults(): AppState {
  return { version: 1, wishDraft: '', durationMinutes: 15, soundEnabled: false,
    reduceMotion: false, pinned: false, view: 'expanded',
    ritual: { status: 'idle', startedAt: null, endedAt: null, durationMs: 900_000, wish: '' } };
}
const finiteTime = (x: unknown): x is number => typeof x === 'number' && Number.isSafeInteger(x) && x >= 0;
const validDuration = (x: unknown): x is Duration => DURATIONS.some(d => d === x);
const object = (x: unknown): x is Record<string, unknown> => !!x && typeof x === 'object' && !Array.isArray(x);
export function advance(state: AppState, now: number): AppState {
  if (!finiteTime(now)) throw new Error('A valid observation time is required');
  const r = state.ritual;
  if (r.status !== 'burning' || r.startedAt === null || now < r.startedAt + r.durationMs) return state;
  return { ...state, ritual: { ...r, status: 'completed', endedAt: r.startedAt + r.durationMs } };
}
export function light(state: AppState, now: number): AppState {
  if (!finiteTime(now)) throw new Error('A valid start time is required');
  const current = advance(state, now);
  if (current.ritual.status === 'burning') return current;
  return { ...current, ritual: { status: 'burning', startedAt: now, endedAt: null,
    durationMs: current.durationMinutes * 60_000, wish: cleanWish(current.wishDraft).trim() } };
}
export function extinguish(state: AppState, now: number): AppState {
  const current = advance(state, now);
  if (current.ritual.status !== 'burning' || current.ritual.startedAt === null) return current;
  return { ...current, ritual: { ...current.ritual, status: 'extinguished', endedAt: Math.max(current.ritual.startedAt, now) } };
}
export function fraction(ritual: Ritual, now: number): number {
  if (ritual.startedAt === null || ritual.status === 'idle') return 0;
  const at = ritual.endedAt ?? now;
  return Math.max(0, Math.min(1, (at - ritual.startedAt) / ritual.durationMs));
}
export function remaining(ritual: Ritual, now: number): string {
  const seconds = Math.ceil(Math.max(0, ritual.durationMs * (1 - fraction(ritual, now))) / 1000);
  return `${Math.floor(seconds / 60).toString().padStart(2, '0')}:${(seconds % 60).toString().padStart(2, '0')}`;
}
export function restore(raw: string | null, now: number): { state: AppState; warning: string | null } {
  const fallback = defaults();
  if (raw === null) return { state: fallback, warning: null };
  try {
    if (new TextEncoder().encode(raw).length > MAX_STATE_BYTES) throw new Error('Saved state is too large');
    const parsed: unknown = JSON.parse(raw);
    if (!object(parsed) || parsed.version !== 1) throw new Error('Saved state is from an unsupported version');
    if (!validDuration(parsed.durationMinutes) || typeof parsed.wishDraft !== 'string' ||
        typeof parsed.soundEnabled !== 'boolean' || typeof parsed.reduceMotion !== 'boolean' ||
        typeof parsed.pinned !== 'boolean' || !['expanded', 'compact'].includes(String(parsed.view))) {
      throw new Error('Saved preferences are not valid');
    }
    const r = parsed.ritual;
    if (!object(r) || !['idle', 'burning', 'completed', 'extinguished'].includes(String(r.status)) ||
        typeof r.wish !== 'string' || !DURATIONS.some(d => d * 60_000 === r.durationMs)) throw new Error('Saved ritual is not valid');
    if (r.status === 'idle') {
      if (r.startedAt !== null || r.endedAt !== null) throw new Error('Idle ritual contains timestamps');
    } else {
      if (!finiteTime(r.startedAt) || r.startedAt > now) throw new Error('Saved start time is in the future or invalid');
      if (r.status === 'burning' && r.endedAt !== null) throw new Error('Burning ritual has an end time');
      if (r.status !== 'burning' && (!finiteTime(r.endedAt) || r.endedAt < r.startedAt || r.endedAt > now || r.endedAt > r.startedAt + Number(r.durationMs))) throw new Error('Saved end time is invalid');
      if (r.status === 'completed' && r.endedAt !== r.startedAt + Number(r.durationMs)) throw new Error('Completed ritual has incomplete timing');
    }
    const state: AppState = { version: 1, wishDraft: cleanWish(parsed.wishDraft), durationMinutes: parsed.durationMinutes,
      soundEnabled: parsed.soundEnabled, reduceMotion: parsed.reduceMotion, pinned: parsed.pinned,
      view: parsed.view as AppState['view'], ritual: { status: r.status as RitualStatus, startedAt: r.startedAt as number | null,
        endedAt: r.endedAt as number | null, durationMs: r.durationMs as number, wish: cleanWish(r.wish) } };
    return { state: advance(state, now), warning: null };
  } catch (error) {
    return { state: fallback, warning: `${error instanceof Error ? error.message : 'Could not read saved state'}. A fresh ritual is ready; the saved file is not replaced until you make a change.` };
  }
}
export const shouldAnimate = (burning: boolean, visible: boolean, reduced: boolean): boolean => burning && visible && !reduced;
