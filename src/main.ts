import { advance, cleanWish, defaults, DURATIONS, extinguish, fraction, light, remaining, restore, type AppState, type Duration } from './core.js';
import { IncenseScene } from './scene.js';
import { desktop, isNative, listenNative, loadState, StateWriter, type DesktopAction } from './platform.js';
const byId = <T extends HTMLElement>(id: string): T => {
  const el = document.getElementById(id);
  if (!el) throw new Error(`Missing interface element: ${id}`);
  return el as T;
};
const wish = byId<HTMLTextAreaElement>('wish');
const lightButton = byId<HTMLButtonElement>('light');
const statusText = byId('status-text');
const scene = new IncenseScene(byId<HTMLCanvasElement>('incense'));
const media = matchMedia('(prefers-reduced-motion: reduce)');
let state: AppState = defaults();
let nativeVisible = true;
let ready = false;
let tickTimer: number | null = null;
let audio: AudioContext | null = null;
const cleanups: (() => void)[] = [];
function notice(message: string): void { const el = byId('notice'); el.textContent = message; el.hidden = false; }
const writer = new StateWriter(notice);
const isVisible = (): boolean => nativeVisible && !document.hidden;
const save = (): Promise<void> => writer.save(state);
async function act(action: DesktopAction): Promise<boolean> {
  try { await desktop(action); return true; }
  catch { notice('That desktop action did not succeed. Your ritual is still here.'); return false; }
}
function chime(): void {
  if (!state.soundEnabled || !isVisible()) return;
  try {
    audio ??= new AudioContext();
    void audio.resume();
    const now = audio.currentTime;
    for (const [frequency, volume] of [[528, .045], [792, .017]] as const) {
      const tone = audio.createOscillator(), gain = audio.createGain();
      tone.frequency.value = frequency; tone.type = 'sine';
      gain.gain.setValueAtTime(.0001, now); gain.gain.exponentialRampToValueAtTime(volume, now + .015);
      gain.gain.exponentialRampToValueAtTime(.0001, now + 1.6);
      tone.connect(gain); gain.connect(audio.destination); tone.start(now); tone.stop(now + 1.7);
      tone.onended = () => { tone.disconnect(); gain.disconnect(); };
    }
  } catch { notice('Audio is unavailable. Your ritual will stay silent.'); }
}
function render(): void {
  const r = state.ritual, burning = r.status === 'burning';
  document.body.classList.toggle('compact', state.view === 'compact');
  if (wish.value !== state.wishDraft) wish.value = state.wishDraft;
  wish.disabled = burning || !ready;
  byId('wish-count').textContent = `${Array.from(state.wishDraft).length} / 160`;
  for (const el of document.querySelectorAll<HTMLInputElement>('input[name="duration"]')) { el.checked = Number(el.value) === state.durationMinutes; el.disabled = burning || !ready; }
  for (const el of document.querySelectorAll<HTMLButtonElement>('[data-wish]')) el.disabled = burning || !ready;
  byId<HTMLInputElement>('sound').checked = state.soundEnabled;
  byId<HTMLInputElement>('motion').checked = state.reduceMotion || media.matches;
  byId<HTMLInputElement>('motion').disabled = media.matches || !ready;
  byId<HTMLInputElement>('sound').disabled = !ready;
  byId('pin').setAttribute('aria-pressed', String(state.pinned));
  lightButton.disabled = !ready;
  lightButton.classList.toggle('burning', burning);
  byId('light-label').textContent = burning ? 'Extinguish gently' : r.status === 'idle' ? 'Light incense' : 'Light another wish';
  byId('compact-light').setAttribute('aria-label', burning ? 'Extinguish incense' : 'Light incense');
  byId('compact-light').setAttribute('title', burning ? 'Extinguish incense' : 'Light incense');
  byId('status-dot').classList.toggle('burning', burning);
  statusText.textContent = { idle: 'Ready when you are', burning: 'A wish is quietly burning', completed: 'A small ritual, complete', extinguished: 'Resting, until next time' }[r.status];
  byId('scene-label').textContent = burning ? 'A WISH, GIVEN A LITTLE SPACE' : 'YOUR QUIET CORNER';
  byId('display-wish').textContent = (r.status === 'idle' ? state.wishDraft : r.wish) || 'A little space for a little wish.';
  const displayed = r.status === 'idle' ? { ...r, durationMs: state.durationMinutes * 60000 } : r;
  byId('remaining').textContent = remaining(displayed, Date.now());
  byId<HTMLProgressElement>('progress').value = fraction(displayed, Date.now());
  scene.update(r, state.reduceMotion || media.matches, isVisible());
  if (tickTimer !== null) { clearTimeout(tickTimer); tickTimer = null; }
  if (burning && isVisible()) tickTimer = window.setTimeout(tick, 1000);
}
function tick(): void {
  tickTimer = null;
  const next = advance(state, Date.now());
  if (next !== state) { state = next; void save(); if (audio) chime(); }
  render();
}
function toggleRitual(): void {
  if (!ready) return;
  const now = Date.now();
  state = state.ritual.status === 'burning' ? extinguish(state, now) : light(state, now);
  if (state.ritual.status === 'burning') chime();
  void save(); render();
}
async function setView(view: AppState['view']): Promise<void> {
  if (!ready) return;
  if (await act(view === 'compact' ? 'compact' : 'expand')) {
    state = { ...state, view }; await save(); render();
    (view === 'compact' ? byId('expand') : lightButton).focus();
  }
}
wish.addEventListener('input', () => { if (!ready) return; state = { ...state, wishDraft: cleanWish(wish.value) }; void save(); render(); });
for (const el of document.querySelectorAll<HTMLButtonElement>('[data-wish]')) {
  el.addEventListener('click', () => { if (!ready) return; state = { ...state, wishDraft: cleanWish(el.dataset.wish ?? '') }; void save(); render(); });
}
for (const el of document.querySelectorAll<HTMLInputElement>('input[name="duration"]')) {
  el.addEventListener('change', () => {
    const duration = Number(el.value);
    if (!ready || !DURATIONS.some(d => d === duration)) return;
    state = { ...state, durationMinutes: duration as Duration }; void save(); render();
  });
}
lightButton.addEventListener('click', toggleRitual);
byId('compact-light').addEventListener('click', toggleRitual);
for (const id of ['compact', 'compact-top']) byId(id).addEventListener('click', () => { void setView('compact'); });
byId('expand').addEventListener('click', () => { void setView('expanded'); });
for (const id of ['hide', 'compact-hide']) byId(id).addEventListener('click', async () => { await save(); await act('hide'); });
byId('pin').addEventListener('click', async () => {
  if (await act(state.pinned ? 'unpin' : 'pin')) { state = { ...state, pinned: !state.pinned }; void save(); render(); }
});
byId('pass-through').addEventListener('click', async () => {
  await save();
  notice('Click-through mode: use the Emberwish tray icon → Show & interact to restore control.');
  await act('click_through');
});
for (const id of ['drag-handle', 'scene-label']) byId(id).addEventListener('pointerdown', event => { if (event.button === 0 && isNative()) void act('drag'); });
byId('sound').addEventListener('change', () => { if (!ready) return; state = { ...state, soundEnabled: byId<HTMLInputElement>('sound').checked }; chime(); void save(); render(); });
byId('motion').addEventListener('change', () => { if (!ready) return; state = { ...state, reduceMotion: byId<HTMLInputElement>('motion').checked }; void save(); render(); });
media.addEventListener('change', render);
document.addEventListener('visibilitychange', tick);
window.addEventListener('pagehide', () => { scene.destroy(); if (tickTimer !== null) clearTimeout(tickTimer); for (const cleanup of cleanups) cleanup(); if (audio) void audio.close(); });
async function start(): Promise<void> {
  document.body.classList.toggle('native', isNative());
  try {
    const restored = restore(await loadState(), Date.now()); state = restored.state;
    if (restored.warning) notice(restored.warning);
  } catch { notice('Saved preferences could not be read. Changes may not persist until storage is available.'); }
  if (isNative()) {
    try {
      cleanups.push(await listenNative<boolean>('desktop-visibility', visible => { nativeVisible = visible; tick(); }));
      cleanups.push(await listenNative<null>('request-hide', async () => { await save(); await act('hide'); }));
      await desktop(state.view === 'compact' ? 'compact' : 'expand');
      await desktop(state.pinned ? 'pin' : 'unpin');
    } catch { notice('Some desktop controls are unavailable. The ritual remains usable.'); }
  }
  ready = true; render();
}
render();
void start();
