/**
 * Bridge to the Python backend (pywebview). When the page is opened in a plain
 * browser (design preview) a small in-memory demo backend answers instead.
 */
const Api = {
  async ready() {
    if (window.pywebview && window.pywebview.api) return true;
    return new Promise(resolve => {
      const t = setTimeout(() => resolve(false), 1200);
      window.addEventListener('pywebviewready', () => { clearTimeout(t); resolve(true); }, { once: true });
    });
  },

  async call(fn, ...args) {
    if (await this.ready()) {
      const api = window.pywebview.api;
      if (typeof api[fn] !== 'function') return {};
      try { return await api[fn](...args); }
      catch (err) { console.error(`API error in ${fn}:`, err); return { ok: false, msg: String(err) }; }
    }
    return Demo.call(fn, ...args);
  },
};

/* ───── Demo backend (browser preview only) ───── */
const Demo = {
  t0: Date.now(),
  frame: null,
  users: [
    { userId: 'subrata', username: 'Subrata Saha', templates: 21, poseCoverage: 9, learned: 3, templateFormat: 2, needsReenroll: false },
    { userId: 'guest_01', username: 'Guest', templates: 0, poseCoverage: 0, learned: 0, templateFormat: 1, needsReenroll: true },
  ],
  apps: [
    { id: 'app_1', name: 'Terminal (sudo)', cmd: 'sudo', icon: 'terminal' },
    { id: 'app_2', name: 'Google Chrome', cmd: 'google-chrome', icon: 'browser' },
  ],
  settings: { matchingThreshold: 0.40, livenessEnabled: true, adaptiveLearning: true, authTimeout: 6 },

  makeFrame() {
    if (this.frame) return this.frame;
    const c = document.createElement('canvas'); c.width = 640; c.height = 360;
    const g = c.getContext('2d');
    const bg = g.createLinearGradient(0, 0, 640, 360); bg.addColorStop(0, '#41505e'); bg.addColorStop(1, '#202a33');
    g.fillStyle = bg; g.fillRect(0, 0, 640, 360);
    g.fillStyle = '#5d4d49'; g.beginPath(); g.ellipse(320, 400, 190, 150, 0, 0, 7); g.fill();
    g.fillStyle = '#c99f86'; g.beginPath(); g.ellipse(320, 168, 74, 94, 0, 0, 7); g.fill();
    g.fillStyle = '#2a2523'; g.beginPath(); g.ellipse(320, 106, 80, 52, 0, Math.PI, 0); g.fill();
    g.fillStyle = '#2a2523'; [-26, 26].forEach(x => { g.beginPath(); g.ellipse(320 + x, 158, 7, 5, 0, 0, 7); g.fill(); });
    g.strokeStyle = '#7a4b45'; g.lineWidth = 4; g.beginPath(); g.arc(320, 200, 20, 0.2, Math.PI - 0.2); g.stroke();
    return (this.frame = c.toDataURL('image/jpeg', 0.8));
  },

  enrollStatus() {
    const q = new URLSearchParams(location.search);
    const forced = q.get('progress');
    const secs = (Date.now() - this.t0) / 1000;
    const p = forced != null ? parseFloat(forced) : Math.min(secs / 24, 1);
    const centerCount = Math.min(4, Math.round(p / 0.2 * 4));
    const rotating = p > 0.2;
    const counts = Array.from({ length: 8 }, (_, k) => {
      const done = Math.max(0, (p - 0.2) / 0.8 * 8 - k);
      return Math.max(0, Math.min(2, Math.round(done * 2)));
    });
    const target = counts.findIndex(c => c < 2);
    const ang = ((target < 0 ? 0 : target) * 45) * Math.PI / 180;
    const wob = Math.sin(secs * 2) * 0.1;
    return {
      ok: true, frame: this.makeFrame(), size: [640, 360], phase: p >= 1 ? 'done' : (rotating ? 'rotate' : 'center'),
      progress: p, centerCount, centerNeeded: 4, sectorCounts: counts, sectorNeeded: 2,
      hint: p >= 1 ? 'All set' : rotating ? 'Turn your head ' + ['right', 'up and right', 'up', 'up and left', 'left', 'down and left', 'down', 'down and right'][Math.max(0, target)] : 'Look straight at the camera',
      box: [0.36, 0.1, 0.28, 0.6], poseUV: rotating ? [Math.cos(ang) * 1.3 + wob, Math.sin(ang) * 1.3 + wob] : [0, 0],
      targetSector: target < 0 ? null : target, captured: false, faceOk: true, canFinish: p > 0.7,
    };
  },

  call(fn, ...a) {
    const q = new URLSearchParams(location.search);
    switch (fn) {
      case 'get_metrics': return { registeredUsersCount: this.users.length, cameraActive: false, daemonActive: true,
        ...this.settings, requiredMatches: 2, detector: 'YuNet', recognizer: 'SFace 128-d', socketPath: '/tmp/facelock.sock' };
      case 'get_users': return q.get('empty') ? [] : this.users;
      case 'get_protected_apps': return q.get('empty') ? [] : this.apps;
      case 'get_logs': return q.get('empty') ? [] : [
        { event: 'AUTH_ATTEMPT', user: 'subrata', status: 'OK', ts: '09:41:07' },
        { event: 'LIVENESS_CHECK', user: 'subrata', status: 'OK', ts: '09:41:06' },
        { event: 'AUTH_ATTEMPT', user: 'guest_01', status: 'FAIL', ts: '09:12:55' },
        { event: 'ENROLLMENT', user: 'subrata', status: 'OK', ts: '08:58:20' },
        { event: 'LOCKOUT', user: 'guest_01', status: 'FAIL', ts: '08:40:03' },
      ];
      case 'enroll_begin': this.t0 = Date.now(); return { ok: true };
      case 'enroll_tick': return this.enrollStatus();
      case 'enroll_finish': return { ok: true, templates: 21, poses: 9, msg: 'Enrolled' };
      case 'enroll_cancel': return { ok: true };
      case 'perception_tick': return { ok: true, frame: this.makeFrame(), size: [640, 360], luma: 118, faces: [{
        box: [0.36, 0.1, 0.28, 0.62], score: 0.94, yaw: -12, pitch: 4, roll: 2, quality: 'good',
        landmarks: [[0.43, 0.3], [0.57, 0.3], [0.5, 0.4], [0.44, 0.52], [0.56, 0.52]] }] };
      case 'verify_begin': this.t0 = Date.now(); return { ok: true };
      case 'verify_tick': {
        const s = (Date.now() - this.t0) / 1000;
        const done = s > 2.6;
        return { ok: true, frame: this.makeFrame(), hint: done ? 'Face recognized' : 'Checking', score: Math.min(0.82, s * 0.3),
          matches: done ? 2 : 0, threshold: 0.4, done, success: done, reason: done ? 'match' : '', box: [0.36, 0.1, 0.28, 0.6] };
      }
      case 'save_settings': this.settings = { matchingThreshold: a[0], livenessEnabled: a[1], adaptiveLearning: a[2], authTimeout: a[3] };
        return { ok: true, msg: 'Settings saved' };
      case 'get_system_installed_apps': return [
        { name: 'Visual Studio Code', cmd: 'code', icon: 'code' }, { name: 'Firefox', cmd: 'firefox', icon: 'browser' },
        { name: 'Terminal', cmd: 'gnome-terminal', icon: 'terminal' }, { name: 'Spotify', cmd: 'spotify', icon: 'media' }];
      case 'account_get': {
        const signed = q.get('signed');
        return { localName: 'Subrata Saha', hasClient: !!signed || !!q.get('client'), clientId: signed ? '1234-demo.apps.googleusercontent.com' : '', hasSecret: false,
          google: signed ? { name: 'Subrata Saha', email: 'you@example.com', picture: '' } : null, google_status: { phase: 'idle' },
          checkup: [
            { id: 'face', title: 'Face profile', detail: 'Enrolled from 9 of 9 angles', ok: true, page: 'enrollment' },
            { id: 'liveness', title: 'Liveness check', detail: 'Blocks flat photos and frozen video', ok: true, page: 'settings' },
            { id: 'fallback', title: 'Fallback passphrase', detail: 'Set for every profile', ok: true, page: 'enrollment' },
            { id: 'strict', title: 'Match strictness', detail: 'Balanced or stricter', ok: true, page: 'settings' },
            { id: 'service', title: 'Lock screen & sudo', detail: 'Unlock service is running', ok: true, page: 'overview' },
            { id: 'google', title: 'Google account', detail: signed ? 'you@example.com' : 'Optional: link to personalise FaceLock', ok: !!signed, page: 'account' }] }; }
      case 'account_google_begin': return q.get('client') || q.get('signed') ? { ok: true } : { ok: false, msg: 'Add your Google OAuth client ID first.' };
      case 'account_google_status': return { ok: true, phase: 'idle' };
      case 'get_app_icons': {
        const cols = ['#4285F4', '#EA4335', '#FBBC04', '#34A853', '#A142F4'];
        return Object.fromEntries((a[0] || []).map((n, i) => [n, 'data:image/svg+xml;utf8,' + encodeURIComponent(
          `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect width="48" height="48" rx="12" fill="${cols[i % 5]}"/><text x="24" y="32" font-size="24" font-family="sans-serif" font-weight="700" text-anchor="middle" fill="#fff">${(n[0] || '?').toUpperCase()}</text></svg>`)]));
      }
      case 'toggle_camera': return { ok: true };
      default: return { ok: true };
    }
  },
};
window.Api = Api;
