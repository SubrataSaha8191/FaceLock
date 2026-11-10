/** Page templates. Each returns an HTML string; behaviour lives in app.js. */
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const initials = n => (String(n).trim().split(/\s+/).map(w => w[0]).join('').slice(0, 2) || '?').toUpperCase();
const TONES = ['tone-blue', 'tone-red', 'tone-yellow', 'tone-green'];
const AVATAR = { 'tone-blue': '#4285F4', 'tone-red': '#EA4335', 'tone-yellow': '#E8A100', 'tone-green': '#34A853' };
const APP_ICON = { code: 'code', terminal: 'terminal', browser: 'globe', settings: 'settings', media: 'media', security: 'shield', app: 'apps' };
const appGlyph = (k, a) => Art.icon(APP_ICON[k] || 'apps');
/** App icon slot: shows the category glyph at once, swapped for the real icon by App.hydrateIcons. */
const appIconSlot = a => {
  const hint = a.icon_name || a.iconName || String(a.cmd || '').trim().split(/\s+/)[0].split('/').pop();
  return `<div class="app-glyph" data-icon="${esc(hint)}">${Art.icon(APP_ICON[a.icon] || 'apps')}</div>`;
};

const strictness = t => t < 0.36 ? 'Easier to unlock' : t > 0.46 ? 'Stricter' : 'Balanced';
const coverageDots = n => `<span class="coverage" title="${n} of 9 head angles enrolled">${Array.from({ length: 9 }, (_, i) => `<i class="${i < n ? 'on' : ''}"></i>`).join('')}</span>`;

const GLOGO = `<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="#4285F4" d="M23.49 12.27c0-.79-.07-1.54-.19-2.27H12v4.51h6.47c-.29 1.48-1.14 2.73-2.4 3.58v3h3.86c2.26-2.09 3.56-5.17 3.56-8.82z"/><path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.86-3c-1.08.72-2.45 1.16-4.07 1.16-3.13 0-5.78-2.11-6.73-4.96H1.29v3.09C3.26 21.3 7.31 24 12 24z"/><path fill="#FBBC05" d="M5.27 14.29c-.25-.72-.38-1.49-.38-2.29s.14-1.57.38-2.29V6.62H1.29C.47 8.24 0 10.06 0 12s.47 3.76 1.29 5.38l3.98-3.09z"/><path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.31 0 3.26 2.7 1.29 6.62l3.98 3.09c.95-2.85 3.6-4.96 6.73-4.96z"/></svg>`;
/** Avatar with the four-colour ring; uses the Google photo when linked. */
const avatarHTML = (a, extra = '') => {
  const g = a && a.google, name = (g && g.name) || (a && a.localName) || 'You';
  const inner = g && g.picture ? `<img src="${esc(g.picture)}" alt="" referrerpolicy="no-referrer" onerror="this.replaceWith(document.createTextNode('${esc(initials(name))}'))">` : esc(initials(name));
  return `<span class="acct-ring ${extra}"><span class="acct-face ${g && !g.picture ? 'g' : ''}">${inner}</span></span>`;
};

const Pages = {
  async overview() {
    const [m, users, apps] = await Promise.all([Api.call('get_metrics'), Api.call('get_users'), Api.call('get_protected_apps')]);
    const U = Array.isArray(users) ? users : [], A = Array.isArray(apps) ? apps : [];
    const needs = U.filter(u => u.needsReenroll).length;
    const online = m.daemonActive && m.daemonCurrent !== false;
    const stale = m.daemonActive && m.daemonCurrent === false;
    const greeting = U.length ? 'Your <span class="grad">face</span> is your key.' : 'Unlock with a <span class="grad">look</span>.';
    const lead = U.length
      ? 'FaceLock recognises you from any angle, in dim light and at a glance. Run a quick unlock test any time.'
      : 'Enroll once by slowly turning your head in a circle. FaceLock then recognises you from every angle, like a phone does.';
    return `
      <div class="stack">
        <section class="hero rise" style="--i:0">
          <div>
            <span class="chip ${online ? 'ok live' : 'warn'}"><span class="dot"></span>${online ? 'Unlock service running' : stale ? 'Restart the unlock service to use your new face' : 'Unlock service offline'}</span>
            <h2 class="display" style="margin-top:16px">${greeting}</h2>
            <p>${lead}</p>
            <div class="actions">
              <button class="btn btn-filled btn-lg" onclick="App.go('${U.length ? 'verify' : 'enrollment'}')">${Art.icon(U.length ? 'verified' : 'person-add')}${U.length ? 'Test unlock' : 'Add your face'}</button>
              ${U.length ? `<button class="btn btn-tonal btn-lg" onclick="App.go('enrollment')">${Art.icon('person-add')}Add another face</button>` : ''}
            </div>
          </div>
          ${Art.hero()}
        </section>

        ${needs ? `<div class="card pad-sm rise row" style="--i:1; background:var(--warning-container); color:var(--warning)">
          ${Art.icon('warning')}<div class="grow"><b>${needs} profile${needs > 1 ? 's' : ''} need${needs > 1 ? '' : 's'} a new scan.</b>
          FaceLock now uses a much more accurate face model, so older profiles must be enrolled again.</div>
          <button class="btn btn-text" style="color:inherit" data-rescan="${esc((U.find(u => u.needsReenroll) || {}).userId)}" data-name="${esc((U.find(u => u.needsReenroll) || {}).username)}">Re-scan face</button></div>` : ''}

        <section class="grid grid-stats">
          ${this.stat(1, 'blue', 'face', U.length, 'Enrolled faces', U.length ? 'Multi-angle profiles' : 'None yet')}
          ${this.stat(2, 'green', 'verified', m.livenessEnabled ? 'On' : 'Off', 'Liveness check', 'Blocks photo replays')}
          ${this.stat(3, 'yellow', 'tune', strictness(m.matchingThreshold), 'Match strictness', 'Threshold ' + Math.round(m.matchingThreshold * 100) + '%')}
          ${this.stat(4, 'red', 'lock', online ? 'Online' : stale ? 'Restart' : 'Offline', 'Lock screen & sudo', stale ? 'sudo systemctl restart facelock' : 'PAM unlock service')}
        </section>

        <section class="grid grid-2">
          <div class="card rise" style="--i:6; height:100%">
            <div class="card-head"><div class="title">${Art.icon('face')}Enrolled faces</div>
              <button class="btn btn-tonal" onclick="App.go('enrollment')">${Art.icon('add')}Add</button></div>
            ${U.length ? `<div class="list">${U.map((u, i) => this.userRow(u, i)).join('')}</div>`
              : `<div class="empty">${Art.emptyUsers()}<h3 class="title">No faces yet</h3><p>Add your face to unlock the lock screen, sudo and protected apps.</p>
                 <button class="btn btn-filled" onclick="App.go('enrollment')">${Art.icon('person-add')}Add your face</button></div>`}
          </div>

          <div class="stack">
            <div class="card rise" style="--i:7; height:100%">
              <div class="card-head"><div class="title">${Art.icon('apps')}Protected apps</div>
                <button class="btn btn-tonal" onclick="App.openAddApp()">${Art.icon('add')}Add app</button></div>
              <div id="protected-apps">${this.appsList(A)}</div>
            </div>
          </div>
        </section>

        <div class="section-title label rise" style="--i:9">How FaceLock recognises you</div>
        <div class="card glow rise" style="--i:10; padding:28px 32px 24px">${Art.pipeline()}
          <div class="tiles" style="grid-template-columns:repeat(4,minmax(0,1fr));margin-top:20px">
            <div class="tile tone-blue"><div class="label">${Art.icon('eye')}Detector</div><b>${esc(m.detector || 'YuNet')}</b></div>
            <div class="tile tone-red"><div class="label">${Art.icon('face')}Recognizer</div><b>${esc(m.recognizer || 'SFace')}</b></div>
            <div class="tile tone-yellow"><div class="label">${Art.icon('lock')}At rest</div><b>AES-256-GCM</b></div>
            <div class="tile tone-green"><div class="label">${Art.icon('history')}Window</div><b>${m.authTimeout || 6} s · ${m.requiredMatches || 2} frames</b></div>
          </div></div>
      </div>`;
  },

  stat(i, tone, icon, value, label, sub) {
    return `<div class="card glow stat tinted tone-${tone} raised rise" style="--i:${i + 1}">
      <div class="icon-bubble">${Art.icon(icon)}</div>
      <svg class="spark" viewBox="0 0 84 28" aria-hidden="true"><path d="M1 22C12 21 14 11 26 15S44 25 54 13 72 7 83 4"/><circle cx="83" cy="4" r="3"/></svg>
      <svg class="i wm" aria-hidden="true"><use href="#i-${icon}"/></svg>
      <div><div class="value">${esc(value)}</div><div style="font-weight:500;margin-top:6px">${esc(label)}</div><div class="sub">${esc(sub)}</div></div>
    </div>`;
  },

  userRow(u, i) {
    const tone = TONES[i % 4];
    const chip = u.needsReenroll ? `<button class="chip warn" style="cursor:pointer" data-rescan="${esc(u.userId)}" data-name="${esc(u.username)}">Re-enroll</button>`
      : `<span class="chip ok">${u.poseCoverage}/9 angles</span>`;
    return `<div class="list-item">
      <div class="avatar" style="background:${AVATAR[tone]}">${esc(initials(u.username))}</div>
      <div class="list-text"><div class="primary">${esc(u.username)}</div>
        <div class="secondary">${u.needsReenroll ? 'Needs a new face scan' : `${u.templates} captures${u.learned ? ` · ${u.learned} learned` : ''}`}</div></div>
      ${u.needsReenroll ? '' : coverageDots(u.poseCoverage)} ${chip}
      <button class="btn-icon" title="Re-scan face" aria-label="Re-scan face for ${esc(u.username)}" data-rescan="${esc(u.userId)}" data-name="${esc(u.username)}">${Art.icon('face')}</button>
      <button class="btn-icon" title="Edit" aria-label="Edit ${esc(u.username)}" data-edit="${esc(u.userId)}" data-name="${esc(u.username)}">${Art.icon('edit')}</button>
      <button class="btn-icon danger" title="Remove" aria-label="Remove ${esc(u.username)}" data-delete="${esc(u.userId)}" data-name="${esc(u.username)}">${Art.icon('delete')}</button>
    </div>`;
  },

  appsList(apps) {
    if (!apps.length) return `<div class="empty">${Art.emptyApps()}<p>Require your face before sensitive apps open.</p></div>`;
    return `<div class="list">${apps.map(a => `<div class="list-item">
      ${appIconSlot(a)}
      <div class="list-text"><div class="primary">${esc(a.name)}</div><div class="secondary mono">${esc(a.cmd)}</div></div>
      <button class="btn btn-text" data-launch="${esc(a.id)}">${Art.icon('bolt')}Open</button>
      <button class="btn-icon danger" title="Stop protecting" aria-label="Stop protecting ${esc(a.name)}" data-remove-app="${esc(a.id)}">${Art.icon('close')}</button>
    </div>`).join('')}</div>`;
  },

  async enrollment() {
    const rs = App.rescan;
    return `
      <div class="enroll-layout">
        <div class="stack">
          <div class="stepper card rise" style="--i:0" id="stepper">
            <div class="step ${rs ? 'done' : 'active'}" data-s="1"><div class="bullet">${rs ? Art.icon('check') : 1}</div><div><div class="t">${rs ? 'Same details' : 'Your details'}</div><div class="d">${rs ? 'Name and passphrase stay' : 'Who is this face for?'}</div></div></div>
            <div class="step ${rs ? 'active' : ''}" data-s="2"><div class="bullet">2</div><div><div class="t">Scan from every angle</div><div class="d">Look ahead, then slowly circle your head</div></div></div>
            <div class="step" data-s="3"><div class="bullet">3</div><div><div class="t">All set</div><div class="d">Test your unlock</div></div></div>
          </div>
          <form class="card stack rise" style="--i:1" id="enroll-form">
            ${rs ? `<div class="row"><div class="avatar" style="background:#4285F4">${esc(initials(rs.name))}</div>
              <div class="list-text"><div class="primary">${esc(rs.name)}</div><div class="secondary">Face profile</div></div></div>
              <p class="body-2" style="font-size:13.5px">Only your face is captured again. Your name and fallback passphrase stay exactly as they are.</p>
              <button class="btn btn-filled btn-lg" type="submit" id="enroll-start">${Art.icon('face')}Start face scan</button>`
            : `
            <label class="field"><input id="enroll-name" placeholder=" " required autocomplete="off"><span>Full name</span></label>
            <div><label class="field"><input id="enroll-secret" type="password" placeholder=" " required><span>Fallback passphrase</span></label>
              <div class="field-help">Used if the camera can't see you.</div></div>
            <button class="btn btn-filled btn-lg" type="submit" id="enroll-start">${Art.icon('face')}Start face scan</button>`}
          </form>
          <div class="card rise" style="--i:2">
            <div class="label" style="margin-bottom:12px">For the best scan</div>
            <div class="tips">
              <div class="tip tone-yellow"><div class="icon-bubble">${Art.icon('light')}</div><div>Face a window or lamp so light falls evenly on your face.</div></div>
              <div class="tip tone-blue"><div class="icon-bubble">${Art.icon('distance')}</div><div>Sit about an arm's length away. No hats or sunglasses.</div></div>
              <div class="tip tone-green"><div class="icon-bubble">${Art.icon('face')}</div><div>Turn slowly. Small head movements are enough.</div></div>
            </div>
          </div>
        </div>

        <div class="card rise" style="--i:1; padding:32px 24px 28px">
          <div id="enroll-ring-host"><div class="empty" style="padding:12px">${Art.hero()}<h3 class="title">Ready when you are</h3><p>${rs ? 'Press Start face scan, then look ahead and slowly circle your head. FaceLock replaces only your face data.' : 'Fill in your details, then start. FaceLock captures you from nine directions so it works at any angle.'}</p></div></div>
          <div class="guide" id="enroll-guide" aria-live="polite"></div>
          <div class="progress" id="enroll-progress" style="max-width:420px;margin:8px auto 0;display:none"><i></i></div>
          <div class="row" style="justify-content:center;margin-top:20px;gap:12px" id="enroll-actions"></div>
        </div>
      </div>`;
  },

  async verify() {
    const users = (await Api.call('get_users')) || [];
    const ok = users.filter(u => !u.needsReenroll);
    return `
      <div class="scan-layout">
        <div class="card rise" style="--i:0; padding:32px 24px 28px">
          <div id="verify-ring-host"><div class="empty" style="padding:12px">${Art.hero()}<h3 class="title">Test your unlock</h3>
            <p>This runs the same check as the lock screen and shows exactly what FaceLock sees.</p></div></div>
          <div class="guide" id="verify-guide" aria-live="polite"></div>
          <div class="row" style="justify-content:center;margin-top:16px" id="verify-actions">
            <button class="btn btn-filled btn-lg" id="verify-start" ${ok.length ? '' : 'disabled'}>${Art.icon('play')}Start test</button>
          </div>
        </div>
        <div class="stack">
          <div class="card rise" style="--i:1">
            <div class="label" style="margin-bottom:8px">Who are you?</div>
            ${ok.length ? `<div class="list" id="verify-users">${ok.map((u, i) => `
              <label class="list-item" style="cursor:pointer">
                <input type="radio" name="verify-user" value="${esc(u.userId)}" ${i === 0 ? 'checked' : ''}>
                <div class="avatar" style="background:${AVATAR[TONES[i % 4]]}">${esc(initials(u.username))}</div>
                <div class="list-text"><div class="primary">${esc(u.username)}</div><div class="secondary">${u.poseCoverage}/9 angles</div></div></label>`).join('')}</div>`
              : `<div class="empty"><p>No usable face profile yet. Add your face first.</p><button class="btn btn-filled" onclick="App.go('enrollment')">Add your face</button></div>`}
          </div>
          <div class="card rise" style="--i:3">
            <div class="label" style="margin-bottom:16px">What happens</div>
            <ol class="flow">
              <li class="tone-blue" style="--i:0"><span class="n" style="--i:0">1</span><div><b>You look at the camera</b><span>Any angle you enrolled works.</span></div></li>
              <li class="tone-yellow" style="--i:1"><span class="n" style="--i:1">2</span><div><b>Frames are checked live</b><span>Light, sharpness and size are screened.</span></div></li>
              <li class="tone-green" style="--i:2"><span class="n" style="--i:2">3</span><div><b>Two matching frames unlock</b><span>Or one very strong match, usually under a second.</span></div></li>
            </ol>
          </div>
          <div class="card rise" style="--i:2" id="verify-result">
            <div class="label" style="margin-bottom:8px">Result</div>
            <div class="kv"><span class="body-2">Match score</span><b id="v-score">-</b></div>
            <div class="kv"><span class="body-2">Matching frames</span><b id="v-matches">-</b></div>
            <div class="kv"><span class="body-2">Needs at least</span><b id="v-threshold">-</b></div>
          </div>
        </div>
      </div>`;
  },

  async perception() {
    return `
      <div class="scan-layout">
        <div class="stack">
          <div class="row between rise" style="--i:0"><div><h2 class="title">Live view</h2><div class="body-2">What the face detector sees right now.</div></div>
            <span class="chip ok live"><span class="dot"></span>Live</span></div>
          <div class="cam-frame mirror rise" style="--i:1" id="perc-frame">
            <img id="perc-img" alt="" src="data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==">
            <svg class="overlay" id="perc-overlay" viewBox="0 0 1000 1000" preserveAspectRatio="none"></svg>
            <div class="cam-placeholder" id="perc-ph">${Art.spinner()}<span>Starting camera…</span></div>
          </div>
          <div class="tiles rise" style="--i:2">
            <div class="tile tone-blue"><div class="label">${Art.icon('face')}Faces</div><b id="t-faces">0</b></div>
            <div class="tile tone-yellow"><div class="label">${Art.icon('light')}Light</div><b id="t-light">-</b></div>
            <div class="tile tone-green"><div class="label">${Art.icon('camera')}Frame</div><b id="t-size">-</b></div>
          </div>
        </div>
        <div class="stack">
          <div class="card rise" style="--i:2">
            <div class="label" style="margin-bottom:10px">Capture quality</div>
            <div class="row wrap" style="gap:8px" id="perc-chips"><span class="chip">Looking for a face</span></div>
          </div>
          <div class="card rise" style="--i:3">
            <div class="label" style="margin-bottom:6px">Head pose</div>
            ${['yaw:Turn', 'pitch:Tilt', 'roll:Roll'].map(s => { const [k, n] = s.split(':');
              return `<div class="meter-row"><span class="body-2">${n}</span><div class="meter"><i id="m-${k}"></i></div><b id="v-${k}" style="text-align:right">0°</b></div>`; }).join('')}
            <div class="field-help" style="margin:8px 0 0">FaceLock accepts all angles you enrolled, not only straight ahead.</div>
          </div>
          <div class="card rise" style="--i:4">
            <div class="label" style="margin-bottom:12px">Ideal framing</div>${Art.framing()}
            <div class="field-help" style="margin:10px 0 0">Centre your face, about an arm's length away, with even light.</div>
          </div>
          <div class="card rise" style="--i:5">
            <div class="kv"><span class="body-2">Image brightness</span><b id="perc-luma">-</b></div>
            <div class="kv"><span class="body-2">Detector confidence</span><b id="perc-score">-</b></div>
          </div>
        </div>
      </div>`;
  },

  async settings() {
    const m = await Api.call('get_metrics');
    const pct = Math.round((m.matchingThreshold || .4) * 100);
    const to = m.authTimeout || 6;
    return `
      <form class="settings-layout" id="settings-form">
        <div class="card rise" style="--i:0">
          <div class="card-head"><div class="title">${Art.icon('tune')}Recognition</div></div>
          <div class="setting-row" style="display:block">
            <div class="row between"><div><div style="font-weight:500">Match strictness</div><div class="body-2">Lower is easier to unlock, higher is harder to fool.</div></div>
              <span class="chip info" id="s-strict">${strictness(pct / 100)}</span></div>
            <div style="margin-top:20px"><input type="range" class="slider" id="s-threshold" min="30" max="60" step="1" value="${pct}">
              <div class="slider-scale"><span>Easier</span><span id="s-thr-val" style="font-weight:500;color:var(--text)">${pct}%</span><span>Stricter</span></div></div>
          </div>
          <div class="setting-row" style="display:block">
            <div class="row between"><div><div style="font-weight:500">Unlock window</div><div class="body-2">How long FaceLock keeps looking before giving up.</div></div>
              <span class="chip info" id="s-timeout-chip">${to} s</span></div>
            <div style="margin-top:20px"><input type="range" class="slider" id="s-timeout" min="3" max="12" step="1" value="${to}">
              <div class="slider-scale"><span>3 s</span><span>12 s</span></div></div>
          </div>
          <div class="setting-row"><div class="grow"><div style="font-weight:500">Liveness check</div><div class="body-2">Rejects flat photos and frozen video.</div></div>
            <label class="switch"><input type="checkbox" id="s-liveness" ${m.livenessEnabled ? 'checked' : ''}><span class="track"></span><span class="thumb">${Art.icon('check')}</span></label></div>
          <div class="setting-row"><div class="grow"><div style="font-weight:500">Learn as I change</div><div class="body-2">Adds confident unlocks to your profile so it follows new glasses, lighting or a haircut.</div></div>
            <label class="switch"><input type="checkbox" id="s-adaptive" ${m.adaptiveLearning ? 'checked' : ''}><span class="track"></span><span class="thumb">${Art.icon('check')}</span></label></div>
          <div class="row" style="justify-content:flex-end;margin-top:auto;padding-top:20px"><button class="btn btn-filled" type="submit">Save changes</button></div>
        </div>
        <div class="stack">
        <div class="card rise" style="--i:1">
          <div class="card-head"><div class="title">${Art.icon('shield')}Security balance</div><span class="chip info" id="g-chip">${strictness(pct / 100)}</span></div>
          <div class="gauge-wrap">${Art.gauge((pct - 30) / 30)}</div>
          <div class="body-2" style="text-align:center;margin-top:4px" id="g-note">Fewer misses, still very hard to impersonate.</div>
        </div>
        <div class="card rise" style="--i:2">
          <div class="card-head"><div class="title">${Art.icon('info')}Trouble unlocking?</div></div>
          <div class="tips">
            <div class="tip tone-blue"><div class="icon-bubble">${Art.icon('person-add')}</div><div><b>Re-run the scan</b> in the lighting where you usually unlock. More angles mean fewer misses.</div></div>
            <div class="tip tone-yellow"><div class="icon-bubble">${Art.icon('light')}</div><div><b>Light your face</b>, not the screen behind you. Backlight is the most common cause.</div></div>
            <div class="tip tone-green"><div class="icon-bubble">${Art.icon('tune')}</div><div><b>Lower the strictness</b> a few points if you still get rejected. Keep liveness on.</div></div>
            <div class="tip tone-red"><div class="icon-bubble">${Art.icon('eye')}</div><div>Use <b>Live view</b> to see how the camera frames you.</div></div>
          </div>
        </div>
        </div>
      </form>`;
  },

  async logs() {
    const logs = (await Api.call('get_logs')) || [];
    const L = Array.isArray(logs) ? logs.slice().reverse() : [];
    const ok = L.filter(l => l.status === 'OK').length;
    const kind = e => /LOCK/.test(e) ? ['red', 'lock'] : /ENROLL|IDENTITY/.test(e) ? ['blue', 'person-add'] : /LIVENESS/.test(e) ? ['yellow', 'eye'] : /PASSWORD/.test(e) ? ['yellow', 'lock'] : ['green', 'verified'];
    const nice = e => String(e).toLowerCase().replace(/_/g, ' ').replace(/^./, c => c.toUpperCase());
    const bad = L.length - ok, locks = L.filter(l => /LOCK/.test(l.event)).length;
    return `
      <div class="stack">
        <div class="tiles rise" style="--i:0">
          <div class="tile tone-blue"><div class="label">${Art.icon('history')}Events</div><b>${L.length}</b></div>
          <div class="tile tone-green"><div class="label">${Art.icon('check')}Successful</div><b>${ok}</b></div>
          <div class="tile tone-red"><div class="label">${Art.icon('warning')}Failed · lockouts</div><b>${bad} · ${locks}</b></div>
        </div>
        <div class="card top rise" style="--i:1">
          <div class="card-head"><div class="title">${Art.icon('history')}Recent activity</div>
            ${L.length ? `<button class="btn btn-outlined" id="clear-logs">${Art.icon('delete')}Clear</button>` : ''}</div>
          ${L.length ? `<div class="list">${L.map(l => { const [t, ic] = kind(l.event); const good = l.status === 'OK';
            return `<div class="log-row"><div class="log-ico tone-${good ? t : 'red'}">${Art.icon(good ? ic : 'close')}</div>
              <div style="font-weight:500">${esc(nice(l.event))}</div><div class="body-2">${esc(l.user)}</div>
              <span class="chip ${good ? 'ok' : 'err'}" style="justify-self:start">${good ? 'Success' : 'Failed'}</span>
              <div class="muted mono" style="text-align:right">${esc(l.ts)}</div></div>`; }).join('')}</div>`
            : `<div class="empty" style="margin:auto 0">${Art.emptyLogs()}<h3 class="title">Nothing here yet</h3><p>Unlocks, enrollments and lockouts will appear here.</p></div>`}
        </div>
      </div>`;
  },

  async account() {
    const a = await Api.call('account_get');
    const g = a.google, name = (g && g.name) || a.localName;
    const items = a.checkup || [], okN = items.filter(i => i.ok).length, total = items.length || 1;
    const circ = 2 * Math.PI * 62, frac = okN / total;
    return `
      <div class="stack">
        <section class="acct-banner rise" style="--i:0">
          <div class="avatar-xl lg">${avatarHTML(a)}<span class="badge">${Art.icon('camera')}</span></div>
          <div class="who">
            <span class="chip ${g ? 'ok' : 'info'}">${g ? 'Google account linked' : 'Local profile'}</span>
            <h2 style="margin-top:10px">${esc(name)}</h2>
            <div class="body-2">${g ? esc(g.email) : 'Signed in on this computer only'}</div>
            <div class="row">
              ${g ? `<button class="btn btn-outlined" id="g-signout">${Art.icon('logout')}Sign out of Google</button>`
                  : `<button class="gbtn" id="g-signin" ${a.hasClient ? '' : 'disabled'}>${GLOGO}Sign in with Google</button>`}
              ${!g && !a.hasClient ? '<span class="body-2" style="font-size:13px">Add a client ID below to enable</span>' : ''}
            </div>
          </div>
          ${Art.hero().replace('class="hero-art"', 'class="hero-art" style="max-width:260px;min-height:0"')}
        </section>

        <section class="grid grid-2">
          <div class="card rise" style="--i:1">
            <div class="card-head"><div class="title">${Art.icon('shield')}Security checkup</div>
              <span class="chip ${okN === total ? 'ok' : 'warn'}">${okN === total ? 'Protected' : (total - okN) + ' to review'}</span></div>
            <div class="checkup">
              <div class="donut"><svg viewBox="0 0 150 150"><defs><linearGradient id="dg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#4285F4"/><stop offset=".5" stop-color="#34A853"/><stop offset="1" stop-color="#FBBC04"/></linearGradient></defs>
                <circle cx="75" cy="75" r="62" fill="none" stroke="var(--container-high)" stroke-width="14"/>
                <circle class="arc" id="donut-arc" cx="75" cy="75" r="62" fill="none" stroke="url(#dg)" stroke-width="14" stroke-linecap="round" stroke-dasharray="${circ.toFixed(1)}" stroke-dashoffset="${(circ * (1 - frac)).toFixed(1)}" style="--from:${circ.toFixed(1)}"/></svg>
                <div class="mid"><b>${okN}/${total}</b><span>Checks</span></div></div>
              <div>${items.map(i => `<button class="check-row ${i.ok ? 'ok' : 'warn'}" data-go="${i.page}">
                <span class="st">${Art.icon(i.ok ? 'check' : 'warning')}</span>
                <span class="grow"><b>${esc(i.title)}</b><small>${esc(i.detail)}</small></span>
                ${i.ok ? '' : '<span class="chip warn">Review</span>'}</button>`).join('')}</div>
            </div>
          </div>

          <div class="stack">
            <form class="card rise" style="--i:2" id="profile-form">
              <div class="card-head"><div class="title">${Art.icon('user')}Profile</div></div>
              <label class="field"><input id="acct-name" placeholder=" " value="${esc(a.localName)}" maxlength="60"><span>Display name</span></label>
              <div class="field-help">Shown in the app. If you link Google, its name is used instead.</div>
              <div class="row" style="justify-content:flex-end;margin-top:14px"><button class="btn btn-tonal" type="submit">Save</button></div>
            </form>

            <form class="card rise" style="--i:3" id="google-form">
              <div class="card-head"><div class="title">${GLOGO.replace('<svg', '<svg style="width:32px;height:32px;padding:6px;border-radius:10px;background:#fff;box-shadow:inset 0 0 0 1px var(--outline-soft)"')}Google sign-in</div>
                ${a.hasClient ? '<span class="chip ok">Client set</span>' : '<span class="chip">Not set up</span>'}</div>
              <p class="body-2" style="font-size:13px">Link a Google account to personalise FaceLock. It is optional and never unlocks anything; only your name, email and photo are read, and no tokens are kept.</p>
              <ol class="steps-mini">
                <li>Open Google Cloud Console, then <b>APIs &amp; Services → Credentials</b></li>
                <li>Create an OAuth client of type <b>Desktop app</b></li>
                <li>Paste its client ID (and secret, if shown) here</li>
              </ol>
              <div class="stack" style="gap:12px">
                <label class="field"><input id="g-client" placeholder=" " value="${esc(a.clientId)}" autocomplete="off" spellcheck="false"><span>Client ID</span></label>
                <label class="field"><input id="g-secret" type="password" placeholder=" " autocomplete="off"><span>Client secret ${a.hasSecret ? '(saved)' : '(optional)'}</span></label>
              </div>
              <div class="row" style="justify-content:flex-end;margin-top:14px"><button class="btn btn-tonal" type="submit">Save client</button></div>
            </form>
          </div>
        </section>
      </div>`;
  }
};
window.Pages = Pages;
