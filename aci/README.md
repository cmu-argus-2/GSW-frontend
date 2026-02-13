# 🛰️ Satellite Command Interface

A web-based interface for building, managing quick commands, and sending commands to satellite ground stations via XML-RPC protocol.

## Overview

This application provides a user-friendly web interface to interact with satellite systems through a ground station. It allows operators to:
- Search and select satellite commands from a comprehensive command database
- Build command packets with proper argument validation
- Manage quick commands for execution
- Monitor ground station connection status in real-time
- Track command execution results
- View packet history

## TODO
- remove reference to splat (ask the necessary info via rpc)
- find a better name for the simple_rpc_clinet.py file
- Fix the issue that the mouse clicking the the command dropdown does not work
- impelemnt the last received packet and packet history
- implement the config page properly (currently it only has the UI, but no functionality)
- implement command scheduling
- get and process ack from groundstation

## Architecture

The system consists of three main components:

1. **Flask Web Server** (`app.py`) - Serves the web interface and handles HTTP API requests
2. **XML-RPC Client** (`simple_rpc_clinet.py`) - Manages communication with the remote ground station server
3. **Web Frontend** (`templates/index.html`, `static/script.js`, `static/style.css`) - Interactive user interface

```
┌─────────────────┐      HTTP       ┌──────────────┐     XML-RPC      ┌──────────────────┐
│   Web Browser   │ ◄─────────────► │ Flask Server │ ◄──────────────► │ Ground Station   │
│   (Frontend)    │                 │  (Backend)   │                  │   RPC Server     │
└─────────────────┘                 └──────────────┘                  └──────────────────┘
```

## Features

### 🔍 Command Search
- **Fuzzy search** - Type partial command names to find matches
- **Keyboard navigation** - Use arrow keys to navigate suggestions
- **Mouse selection** - Click on any suggestion to select it
- **Auto-complete** - Dropdown shows command ID, arguments, and size

### ⚡ Quick Command Management
- **Quick Access Library** - Save frequently used commands to a dedicated panel
- **Predefined commands** - Auto-load essential commands from JSON config on startup
- **Argument validation** - Automatic type conversion (int, float, string) before saving
- **Persistency** - Build a command once, add it to the list, and execute it multiple times
- **Manage List** - Remove or reorder commands in your Quick Command view

### 📡 Real-Time Status Monitoring
- **Ground station status** - Visual indicator shows connection state
- **Auto-ping** - Background thread checks server availability every 5 seconds
- **Packet history** - View last 50 received packets with timestamps
- **Command feedback** - Visual flash (green/red) indicates success/failure

### ⚙️ Server Configuration
- **Dynamic address update** - Change RPC server IP and port without restart
- **Server controls** - Start, stop, and restart the ground station server
- **Settings persistence** - Server configuration saved to browser localStorage

## Project Structure

```
satellite-command-interface/
├── app.py                      # Flask backend server
├── simple_rpc_clinet.py        # XML-RPC client with auto-ping
├── predefined_commands.json    # Pre-configured commands to load on startup
├── README.md                   # This file
├── templates/
│   └── index.html              # Main HTML template
└── static/
    ├── script.js               # Frontend JavaScript logic
    └── style.css               # Styling and animations
```

## Installation

### Prerequisites
- Python 3.7+
- Flask

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd satellite-command-interface
```

2. Install dependencies:
```bash
pip install flask
```

3. Configure the ground station server address in `simple_rpc_clinet.py`:
```python
address = ("YOUR_SERVER_IP", 8000)
```

4. (Optional) Add predefined commands to `predefined_commands.json`:
```json
[
    {
        "command": "ping",
        "arguments": {}
    },
    {
        "command": "set_mode",
        "arguments": {
            "mode": "1"
        }
    }
]
```

## Usage

### Starting the Server

```bash
python app.py
```

The server will start on `http://0.0.0.0:5001`

### Using the Interface

1. **Search for a command**
   - Click in the search box or start typing
   - Use arrow keys or mouse to select a command
   - Press Enter or click to select

2. **Fill in arguments**
   - Input fields appear automatically for selected command
   - Enter values for each required argument

3. **Add to quick commands**
    - Click "Add to Quick Commands" button
    - Command appears in the quick commands panel

4. **Send commands**
    - Click "Send Command" on any quick command
   - Watch for visual feedback (green = success, red = error)

5. **Monitor status**
   - Ground station light indicator shows connection state
   - Packet history displays received telemetry

### Configuration

Click the ⚙️ (gear) button to:
- Update XML-RPC server IP and port
- Start/stop/restart the ground station server
- View current connection settings

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serve main interface |
| `/api/commands` | GET | List all available commands |
| `/api/predefined_commands` | GET | Get predefined commands from JSON |
| `/api/send_command` | POST | Send a command to the satellite |
| `/api/ground_station_status` | GET | Check if ground station is active |
| `/api/update_server_address` | POST | Update RPC server address |
| `/api/server_control` | POST | Start/stop/restart RPC server |

## Customization

### Adding Predefined Commands

Edit `predefined_commands.json`:

```json
[
    {
        "command": "your_command_name",
        "arguments": {
            "arg1": "value1",
            "arg2": "value2"
        }
    }
]
```

### Styling

Modify `static/style.css` to customize:
- Color scheme (currently dark blue theme)
- Layout and spacing
- Animation effects
- Status indicators

## Technical Details

### Command Type Validation

The system automatically converts argument types based on format specifiers:
- **Integers**: `b, B, ?, h, H, i, I, l, L, q, Q, n, N`
- **Floats**: `e, d, F, D`
- **Strings**: `s, p`

### Connection Management

- Background thread pings server every 5 seconds
- Connection status updates automatically
- Visual indicator (green/red light) shows state
- Graceful degradation if server is unavailable

## Troubleshooting

**Commands not sending?**
- Check ground station status indicator
- Verify server IP and port in configuration
- Check browser console for errors

**Dropdown not working?**
- Ensure JavaScript is enabled
- Check that commands are loading (view console)
- Try refreshing the page

**Server connection failing?**
- Verify XML-RPC server is running
- Check firewall settings
- Confirm IP address and port are correct
