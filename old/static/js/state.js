/**
 * ARGUS Mission Control - Frontend State Management
 * Centralized state store for telemetry, commands, and system status
 */

class AppStateManager {
    constructor() {
        this.state = {
            telemetry: {
                CDH: null,
                EPS: null,
                ADCS: null,
                GPS: null,
                lastUpdate: null,
                history: {
                    CDH: [],
                    EPS: [],
                    ADCS: [],
                    GPS: []
                }
            },
            commandQueue: [],
            linkStatus: {
                status: 'unknown',
                lastContact: null,
                lastTmAge: null
            },
            met: {
                totalSeconds: 0,
                formatted: '---:--:--:--'
            },
            spacecraftTime: null,
            config: {
                missionStart: null,
                mockMode: false
            }
        };

        this.listeners = new Map();
        this.historyMaxLength = 300; // 5 minutes at 1Hz
    }

    // ==================== TELEMETRY ====================

    updateTelemetry(subsystem, data) {
        if (!['CDH', 'EPS', 'ADCS', 'GPS'].includes(subsystem)) {
            console.warn(`Unknown subsystem: ${subsystem}`);
            return;
        }

        this.state.telemetry[subsystem] = data;
        this.state.telemetry.lastUpdate = Date.now();

        // Add to history
        this.state.telemetry.history[subsystem].push({
            timestamp: Date.now(),
            data: { ...data }
        });

        // Trim history
        if (this.state.telemetry.history[subsystem].length > this.historyMaxLength) {
            this.state.telemetry.history[subsystem].shift();
        }

        this.notify(`telemetry.${subsystem}`, data);
        this.notify('telemetry', this.state.telemetry);
    }

    getTelemetry(subsystem) {
        return subsystem ? this.state.telemetry[subsystem] : this.state.telemetry;
    }

    getTelemetryHistory(subsystem, field) {
        const history = this.state.telemetry.history[subsystem] || [];
        if (!field) return history;

        return history.map(entry => ({
            timestamp: entry.timestamp,
            value: entry.data[field]
        }));
    }

    // ==================== COMMAND QUEUE ====================

    setCommandQueue(queue) {
        this.state.commandQueue = queue;
        this.notify('commandQueue', queue);
    }

    getCommandQueue() {
        return this.state.commandQueue;
    }

    getNextCommand() {
        return this.state.commandQueue[0] || null;
    }

    // ==================== LINK STATUS ====================

    setLinkStatus(status, lastContact, lastTmAge) {
        this.state.linkStatus = {
            status,
            lastContact,
            lastTmAge
        };
        this.notify('linkStatus', this.state.linkStatus);
    }

    getLinkStatus() {
        return this.state.linkStatus;
    }

    // ==================== MET ====================

    setMET(totalSeconds, formatted) {
        this.state.met = { totalSeconds, formatted };
        this.notify('met', this.state.met);
    }

    getMET() {
        return this.state.met;
    }

    // ==================== SPACECRAFT TIME ====================

    setSpacecraftTime(time) {
        this.state.spacecraftTime = time;
        this.notify('spacecraftTime', time);
    }

    getSpacecraftTime() {
        return this.state.spacecraftTime;
    }

    // ==================== CONFIG ====================

    setConfig(config) {
        this.state.config = { ...this.state.config, ...config };
        this.notify('config', this.state.config);
    }

    getConfig() {
        return this.state.config;
    }

    // ==================== OBSERVER PATTERN ====================

    subscribe(key, callback) {
        if (!this.listeners.has(key)) {
            this.listeners.set(key, []);
        }
        this.listeners.get(key).push(callback);

        // Return unsubscribe function
        return () => {
            const callbacks = this.listeners.get(key);
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        };
    }

    notify(key, data) {
        const callbacks = this.listeners.get(key) || [];
        callbacks.forEach(cb => {
            try {
                cb(data);
            } catch (err) {
                console.error(`Error in state listener for ${key}:`, err);
            }
        });
    }

    // ==================== UTILITIES ====================

    getFullState() {
        return { ...this.state };
    }

    reset() {
        this.state.telemetry.CDH = null;
        this.state.telemetry.EPS = null;
        this.state.telemetry.ADCS = null;
        this.state.telemetry.GPS = null;
        this.state.telemetry.lastUpdate = null;
        this.state.commandQueue = [];
        this.notify('reset', null);
    }
}

// Global state instance
window.AppState = new AppStateManager();
