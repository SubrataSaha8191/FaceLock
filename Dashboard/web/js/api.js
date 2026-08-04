/**
 * FaceLock Web Bridge API Handler — Dynamic PyWebView IPC Resolver
 */
const Api = {
    _mockUsers: [],

    async waitForPyWebView() {
        if (window.pywebview && window.pywebview.api) return true;
        return new Promise(resolve => {
            const timer = setTimeout(() => resolve(false), 2000);
            const check = () => {
                if (window.pywebview && window.pywebview.api) {
                    clearTimeout(timer);
                    resolve(true);
                } else {
                    setTimeout(check, 50);
                }
            };
            window.addEventListener('pywebviewready', () => {
                clearTimeout(timer);
                resolve(true);
            }, { once: true });
            check();
        });
    },

    async call(fnName, ...args) {
        await this.waitForPyWebView();
        if (window.pywebview && window.pywebview.api && window.pywebview.api[fnName]) {
            try {
                return await window.pywebview.api[fnName](...args);
            } catch (err) {
                console.error(`API Error on ${fnName}:`, err);
            }
        }
        return this.getMockData(fnName, ...args);
    },

    getMockData(fnName, ...args) {
        if (fnName === 'get_metrics') {
            return {
                registeredUsersCount: 0,
                cameraActive: false, livenessEnabled: true,
                matchingThreshold: 0.6, daemonActive: true
            };
        }
        if (fnName === 'get_users') return [];
        if (fnName === 'delete_user') return { ok: true, msg: 'User deleted' };
        if (fnName === 'get_logs') return [];
        if (fnName === 'save_settings') return { ok: true, msg: 'Settings saved' };
        if (fnName === 'enroll_user') return { ok: true, msg: 'User enrolled' };
        if (fnName === 'toggle_camera') return { ok: true };
        return {};
    }
};

window.Api = Api;
