// Global variables
let commands = [];
let commandQueue = [];
let selectedCommand = null;
let packetHistory = [];

/**
 * Load commands from the Flask API
 */
async function loadCommands() {
    try {
        const response = await fetch('/api/commands');
        const data = await response.json();
        if (data.success) {
            commands = data.commands;
        }
    } catch (error) {
        console.error('Error loading commands:', error);
    }
}

/**
 * Load predefined commands and add them to the queue
 */
async function loadPredefinedCommands() {
    try {
        const response = await fetch('/api/predefined_commands');
        const data = await response.json();
        if (data.success && data.commands.length > 0) {
            data.commands.forEach(predefinedCmd => {
                addCommandToQueue(predefinedCmd.command, predefinedCmd.arguments, true);
            });
        }
    } catch (error) {
        console.error('Error loading predefined commands:', error);
    }
}

/**
 * Fuzzy search algorithm - scores how well a query matches a string
 */
function fuzzyScore(query, str) {
    const queryLower = query.toLowerCase();
    const strLower = str.toLowerCase();
    
    if (queryLower === strLower) return 1000; // Exact match
    if (strLower.includes(queryLower)) return 500; // Substring match
    
    let score = 0;
    let queryIdx = 0;
    let prevMatchIdx = -1;
    
    for (let i = 0; i < strLower.length && queryIdx < queryLower.length; i++) {
        if (strLower[i] === queryLower[queryIdx]) {
            // Award points for matches
            score += 10;
            // Bonus for consecutive matches
            if (i === prevMatchIdx + 1) score += 5;
            // Bonus for matching at word boundaries
            if (i === 0 || strLower[i - 1] === '_' || strLower[i - 1] === ' ') score += 20;
            prevMatchIdx = i;
            queryIdx++;
        }
    }
    
    // If we matched all characters, score is higher
    if (queryIdx === queryLower.length) {
        return score + 100;
    }
    
    return 0;
}

/**
 * Get filtered and sorted commands based on fuzzy search
 */
function getFilteredCommands(query) {
    if (!query.trim()) {
        return commands;
    }
    
    const scored = commands
        .map(cmd => ({
            cmd,
            score: fuzzyScore(query, cmd.name)
        }))
        .filter(item => item.score > 0)
        .sort((a, b) => b.score - a.score);
    
    return scored.map(item => item.cmd);
}

/**
 * Render the command suggestions dropdown
 */
function renderSuggestions(filteredCommands, selectedIndex) {
    const suggestionsList = document.getElementById('command-suggestions');
    
    if (filteredCommands.length === 0) {
        suggestionsList.innerHTML = '<div class="suggestion-item no-results">No commands found</div>';
        return;
    }
    
    suggestionsList.innerHTML = filteredCommands
        .map((cmd, idx) => `
            <div class="suggestion-item ${idx === selectedIndex ? 'selected' : ''}" data-index="${idx}">
                <div class="suggestion-name">${cmd.name}</div>
                <div class="suggestion-meta">ID: ${cmd.id} | ${cmd.size} bytes</div>
            </div>
        `)
        .join('');
}

/**
 * Select a command and populate arguments
 */
function selectCommand(cmd) {
    selectedCommand = cmd;
    document.getElementById('command-input').value = cmd.name;
    document.getElementById('command-suggestions-container').style.display = 'none';
    
    displayArgumentInputs();
    document.getElementById('add-command-btn').disabled = false;
    document.getElementById('command-info').textContent = 
        `ID: ${selectedCommand.id} | Size: ${selectedCommand.size} bytes`;
}

/**
 * Handle command search input and navigation
 */
let currentSelectedIndex = -1;
let currentFilteredCommands = [];

/**
 * CONFIG MODAL FUNCTIONS
 */

/**
 * Open the config modal
 */
function openConfigModal() {
    const modal = document.getElementById('config-modal');
    modal.style.display = 'flex';
    
    // Load current server settings (you might want to fetch these from the server)
    loadServerSettings();
}

/**
 * Close the config modal
 */
function closeConfigModal() {
    const modal = document.getElementById('config-modal');
    modal.style.display = 'none';
}

/**
 * Load current server settings from localStorage or fetch from server
 */
function loadServerSettings() {
    // Try to get from localStorage first
    const savedIp = localStorage.getItem('rpc-server-ip') || '172.20.70.133';
    const savedPort = localStorage.getItem('rpc-server-port') || '8000';
    
    document.getElementById('server-ip').value = savedIp;
    document.getElementById('server-port').value = savedPort;
}

/**
 * Update the server address
 */
async function updateServerAddress() {
    const ip = document.getElementById('server-ip').value.trim();
    const port = document.getElementById('server-port').value.trim();
    
    if (!ip || !port) {
        alert('Please enter both IP and port');
        return;
    }
    
    // Validate port is a number
    if (isNaN(port) || port < 1 || port > 65535) {
        alert('Port must be a number between 1 and 65535');
        return;
    }
    
    try {
        // Send update to server
        const response = await fetch('/api/update_server_address', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                ip: ip,
                port: parseInt(port)
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Save to localStorage
            localStorage.setItem('rpc-server-ip', ip);
            localStorage.setItem('rpc-server-port', port);
            
            alert('Server address updated successfully');
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('Failed to update server address: ' + error.message);
    }
}

/**
 * Start the RPC server
 */
async function startServer() {
    try {
        const response = await fetch('/api/server_control', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'start'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Server started successfully');
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('Failed to start server: ' + error.message);
    }
}

/**
 * Stop the RPC server
 */
async function stopServer() {
    try {
        const response = await fetch('/api/server_control', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'stop'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Server stopped successfully');
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('Failed to stop server: ' + error.message);
    }
}

/**
 * Restart the RPC server
 */
async function restartServer() {
    try {
        const response = await fetch('/api/server_control', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'restart'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Server restarted successfully');
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('Failed to restart server: ' + error.message);
    }
}

/**
 * Display input fields for command arguments
 */
function displayArgumentInputs() {
    const container = document.getElementById('arguments-container');
    container.innerHTML = '';

    if (selectedCommand.arguments.length === 0) {
        container.innerHTML = '<p style="color: #888; font-style: italic;">No arguments required</p>';
        return;
    }

    selectedCommand.arguments.forEach(arg => {
        const div = document.createElement('div');
        div.className = 'argument-input';
        div.innerHTML = `
            <label for="arg-${arg}">${arg}:</label>
            <input type="text" id="arg-${arg}" placeholder="Enter ${arg}">
        `;
        container.appendChild(div);
    });
}

/**
 * Add command to the queue programmatically
 * @param {string} commandName - The command name
 * @param {object} args - The command arguments
 * @param {boolean} isPredefined - Whether this is a predefined command
 */
function addCommandToQueue(commandName, args, isPredefined = false) {
    const queueItem = {
        id: Date.now() + Math.random(), // Ensure unique ID
        command: commandName,
        arguments: args,
        timestamp: new Date().toLocaleTimeString(),
        predefined: isPredefined
    };

    commandQueue.push(queueItem);
    renderQueue();
}

/**
 * Add command to the queue
 */
document.getElementById('add-command-btn').addEventListener('click', function() {
    if (!selectedCommand) return;

    const args = {};
    selectedCommand.arguments.forEach(arg => {
        const input = document.getElementById(`arg-${arg}`);
        args[arg] = input.value;
    });

    addCommandToQueue(selectedCommand.name, args, false);
    
    // Reset form
    document.getElementById('command-input').value = '';
    document.getElementById('arguments-container').innerHTML = '';
    document.getElementById('add-command-btn').disabled = true;
    document.getElementById('command-info').textContent = '';
    selectedCommand = null;
    
    // Hide suggestions
    document.getElementById('command-suggestions-container').style.display = 'none';
});

/**
 * Render the command queue to the DOM
 */
function renderQueue() {
    const container = document.getElementById('command-queue');
    
    if (commandQueue.length === 0) {
        container.innerHTML = '<div class="empty-state">No commands in queue. Add a command to get started.</div>';
        return;
    }

    container.innerHTML = commandQueue.map(item => `
        <div class="command-item" data-command-id="${item.id}">
            <button class="remove-btn" onclick="removeFromQueue(${item.id})">✕</button>
            <h3>
                ${item.command}
                ${item.predefined ? '<span class="predefined-badge">Predefined</span>' : ''}
            </h3>
            <div class="command-args">
                ${Object.keys(item.arguments).length > 0 
                    ? Object.entries(item.arguments).map(([k, v]) => `${k}: ${v}`).join(' | ')
                    : 'No arguments'}
            </div>
            <div style="font-size: 0.8em; color: #888;">Added: ${item.timestamp}</div>
            <button onclick="sendCommand(${item.id})">Send Command</button>
            <div class="command-status" id="status-${item.id}"></div>
        </div>
    `).join('');
}

/**
 * Remove command from the queue
 */
function removeFromQueue(id) {
    commandQueue = commandQueue.filter(item => item.id !== id);
    renderQueue();
}

/**
 * Trigger the flash animation on a command element
 * @param {HTMLElement} element - The command element to animate
 * @param {string} type - 'success' or 'error'
 */
function triggerFlashAnimation(element, type) {
    if (!element) return;

    // Remove all animation classes first
    element.classList.remove('animating-success', 'animating-error');
    
    // Force a reflow to reset the animation
    void element.offsetWidth;
    
    // Add the appropriate animation class
    if (type === 'success') {
        element.classList.add('animating-success');
    } else if (type === 'error') {
        element.classList.add('animating-error');
    }
    
    // Remove the animation class after it completes so it can be retriggered
    setTimeout(() => {
        element.classList.remove('animating-success', 'animating-error');
    }, 800);
}

/**
 * Show status message below command
 * @param {HTMLElement} statusElement - The status element
 * @param {string} message - The message to display
 * @param {string} type - 'success' or 'error'
 * @param {number} duration - How long to show in milliseconds
 */
function showStatusMessage(statusElement, message, type, duration) {
    if (!statusElement) return;
    
    statusElement.textContent = message;
    statusElement.className = `command-status show ${type}`;
    
    // Auto-hide after specified duration
    setTimeout(() => {
        statusElement.classList.remove('show');
        statusElement.textContent = '';
        statusElement.className = 'command-status';
    }, duration);
}

/**
 * Send command to the satellite via API
 */
async function sendCommand(id) {
    const item = commandQueue.find(cmd => cmd.id === id);
    if (!item) return;

    try {
        // Get the command element and status element
        const commandElement = document.querySelector(`[data-command-id="${id}"]`);
        const statusElement = document.getElementById(`status-${id}`);

        // Make the API request
        const response = await fetch('/api/send_command', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                command: item.command,
                arguments: item.arguments
            })
        });

        const data = await response.json();
        
        // Handle success response
        if (data.success) {
            triggerFlashAnimation(commandElement, 'success');
            showStatusMessage(statusElement, '✅ Command sent successfully', 'success', 3000);
            console.log('Command sent:', item.command);
        } 
        // Handle error response
        else {
            triggerFlashAnimation(commandElement, 'error');
            showStatusMessage(statusElement, `❌ Error: ${data.error}`, 'error', 5000);
            console.error('Command error:', data.error);
        }
    } 
    // Handle network/exception errors
    catch (error) {
        const commandElement = document.querySelector(`[data-command-id="${id}"]`);
        const statusElement = document.getElementById(`status-${id}`);
        
        triggerFlashAnimation(commandElement, 'error');
        showStatusMessage(statusElement, `❌ Error: ${error.message}`, 'error', 5000);
        console.error('Command exception:', error.message);
    }
}

/**
 * Update the packet display with the latest received packet
 */
async function updatePacketDisplay() {
    try {
        const response = await fetch('/api/last_packet');
        const data = await response.json();
        
        const container = document.getElementById('packet-display');
        
        if (!data.success || !data.has_packet) {
            container.innerHTML = '<div class="no-packet">No packets received yet.</div>';
            return;
        }

        container.innerHTML = `
            <div class="packet-info">
                <div class="packet-field">
                    <strong>Received:</strong>
                    ${data.timestamp}
                </div>
                <div class="packet-field">
                    <strong>Time Ago:</strong>
                    <span class="time-ago">${data.seconds_ago} seconds ago</span>
                </div>
                <div class="packet-field">
                    <strong>Data (Hex):</strong>
                    <div class="packet-data">${data.hex_data}</div>
                </div>
            </div>
        `;

        // Update history if this is a new packet
        if (data.has_packet && (packetHistory.length === 0 || 
            packetHistory[0].hex_data !== data.hex_data)) {
            packetHistory.unshift({
                timestamp: data.timestamp,
                hex_data: data.hex_data
            });
            // Keep only last 50 packets
            if (packetHistory.length > 50) {
                packetHistory = packetHistory.slice(0, 50);
            }
            renderPacketHistory();
        }
    } catch (error) {
        console.error('Error updating packet display:', error);
    }
}

/**
 * Render the packet history to the DOM
 */
function renderPacketHistory() {
    const container = document.getElementById('packet-history');
    
    if (packetHistory.length === 0) {
        container.innerHTML = '<div class="no-history">No packets received yet.</div>';
        return;
    }

    container.innerHTML = packetHistory.map((packet, index) => `
        <div class="history-item">
            <div class="history-time">
                <strong>#${packetHistory.length - index}</strong><br>
                ${packet.timestamp}
            </div>
            <div class="history-data">${packet.hex_data}</div>
        </div>
    `).join('');
}

/**
 * Update the ground station status indicator
 */
async function updateGroundStationStatus() {
    try {
        const response = await fetch('/api/ground_station_status');
        const data = await response.json();
        
        const light = document.getElementById('gs-status-light');
        const text = document.getElementById('gs-status-text');
        
        if (data.success) {
            if (data.active) {
                light.className = 'status-light active';
                text.textContent = 'Ground Station: Online';
            } else {
                light.className = 'status-light inactive';
                text.textContent = 'Ground Station: Offline';
            }
        }
    } catch (error) {
        console.error('Error updating ground station status:', error);
    }
}

/**
 * Initialize the page when document is loaded
 */
document.addEventListener('DOMContentLoaded', function() {
    // Load initial data
    loadCommands();
    loadPredefinedCommands();
    
    // Setup config modal event listeners
    const configBtn = document.getElementById('config-btn');
    const modal = document.getElementById('config-modal');
    const closeBtn = document.getElementById('modal-close-btn');
    const updateServerBtn = document.getElementById('update-server-btn');
    const startServerBtn = document.getElementById('start-server-btn');
    const stopServerBtn = document.getElementById('stop-server-btn');
    const restartServerBtn = document.getElementById('restart-server-btn');
    
    configBtn.addEventListener('click', openConfigModal);
    closeBtn.addEventListener('click', closeConfigModal);
    updateServerBtn.addEventListener('click', updateServerAddress);
    startServerBtn.addEventListener('click', startServer);
    stopServerBtn.addEventListener('click', stopServer);
    restartServerBtn.addEventListener('click', restartServer);
    
    // Close modal when clicking outside of it
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeConfigModal();
        }
    });
    
    // Setup command search
    const commandInput = document.getElementById('command-input');
    const suggestionsContainer = document.getElementById('command-suggestions-container');
    
    if (commandInput) {
        // Show all commands when input is focused and empty
        commandInput.addEventListener('focus', function(e) {
            const query = e.target.value;
            if (query.trim() === '') {
                currentFilteredCommands = commands;
                currentSelectedIndex = 0;
                suggestionsContainer.style.display = 'block';
                renderSuggestions(currentFilteredCommands, currentSelectedIndex);
            }
        });
        
        commandInput.addEventListener('input', function(e) {
            const query = e.target.value;
            currentFilteredCommands = getFilteredCommands(query);
            currentSelectedIndex = currentFilteredCommands.length > 0 ? 0 : -1;
            
            if (query.trim() === '') {
                suggestionsContainer.style.display = 'block';
                renderSuggestions(currentFilteredCommands, currentSelectedIndex);
            } else {
                suggestionsContainer.style.display = 'block';
                renderSuggestions(currentFilteredCommands, currentSelectedIndex);
            }
        });
        
        commandInput.addEventListener('keydown', function(e) {
            if (suggestionsContainer.style.display === 'none') return;
            
            switch(e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    currentSelectedIndex = Math.min(currentSelectedIndex + 1, currentFilteredCommands.length - 1);
                    renderSuggestions(currentFilteredCommands, currentSelectedIndex);
                    break;
                    
                case 'ArrowUp':
                    e.preventDefault();
                    currentSelectedIndex = Math.max(currentSelectedIndex - 1, 0);
                    renderSuggestions(currentFilteredCommands, currentSelectedIndex);
                    break;
                    
                case 'Enter':
                    e.preventDefault();
                    if (currentSelectedIndex >= 0 && currentSelectedIndex < currentFilteredCommands.length) {
                        selectCommand(currentFilteredCommands[currentSelectedIndex]);
                    }
                    break;
                    
                case 'Escape':
                    e.preventDefault();
                    suggestionsContainer.style.display = 'none';
                    break;
            }
        });
    }
    
    // Close suggestions when clicking outside
    document.addEventListener('click', function(e) {
        if (commandInput && !commandInput.contains(e.target) && !suggestionsContainer.contains(e.target)) {
            suggestionsContainer.style.display = 'none';
        }
    });
    
    // Update packet display every 2 seconds
    setInterval(updatePacketDisplay, 2000);
    updatePacketDisplay();

    // Update ground station status every 2 seconds
    setInterval(updateGroundStationStatus, 2000);
    updateGroundStationStatus();
});