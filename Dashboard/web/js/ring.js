/**
 * Face ring: the circular camera view with a segmented progress ring.
 *
 * Enrollment: eight segments, one per head direction, fill as that direction is
 * captured; a dot shows where the head is right now; the next target is drawn heavier.
 * Verify: a four-colour scanner arc spins while the face is checked, then the ring
 * resolves to a success check or an error shake.
 *
 * Geometry is in the 400x400 viewBox. The ring is mirrored like the preview, so
 * "right" on screen is the user's own right.
 */
const GOOGLE = ['#4285F4', '#EA4335', '#FBBC04', '#34A853'];
const SECTORS = 8;
const CX = 200, CY = 200, R = 184;

function polar(deg, r = R) {
  const a = deg * Math.PI / 180;
  return [CX + r * Math.cos(a), CY - r * Math.sin(a)];
}
function arcPath(centerDeg, spanDeg, r = R) {
  const [x1, y1] = polar(centerDeg - spanDeg / 2, r);
  const [x2, y2] = polar(centerDeg + spanDeg / 2, r);
  return `M${x1.toFixed(2)} ${y1.toFixed(2)} A${r} ${r} 0 0 0 ${x2.toFixed(2)} ${y2.toFixed(2)}`;
}

class FaceRing {
  constructor(host, { mode = 'enroll' } = {}) {
    this.host = host;
    this.mode = mode;
    this.state = 'idle';
    host.innerHTML = this._markup();
    this.stage = host.querySelector('.ring-stage');
    this.img = host.querySelector('img');
    this.segs = [...host.querySelectorAll('.ring-seg')];
    this.dot = host.querySelector('.ring-dot');
    this.arrow = host.querySelector('.ring-arrow-wrap');
    this.centerArc = host.querySelector('.ring-center');
    this.placeholder = host.querySelector('.cam-placeholder');
    this.scan = host.querySelector('.ring-scan');
  }

  _markup() {
    const segs = Array.from({ length: SECTORS }, (_, k) => {
      const d = arcPath(k * 45, 34);
      const c = GOOGLE[k % 4];
      return `<g>
        <path d="${d}" stroke="var(--outline)" stroke-opacity=".45" stroke-width="10" stroke-linecap="round" fill="none"/>
        <path class="ring-seg" data-k="${k}" d="${d}" stroke="${c}" stroke-opacity="0" stroke-width="10" stroke-linecap="round" fill="none"/>
      </g>`;
    }).join('');
    const scanArcs = GOOGLE.map((c, i) =>
      `<path d="${arcPath(i * 90 + 45, 62)}" stroke="${c}" stroke-width="10" stroke-linecap="round" fill="none"/>`).join('');
    const circ = 2 * Math.PI * 166;
    const confetti = Array.from({ length: 14 }, (_, i) => {
      const a = (i / 14) * Math.PI * 2, d = 120 + (i % 3) * 22;
      return `<circle class="confetti" cx="200" cy="200" r="${4 + (i % 3)}" fill="${GOOGLE[i % 4]}"
        style="--cx:${(Math.cos(a) * d).toFixed(0)}px; --cy:${(Math.sin(a) * d).toFixed(0)}px; animation-delay:${(i % 5) * 30}ms"/>`;
    }).join('');
    return `
    <div class="ring-stage">
      <div class="cam-circle">
        <img alt="" src="data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==">
        <div class="cam-placeholder">${Art.spinner()}<span>Starting camera…</span></div>
        <div class="shade"></div>
      </div>
      <svg class="ring" viewBox="0 0 400 400" aria-hidden="true">
        <circle cx="200" cy="200" r="166" fill="none" stroke="var(--outline)" stroke-opacity=".35" stroke-width="4"/>
        <circle class="ring-center" cx="200" cy="200" r="166" fill="none" stroke="#4285F4" stroke-width="4" stroke-linecap="round"
          stroke-dasharray="0 ${circ.toFixed(1)}" transform="rotate(-90 200 200)" style="transition: stroke-dasharray .4s var(--ease-out)"/>
        <g class="ring-segs">${segs}</g>
        <g class="ring-scan" style="display:none">${scanArcs}</g>
        <circle class="ring-dot" cx="200" cy="200" r="7" fill="#fff" stroke="var(--g-blue)" stroke-width="3" style="display:none"/>
        <g class="ring-arrow-wrap" style="display:none"><g class="ring-arrow"><path d="M-13 -8l13 11 13-11" fill="none" stroke="var(--g-blue)" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/></g></g>
        <g class="result" style="display:none">
          <circle class="success-disc" cx="200" cy="200" r="156" fill="var(--g-green)" fill-opacity=".92"/>
          <path class="check" d="M145 205l37 37 75-84" fill="none" stroke="#fff" stroke-width="16" stroke-linecap="round" stroke-linejoin="round"/>
          <g class="confetti-wrap">${confetti}</g>
        </g>
      </svg>
    </div>`;
  }

  setFrame(src) {
    if (!src) return;
    this.img.src = src;
    if (this.placeholder) { this.placeholder.remove(); this.placeholder = null; }
  }

  /** Apply an enrollment status payload from the backend. */
  update(st) {
    if (this.state === 'success') return;
    const counts = st.sectorCounts || [];
    const needed = st.sectorNeeded || 2;
    this.segs.forEach((el, k) => {
      const frac = Math.min((counts[k] || 0) / needed, 1);
      const isTarget = k === st.targetSector && st.phase === 'rotate';
      el.setAttribute('stroke-opacity', frac === 0 ? (isTarget ? 0.38 : 0) : (0.35 + 0.65 * frac).toFixed(2));
      const isT = k === st.targetSector && st.phase === 'rotate';
      if (el.classList.contains('target') !== isT) el.classList.toggle('target', isT);
    });
    const inCenter = st.phase === 'center';
    const circ = 2 * Math.PI * 166;
    const cFrac = inCenter ? (st.centerCount || 0) / (st.centerNeeded || 4) : 1;
    this.centerArc.setAttribute('stroke-dasharray', `${(circ * cFrac).toFixed(1)} ${circ.toFixed(1)}`);
    this.centerArc.setAttribute('stroke', inCenter ? '#4285F4' : '#34A853');
    this.centerArc.style.opacity = inCenter || st.phase === 'rotate' ? 1 : 0;
    this.stage.querySelector('.ring-segs').style.opacity = inCenter ? 0.5 : 1;

    // Head position dot (only meaningful while rotating).
    if (st.phase === 'rotate' && st.faceOk) {
      let [u, v] = st.poseUV || [0, 0];
      // Smooth the head-position dot so detector jitter doesn't make it shake.
      this._u = this._u === undefined ? u : this._u + (u - this._u) * 0.3;
      this._v = this._v === undefined ? v : this._v + (v - this._v) * 0.3;
      u = this._u; v = this._v;
      const m = Math.hypot(u, v), max = 1.9;
      if (m > max) { u = u / m * max; v = v / m * max; }
      this.dot.style.display = '';
      this.dot.setAttribute('cx', (CX + u * 50).toFixed(1));
      this.dot.setAttribute('cy', (CY - v * 50).toFixed(1));
    } else {
      this.dot.style.display = 'none'; this._u = this._v = undefined;
    }

    // Arrow outside the ring pointing at the next sector.
    if (st.phase === 'rotate' && st.targetSector != null) {
      const th = st.targetSector * 45;
      const [x, y] = polar(th, R + 26);
      const rad = th * Math.PI / 180;
      this.arrow.style.display = '';
      if (this._tgt !== th) {
        this._tgt = th;
        this.arrow.setAttribute('transform', `translate(${x.toFixed(1)} ${y.toFixed(1)}) rotate(${90 - th})`);
      }
      this.arrow.firstElementChild.style.setProperty('--nx', '0px');
      this.arrow.firstElementChild.style.setProperty('--ny', '6px');
      this.arrow.firstElementChild.style.animationName = 'nudge-out';
    } else {
      this.arrow.style.display = 'none';
    }
  }

  setScanning(on) {
    this.scan.style.display = on ? '' : 'none';
    if (on) this.segs.forEach(s => s.setAttribute('stroke-opacity', 0));
  }

  success() {
    this.state = 'success';
    this.setScanning(false);
    this.dot.style.display = 'none';
    this.arrow.style.display = 'none';
    this.stage.querySelector('.ring-segs').style.opacity = 0;
    this.centerArc.style.opacity = 0;
    this.stage.querySelector('.result').style.display = '';
    this.stage.classList.add('state-success');
  }

  error() {
    this.state = 'error';
    this.setScanning(false);
    this.stage.classList.remove('state-error');
    void this.stage.offsetWidth;
    this.stage.classList.add('state-error');
    this.segs.forEach(s => { s.setAttribute('stroke', '#EA4335'); s.setAttribute('stroke-opacity', .85); });
  }

  reset() {
    this.state = 'idle';
    this.stage.classList.remove('state-success', 'state-error');
    this.stage.querySelector('.result').style.display = 'none';
    this.stage.querySelector('.ring-segs').style.opacity = 1;
    this.segs.forEach((s, k) => { s.setAttribute('stroke', GOOGLE[k % 4]); s.setAttribute('stroke-opacity', 0); });
    this.centerArc.setAttribute('stroke-dasharray', `0 ${(2 * Math.PI * 166).toFixed(1)}`);
  }
}
window.FaceRing = FaceRing;
