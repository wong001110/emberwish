import type { AppState } from './core.js';
export type DesktopAction = 'compact' | 'expand' | 'hide' | 'quit' | 'pin' | 'unpin' | 'click_through' | 'drag';
interface NativeApi {
  core: { invoke<T>(command: string, args?: Record<string, unknown>): Promise<T> };
  event: { listen<T>(name: string, handler: (event: { payload: T }) => void): Promise<() => void> };
}
declare global { interface Window { __TAURI__?: NativeApi } }
const STORAGE_KEY = 'emberwish.state.v1';
export const isNative = (): boolean => typeof window.__TAURI__?.core?.invoke === 'function';
export async function loadState(): Promise<string | null> {
  return isNative() ? window.__TAURI__!.core.invoke<string | null>('load_state') : localStorage.getItem(STORAGE_KEY);
}
/** Serial saves prevent an older asynchronous write winning. A single pending
 * snapshot coalesces input bursts; callers await all saves present before settling. */
export class StateWriter {
  private pending: string | null = null;
  private running: Promise<void> | null = null;
  constructor(
    private readonly onError: (message: string) => void,
    private readonly persist: (json: string) => Promise<unknown> = async json => {
      if (isNative()) await window.__TAURI__!.core.invoke('save_state', { json });
      else localStorage.setItem(STORAGE_KEY, json);
    },
  ) {}
  save(state: AppState): Promise<void> {
    this.pending = JSON.stringify(state);
    return this.flush();
  }
  private flush(): Promise<void> {
    if (this.running) return this.running;
    this.running = Promise.resolve().then(() => this.drain()).finally(() => {
      this.running = null;
      // A save can arrive between drain completion and this finalizer.
      if (this.pending !== null) return this.flush();
    });
    return this.running;
  }
  private async drain(): Promise<void> {
    while (this.pending !== null) {
      const json = this.pending;
      this.pending = null;
      try { await this.persist(json); }
      catch { this.onError('This change could not be saved. The ritual still works, but may not survive a restart.'); }
    }
  }
}
export async function desktop(action: DesktopAction): Promise<void> {
  if (isNative()) await window.__TAURI__!.core.invoke('desktop_action', { action });
}
export async function listenNative<T>(name: string, handler: (payload: T) => void): Promise<() => void> {
  if (!isNative()) return () => {};
  return window.__TAURI__!.event.listen<T>(name, event => handler(event.payload));
}
