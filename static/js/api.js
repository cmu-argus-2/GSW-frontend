/**
 * ARGUS Mission Control - REST API Client
 * Handles all HTTP communication with the backend
 */

class APIClient {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `HTTP ${response.status}`);
            }

            return data;
        } catch (err) {
            console.error(`API Error [${endpoint}]:`, err);
            throw err;
        }
    }

    // ==================== TELEMETRY ====================

    async getLatestTelemetry(type = 'nominal') {
        return this.request(`/api/telemetry/latest/${type}`);
    }

    async getTelemetryHistory(type = 'nominal', page = 1, limit = 50) {
        return this.request(`/api/telemetry/history?type=${type}&page=${page}&limit=${limit}`);
    }

    async getSubsystemTelemetry(subsystem) {
        return this.request(`/api/telemetry/subsystem/${subsystem}`);
    }

    // ==================== COMMANDS ====================

    async getCommandQueue() {
        return this.request('/api/commands/queue');
    }

    async addCommand(commandId, args = {}) {
        return this.request('/api/commands/queue', {
            method: 'POST',
            body: JSON.stringify({ command_id: commandId, args })
        });
    }

    async deleteCommand(cmdId) {
        return this.request(`/api/commands/queue/${cmdId}`, {
            method: 'DELETE'
        });
    }

    async getCommandHistory(page = 1, limit = 50) {
        return this.request(`/api/commands/history?page=${page}&limit=${limit}`);
    }

    async getCommandDefinitions() {
        return this.request('/api/commands/definitions');
    }

    async sendEStop() {
        return this.request('/api/commands/estop', {
            method: 'POST'
        });
    }

    // ==================== SYSTEM ====================

    async getLinkStatus() {
        return this.request('/api/system/link-status');
    }

    async getMET() {
        return this.request('/api/system/met');
    }

    async getHealth() {
        return this.request('/api/system/health');
    }

    async getConfig() {
        return this.request('/api/system/config');
    }
}

// Global API client instance
window.API = new APIClient();
