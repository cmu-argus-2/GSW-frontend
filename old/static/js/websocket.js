/**
 * ARGUS Mission Control - WebSocket Manager
 * Handles real-time telemetry streaming via Socket.IO
 */

class TelemetryWebSocket {
    constructor() {
        this.socket = null;
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.handlers = new Map();
    }

    connect() {
        if (this.socket) {
            console.log('WebSocket already initialized');
            return;
        }

        this.socket = io({
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionDelayMax: 5000,
            reconnectionAttempts: this.maxReconnectAttempts
        });

        this.setupEventHandlers();
    }

    setupEventHandlers() {
        // Connection events
        this.socket.on('connect', () => {
            console.log('WebSocket connected');
            this.connected = true;
            this.reconnectAttempts = 0;
            this.updateLinkIndicator('connected');
            this.subscribeToTelemetry();
        });

        this.socket.on('disconnect', (reason) => {
            console.log('WebSocket disconnected:', reason);
            this.connected = false;
            this.updateLinkIndicator('disconnected');
        });

        this.socket.on('connect_error', (error) => {
            console.error('WebSocket connection error:', error);
            this.reconnectAttempts++;
            if (this.reconnectAttempts >= this.maxReconnectAttempts) {
                console.error('Max reconnection attempts reached');
            }
        });

        // Telemetry events
        this.socket.on('telemetry_update', (data) => {
            this.handleTelemetryUpdate(data);
        });

        this.socket.on('link_status', (data) => {
            this.handleLinkStatus(data);
        });

        this.socket.on('command_queue', (data) => {
            this.handleCommandQueue(data);
        });

        this.socket.on('telemetry_error', (data) => {
            console.error('Telemetry error:', data.error);
        });

        // Subscription confirmation
        this.socket.on('subscription_confirmed', (data) => {
            console.log('Telemetry subscription confirmed:', data);
        });
    }

    subscribeToTelemetry() {
        if (!this.connected) return;

        this.socket.emit('subscribe_telemetry', {
            subsystems: ['CDH', 'EPS', 'ADCS', 'GPS'],
            interval: 1.0
        });
    }

    handleTelemetryUpdate(data) {
        const { subsystem, data: telemetryData, timestamp } = data;

        // Update global state
        if (window.AppState) {
            window.AppState.updateTelemetry(subsystem, telemetryData);
        }

        // Call registered handlers
        const handler = this.handlers.get(subsystem);
        if (handler) {
            handler(telemetryData);
        }

        // Dispatch DOM event for components
        document.dispatchEvent(new CustomEvent('telemetry:update', {
            detail: { subsystem, data: telemetryData, timestamp }
        }));

        // Update spacecraft time from CDH
        if (subsystem === 'CDH' && telemetryData.TIME) {
            const scTime = new Date(telemetryData.TIME * 1000);
            if (window.AppState) {
                window.AppState.setSpacecraftTime(scTime);
            }
            this.updateSpacecraftTimeDisplay(scTime);
        }
    }

    handleLinkStatus(data) {
        const { status, last_contact, last_tm_age_seconds } = data;

        if (window.AppState) {
            window.AppState.setLinkStatus(status, last_contact, last_tm_age_seconds);
        }

        this.updateLinkIndicator(status, last_tm_age_seconds);
    }

    handleCommandQueue(data) {
        if (window.AppState) {
            window.AppState.setCommandQueue(data.queue);
        }

        document.dispatchEvent(new CustomEvent('commands:update', {
            detail: { queue: data.queue }
        }));
    }

    updateLinkIndicator(status, lastTmAge = null) {
        const dot = document.getElementById('link-status-dot');
        const text = document.getElementById('link-status-text');
        const age = document.getElementById('link-age');

        if (dot) {
            dot.className = 'status-dot';
            if (status === 'connected') {
                dot.classList.add('connected');
            } else if (status === 'disconnected') {
                dot.classList.add('disconnected');
            } else {
                dot.classList.add('unknown');
            }
        }

        if (text) {
            text.textContent = status === 'connected' ? 'LIVE' : 'NO LINK';
        }

        if (age && lastTmAge !== null) {
            age.textContent = `Last: ${lastTmAge.toFixed(1)}s`;
        }
    }

    updateSpacecraftTimeDisplay(scTime) {
        const display = document.getElementById('sc-time-display');
        if (display && scTime) {
            display.textContent = scTime.toISOString().substr(11, 8);
        }
    }

    registerHandler(subsystem, callback) {
        this.handlers.set(subsystem, callback);
    }

    unregisterHandler(subsystem) {
        this.handlers.delete(subsystem);
    }

    requestCommandQueueUpdate() {
        if (this.connected) {
            this.socket.emit('command_queue_update');
        }
    }

    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
            this.connected = false;
        }
    }
}

// Global WebSocket instance
window.TelemetryWS = new TelemetryWebSocket();
