/**
 * ARGUS Mission Control - Main Application
 * Initializes all components and handles global interactions
 */

// Track when we last received a heartbeat
let lastHeartbeatTime = null;

document.addEventListener('DOMContentLoaded', () => {
    console.log('ARGUS Mission Control initializing...');
    initializeApp();
});

async function initializeApp() {
    try {
        // Load system config
        const config = await window.API.getConfig();
        if (window.AppState) {
            window.AppState.setConfig(config);
        }
        console.log('Config loaded:', config);

        // Initialize MET clock
        if (window.METClock) {
            await window.METClock.init();
        }

        // Initialize ground time clock
        if (window.GroundTimeClock) {
            window.GroundTimeClock.start();
        }

        // Initialize WebSocket connection
        if (window.TelemetryWS) {
            window.TelemetryWS.connect();
        }

        // Initialize telemetry tiles
        if (window.TelemetryTiles) {
            window.TelemetryTiles.init();
        }

        // Initialize command strip
        if (window.CommandStrip) {
            window.CommandStrip.init();
        }

        // Setup E-STOP handler
        setupEStopHandler();

        // Start polling at 2s interval (primary data fetch mechanism)
        startPolling();

        // Start heartbeat age ticker (updates the display every second)
        startHeartbeatAgeTicker();

        console.log('ARGUS Mission Control initialized successfully');

    } catch (err) {
        console.error('Error initializing application:', err);
    }
}

// ==================== POLLING (every 2s) ====================

function startPolling() {
    console.log('Starting telemetry polling (2s interval)...');

    // Immediate first fetch
    pollTelemetry();
    pollCommandQueue();

    // Then repeat every 2 seconds
    setInterval(pollTelemetry, 2000);
    setInterval(pollCommandQueue, 5000);
}

async function pollTelemetry() {
    try {
        const telemetry = await window.API.getLatestTelemetry('nominal');
        if (telemetry && telemetry.rx_data) {
            const data = telemetry.rx_data;
            if (data.CDH) {
                window.AppState.updateTelemetry('CDH', data.CDH);

                // Record heartbeat arrival time
                lastHeartbeatTime = Date.now();
                updateHeartbeatAgeDisplay(0);
            }
            if (data.EPS) window.AppState.updateTelemetry('EPS', data.EPS);
            if (data.ADCS) window.AppState.updateTelemetry('ADCS', data.ADCS);
            if (data.GPS) window.AppState.updateTelemetry('GPS', data.GPS);
        }

        // Link status
        const linkStatus = await window.API.getLinkStatus();
        if (window.AppState && linkStatus) {
            window.AppState.setLinkStatus(
                linkStatus.status,
                linkStatus.last_contact,
                linkStatus.last_tm_age_seconds
            );

            // Update link indicator in topbar
            if (window.TelemetryWS) {
                window.TelemetryWS.updateLinkIndicator(
                    linkStatus.status,
                    linkStatus.last_tm_age_seconds
                );
            }
        }

    } catch (err) {
        // Silently fail - backend may not be running
    }
}

async function pollCommandQueue() {
    try {
        const queue = await window.API.getCommandQueue();
        if (window.AppState) {
            window.AppState.setCommandQueue(queue);
        }
        document.dispatchEvent(new CustomEvent('commands:update', {
            detail: { queue }
        }));
    } catch (err) {
        // Silently fail
    }
}

// ==================== HEARTBEAT AGE ====================

function startHeartbeatAgeTicker() {
    // Update the heartbeat age display every second
    setInterval(() => {
        if (lastHeartbeatTime === null) {
            updateHeartbeatAgeDisplay(null);
            return;
        }
        const ageSeconds = Math.floor((Date.now() - lastHeartbeatTime) / 1000);
        updateHeartbeatAgeDisplay(ageSeconds);
    }, 1000);
}

function updateHeartbeatAgeDisplay(ageSeconds) {
    const el = document.getElementById('heartbeat-age-display');
    if (!el) return;

    if (ageSeconds === null) {
        el.textContent = '-- s';
        el.style.color = 'var(--argus-muted)';
        return;
    }

    el.textContent = `${ageSeconds} s`;

    // Color coding: green <10s, yellow <30s, red >=30s
    if (ageSeconds < 10) {
        el.style.color = 'var(--argus-success)';
    } else if (ageSeconds < 30) {
        el.style.color = 'var(--argus-warning)';
    } else {
        el.style.color = 'var(--argus-danger)';
    }
}

// ==================== E-STOP ====================

function setupEStopHandler() {
    const estopBtn = document.getElementById('estop-btn');
    const modal = document.getElementById('estop-modal');
    const cancelBtn = document.getElementById('estop-cancel');
    const confirmBtn = document.getElementById('estop-confirm');

    if (!estopBtn || !modal) return;

    estopBtn.addEventListener('click', () => {
        modal.classList.add('active');
    });

    cancelBtn.addEventListener('click', () => {
        modal.classList.remove('active');
    });

    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('active');
        }
    });

    confirmBtn.addEventListener('click', async () => {
        try {
            confirmBtn.disabled = true;
            confirmBtn.textContent = 'SENDING...';

            const result = await window.API.sendEStop();

            if (result.success) {
                confirmBtn.textContent = 'SENT';
                confirmBtn.style.backgroundColor = 'var(--argus-success)';

                setTimeout(() => {
                    modal.classList.remove('active');
                    confirmBtn.disabled = false;
                    confirmBtn.textContent = 'CONFIRM E-STOP';
                    confirmBtn.style.backgroundColor = '';
                }, 1500);

            } else {
                throw new Error(result.error || 'E-STOP failed');
            }

        } catch (err) {
            console.error('E-STOP error:', err);
            confirmBtn.textContent = 'ERROR - RETRY';
            confirmBtn.disabled = false;
        }
    });

    // Keyboard shortcut: Ctrl+Shift+E for E-STOP
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.shiftKey && e.key === 'E') {
            e.preventDefault();
            modal.classList.add('active');
        }

        if (e.key === 'Escape' && modal.classList.contains('active')) {
            modal.classList.remove('active');
        }
    });
}
