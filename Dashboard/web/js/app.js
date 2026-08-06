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
        const fill = document.getElementById('sidebar-fill-bg');
        const drawer = document.getElementById('sidebar-drawer');
        const btn = document.getElementById('menu-btn');
        if (!btn) return;
        const rect = btn.getBoundingClientRect();
        const cx = Math.round(rect.left + rect.width / 2);
        const cy = Math.round(rect.top + rect.height / 2);

        if (this.isSidebarOpen) {
            fill.classList.add('open'); drawer.classList.add('open');
            if (typeof gsap !== 'undefined') {
                gsap.set(drawer, { opacity: 1 });
                gsap.fromTo(fill, { clipPath: `circle(0px at ${cx}px ${cy}px)` }, { clipPath: `circle(160% at ${cx}px ${cy}px)`, duration: 0.65, ease: 'power4.inOut' });
                gsap.fromTo('.sidebar-header, .nav-item', { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.55, stagger: 0.06, ease: 'power3.out', delay: 0.15 });
            }
        } else {
            if (typeof gsap !== 'undefined') {
                gsap.to('.sidebar-header, .nav-item', { opacity: 0, y: -20, duration: 0.2, ease: 'power2.in' });
                gsap.to(fill, {
                    clipPath: `circle(0px at ${cx}px ${cy}px)`, duration: 0.55, ease: 'power4.inOut', delay: 0.05,
                    onComplete: () => { fill.classList.remove('open'); drawer.classList.remove('open'); }
                });
            } else { fill.classList.remove('open'); drawer.classList.remove('open'); }
        }
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
