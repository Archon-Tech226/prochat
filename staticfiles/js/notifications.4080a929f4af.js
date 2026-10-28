// static/js/notifications.js
// ProChat Notification WebSocket Client

(function() {
    if (!document.body) return;

    // Only connect if user is logged in (check for sidebar)
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar) return;

    const wsUrl = `ws://${window.location.host}/ws/notifications/`;
    let ws;
    let reconnectTimer;

    function connect() {
        try {
            ws = new WebSocket(wsUrl);
        } catch(e) {
            console.log('WebSocket not available — dev mode');
            return;
        }

        ws.onopen = () => {
            console.log('Notifications connected');
            // Clear reconnect timer on successful connect
            if (reconnectTimer) clearTimeout(reconnectTimer);
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.type === 'unread_count') {
                updateBadge(data.count);
            } else if (data.type === 'notification') {
                showToast(data.title, data.body, data.notif_type);
                // Increment badge
                const badge = document.getElementById('notif-count');
                if (badge) {
                    const current = parseInt(badge.textContent || '0');
                    updateBadge(current + 1);
                }
            }
        };

        ws.onclose = (e) => {
            // Only reconnect if not a normal closure
            if (e.code !== 1000) {
                reconnectTimer = setTimeout(connect, 5000);
            }
        };

        ws.onerror = (e) => {
            // Silently fail in dev mode — no console spam
            console.log('Notification WS unavailable (run with Daphne for WebSocket support)');
        };
    }

    function updateBadge(count) {
        const badge = document.getElementById('notif-count');
        const unreadBadge = document.getElementById('unread-badge');

        if (count > 0) {
            if (badge) { badge.textContent = count; badge.style.display = 'block'; }
            if (unreadBadge) { unreadBadge.textContent = count; unreadBadge.style.display = 'inline-block'; }
        } else {
            if (badge) badge.style.display = 'none';
            if (unreadBadge) unreadBadge.style.display = 'none';
        }
    }

    function showToast(title, body, type) {
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed;
            bottom: 80px;
            right: 20px;
            background: var(--bg2);
            border: 1px solid var(--border3);
            border-radius: 12px;
            padding: 12px 16px;
            max-width: 300px;
            z-index: 9999;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
            animation: fadeUp 0.3s ease;
            font-family: var(--font);
        `;

        const icons = { message: '💬', meeting: '📹', task: '✓', payment: '💳', system: '⬡' };
        const icon = icons[type] || '🔔';

        toast.innerHTML = `
            <div style="display:flex;align-items:flex-start;gap:10px">
                <span style="font-size:18px">${icon}</span>
                <div style="flex:1">
                    <div style="font-size:13px;font-weight:600;color:var(--text);margin-bottom:2px">${title}</div>
                    <div style="font-size:12px;color:var(--text3)">${body}</div>
                </div>
                <span style="cursor:pointer;color:var(--text3);font-size:16px" onclick="this.parentElement.parentElement.remove()">×</span>
            </div>
        `;

        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 5000);
    }

    // Start connection
    connect();
})();