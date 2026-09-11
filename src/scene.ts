import { fraction, shouldAnimate, type Ritual } from './core.js';
/** One bounded Canvas scene. All geometry is original and generated locally. */
export class IncenseScene {
  private ctx: CanvasRenderingContext2D;
  private timer: number | null = null;
  private visible = true;
  private reduced = false;
  private ritual: Ritual = { status: 'idle', startedAt: null, endedAt: null, durationMs: 900000, wish: '' };
  private frames = 0;
  private observer: ResizeObserver;
  constructor(private canvas: HTMLCanvasElement) {
    const ctx = canvas.getContext('2d', { alpha: true });
    if (!ctx) throw new Error('Canvas 2D is unavailable');
    this.ctx = ctx;
    this.observer = new ResizeObserver(() => this.draw());
    this.observer.observe(canvas);
    this.draw();
  }
  update(ritual: Ritual, reduced: boolean, visible: boolean): void {
    const changed = this.ritual !== ritual || this.reduced !== reduced || this.visible !== visible;
    this.ritual = ritual; this.reduced = reduced; this.visible = visible;
    const animate = shouldAnimate(ritual.status === 'burning', visible, reduced);
    if (!animate && this.timer !== null) { window.clearTimeout(this.timer); this.timer = null; }
    if (visible && (changed || (reduced && ritual.status === 'burning'))) this.draw();
    if (animate && this.timer === null) this.schedule();
  }
  private schedule(): void {
    this.timer = window.setTimeout(() => {
      this.timer = null;
      if (!shouldAnimate(this.ritual.status === 'burning', this.visible, this.reduced)) return;
      this.draw();
      this.schedule();
    }, 1000 / 30);
  }
  destroy(): void {
    if (this.timer !== null) window.clearTimeout(this.timer);
    this.observer.disconnect();
  }
  private ellipse(x: number, y: number, rx: number, ry: number, fill: string | CanvasGradient): void {
    const c = this.ctx;
    c.beginPath(); c.ellipse(x, y, rx, ry, 0, 0, Math.PI * 2); c.fillStyle = fill; c.fill();
  }
  draw(): void {
    if (!this.visible) return;
    const c = this.ctx;
    const box = this.canvas.getBoundingClientRect();
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    const w = Math.max(1, Math.round(box.width * ratio)), h = Math.max(1, Math.round(box.height * ratio));
    if (this.canvas.width !== w || this.canvas.height !== h) { this.canvas.width = w; this.canvas.height = h; }
    c.setTransform(1, 0, 0, 1, 0, 0); c.clearRect(0, 0, w, h);
    const scale = Math.min(w / 480, h / 430);
    c.setTransform(scale, 0, 0, scale, (w - 480 * scale) / 2, (h - 430 * scale) / 2);
    const now = Date.now();
    const burning = this.ritual.status === 'burning';
    const used = fraction(this.ritual, now);
    const tip = 153 + used * 129;
    const t = this.reduced ? 0 : (now % 600000) / 1000;
    this.ellipse(240, 358, 147, 22, 'rgba(9,24,22,.23)');
    this.ellipse(240, 347, 126, 28, '#77674e');
    this.ellipse(240, 342, 126, 27, '#b09c78');
    this.ellipse(240, 339, 117, 23, '#c0ae8d');
    this.ellipse(240, 338, 91, 17, 'rgba(35,50,40,.2)');
    this.ellipse(240, 334, 45, 13, '#253e36');
    const bowl = c.createLinearGradient(146, 280, 309, 335);
    bowl.addColorStop(0, '#769487'); bowl.addColorStop(.4, '#567969'); bowl.addColorStop(1, '#243f36');
    c.beginPath(); c.moveTo(148, 286); c.bezierCurveTo(152, 347, 327, 357, 332, 286); c.closePath(); c.fillStyle = bowl; c.fill();
    c.strokeStyle = 'rgba(205,228,200,.16)'; c.lineWidth = 1.6;
    for (let i = 0; i < 4; i++) { c.beginPath(); c.ellipse(240, 293 + i * 8, 87 - i * 8, 25 - i * 2, 0, 0, Math.PI); c.stroke(); }
    this.ellipse(240, 286, 93, 30, '#8ca296');
    this.ellipse(240, 284, 86, 25, '#344e42');
    this.ellipse(240, 285, 77, 20, '#b4b098');
    this.ellipse(237, 288, 70, 16, '#c5c0a5');
    for (let i = 0; i < 34; i++) {
      const a = i * 2.39996, r = Math.sqrt(i / 34);
      this.ellipse(240 + Math.cos(a) * 67 * r, 287 + Math.sin(a) * 13 * r, .9, .5, i % 2 ? '#8c947d' : '#e0d5b5');
    }
    c.lineCap = 'round'; c.lineWidth = 4.7; c.strokeStyle = '#cdaa73';
    c.beginPath(); c.moveTo(240, 288); c.lineTo(237, tip); c.stroke();
    c.lineWidth = 1.2; c.strokeStyle = '#f0d1a0'; c.beginPath(); c.moveTo(239, 282); c.lineTo(236, tip + 3); c.stroke();
    if (burning) {
      const glow = c.createRadialGradient(237, tip, 0, 237, tip, 23);
      glow.addColorStop(0, 'rgba(252,132,65,.65)'); glow.addColorStop(.3, 'rgba(251,144,68,.18)'); glow.addColorStop(1, 'rgba(247,137,68,0)');
      this.ellipse(237, tip, 23, 23, glow);
      this.ellipse(237, tip, 3, 3.6, '#ffd491');
      const height = Math.min(190, tip - 16);
      for (let ribbon = 0; ribbon < 5; ribbon++) {
        c.beginPath();
        for (let j = 0; j <= 32; j++) {
          const p = j / 32, y = tip - p * height;
          const x = 237 + Math.sin(p * 7.5 - t * .6 + ribbon * .32) * (3 + p * 17) + p * 11;
          if (j === 0) c.moveTo(x, y); else c.lineTo(x, y);
        }
        c.lineWidth = 1.8 + ribbon * 1.5;
        const smoke = c.createLinearGradient(0, tip, 0, tip - height);
        smoke.addColorStop(0, 'rgba(233,226,205,.12)'); smoke.addColorStop(.3, 'rgba(224,224,208,.095)'); smoke.addColorStop(1, 'rgba(218,223,209,0)');
        c.strokeStyle = smoke; c.stroke();
      }
    } else if (this.ritual.status === 'extinguished') {
      this.ellipse(237, tip, 2.4, 2.8, '#665c49');
    }
    this.canvas.dataset.renderCount = String(++this.frames);
    this.canvas.dataset.burning = String(burning);
  }
}
