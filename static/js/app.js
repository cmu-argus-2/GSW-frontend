/**
 * ARGUS Mission Control - Main Application
 * Initializes all components and handles global interactions
 */

document.addEventListener('DOMContentLoaded', () => {
    console.log('ARGUS Mission Control initializing...');

    // Initialize components
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

        // Initial data fetch (fallback if WebSocket is slow)
        await fetchInitialData();

        console.log('ARGUS Mission Control initialized successfully');

    } catch (err) {
        console.error('Error initializing application:', err);
    }
}

async function fetchInitialData() {
    try {
        // Fetch initial telemetry
        const telemetry = await window.API.getLatestTelemetry('nominal');
        if (telemetry && telemetry.rx_data) {
            const data = telemetry.rx_data;
            if (data.CDH) window.AppState.updateTelemetry('CDH', data.CDH);
            if (data.EPS) window.AppState.updateTelemetry('EPS', data.EPS);
            if (data.ADCS) window.AppState.updateTelemetry('ADCS', data.ADCS);
            if (data.GPS) window.AppState.updateTelemetry('GPS', data.GPS);
        }

        // Fetch initial command queue
        const queue = await window.API.getCommandQueue();
        if (window.AppState) {
            window.AppState.setCommandQueue(queue);
        }

        // Fetch link status
        const linkStatus = await window.API.getLinkStatus();
        if (window.AppState && linkStatus) {
            window.AppState.setLinkStatus(
                linkStatus.status,
                linkStatus.last_contact,
                linkStatus.last_tm_age_seconds
            );
        }

    } catch (err) {
        console.warn('Error fetching initial data (may be in mock mode):', err);
    }
}

function setupEStopHandler() {
    const estopBtn = document.getElementById('estop-btn');
    const modal = document.getElementById('estop-modal');
    const cancelBtn = document.getElementById('estop-cancel');
    const confirmBtn = document.getElementById('estop-confirm');

    if (!estopBtn || !modal) return;

    // Open modal
    estopBtn.addEventListener('click', () => {
        modal.classList.add('active');
    });

    // Cancel
    cancelBtn.addEventListener('click', () => {
        modal.classList.remove('active');
    });

    // Click outside to close
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('active');
        }
    });

    // Confirm E-STOP
    confirmBtn.addEventListener('click', async () => {
        try {
            confirmBtn.disabled = true;
            confirmBtn.textContent = 'SENDING...';

            const result = await window.API.sendEStop();

            if (result.success) {
                confirmBtn.textContent = 'SENT';
                confirmBtn.style.backgroundColor = 'var(--argus-success)';

                // Close modal after short delay
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

        // Escape to close modal
        if (e.key === 'Escape' && modal.classList.contains('active')) {
            modal.classList.remove('active');
        }
    });
}

// Polling fallback for when WebSocket isn't available
function startPollingFallback() {
    console.log('Starting polling fallback...');

    setInterval(async () => {
        try {
            const telemetry = await window.API.getLatestTelemetry('nominal');
            if (telemetry && telemetry.rx_data) {
                const data = telemetry.rx_data;
                if (data.CDH) window.AppState.updateTelemetry('CDH', data.CDH);
                if (data.EPS) window.AppState.updateTelemetry('EPS', data.EPS);
                if (data.ADCS) window.AppState.updateTelemetry('ADCS', data.ADCS);
                if (data.GPS) window.AppState.updateTelemetry('GPS', data.GPS);
            }
        } catch (err) {
            // Silently fail
        }
    }, 2000);
}

// Export for testing
window.ARGUSApp = {
    initialize: initializeApp,
    fetchInitialData,
    startPollingFallback
};
