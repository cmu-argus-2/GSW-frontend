/**
 * ARGUS Mission Control - Trend Chart Component
 * Plotly.js-based real-time trend visualization
 */

class TrendChart {
    constructor(containerId, config = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.config = {
            maxPoints: config.maxPoints || 300, // 5 minutes at 1Hz
            fields: config.fields || ['EPS.BATTERY_PACK_REPORTED_SOC', 'EPS.BATTERY_PACK_VOLTAGE'],
            ...config
        };

        this.traces = new Map();
        this.currentTab = 'power';

        this.tabConfigs = {
            power: {
                fields: [
                    { path: 'EPS.BATTERY_PACK_REPORTED_SOC', name: 'Battery SOC', color: '#22C55E', yaxis: 'y' },
                    { path: 'EPS.BATTERY_PACK_VOLTAGE', name: 'Voltage (mV)', color: '#22D3EE', yaxis: 'y2' }
                ]
            },
            thermal: {
                fields: [
                    { path: 'EPS.MAINBOARD_TEMPERATURE', name: 'Mainboard', color: '#EF4444', divisor: 10 },
                    { path: 'EPS.BATTERY_PACK_TEMPERATURE', name: 'Battery', color: '#FACC15', divisor: 10 }
                ]
            },
            adcs: {
                fields: [
                    { path: 'ADCS.GYRO_X', name: 'Gyro X', color: '#EF4444' },
                    { path: 'ADCS.GYRO_Y', name: 'Gyro Y', color: '#22C55E' },
                    { path: 'ADCS.GYRO_Z', name: 'Gyro Z', color: '#3B82F6' }
                ]
            },
            gps: {
                fields: [
                    { path: 'GPS.NUMBER_OF_SV', name: 'Satellites', color: '#22D3EE' },
                    { path: 'GPS.FIX_MODE', name: 'Fix Mode', color: '#A78BFA' }
                ]
            }
        };

        this.init();
    }

    init() {
        if (!this.container) {
            console.warn(`Trend chart container not found: ${this.containerId}`);
            return;
        }

        this.layout = {
            paper_bgcolor: 'transparent',
            plot_bgcolor: '#111827',
            font: { color: '#9ca3af', family: 'Inter, sans-serif', size: 10 },
            xaxis: {
                type: 'date',
                gridcolor: '#1f2937',
                linecolor: '#1f2937',
                tickformat: '%H:%M:%S'
            },
            yaxis: {
                gridcolor: '#1f2937',
                linecolor: '#1f2937',
                side: 'left'
            },
            yaxis2: {
                gridcolor: '#1f2937',
                linecolor: '#1f2937',
                side: 'right',
                overlaying: 'y'
            },
            margin: { t: 10, r: 50, b: 30, l: 50 },
            showlegend: true,
            legend: {
                orientation: 'h',
                y: -0.15,
                font: { size: 9 }
            }
        };

        this.plotlyConfig = {
            displayModeBar: false,
            responsive: true
        };

        // Initialize with current tab
        this.switchTab(this.currentTab);

        // Subscribe to telemetry updates
        document.addEventListener('telemetry:update', (e) => {
            this.addDataPoint(e.detail);
        });
    }

    switchTab(tabName) {
        this.currentTab = tabName;
        const tabConfig = this.tabConfigs[tabName];

        if (!tabConfig) {
            console.warn(`Unknown tab: ${tabName}`);
            return;
        }

        // Clear existing traces
        this.traces.clear();

        // Create new traces for this tab
        const traces = tabConfig.fields.map((field, idx) => {
            const trace = {
                x: [],
                y: [],
                type: 'scatter',
                mode: 'lines',
                name: field.name,
                line: { color: field.color, width: 1.5 },
                yaxis: field.yaxis || 'y'
            };

            this.traces.set(field.path, {
                trace,
                index: idx,
                divisor: field.divisor || 1
            });

            return trace;
        });

        // Render chart
        Plotly.newPlot(this.container, traces, this.layout, this.plotlyConfig);
    }

    addDataPoint(detail) {
        const { subsystem, data, timestamp } = detail;
        const time = new Date(timestamp);

        let updated = false;

        for (const [fieldPath, traceInfo] of this.traces) {
            const [sub, field] = fieldPath.split('.');
            if (sub !== subsystem) continue;

            let value = data[field];
            if (value === undefined || value === null) continue;

            // Apply divisor if needed
            value = value / traceInfo.divisor;

            // Add point
            traceInfo.trace.x.push(time);
            traceInfo.trace.y.push(value);

            // Trim to max points
            if (traceInfo.trace.x.length > this.config.maxPoints) {
                traceInfo.trace.x.shift();
                traceInfo.trace.y.shift();
            }

            updated = true;
        }

        if (updated) {
            this.redraw();
        }
    }

    redraw() {
        const traces = Array.from(this.traces.values()).map(t => t.trace);
        Plotly.react(this.container, traces, this.layout, this.plotlyConfig);
    }

    clear() {
        for (const traceInfo of this.traces.values()) {
            traceInfo.trace.x = [];
            traceInfo.trace.y = [];
        }
        this.redraw();
    }

    destroy() {
        Plotly.purge(this.container);
    }
}

// Export for use in other scripts
window.TrendChart = TrendChart;
