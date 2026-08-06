/**
 * Dynamic Page Templates — Dynamic Canvas Structured Telemetry & Layout
 */
const Pages = {
    async overview() {
        const m = await Api.call('get_metrics'), users = await Api.call('get_users');
        const count = users ? users.length : (m.registeredUsersCount || 0), thresh = (m.matchingThreshold * 100).toFixed(0);
        return `
            <div class="page-enter overview-structured-grid">
                <div class="metrics-top-bar gsap-hidden">
                    <div class="metric-block"><div class="hero-label">ANTI-SPOOF LIVENESS</div><div class="hero-number" style="font-size:36px; background:var(--orange-grad); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">${m.livenessEnabled ? 'ACTIVE' : 'OFF'}</div><div class="meta-value">LBP Texture & Blink Gate</div></div>
                    <div class="metric-block"><div class="hero-label">CAMERA PIPELINE</div><div class="hero-number" style="font-size:36px;">${m.cameraActive ? 'LIVE' : 'IDLE'}</div><div class="meta-value">OpenCV Video Frame Loop</div></div>
                    <div class="metric-block"><div class="hero-label">COSINE THRESHOLD</div><div class="hero-number" style="font-size:36px;">${thresh}%</div><div class="meta-value">Identity Match Score Cutoff</div></div>
                    <div class="metric-block"><div class="hero-label">PAM SECURITY GATE</div><div class="hero-number" style="font-size:36px; color:#10B981;">ONLINE</div><div class="meta-value">Linux Auth Listener Active</div></div>
                </div>
                <div class="main-workspace-row">
                    <div class="workspace-main-panel gsap-hidden">
                        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:16px;"><div class="hero-label" style="font-size:12px; letter-spacing:2.5px; margin:0;">ENROLLED IDENTITIES (${count})</div></div>
                        ${users.length === 0 ? `<div style="padding:24px 0;"><button class="btn btn-spline-center" onclick="App.navigateTo('enrollment')">+ ENROLL NEW IDENTITY</button><p class="subtext-hero">Zero identities enrolled. Register a 128D face template for Unix PAM biometric authentication.</p></div>` : `
                            <div class="user-list-container">
                                ${users.map(u => `
                                    <div class="user-row" style="max-width:100%;">
                                        <div class="user-avatar">${u.username.substring(0,2).toUpperCase()}</div>
                                        <div class="user-info"><div class="user-name">${u.username}</div><div class="user-id">ID: ${u.userId}</div></div>
                                        <span class="user-tag">128D VECTOR</span>
                                        <div style="display:flex; align-items:center; gap:8px;">
                                            <button class="btn-icon-secondary" title="Edit Identity Details" onclick="App.openEditModal('${u.userId}', '${u.username.replace(/'/g, "\\'")}')"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg></button>
                                            <button class="btn-icon-danger" title="Remove User" onclick="App.deleteUser('${u.userId}')"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg></button>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                            <p class="subtext-hero" style="font-size:12px; margin-top:16px;">FaceLock bio-encryption active. Ready for Linux PAM unlock.</p>
                        `}
                    </div>
                    <div class="workspace-side-panel gsap-hidden">
                        <div class="hero-label" style="margin-bottom:16px;">SYSTEM DIAGNOSTICS</div>
                        <div class="sys-row"><div><span class="sys-dot"></span><span>OpenCV Frame Pipeline</span></div><strong>${m.cameraActive?'ACTIVE':'READY'}</strong></div>
                        <div class="sys-row"><div><span class="sys-dot"></span><span>Haar Cascade Detector</span></div><strong>OK</strong></div>
                        <div class="sys-row"><div><span class="sys-dot"></span><span>PAM Listener Socket</span></div><strong>ONLINE</strong></div>
                        <div class="sys-row"><div><span class="sys-dot"></span><span>AES-256 Storage Gate</span></div><strong>ENCRYPTED</strong></div>
                        <div style="margin-top:24px; padding-top:20px; border-top:1px solid var(--border);"><div class="hero-label">DAEMON SOCKET IPC</div><div class="meta-value" style="margin-top:6px;">Unix Domain Socket active at <code>~/.facelock/facelock.sock</code></div></div>
                    </div>
                </div>
            </div>`;
    },

    async enrollment() {
        return `
            <div class="page-enter" style="width:100%; height:100%;">
                <div style="display:grid; grid-template-columns: 340px 1fr; gap:36px; align-items:stretch; height:100%;">
                    <div class="gsap-hidden">
                        <div class="section-title" style="margin-bottom:20px;">BIOMETRIC CREDENTIALS</div>
                        <form onsubmit="App.handleEnroll(event)">
                            <div class="form-group"><label class="form-label">USER ID</label><input type="text" id="enroll-id" class="form-input" placeholder="usr_101" required></div>
                            <div class="form-group"><label class="form-label">FULL NAME</label><input type="text" id="enroll-name" class="form-input" placeholder="Alice Smith" required></div>
                            <div class="form-group"><label class="form-label">PASSPHRASE</label><input type="password" id="enroll-secret" class="form-input" placeholder="Master key" required></div>
                            <button type="submit" class="btn btn-accent" style="width:100%; justify-content:center; margin-top:8px;">CAPTURE & ENROLL</button>
                            <div id="enroll-msg" class="meta-value" style="margin-top:14px; text-align:center;"></div>
                        </form>
                        <div style="margin-top:24px; padding-top:16px; border-top:1px solid var(--border);">
                            <div class="section-title" style="font-size:13px; margin-bottom:8px;">ENROLLMENT CHECKLIST</div>
                            <div class="sys-row"><div><span class="sys-dot"></span><span>Center face in camera view</span></div></div>
                            <div class="sys-row"><div><span class="sys-dot"></span><span>Ensure bright ambient light</span></div></div>
                        </div>
                    </div>
                    <div class="gsap-hidden" style="display:flex; flex-direction:column; gap:12px; height:100%;">
                        <div style="display:flex; align-items:center; justify-content:space-between;"><span class="section-title">HIGH-RESOLUTION VIEWPORT</span><span class="status-pill"><span class="pulse-dot"></span>RAW CAMERA STREAM</span></div>
                        <img id="camera-stream" class="camera-feed-lg" alt="Camera" src="data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='640' height='480'><rect fill='%230F172A'/></svg>">
                    </div>
                </div>
            </div>`;
    },

    async perception() {
        return `
            <div class="page-enter" style="width:100%; height:100%;">
                <div style="display:grid; grid-template-columns: 1fr 340px; gap:40px; align-items:stretch; height:100%;">
                    <div class="gsap-hidden" style="display:flex; flex-direction:column; gap:12px; height:100%;">
                        <div style="display:flex; align-items:center; justify-content:space-between;"><span class="section-title">PERCEPTION CAMERA FEED</span><span class="status-pill"><span class="pulse-dot"></span>30 FPS REAL-TIME</span></div>
                        <img id="camera-stream" class="camera-feed-lg" alt="Camera" src="data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='640' height='480'><rect fill='%230F172A'/></svg>">
                    </div>
                    <div class="gsap-hidden">
                        <div class="section-title" style="margin-bottom:16px;">LIVE TELEMETRY</div>
                        <div class="sys-row"><span>Frame Resolution</span><strong>640 x 480 px</strong></div>
                        <div class="sys-row"><span>Cascade Engine</span><strong>OpenCV Haar</strong></div>
                        <div class="sys-row"><span>Liveness Analyzer</span><strong>LBP Texture Gate</strong></div>
                        <div class="sys-row"><span>Matching Model</span><strong>128D Cosine Sim</strong></div>
                        <div style="margin-top:24px; padding-top:16px; border-top:1px solid var(--border);"><div class="hero-label">IPC SOCKET DAEMON</div><div class="meta-value">Unix Domain Socket listener active at <code>~/.facelock/facelock.sock</code> for Linux PAM login.</div></div>
                    </div>
                </div>
            </div>`;
    },

    async settings() {
        const m = await Api.call('get_metrics'), t = (m.matchingThreshold * 100).toFixed(0);
        return `
            <div class="page-enter" style="max-width:1150px; margin:0 auto; padding-bottom:40px;">
                <div style="display:grid; grid-template-columns: 1fr 380px; gap:44px; align-items:start;">
                    <div class="gsap-hidden">
                        <div class="section-title" style="margin-bottom:12px;">SECURITY CONFIGURATION</div>
                        <p class="meta-value" style="margin-bottom:24px;">Adjust system sensitivity and anti-spoof protection thresholds for Linux PAM login verification.</p>
                        <form onsubmit="App.handleSaveSettings(event)">
                            <div class="setting-row"><div><div class="setting-label">COSINE THRESHOLD</div><div class="setting-desc">Minimum vector similarity required to match face</div></div><div style="display:flex;align-items:center;gap:14px;"><input type="range" id="setting-threshold" min="40" max="95" value="${t}" oninput="document.getElementById('thresh-val').textContent=this.value+'%'"><span id="thresh-val" class="hero-number" style="font-size:24px;">${t}%</span></div></div>
                            <div class="setting-row"><div><div class="setting-label">ANTI-SPOOF LIVENESS</div><div class="setting-desc">Reject photos, screens, & texture spoofs</div></div><input type="checkbox" id="setting-liveness" ${m.livenessEnabled?'checked':''} style="width:20px;height:20px;accent-color:#2563EB;"></div>
                            <div style="margin-top:28px;display:flex;align-items:center;justify-content:space-between;"><span id="settings-msg" class="meta-value"></span><button type="submit" class="btn btn-accent">SAVE CONFIG</button></div>
                        </form>
                    </div>
                    <div class="gsap-hidden">
                        <div class="section-title" style="margin-bottom:12px;">WHAT IS COSINE THRESHOLD?</div>
                        <div class="meta-value" style="margin-bottom:16px;">It sets the mathematical similarity cutoff score (40%-95%) for comparing two 128D facial feature vectors. Higher values increase strictness against false matches.</div>
                        <div class="sys-row"><span>Key Derivation</span><strong>PBKDF2 (100k)</strong></div>
                        <div class="sys-row"><span>Vector Storage</span><strong>AES-256-GCM</strong></div>
                        <div class="sys-row"><span>Max Auth Lockout</span><strong>3 Failures</strong></div>
                    </div>
                </div>
            </div>`;
    },

    async logs() {
        const logs = await Api.call('get_logs') || [];
        const total = logs.length, okCount = logs.filter(l => l.status === 'OK').length;
        return `
            <div class="page-enter" style="max-width:1150px; margin:0 auto; padding-bottom:40px;">
                <div class="gsap-hidden">
                    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:24px;">
                        <div><span class="section-title">SECURITY AUDIT LOGS</span><div class="meta-value" style="margin-top:4px;">Total Events Recorded: <strong>${total}</strong> | Authentications: <strong>${okCount} OK</strong></div></div>
                        <button class="btn btn-secondary" style="font-size:12px; padding:8px 16px;" onclick="App.clearLogs()">CLEAR HISTORY</button>
                    </div>
                    <div>
                        ${logs.length === 0 ? '<div class="empty-state">No audit log records found in SQLite database.</div>' : ''}
                        ${logs.map(l => `<div class="log-row"><div class="log-event">${l.event}</div><div class="log-user">${l.user}</div><div class="log-status ${l.status === 'OK' ? 'ok' : 'fail'}">${l.status}</div><div class="log-time">${l.ts}</div></div>`).join('')}
                    </div>
                </div>
            </div>`;
    }
};
window.Pages = Pages;
