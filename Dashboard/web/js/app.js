/** Application controller: routing, camera loops, enrollment and unlock flows. */
const sleep = ms => new Promise(r => setTimeout(r, ms));
const $ = (s, r = document) => r.querySelector(s);
/**
 * Steady guidance text. A new message is shown only after it has been the latest
 * one for `hold` ms AND the current one has been on screen for `minShow` ms, so
 * momentary detector hiccups never make the text flicker. The DOM is untouched
 * while the message is unchanged.
 */
class HintBox {
  constructor(el, { hold = 450, minShow = 1200 } = {}) {
    this.el = el; this.hold = hold; this.minShow = minShow;
    this.key = null; this.cand = null; this.since = 0; this.shownAt = 0;
  }
  set(html, key = html) {
    const now = performance.now();
    if (key === this.key) { this.cand = null; return; }
    if (this.key === null) return this.show(html, key, now);
    if (this.cand !== key) { this.cand = key; this.candHtml = html; this.since = now; return; }
    if (now - this.since >= this.hold && now - this.shownAt >= this.minShow) this.show(html, key, now);
  }
  force(html, key = html) { this.show(html, key, performance.now()); }
  show(html, key, now) {
    this.key = key; this.cand = null; this.shownAt = now;
    this.el.innerHTML = html;
    this.el.classList.remove('fade'); void this.el.offsetWidth; this.el.classList.add('fade');
  }
}

const TITLES = { overview: 'Home', enrollment: 'Face scan', verify: 'Test unlock', perception: 'Live view', settings: 'Settings', logs: 'Activity', account: 'Your account' };
const SUBS = {
  overview: 'Your faces, apps and protection at a glance', enrollment: 'Look ahead, then slowly circle your head',
  verify: 'Try the same check the lock screen runs', perception: 'See what the camera and detector see',
  settings: 'Tune how strict and how patient unlocking is', logs: 'Unlocks, enrollments and lockouts',
  account: 'Profile, security checkup and Google sign-in',
};
const TONES_PAGE = { overview: '#4285F4', enrollment: '#34A853', verify: '#F9AB00', perception: '#EA4335', settings: '#A142F4', logs: '#12B5CB', account: '#4285F4' };
const ICONS = { overview: 'm-home', enrollment: 'm-enroll', verify: 'm-verify', perception: 'm-live', settings: 'm-settings', logs: 'm-activity', account: 'm-account' };

const App = {
  page: 'overview',
  rescan: null,       // {id, name} when re-capturing only the face of an existing profile
  cleanup: null,       // stops loops belonging to the current page
  token: 0,            // invalidates in-flight renders after navigation

  async init() {
    $('#rail-logo').innerHTML = Art.logo(44);
    await this.loadAccount();
    this.bind();
    this.syncThemeIcon();
    const start = new URLSearchParams(location.search).get('page');
    await this.go(TITLES[start] ? start : 'overview', true);
    this.previewHooks();
  },

  /** Design-preview helpers; only active when the page is opened outside the desktop app. */
  async previewHooks() {
    if (window.pywebview) return;
    const q = new URLSearchParams(location.search);
    if (q.get('still')) document.head.insertAdjacentHTML('beforeend', '<style>*{animation:none!important}.rise{opacity:1!important}</style>');
    if (q.get('pop')) this.togglePopover(true);
    if (q.get('auto') === 'apps') this.openAddApp();
    if (q.get('auto') === 'confirm') this.confirm({ title: 'Remove this face profile?', body: '"Subrata Saha" will no longer unlock this computer, and its face data is deleted. You can add it again any time.', ok: 'Remove', danger: true, icon: 'delete' });
    if (q.get('auto') === 'rescan') { this.rescan = { id: 'user_01', name: 'Subrata Saha' }; await this.go('enrollment', true); }
    if (q.get('auto') === 'enroll') {
      $('#enroll-name').value = 'Subrata Saha'; $('#enroll-secret').value = 'x';
      Enroll.start();
    } else if (q.get('auto') === 'verify') {
      setTimeout(() => $('#verify-start').click(), 100);
    }
  },

  bind() {
    document.querySelectorAll('.rail-item').forEach(b => b.addEventListener('click', () => this.go(b.dataset.page)));
    $('#enroll-cta').addEventListener('click', () => this.go('enrollment'));
    $('#test-cta').addEventListener('click', () => this.go('verify'));
    $('#account-btn').addEventListener('click', e => { e.stopPropagation(); this.togglePopover(); });
    document.addEventListener('mousedown', e => { if (!e.target.closest('#acct-pop, #account-btn')) this.togglePopover(false); });
    $('#theme-btn').addEventListener('click', () => this.toggleTheme());
    // Soft glow follows the pointer, but only on cards opted in with .glow (never over camera, forms or lists).
    document.addEventListener('pointermove', e => {
      const c = e.target.closest && e.target.closest('.glow'); if (!c) return;
      const r = c.getBoundingClientRect();
      c.style.setProperty('--mx', (e.clientX - r.left) + 'px'); c.style.setProperty('--my', (e.clientY - r.top) + 'px');
    }, { passive: true });
    document.addEventListener('click', e => this.onClick(e));
    document.addEventListener('keydown', e => { if (e.key === 'Escape') document.querySelectorAll('.scrim.open').forEach(s => s.classList.remove('open')); this.togglePopover(false); });
    $('#edit-form').addEventListener('submit', e => this.submitEdit(e));
    $('#app-search').addEventListener('input', e => this.filterApps(e.target.value));
    document.querySelectorAll('.scrim').forEach(s => s.addEventListener('mousedown', e => { if (e.target === s) s.classList.remove('open'); }));
  },

  /* ───── routing ───── */
  async go(page, force = false) {
    if (!force && page === this.page && $('#page').children.length) return;
    if (page !== 'enrollment') this.rescan = null;
    $('#page').classList.remove('still');
    this.stopLoops();
    const my = ++this.token;
    this.page = page;
    document.querySelectorAll('.rail-item').forEach(b => b.classList.toggle('active', b.dataset.page === page));
    $('#page-title').textContent = TITLES[page];
    $('#page-sub').textContent = SUBS[page] || '';
    const ico = $('#bar-ico'); ico.querySelector('use').setAttribute('href', '#' + ICONS[page]);
    document.documentElement.style.setProperty('--bar-tone', TONES_PAGE[page] || '#4285F4');
    $('#enroll-cta').style.display = page === 'enrollment' ? 'none' : '';
    $('#test-cta').style.display = page === 'verify' ? 'none' : '';
    $('#account-btn').classList.toggle('active', page === 'account');
    this.togglePopover(false);
    const html = await Pages[page]();
    if (my !== this.token) return;
    const el = $('#page');
    el.innerHTML = html;
    $('#page-wrap').scrollTop = 0;
    this.mount(page);
  },

  /**
   * Re-render the current page in place: same scroll position, no entrance animations,
   * no blank frame. Used after edits/deletes/saves instead of a full navigation.
   */
  async refresh() {
    const page = this.page, my = ++this.token, wrap = $('#page-wrap'), top = wrap.scrollTop;
    const html = await Pages[page]();
    if (my !== this.token) return;
    this.stopLoops();
    const el = $('#page');
    el.classList.add('still');
    el.innerHTML = html;
    wrap.scrollTop = top;
    this.mount(page);
  },

  stopLoops() {
    if (this.cleanup) { try { this.cleanup(); } catch (e) { console.error(e); } this.cleanup = null; }
  },

  mount(page) {
    if (page === 'enrollment') this.cleanup = Enroll.mount();
    else if (page === 'verify') this.cleanup = Verify.mount();
    else if (page === 'perception') this.cleanup = Perception.mount();
    else if (page === 'settings') this.mountSettings();
    else if (page === 'account') this.mountAccount();
    if (page === 'overview') this.hydrateIcons($('#protected-apps'));
    if (page === 'logs') { const b = $('#clear-logs'); if (b) b.onclick = () => this.clearLogs(); }
  },

  /* ───── themed confirm ───── */
  confirm({ title, body, ok = 'Confirm', danger = false, icon = 'warning' }) {
    return new Promise(resolve => {
      const m = $('#confirm-modal'), okb = $('#confirm-ok'), cb = $('#confirm-cancel');
      $('#confirm-title').textContent = title; $('#confirm-body').textContent = body;
      const ico = $('#confirm-ico'); ico.className = 'confirm-ico' + (danger ? ' danger' : ''); ico.innerHTML = Art.icon(icon);
      okb.textContent = ok; okb.className = 'btn ' + (danger ? 'btn-danger-filled' : 'btn-filled');
      const ac = new AbortController();
      const done = v => { ac.abort(); m.classList.remove('open'); resolve(v); };
      okb.addEventListener('click', () => done(true), { signal: ac.signal });
      cb.addEventListener('click', () => done(false), { signal: ac.signal });
      m.addEventListener('mousedown', e => { if (e.target === m) done(false); }, { signal: ac.signal });
      document.addEventListener('keydown', e => { if (e.key === 'Escape') done(false); }, { signal: ac.signal });
      m.classList.add('open'); cb.focus();
    });
  },

  /* ───── account ───── */
  acct: null,
  async loadAccount() {
    this.acct = await Api.call('account_get');
    $('#rail-avatar').innerHTML = avatarHTML(this.acct).replace(/^<span class="acct-ring ">/, '').replace(/<\/span>$/, '');
  },

  async togglePopover(force) {
    const pop = $('#acct-pop');
    const open = force === undefined ? !pop.classList.contains('open') : force;
    if (!open) { pop.classList.remove('open'); return; }
    await this.loadAccount();
    const a = this.acct, g = a.google, name = (g && g.name) || a.localName;
    const okN = (a.checkup || []).filter(i => i.ok).length, tot = (a.checkup || []).length;
    pop.innerHTML = `
      <div class="pop-top"><div class="avatar-xl">${avatarHTML(a)}<span class="badge">${Art.icon('camera')}</span></div>
        <div class="name">${esc(name)}</div><div class="mail">${g ? esc(g.email) : 'Local profile on this computer'}</div>
        <button class="btn btn-outlined" data-go="account">Manage your FaceLock account</button></div>
      <div class="pop-rows">
        <button class="pop-row" data-go="account">${Art.icon('shield')}<span class="grow">Security checkup<small>${okN} of ${tot} checks passed</small></span>${okN < tot ? '<span class="chip warn">Review</span>' : '<span class="chip ok">All good</span>'}</button>
        ${g ? `<button class="pop-row" id="pop-signout">${Art.icon('logout')}<span class="grow">Sign out of Google</span></button>`
            : `<button class="pop-row" data-go="account">${GLOGO.replace('<svg', '<svg class="i"')}<span class="grow">Sign in with Google<small>${a.hasClient ? 'Link your account' : 'Add a client ID to enable'}</small></span></button>`}
        <button class="pop-row" data-go="settings">${Art.icon('tune')}<span class="grow">Recognition settings</span></button>
      </div>
      <div class="pop-foot">Your face data never leaves this computer</div>`;
    const so = $('#pop-signout'); if (so) so.onclick = async () => { await Api.call('account_signout'); await this.loadAccount(); this.togglePopover(false); this.toast('Signed out of Google'); if (this.page === 'account') this.refresh(); };
    pop.classList.add('open');
  },

  mountAccount() {
    $('#profile-form').onsubmit = async e => { e.preventDefault(); await Api.call('account_set_name', $('#acct-name').value); this.toast('Profile saved'); await this.loadAccount(); this.refresh(); };
    $('#google-form').onsubmit = async e => {
      e.preventDefault();
      const r = await Api.call('account_save_client', $('#g-client').value, $('#g-secret').value);
      this.toast(r.msg || 'Saved'); if (r.ok) this.refresh();
    };
    const si = $('#g-signin'); if (si) si.onclick = () => this.googleSignIn();
    const so = $('#g-signout'); if (so) so.onclick = async () => { await Api.call('account_signout'); this.toast('Signed out of Google'); await this.loadAccount(); this.refresh(); };
  },

  async googleSignIn() {
    const btn = $('#g-signin');
    const r = await Api.call('account_google_begin');
    if (!r.ok) { this.toast(r.msg || 'Could not start sign-in'); return; }
    btn.disabled = true; btn.lastChild.textContent = 'Waiting for your browser…';
    this.toast('Finish signing in in your browser');
    for (let i = 0; i < 200 && this.page === 'account'; i++) {
      await sleep(1000);
      const st = await Api.call('account_google_status');
      if (st.phase === 'done') { this.toast('Signed in as ' + (st.message || 'your Google account')); await this.loadAccount(); this.refresh(); return; }
      if (st.phase === 'error') { this.toast(st.message || 'Sign-in failed'); this.refresh(); return; }
      if (st.phase === 'idle') break;
    }
  },

  /* ───── theme + feedback ───── */
  toggleTheme() {
    const next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    try { localStorage.setItem('fl-theme', next); } catch (e) {}
    this.syncThemeIcon();
  },
  syncThemeIcon() {
    const dark = document.documentElement.getAttribute('data-theme') === 'dark';
    $('#theme-btn use').setAttribute('href', dark ? '#i-sun' : '#i-moon');
  },
  toast(msg) {
    const s = $('#snackbar'); $('#snack-text').textContent = msg;
    s.classList.add('show'); clearTimeout(this._toast);
    this._toast = setTimeout(() => s.classList.remove('show'), 3600);
  },

  /* ───── delegated clicks ───── */
  async onClick(e) {
    const t = e.target.closest('[data-edit],[data-delete],[data-launch],[data-remove-app],[data-close],[data-add-app],[data-go],[data-rescan]');
    if (!t) return;
    const d = t.dataset;
    if (d.rescan !== undefined) { this.rescan = { id: d.rescan, name: d.name }; this.go('enrollment', true); }
    else if (d.go) this.go(d.go);
    else if (d.close) $('#' + d.close).classList.remove('open');
    else if (d.edit !== undefined) this.openEdit(d.edit, d.name);
    else if (d.delete !== undefined) {
      if (!await this.confirm({ title: 'Remove this face profile?', body: `"${d.name || d.delete}" will no longer unlock this computer, and its face data is deleted. You can add it again any time.`, ok: 'Remove', danger: true, icon: 'delete' })) return;
      await Api.call('delete_user', d.delete); this.toast('Face profile removed'); this.refresh();
    }
    else if (d.launch !== undefined) { await Api.call('launch_protected_app', d.launch); this.toast('Verifying your face to open the app…'); }
    else if (d.removeApp !== undefined) { await Api.call('remove_protected_app', d.removeApp); this.refreshApps(); }
    else if (d.addApp !== undefined) this.protectApp(+d.addApp);
  },

  /* ───── identities ───── */
  openEdit(id, name) {
    $('#edit-orig-userid').value = id; $('#edit-username').value = name;
    $('#edit-modal').classList.add('open'); $('#edit-username').focus();
  },
  async submitEdit(e) {
    e.preventDefault();
    const o = $('#edit-orig-userid').value, n = $('#edit-username').value.trim();
    if (!o || !n) return;
    await Api.call('update_user', o, o, n);
    $('#edit-modal').classList.remove('open'); this.toast('Saved'); this.refresh();
  },
  async clearLogs() {
    if (!await this.confirm({ title: 'Clear activity history?', body: 'All recorded unlocks, enrollments and lockouts will be deleted. This can\'t be undone.', ok: 'Clear history', danger: true, icon: 'delete' })) return;
    await Api.call('clear_logs'); this.refresh();
  },

  /* ───── protected apps ───── */
  installed: [],
  async openAddApp() {
    $('#app-modal').classList.add('open'); $('#app-search').value = '';
    $('#installed-apps').innerHTML = `<div class="empty">${Art.spinner()}</div>`;
    this.installed = (await Api.call('get_system_installed_apps')) || [];
    this.renderApps(this.installed);
    $('#app-search').focus();
  },
  renderApps(list) {
    this.shown = list;
    $('#installed-apps').innerHTML = list.length ? list.map((a, i) => `
      <button class="list-item" style="text-align:left;width:100%" data-add-app="${i}">
        ${appIconSlot(a)}
        <div class="list-text"><div class="primary">${esc(a.name)}</div><div class="secondary mono">${esc(a.cmd)}</div></div>
        <span class="chip info">Protect</span></button>`).join('')
      : `<div class="empty"><p>No matching apps.</p></div>`;
    this.hydrateIcons($('#installed-apps'));
  },
  filterApps(q) {
    const terms = q.toLowerCase().split(/\s+/).filter(Boolean);
    this.renderApps(this.installed.filter(a => { const h = `${a.name} ${a.cmd} ${a.kw || ''}`.toLowerCase(); return terms.every(t => h.includes(t)); }));
  },
  async protectApp(i) {
    const a = this.shown[i]; if (!a) return;
    await Api.call('add_protected_app', a.name, a.cmd, a.icon, a.iconName || '');
    $('#app-modal').classList.remove('open'); this.toast(`${a.name} now needs your face`); this.refreshApps();
  },
  async refreshApps() {
    const apps = (await Api.call('get_protected_apps')) || [];
    const el = $('#protected-apps'); if (el) { el.innerHTML = Pages.appsList(apps); this.hydrateIcons(el); }
  },

  /* ───── real app icons ───── */
  iconCache: {},
  async hydrateIcons(root) {
    if (!root) return;
    const slots = [...root.querySelectorAll('.app-glyph[data-icon]:not(.has-img)')];
    const need = [...new Set(slots.map(e => e.dataset.icon).filter(n => n && !(n in this.iconCache)))].slice(0, 80);
    if (need.length) {
      const got = (await Api.call('get_app_icons', need)) || {};
      need.forEach(n => { this.iconCache[n] = got[n] || null; });
    }
    slots.forEach(e => {
      const uri = this.iconCache[e.dataset.icon];
      if (uri && e.isConnected) { e.innerHTML = `<img alt="" src="${uri}">`; e.classList.add('has-img'); }
    });
  },

  /* ───── settings ───── */
  mountSettings() {
    const thr = $('#s-threshold'), to = $('#s-timeout');
    const paint = el => el.style.setProperty('--pct', ((el.value - el.min) / (el.max - el.min) * 100) + '%');
    const sync = () => {
      paint(thr); paint(to);
      $('#s-thr-val').textContent = thr.value + '%';
      $('#s-strict').textContent = strictness(thr.value / 100);
      Art.setGauge((thr.value - 30) / 30);
      $('#g-chip').textContent = strictness(thr.value / 100);
      $('#g-note').textContent = thr.value < 36 ? 'Easiest unlocking. Best for dim or tricky lighting.' : thr.value > 46 ? 'Very strict. You may need better light or more angles.' : 'Fewer misses, still very hard to impersonate.';
      $('#s-timeout-chip').textContent = to.value + ' s';
    };
    thr.oninput = to.oninput = sync; sync();
    $('#settings-form').onsubmit = async e => {
      e.preventDefault();
      const r = await Api.call('save_settings', thr.value / 100, $('#s-liveness').checked, $('#s-adaptive').checked, +to.value);
      this.toast(r.msg || 'Settings saved');
    };
  },
};

/* ═════════════ Guided enrollment ═════════════ */
const Enroll = {
  mount() {
    this.running = false; this.ring = null; this.done = false;
    const form = $('#enroll-form');
    form.onsubmit = e => { e.preventDefault(); this.start(); };
    return () => this.stop();
  },

  setStep(n) {
    document.querySelectorAll('#stepper .step').forEach(s => {
      const k = +s.dataset.s;
      s.classList.toggle('active', k === n); s.classList.toggle('done', k < n);
      s.querySelector('.bullet').innerHTML = k < n ? Art.icon('check') : k;
    });
  },

  async start() {
    const rs = App.rescan;
    const id = rs ? rs.id : '', name = rs ? rs.name : $('#enroll-name').value.trim(), pass = rs ? '' : $('#enroll-secret').value;
    if (!name || (!rs && !pass)) return;
    this.form = { id, name, pass, keep: !!rs };
    const btn = $('#enroll-start'); btn.disabled = true;
    const r = await Api.call('enroll_begin');
    btn.disabled = false;
    if (!r.ok) { App.toast(r.msg || 'Camera unavailable'); return; }
    this.setStep(2);
    $('#enroll-form').querySelectorAll('input').forEach(i => i.disabled = true);
    if (App.rescan) $('#enroll-form').style.display = 'none';
    btn.style.display = 'none';
    this.ring = new FaceRing($('#enroll-ring-host'), { mode: 'enroll' });
    this.hint = new HintBox($('#enroll-guide'));
    this.hint.force('Look straight at the camera');
    $('#enroll-progress').style.display = '';
    $('#enroll-actions').innerHTML = `
      <button class="btn btn-text" id="enroll-cancel">Cancel</button>
      <button class="btn btn-tonal" id="enroll-finish" disabled>${Art.icon('check')}Finish with current coverage</button>`;
    $('#enroll-cancel').onclick = () => this.cancel();
    $('#enroll-finish').onclick = () => this.finish();
    this.running = true;
    this.loop();
  },

  async loop() {
    let misses = 0;
    while (this.running) {
      const st = await Api.call('enroll_tick');
      if (!this.running) break;
      if (!st.ok) { if (++misses > 20) { this.fail(st.msg || 'Camera stopped responding'); return; } await sleep(150); continue; }
      misses = 0;
      this.ring.setFrame(st.frame);
      this.ring.update(st);
      const arrow = st.phase === 'rotate' && st.targetSector != null
        ? `<span class="guide-arrow" style="transform:rotate(${90 - st.targetSector * 45}deg)">${Art.icon('chevron')}</span>` : '';
      this.hint.set(arrow + `<span>${esc(st.hint)}</span>`, st.hint);
      const p = $('#enroll-progress i'); if (p) { const w = Math.round(st.progress * 100) + '%'; if (p.style.width !== w) p.style.width = w; }
      const f = $('#enroll-finish'); if (f && f.disabled === st.canFinish) f.disabled = !st.canFinish;
      if (st.phase === 'done') { this.finish(); return; }
      await sleep(20);
    }
  },

  async finish() {
    if (this.done) return;
    this.done = true; this.running = false;
    const f = this.form;
    const r = await Api.call('enroll_finish', f.id, f.name, f.pass, f.keep);
    if (!r.ok) { this.done = false; App.toast(r.msg || 'Enrollment failed'); this.running = true; this.loop(); return; }
    this.ring.success();
    await Api.call('toggle_camera', false);
    this.setStep(3);
    $('#enroll-guide').className = 'guide ok';
    this.hint.force('You\'re all set');
    $('#enroll-actions').innerHTML = `
      <button class="btn btn-filled btn-lg" id="enroll-test">${Art.icon('verified')}Test unlock</button>
      <button class="btn btn-tonal btn-lg" id="enroll-home">Done</button>`;
    $('#enroll-test').onclick = () => App.go('verify'); $('#enroll-home').onclick = () => App.go('overview');
    App.toast(`${r.templates} captures across ${r.poses} angles saved`);
  },

  fail(msg) { this.running = false; App.toast(msg); },
  async cancel() { this.stop(); await Api.call('enroll_cancel'); App.go('overview'); },
  stop() { this.running = false; Api.call('toggle_camera', false); },
};

/* ═════════════ Test unlock ═════════════ */
const Verify = {
  mount() {
    this.running = false;
    const b = $('#verify-start'); if (b) b.onclick = () => this.start();
    return () => this.stop();
  },

  async start() {
    const sel = document.querySelector('input[name="verify-user"]:checked');
    if (!sel) return;
    const r = await Api.call('verify_begin', sel.value);
    if (!r.ok) { App.toast(r.msg || 'Camera unavailable'); return; }
    this.ring = new FaceRing($('#verify-ring-host'), { mode: 'verify' });
    this.ring.setScanning(true);
    $('#verify-actions').innerHTML = '';
    const g = $('#verify-guide'); g.className = 'guide';
    this.hint = new HintBox(g, { hold: 350, minShow: 900 }); this.hint.force('Look at the camera');
    this.running = true;
    let miss = 0;
    while (this.running) {
      const p = await Api.call('verify_tick');
      if (!this.running) break;
      if (!p.ok && !p.done) { if (++miss > 20) break; await sleep(100); continue; }
      if (p.frame) this.ring.setFrame(p.frame);
      $('#v-score').textContent = p.score ? p.score.toFixed(2) : '-';
      $('#v-matches').textContent = p.matches ?? '-';
      if (p.threshold) $('#v-threshold').textContent = p.threshold.toFixed(2);
      if (p.done) { this.finish(p); return; }
      this.hint.set(esc(p.hint || 'Look at the camera'), p.hint || 'Look at the camera');
      await sleep(15);
    }
  },

  finish(p) {
    this.running = false;
    const g = $('#verify-guide');
    Api.call('toggle_camera', false);
    if (p.success) { this.ring.success(); g.className = 'guide ok'; this.hint.force('Unlocked'); }
    else {
      this.ring.error(); g.className = 'guide err';
      this.hint.force(({
        no_face: "Couldn't see your face", low_quality: 'The image was too dark or unclear', mismatch: "That didn't look like you",
        liveness_failed: 'Liveness check failed', locked: 'Too many attempts, try again later', re_enroll_required: 'Please enroll again',
      })[p.reason] || p.hint || 'Not recognised');
    }
    $('#verify-actions').innerHTML = `<button class="btn btn-tonal btn-lg" id="verify-again">${Art.icon('refresh')}Test again</button>`;
    $('#verify-again').onclick = () => App.refresh();
  },

  stop() { this.running = false; Api.call('toggle_camera', false); },
};

/* ═════════════ Live view ═════════════ */
const Perception = {
  mount() {
    this.running = true;
    Api.call('toggle_camera', true).then(() => this.loop());
    return () => { this.running = false; Api.call('toggle_camera', false); };
  },

  async loop() {
  const bar = (id, v, lim = 45) => {
    const el = $('#m-' + id), t = $('#v-' + id); if (!el) return;
    const c = Math.max(-lim, Math.min(lim, v)) / lim * 50;
    el.style.left = (c < 0 ? 50 + c : 50) + '%'; el.style.width = Math.abs(c) + '%';
    t.textContent = Math.round(v) + '°';
  };
  while (this.running) {
    const r = await Api.call('perception_tick');
    if (!this.running) break;
    if (!r.ok) { await sleep(200); continue; }
    const img = $('#perc-img'), ph = $('#perc-ph');
    if (!img) return;
    img.src = r.frame; if (ph) ph.remove();
    $('#perc-luma').textContent = r.luma + ' / 255';
    $('#t-faces').textContent = r.faces.length; $('#t-light').textContent = r.luma < 60 ? 'Low' : r.luma > 200 ? 'Harsh' : 'Good'; $('#t-size').textContent = r.size[0] + '×' + r.size[1];
    const f = r.faces[0], ov = $('#perc-overlay');
    if (!f) {
      ov.innerHTML = '';
      $('#perc-chips').innerHTML = `<span class="chip warn">${Art.icon('face', 'sm')}No face found</span>` + (r.luma < 60 ? '<span class="chip warn">Too dark</span>' : '');
      $('#perc-score').textContent = '-'; bar('yaw', 0); bar('pitch', 0); bar('roll', 0);
    } else {
      // The preview is mirrored like a mirror; mirror the overlay too.
      const [bx, y, w, h] = f.box.map(v => v * 1000), x = 1000 - bx - w, good = f.quality === 'good', col = good ? '#34A853' : '#FBBC04', L = Math.min(w, h) * .22;
      const corners = [[x, y, 1, 1], [x + w, y, -1, 1], [x + w, y + h, -1, -1], [x, y + h, 1, -1]]
        .map(([cx, cy, dx, dy]) => `<path d="M${cx} ${cy + dy * L}V${cy}H${cx + dx * L}" fill="none" stroke="${col}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>`).join('');
      const dots = f.landmarks.map(([lx, ly], i) => `<circle cx="${(1 - lx) * 1000}" cy="${ly * 1000}" r="6" fill="${['#4285F4', '#EA4335', '#FBBC04', '#34A853', '#34A853'][i]}"/>`).join('');
      ov.innerHTML = corners + dots;
      $('#perc-chips').innerHTML = good ? `<span class="chip ok">${Art.icon('check', 'sm')}Good capture</span>`
        : `<span class="chip warn">${Art.icon('warning', 'sm')}${esc(f.quality)}</span>`;
      $('#perc-score').textContent = Math.round(f.score * 100) + '%';
      bar('yaw', -f.yaw); bar('pitch', f.pitch); bar('roll', f.roll);
    }
    await sleep(15);
  }
  },
};

window.App = App;
document.addEventListener('DOMContentLoaded', () => App.init());
