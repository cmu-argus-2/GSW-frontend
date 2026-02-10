/**
 * ARGUS Mission Control - Command Strip Component
 * Displays and manages the command queue in the mini strip view
 */

class CommandStripManager {
    constructor() {
        this.queue = [];
        this.commandNames = {
            0x40: 'FORCE_REBOOT',
            0x41: 'SWITCH_STATE',
            0x42: 'UPLINK_TIME',
            0x43: 'UPLINK_ORBIT',
            0x44: 'OFF_PAYLOAD',
            0x45: 'SCHEDULE_OD',
            0x46: 'REQ_TM_NOM',
            0x47: 'REQ_TM_HAL',
            0x48: 'REQ_TM_STOR',
            0x49: 'REQ_TM_PAY',
            0x4A: 'FILE_META',
            0x4B: 'FILE_PKT',
            0x50: 'DL_ALL_FILES'
        };
    }

    init() {
        // Listen for command queue updates
        document.addEventListener('commands:update', (e) => {
            this.updateQueue(e.detail.queue);
        });

        // Subscribe to state changes
        if (window.AppState) {
            window.AppState.subscribe('commandQueue', (queue) => {
                this.updateQueue(queue);
            });
        }

        // Initial load
        this.loadQueue();

        // Refresh every 5 seconds
        setInterval(() => this.loadQueue(), 5000);
    }

    async loadQueue() {
        try {
            const queue = await window.API.getCommandQueue();
            this.updateQueue(queue);
        } catch (err) {
            console.error('Error loading command queue:', err);
        }
    }

    updateQueue(queue) {
        this.queue = queue;

        // Update count
        const countEl = document.getElementById('command-queue-count');
        if (countEl) {
            countEl.textContent = `${queue.length} queued`;
        }

        // Update next command
        this.updateNextCommand(queue[0]);

        // Update scheduled commands preview
        this.updateScheduledPreview(queue.slice(1, 4)); // Show next 3
    }

    updateNextCommand(cmd) {
        const nameEl = document.getElementById('next-command-name');
        const argsEl = document.getElementById('next-command-args');
        const countdownEl = document.getElementById('next-command-countdown');
        const container = document.getElementById('next-command');

        if (!cmd) {
            if (nameEl) nameEl.textContent = 'REQ_TM_NOM (default)';
            if (argsEl) argsEl.textContent = 'Queue empty - default request';
            if (countdownEl) countdownEl.textContent = 'NEXT';
            if (container) container.style.opacity = '0.7';
            return;
        }

        if (container) container.style.opacity = '1';

        const cmdName = this.commandNames[cmd.command_id] || cmd.command_name || `CMD_${cmd.command_id}`;
        if (nameEl) nameEl.textContent = cmdName;

        if (argsEl) {
            const argsStr = Object.keys(cmd.args || {}).length > 0
                ? JSON.stringify(cmd.args)
                : 'No arguments';
            argsEl.textContent = argsStr;
        }

        if (countdownEl) {
            countdownEl.textContent = 'NEXT';
        }
    }

    updateScheduledPreview(commands) {
        const container = document.getElementById('scheduled-commands');
        if (!container) return;

        if (commands.length === 0) {
            container.innerHTML = '<div class="text-muted" style="font-size: 0.75rem; padding: var(--space-sm);">No additional commands scheduled</div>';
            return;
        }

        container.innerHTML = commands.map((cmd, idx) => {
            const cmdName = this.commandNames[cmd.command_id] || cmd.command_name || `CMD_${cmd.command_id}`;
            const time = new Date(cmd.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

            return `
                <div class="command-item scheduled">
                    <span class="command-name">${cmdName}</span>
                    <span class="text-muted" style="font-size: 0.75rem;">${time}</span>
                </div>
            `;
        }).join('');
    }

    getCommandDisplayName(cmdId) {
        return this.commandNames[cmdId] || `CMD_0x${cmdId.toString(16).toUpperCase()}`;
    }
}

// Global instance
window.CommandStrip = new CommandStripManager();
