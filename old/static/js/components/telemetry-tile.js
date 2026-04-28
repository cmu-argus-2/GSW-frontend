/**
 * ARGUS Mission Control - Telemetry Tile Manager
 * Updates telemetry tiles with real-time data
 */

class TelemetryTileManager {
    constructor() {
        this.tiles = new Map();
        this.sparklines = new Map();
        this.thresholds = this.getDefaultThresholds();
    }

    init() {
        // Listen for telemetry updates
        document.addEventListener('telemetry:update', (e) => {
            this.handleTelemetryUpdate(e.detail);
        });

        // Subscribe to state changes
        if (window.AppState) {
            window.AppState.subscribe('telemetry', (data) => {
                this.updateAllTiles(data);
            });
        }
    }

    getDefaultThresholds() {
        return {
            'EPS.BATTERY_PACK_REPORTED_SOC': { warn: 30, critical: 15, inverse: true },
            'EPS.MAINBOARD_TEMPERATURE': { warn: 50, critical: 70, divisor: 10 },
            'EPS.BATTERY_PACK_VOLTAGE': { warn: 7000, critical: 6500, inverse: true },
            'CDH.CURRENT_RAM_USAGE': { warn: 80, critical: 95 },
            'CDH.SD_USAGE': { warn: 80000000, critical: 95000000 }
        };
    }

    handleTelemetryUpdate(detail) {
        const { subsystem, data } = detail;
        this.updateSubsystemTiles(subsystem, data);
    }

    updateAllTiles(telemetry) {
        if (telemetry.CDH) this.updateSubsystemTiles('CDH', telemetry.CDH);
        if (telemetry.EPS) this.updateSubsystemTiles('EPS', telemetry.EPS);
        if (telemetry.ADCS) this.updateSubsystemTiles('ADCS', telemetry.ADCS);
        if (telemetry.GPS) this.updateSubsystemTiles('GPS', telemetry.GPS);

        // Update last update time
        const lastUpdateEl = document.getElementById('last-update-time');
        if (lastUpdateEl && telemetry.lastUpdate) {
            const time = new Date(telemetry.lastUpdate);
            lastUpdateEl.textContent = time.toLocaleTimeString();
        }
    }

    updateSubsystemTiles(subsystem, data) {
        switch (subsystem) {
            case 'CDH':
                this.updateCDHTiles(data);
                break;
            case 'EPS':
                this.updateEPSTiles(data);
                break;
            case 'ADCS':
                this.updateADCSTiles(data);
                break;
            case 'GPS':
                this.updateGPSTiles(data);
                break;
        }
    }

    updateCDHTiles(data) {
        // Spacecraft state card
        this.updateElement('sc-state-value', this.getStateName(data.SC_STATE));
        this.updateElement('reboot-count-value', data.REBOOT_COUNT);
        this.updateElement('watchdog-value', data.WATCHDOG_TIMER);

        // RAM tile
        const ramValue = data.CURRENT_RAM_USAGE;
        this.updateElement('tile-ram-value', ramValue);
        this.updateProgressBar('tile-ram-bar', ramValue, 100);
        this.updateTileStatus('tile-ram-status', 'CDH.CURRENT_RAM_USAGE', ramValue);

        // SD tile
        const sdMB = (data.SD_USAGE / 1000000).toFixed(1);
        this.updateElement('tile-sd-value', sdMB);
    }

    updateEPSTiles(data) {
        // Battery SOC
        const soc = data.BATTERY_PACK_REPORTED_SOC;
        this.updateElement('tile-battery-soc-value', soc);
        this.updateElement('battery-soc-display', `${soc}%`);
        this.updateProgressBar('tile-battery-soc-bar', soc, 100);
        this.updateBatteryFill('battery-fill', soc);
        this.updateTileStatus('tile-battery-soc-status', 'EPS.BATTERY_PACK_REPORTED_SOC', soc);

        // Battery voltage
        const voltage = (data.BATTERY_PACK_VOLTAGE / 1000).toFixed(2);
        this.updateElement('tile-voltage-value', voltage);
        this.updateElement('battery-voltage-value', `${voltage} V`);
        this.updateTileStatus('tile-voltage-status', 'EPS.BATTERY_PACK_VOLTAGE', data.BATTERY_PACK_VOLTAGE);

        // Battery current
        this.updateElement('battery-current-value', `${data.BATTERY_PACK_CURRENT} mA`);

        // Battery temperature
        const batteryTemp = (data.BATTERY_PACK_TEMPERATURE / 10).toFixed(1);
        this.updateElement('battery-temp-value', `${batteryTemp} C`);

        // Mainboard temperature
        const mainboardTemp = (data.MAINBOARD_TEMPERATURE / 10).toFixed(1);
        this.updateElement('tile-mainboard-temp-value', mainboardTemp);
        this.updateTileStatus('tile-mainboard-temp-status', 'EPS.MAINBOARD_TEMPERATURE', data.MAINBOARD_TEMPERATURE);

        // Time to empty
        const tte = this.formatSeconds(data.BATTERY_PACK_TTE);
        this.updateElement('battery-tte-value', tte);

        // Low power mode
        this.updateElement('low-power-value', data.EPS_POWER_FLAG ? 'YES' : 'NO');

        // RF LDO
        this.updateElement('tile-rf-value', data.RF_LDO_OUTPUT_CURRENT);

        // Solar power (aggregate)
        const solarPower = this.calculateSolarPower(data);
        this.updateElement('tile-solar-value', solarPower.toFixed(0));

        // Power status badge
        this.updatePowerStatusBadge(data);
    }

    updateADCSTiles(data) {
        // ADCS mode
        this.updateElement('adcs-mode-value', this.getADCSModeName(data.MODE));
        this.updateElement('adcs-mode-display', this.getADCSModeName(data.MODE));

        // Gyro values
        const gyroX = data.GYRO_X?.toFixed(3) || '--';
        const gyroY = data.GYRO_Y?.toFixed(3) || '--';
        const gyroZ = data.GYRO_Z?.toFixed(3) || '--';
        this.updateElement('gyro-xyz-value', `${gyroX}, ${gyroY}, ${gyroZ}`);

        // Gyro RMS
        const gyroRMS = Math.sqrt(
            Math.pow(data.GYRO_X || 0, 2) +
            Math.pow(data.GYRO_Y || 0, 2) +
            Math.pow(data.GYRO_Z || 0, 2)
        ).toFixed(4);
        this.updateElement('tile-gyro-value', gyroRMS);
        this.updateElement('gyro-rms-value', `${gyroRMS} rad/s`);

        // Magnetometer
        const magX = data.MAG_X?.toFixed(2) || '--';
        const magY = data.MAG_Y?.toFixed(2) || '--';
        const magZ = data.MAG_Z?.toFixed(2) || '--';
        this.updateElement('mag-xyz-value', `${magX}, ${magY}, ${magZ}`);

        // Sun status
        this.updateElement('sun-status-value', data.SUN_STATUS ? 'VALID' : 'INVALID');

        // Sun vector
        const sunX = data.SUN_VEC_X?.toFixed(2) || '--';
        const sunY = data.SUN_VEC_Y?.toFixed(2) || '--';
        const sunZ = data.SUN_VEC_Z?.toFixed(2) || '--';
        this.updateElement('sun-vec-value', `${sunX}, ${sunY}, ${sunZ}`);
    }

    updateGPSTiles(data) {
        // Fix mode
        const fixMode = this.getGPSFixMode(data.FIX_MODE);
        this.updateElement('gps-fix-value', fixMode);
        this.updateElement('gps-fix-mode-value', fixMode);

        // GPS status badge
        const badge = document.getElementById('gps-status-badge');
        if (badge) {
            badge.textContent = fixMode;
            badge.className = 'status-badge';
            if (data.FIX_MODE === 3) {
                badge.classList.add('nominal');
            } else if (data.FIX_MODE === 2) {
                badge.classList.add('warning');
            } else {
                badge.classList.add('critical');
            }
        }

        // Satellites
        this.updateElement('gps-sv-count-value', data.NUMBER_OF_SV);

        // Position
        const lat = (data.LATITUDE / 1e7).toFixed(6);
        const lon = (data.LONGITUDE / 1e7).toFixed(6);
        const alt = (data.ELLIPSOID_ALT / 100000).toFixed(2); // cm to km

        this.updateElement('gps-lat-value', `${lat}`);
        this.updateElement('gps-lon-value', `${lon}`);
        this.updateElement('gps-alt-value', `${alt} km`);

        // GNSS time
        this.updateElement('gps-gnss-time-value', `W${data.GNSS_WEEK}`);
    }

    // ==================== HELPER METHODS ====================

    updateElement(id, value) {
        const el = document.getElementById(id);
        if (el) {
            el.textContent = value ?? '--';
        }
    }

    updateProgressBar(id, value, max) {
        const bar = document.getElementById(id);
        if (bar) {
            const percent = Math.min(100, Math.max(0, (value / max) * 100));
            bar.style.width = `${percent}%`;
        }
    }

    updateBatteryFill(id, soc) {
        const fill = document.getElementById(id);
        if (fill) {
            fill.style.height = `${soc}%`;
            fill.className = 'battery-fill';
            if (soc > 50) {
                fill.classList.add('high');
            } else if (soc > 20) {
                fill.classList.add('medium');
            } else {
                fill.classList.add('low');
            }
        }
    }

    updateTileStatus(statusId, field, value) {
        const statusEl = document.getElementById(statusId);
        if (!statusEl) return;

        const threshold = this.thresholds[field];
        if (!threshold) {
            statusEl.textContent = 'NOMINAL';
            statusEl.className = 'tile-status nominal';
            return;
        }

        let normalizedValue = value;
        if (threshold.divisor) {
            normalizedValue = value / threshold.divisor;
        }

        let status = 'nominal';
        if (threshold.inverse) {
            // Lower is worse
            if (normalizedValue <= threshold.critical) {
                status = 'critical';
            } else if (normalizedValue <= threshold.warn) {
                status = 'warning';
            }
        } else {
            // Higher is worse
            if (normalizedValue >= threshold.critical) {
                status = 'critical';
            } else if (normalizedValue >= threshold.warn) {
                status = 'warning';
            }
        }

        statusEl.textContent = status.toUpperCase();
        statusEl.className = `tile-status ${status}`;
    }

    updatePowerStatusBadge(data) {
        const badge = document.getElementById('power-status-badge');
        if (!badge) return;

        const soc = data.BATTERY_PACK_REPORTED_SOC;
        if (data.EPS_POWER_FLAG || soc < 15) {
            badge.textContent = 'CRITICAL';
            badge.className = 'status-badge critical';
        } else if (soc < 30) {
            badge.textContent = 'WARNING';
            badge.className = 'status-badge warning';
        } else {
            badge.textContent = 'NOMINAL';
            badge.className = 'status-badge nominal';
        }
    }

    calculateSolarPower(data) {
        const panels = [
            { v: data.XP_SOLAR_CHARGE_VOLTAGE, i: data.XP_SOLAR_CHARGE_CURRENT },
            { v: data.XM_SOLAR_CHARGE_VOLTAGE, i: data.XM_SOLAR_CHARGE_CURRENT },
            { v: data.YP_SOLAR_CHARGE_VOLTAGE, i: data.YP_SOLAR_CHARGE_CURRENT },
            { v: data.YM_SOLAR_CHARGE_VOLTAGE, i: data.YM_SOLAR_CHARGE_CURRENT },
            { v: data.ZP_SOLAR_CHARGE_VOLTAGE, i: data.ZP_SOLAR_CHARGE_CURRENT },
            { v: data.ZM_SOLAR_CHARGE_VOLTAGE, i: data.ZM_SOLAR_CHARGE_CURRENT }
        ];

        return panels.reduce((total, p) => {
            if (p.v && p.i) {
                return total + (p.v * p.i / 1000); // mV * mA / 1000 = mW
            }
            return total;
        }, 0);
    }

    getStateName(state) {
        const states = ['STARTUP', 'DETUMBLING', 'NOMINAL', 'EXPERIMENT', 'LOW_POWER', 'SAFE'];
        return states[state] || `STATE_${state}`;
    }

    getADCSModeName(mode) {
        const modes = ['IDLE', 'DETUMBLE', 'SUN_POINT', 'NADIR_POINT'];
        return modes[mode] || `MODE_${mode}`;
    }

    getGPSFixMode(mode) {
        const modes = { 0: 'No Fix', 2: '2D Fix', 3: '3D Fix' };
        return modes[mode] || `Fix ${mode}`;
    }

    formatSeconds(seconds) {
        if (!seconds || seconds < 0) return '--:--';
        const hours = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        return `${hours}:${String(mins).padStart(2, '0')}`;
    }
}

// Global instance
window.TelemetryTiles = new TelemetryTileManager();
