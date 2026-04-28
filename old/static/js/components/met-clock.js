/**
 * ARGUS Mission Control - Mission Elapsed Time Clock
 * Displays and updates MET based on configured mission start time
 */

class METClock {
    constructor(displayElementId = 'met-display') {
        this.displayElement = document.getElementById(displayElementId);
        this.missionStart = null;
        this.intervalId = null;
    }

    async init() {
        try {
            // Fetch mission start time from config
            const config = await window.API.getConfig();
            if (config.mission_start) {
                this.missionStart = new Date(config.mission_start);
                this.start();
            } else {
                console.warn('Mission start time not configured');
                this.displayElement.textContent = '---:--:--:--';
            }
        } catch (err) {
            console.error('Error fetching MET config:', err);
            // Fallback: try to fetch MET directly
            this.startWithAPIPolling();
        }
    }

    start() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }

        this.update();
        this.intervalId = setInterval(() => this.update(), 1000);
    }

    startWithAPIPolling() {
        // Fallback: poll MET from API every second
        this.intervalId = setInterval(async () => {
            try {
                const met = await window.API.getMET();
                this.displayElement.textContent = met.formatted;
                if (window.AppState) {
                    window.AppState.setMET(met.total_seconds, met.formatted);
                }
            } catch (err) {
                // Silently fail
            }
        }, 1000);
    }

    update() {
        if (!this.missionStart) return;

        const now = new Date();
        const diff = now - this.missionStart;

        if (diff < 0) {
            // Mission hasn't started yet
            this.displayElement.textContent = 'T-' + this.formatDuration(Math.abs(diff));
            return;
        }

        const formatted = this.formatDuration(diff);
        this.displayElement.textContent = formatted;

        if (window.AppState) {
            window.AppState.setMET(Math.floor(diff / 1000), formatted);
        }
    }

    formatDuration(ms) {
        const totalSeconds = Math.floor(ms / 1000);
        const days = Math.floor(totalSeconds / 86400);
        const hours = Math.floor((totalSeconds % 86400) / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = totalSeconds % 60;

        return `${String(days).padStart(3, '0')}:${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    }

    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }

    setMissionStart(dateOrString) {
        this.missionStart = typeof dateOrString === 'string'
            ? new Date(dateOrString)
            : dateOrString;
        this.start();
    }
}

// Ground time clock
class GroundTimeClock {
    constructor(displayElementId = 'ground-time-display') {
        this.displayElement = document.getElementById(displayElementId);
        this.intervalId = null;
    }

    start() {
        this.update();
        this.intervalId = setInterval(() => this.update(), 1000);
    }

    update() {
        const now = new Date();
        this.displayElement.textContent = now.toISOString().substr(11, 8);
    }

    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }
}

// Global instances
window.METClock = new METClock();
window.GroundTimeClock = new GroundTimeClock();
