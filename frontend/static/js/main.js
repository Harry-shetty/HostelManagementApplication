// Nestora Housing Main JavaScript & Real-Time Socket.IO Client
document.addEventListener('DOMContentLoaded', () => {
    // -------------------------------------------------------------
    // Keyboard Shortcuts & Global Modal Controls
    // -------------------------------------------------------------
    document.addEventListener('keydown', (e) => {
        // CMD/CTRL + K to focus search
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.getElementById('hostel-search-input') || document.querySelector('.search-field input');
            if (searchInput) {
                searchInput.focus();
            }
        }
        // Escape key closes modals and drawer
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal-layer').forEach(modal => {
                modal.style.display = 'none';
            });
            if (typeof closeSidebar === 'function') {
                closeSidebar();
            }
        }
    });

    // Reset mobile sidebar when resizing window to desktop
    window.addEventListener('resize', () => {
        if (window.innerWidth > 800) {
            if (typeof closeSidebar === 'function') {
                closeSidebar();
            }
        }
    });

    // -------------------------------------------------------------
    // Real-Time Socket.IO Client
    // -------------------------------------------------------------
    initSocketIO();
});

/**
 * Real-Time Toast Notification Handler
 */
function showToast(title, message, level = 'info', duration = 5000) {
    const container = document.getElementById('nestora-toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast-message`;

    const iconMap = {
        'info': '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4m0-4h.01"/></svg>',
        'success': '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m5 12 4 4L19 6"/></svg>',
        'warning': '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4m0 4h.01"/></svg>',
        'danger': '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="m15 9-6 6m0-6 6 6"/></svg>'
    };

    const iconSvg = iconMap[level] || iconMap.info;
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    toast.innerHTML = `
        <div class="toast-icon ${level}">${iconSvg}</div>
        <div class="toast-content">
            <h4 class="toast-title">${title}</h4>
            <p class="toast-body">${message}</p>
            <span class="toast-time">${timeStr} · Live Sync</span>
        </div>
        <button type="button" class="toast-close" aria-label="Close notification" onclick="this.closest('.toast-message').remove()">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m6 6 12 12M18 6 6 18"/></svg>
        </button>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('toast-hide');
        setTimeout(() => toast.remove(), 260);
    }, duration);
}

/**
 * Initialize Socket.IO Client Connection & Real-Time Listeners
 */
function initSocketIO() {
    if (typeof io === 'undefined') {
        console.warn('Socket.IO client library not loaded. Live sync unavailable.');
        return;
    }

    try {
        const socket = io({
            transports: ['polling', 'websocket'],
            reconnectionAttempts: 15,
            reconnectionDelay: 1500,
            timeout: 20000
        });

        const indicators = document.querySelectorAll('.live-sync-indicator');

        const updateStatus = (isOnline) => {
            indicators.forEach(ind => {
                if (isOnline) {
                    ind.classList.remove('offline');
                    ind.innerHTML = '<span class="live-dot"></span>LIVE';
                    ind.setAttribute('title', 'Real-Time Sync: Connected');
                } else {
                    ind.classList.add('offline');
                    ind.innerHTML = '<span class="live-dot"></span>OFFLINE';
                    ind.setAttribute('title', 'Real-Time Sync: Disconnected / Reconnecting');
                }
            });
        };

        socket.on('connect', () => {
            console.log(`%c[Nestora Live]%c Connected to Socket.IO (ID: ${socket.id})`, 'color: #2e7d32; font-weight: bold;', 'color: inherit;');
            updateStatus(true);

            // Subscribe to user role channel & bedmap updates
            const userRole = (window.NESTORA_USER && window.NESTORA_USER.role) || 'student';
            socket.emit('subscribe', { channel: 'bedmap', role: userRole });
        });

        socket.on('disconnect', () => {
            console.warn('[Nestora Live] Socket.IO disconnected.');
            updateStatus(false);
        });

        socket.on('connect_error', () => {
            updateStatus(false);
        });

        // -------------------------------------------------------------
        // Live Event: In-App Notification
        // -------------------------------------------------------------
        socket.on('notification', (data) => {
            if (!data) return;
            showToast(data.title || 'New Notification', data.message || '', data.level || 'info');

            // Pulse bell icon
            const bell = document.querySelector('.icon-btn.has-dot');
            if (bell) {
                bell.style.animation = 'notification-pulse 0.4s 3 ease-in-out';
                setTimeout(() => bell.style.animation = '', 1500);
            }
        });

        // -------------------------------------------------------------
        // Live Event: Bed Inventory Updated
        // -------------------------------------------------------------
        socket.on('bed_updated', (data) => {
            if (!data) return;
            console.log('[Nestora Live] Bed updated:', data);

            // Show real-time toast
            showToast(
                'Live Bed Inventory Update',
                `${data.bed_label} status updated to "${data.status}" (${data.student_name})`,
                data.status === 'occupied' ? 'warning' : 'success'
            );

            // Update interactive bed map if open on current page
            const roomButtons = document.querySelectorAll('.room-btn');
            roomButtons.forEach(btn => {
                const roomNum = btn.getAttribute('data-room');
                if (data.room_number && roomNum === data.room_number) {
                    btn.style.boxShadow = '0 0 0 3px rgba(200, 241, 105, 0.7)';
                    setTimeout(() => btn.style.boxShadow = '', 2000);
                }
            });
        });

        // -------------------------------------------------------------
        // Live Event: Allocation Override Applied
        // -------------------------------------------------------------
        socket.on('allocation_override', (data) => {
            if (!data) return;
            console.log('[Nestora Live] Allocation override:', data);

            showToast(
                'Allocation Override',
                `${data.student_name} reallocated to ${data.new_bed}`,
                'info'
            );

            // If on Draft Review table, highlight updated cell
            const bedCell = document.querySelector('.rec-bed-label');
            if (bedCell) {
                bedCell.textContent = data.new_bed;
                bedCell.style.background = '#effbd3';
                setTimeout(() => bedCell.style.background = '', 2500);
            }
        });

        // -------------------------------------------------------------
        // Live Event: New Live Activity Feed Item
        // -------------------------------------------------------------
        socket.on('new_activity', (data) => {
            if (!data) return;
            const recentContainer = document.querySelector('.recent');
            if (recentContainer) {
                const row = document.createElement('div');
                row.style.animation = 'card-rise 0.4s ease';
                row.innerHTML = `
                    <span class="activity-dot"></span>
                    <p>
                        <strong>${data.action}</strong>
                        <small>${data.actor} &middot; ${data.time || 'Just now'}</small>
                    </p>
                `;
                const head = recentContainer.querySelector('.panel-head');
                if (head && head.nextSibling) {
                    recentContainer.insertBefore(row, head.nextSibling);
                } else {
                    recentContainer.appendChild(row);
                }
            }
        });

        // Expose globally for manual tests or page interactions
        window.NestoraLive = {
            socket,
            showToast
        };

    } catch (err) {
        console.error('Socket.IO initialization error:', err);
    }
}
