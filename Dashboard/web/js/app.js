/**
 * Application Controller — 60FPS GSAP Circle Zoom & Centered Large Text Reveal
 */
const App = {
    currentPage: 'overview', cameraTimer: null, isSidebarOpen: false,

    async init() {
        this.bindEvents();
        await this.renderPage(this.currentPage);
    },

    bindEvents() {
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', e => this.navigateTo(e.currentTarget.dataset.page));
        });
        window.addEventListener('pywebviewready', () => this.renderPage(this.currentPage));
    },

    toggleSidebar() {
        this.isSidebarOpen = !this.isSidebarOpen;
        const fill = document.getElementById('sidebar-fill-bg'), drawer = document.getElementById('sidebar-drawer'), btn = document.getElementById('menu-btn');
        if (!btn) return;
        const rect = btn.getBoundingClientRect(), cx = Math.round(rect.left + rect.width / 2), cy = Math.round(rect.top + rect.height / 2);
        if (this.isSidebarOpen) {
            fill.classList.add('open'); drawer.classList.add('open');
            if (typeof gsap !== 'undefined') {
                gsap.set(drawer, { opacity: 1 });
                gsap.fromTo(fill, { clipPath: `circle(0px at ${cx}px ${cy}px)` }, { clipPath: `circle(160% at ${cx}px ${cy}px)`, duration: 0.65, ease: 'power4.inOut' });
                gsap.fromTo('.sidebar-header, .nav-item', { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.55, stagger: 0.06, ease: 'power3.out', delay: 0.15 });
            }
        } else if (typeof gsap !== 'undefined') {
            gsap.to('.sidebar-header, .nav-item', { opacity: 0, y: -20, duration: 0.2, ease: 'power2.in' });
            gsap.to(fill, { clipPath: `circle(0px at ${cx}px ${cy}px)`, duration: 0.55, ease: 'power4.inOut', delay: 0.05, onComplete: () => { fill.classList.remove('open'); drawer.classList.remove('open'); } });
        } else { fill.classList.remove('open'); drawer.classList.remove('open'); }
    },

    navigateTo(page) {
        if (this.isSidebarOpen) this.toggleSidebar();
        if (this.currentPage === page) return;
        document.querySelectorAll('.nav-item').forEach(el => el.classList.toggle('active', el.dataset.page === page));
        this.currentPage = page;
        const titles = { overview:'OVERVIEW', enrollment:'ENROLLMENT', perception:'PERCEPTION', settings:'CONFIGURATION', logs:'SECURITY LOGS' };
        const pt = document.getElementById('page-title');
        if (pt) pt.textContent = titles[page] || 'FACELOCK';
        this.renderPage(page);
    },

    async renderPage(page) {
        const container = document.getElementById('page-container');
        this.stopCameraLoop();
        if (typeof gsap !== 'undefined') await gsap.to(container, { opacity: 0, y: 15, duration: 0.15, ease: 'power2.in' });
        if (Pages[page]) container.innerHTML = await Pages[page]();
        if (typeof gsap !== 'undefined') {
            gsap.set(container, { opacity: 1, y: 0 });
            const hidden = container.querySelectorAll('.gsap-hidden');
            gsap.fromTo(hidden, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.5, stagger: 0.08, ease: 'power3.out' });
        }
        if (page === 'enrollment' || page === 'perception') {
            await Api.call('toggle_camera', true);
            this.startCameraLoop();
        }
    },

    startCameraLoop() {
        this.stopCameraLoop();
        this.cameraTimer = setInterval(async () => {
            const img = document.getElementById('camera-stream');
            if (img) { const b = await Api.call('get_camera_frame'); if (b) img.src = b; }
        }, 100);
    },

    stopCameraLoop() { if (this.cameraTimer) { clearInterval(this.cameraTimer); this.cameraTimer = null; } },
    async deleteUser(uid) { await Api.call('delete_user', uid); await this.renderPage(this.currentPage); },
    openEditModal(uid, username) {
        document.getElementById('edit-orig-userid').value = uid;
        document.getElementById('edit-userid').value = uid;
        document.getElementById('edit-username').value = username;
        document.getElementById('edit-modal-backdrop').style.display = 'flex';
    },
    closeEditModal() { document.getElementById('edit-modal-backdrop').style.display = 'none'; },
    async submitEditModal(e) {
        e.preventDefault();
        const origId = document.getElementById('edit-orig-userid').value, newId = document.getElementById('edit-userid').value.trim(), newName = document.getElementById('edit-username').value.trim();
        if (origId && newId && newName) { await Api.call('update_user', origId, newId, newName); this.closeEditModal(); await this.renderPage(this.currentPage); }
    },
    async clearLogs() { if (confirm('Are you sure you want to clear all security audit logs?')) { await Api.call('clear_logs'); await this.renderPage(this.currentPage); } },
    installedOSApps: [],
    async openAddAppModal() {
        document.getElementById('app-modal-backdrop').style.display = 'flex';
        this.installedOSApps = await Api.call('get_system_installed_apps') || [];
        this.renderInstalledAppsGrid(this.installedOSApps);
    },
    closeAddAppModal() { document.getElementById('app-modal-backdrop').style.display = 'none'; },
    renderInstalledAppsGrid(apps) {
        const grid = document.getElementById('installed-apps-grid');
        if (!grid) return;
        if (!apps.length) { grid.innerHTML = '<div class="meta-value" style="padding:12px;">No matching applications found.</div>'; return; }
        grid.innerHTML = apps.map(a => `<div onclick="App.protectInstalledApp('${encodeURIComponent(JSON.stringify(a))}')" style="display:flex; align-items:center; justify-content:space-between; background:#181818; border:1px solid var(--border); border-radius:10px; padding:10px 14px; cursor:pointer;"><div style="display:flex; align-items:center; gap:12px; overflow:hidden;"><div style="color:#2563EB; display:flex; align-items:center; flex-shrink:0;">${appIcons[a.icon] || appIcons.app}</div><div style="overflow:hidden;"><div style="font-size:13px; font-weight:600; color:var(--text-primary); text-overflow:ellipsis; overflow:hidden; white-space:nowrap;">${a.name}</div><div style="font-size:10px; color:var(--text-dim); font-family:monospace; text-overflow:ellipsis; overflow:hidden; white-space:nowrap;">${a.cmd}</div></div></div><span style="font-size:10px; font-weight:700; color:#60A5FA; background:rgba(37,99,235,0.15); padding:4px 10px; border-radius:12px; flex-shrink:0;">+ LOCK</span></div>`).join('');
    },
    filterInstalledApps(q) {
        const raw = (q || '').toLowerCase().trim(), norm = raw.replace(/[\s\-_]+/g, ''), tokens = raw.split(/\s+/).filter(Boolean);
        if (!raw) { this.renderInstalledAppsGrid(this.installedOSApps); return; }
        const res = this.installedOSApps.filter(a => {
            const full = `${a.name} ${a.cmd} ${a.kw || ''}`.toLowerCase(), fullNorm = full.replace(/[\s\-_]+/g, '');
            if (fullNorm.includes(norm)) return true;
            return tokens.every(t => full.includes(t) || (t === 'vs' && full.includes('visual')) || (t === 'code' && full.includes('code')));
        });
        this.renderInstalledAppsGrid(res);
    },
    async protectInstalledApp(enc) {
        const a = JSON.parse(decodeURIComponent(enc));
        await Api.call('add_protected_app', a.name, a.cmd, a.icon);
        this.closeAddAppModal();
        await this.refreshProtectedAppsList();
    },
    async removeApp(appId) {
        await Api.call('remove_protected_app', appId);
        await this.refreshProtectedAppsList();
    },
    async refreshProtectedAppsList() {
        const apps = await Api.call('get_protected_apps') || [];
        const container = document.getElementById('protected-apps-list');
        if (!container) return;
        container.innerHTML = apps.length === 0 ? '<div class="meta-value">No custom applications protected yet. Click + ADD APP to secure software.</div>' : apps.map(a => `<div style="display:flex; align-items:center; justify-content:space-between; background:#181818; border:1px solid var(--border); border-radius:10px; padding:10px 14px;"><div style="display:flex; align-items:center; gap:12px;"><div style="color:#2563EB; display:flex; align-items:center;">${appIcons[a.icon] || appIcons.app}</div><div><div style="font-size:13px; font-weight:600; color:var(--text-primary);">${a.name}</div><div style="font-size:10px; color:var(--text-dim); font-family:monospace;">${a.cmd}</div></div></div><div style="display:flex; align-items:center; gap:8px;"><button class="btn btn-secondary" style="font-size:10px; padding:4px 8px; font-weight:700; color:#60A5FA; border-color:rgba(37,99,235,0.4);" onclick="App.launchApp('${a.id}')" title="Real-Time FaceLock Gate Launch">⚡ LAUNCH</button><button class="btn-icon-danger" style="width:24px; height:24px;" title="Remove App Protection" onclick="App.removeApp('${a.id}')"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button></div></div>`).join('');
    },
    async launchApp(appId) { await Api.call('launch_protected_app', appId); },
    async handleEnroll(e) {
        e.preventDefault();
        const msg = document.getElementById('enroll-msg');
        msg.textContent = 'Capturing template...';
        const r = await Api.call('enroll_user', document.getElementById('enroll-id').value, document.getElementById('enroll-name').value, document.getElementById('enroll-secret').value);
        msg.textContent = r.msg || 'Done';
        if (r && r.ok) setTimeout(() => this.navigateTo('overview'), 900);
    },
    async handleSaveSettings(e) {
        e.preventDefault();
        const r = await Api.call('save_settings', parseFloat(document.getElementById('setting-threshold').value) / 100, document.getElementById('setting-liveness').checked);
        const msg = document.getElementById('settings-msg');
        msg.textContent = r.msg || 'Saved';
        setTimeout(() => { if (msg) msg.textContent = ''; }, 3000);
    }
};

window.App = App;
document.addEventListener('DOMContentLoaded', () => App.init());
