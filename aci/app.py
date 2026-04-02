"""
Satellite Command Interface
A simple Flask web app to build and send commands to the satellite.
"""

from flask import Flask, render_template, request, jsonify
from datetime import datetime
import json
import threading
import time

from simple_rpc_clinet import SimpleRPCClient, address

import logging

# Disable the werkzeug logger for standard info (requests)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

rpc_client = SimpleRPCClient(address)

app = Flask(__name__)

# Store the last received packet info
last_packet = {
    'data': None,
    'timestamp': None,
    'hex_data': None
}

# Store packet history (last 50 packets)
packet_history = []

# Ground station status
ground_station_active = False

# Buffer of received packets from the satellite (for display in UI)
from collections import deque as _deque
received_packets_buffer = _deque(maxlen=200)
_rx_buffer_lock = threading.Lock()

# Automated image downlink state
downlink_state = {
    'running': False,
    'tid': None,
    'step': '',
    'total': 0,
    'received': 0,
    'done': False,
    'success': False,
    'error': None
}
_downlink_stop_flag = False
_downlink_lock = threading.Lock()

INT_FORMATS = {'b', 'B', '?', 'h', 'H', 'i', 'I', 'l', 'L', 'q', 'Q', 'n', 'N'}
FLOAT_FORMATS = {'e', 'd', 'F', 'D', 'f'}
STRING_FORMATS = {'s', 'p'}


def normalize_command_definitions(raw_definitions):
    """
    Normalize the RPC command metadata into a consistent mapping keyed by
    command name.
    """
    command_map = {}

    if isinstance(raw_definitions, dict):
        iterable = []
        for command_name, definition in raw_definitions.items():
            normalized_definition = dict(definition or {})
            normalized_definition.setdefault('name', command_name)
            iterable.append(normalized_definition)
    elif isinstance(raw_definitions, list):
        iterable = raw_definitions
    else:
        raise ValueError('RPC command definitions must be a list or dict')

    for definition in iterable:
        if not isinstance(definition, dict):
            raise ValueError('Each command definition returned by RPC must be a dict')

        command_name = definition.get('name')
        if not command_name:
            raise ValueError('Command definition is missing required field: name')

        raw_arguments = definition.get('arguments', [])
        argument_names = []
        argument_types = {}

        for argument in raw_arguments:
            if isinstance(argument, dict):
                argument_name = argument.get('name')
                argument_type = argument.get('type')
            else:
                argument_name = argument
                argument_type = None

            if not argument_name:
                raise ValueError(f"Command '{command_name}' has an argument without a name")

            argument_names.append(argument_name)
            if argument_type:
                argument_types[argument_name] = argument_type

        command_map[command_name] = {
            'name': command_name,
            'id': definition.get('id', 0),
            'arguments': argument_names,
            'argument_types': argument_types,
            'precondition': definition.get('precondition', ''),
            'size': definition.get('size', 0)
        }

    return command_map


def get_rpc_command_definitions():
    """Fetch and normalize command metadata from the SimpleRPC server."""
    raw_definitions = rpc_client.get_command_definitions()
    return normalize_command_definitions(raw_definitions)


def coerce_argument_value(arg_name, arg_value, arg_format):
    """Convert incoming string values from the UI to the expected Python type."""
    if arg_format in INT_FORMATS:
        return int(arg_value)
    if arg_format in FLOAT_FORMATS:
        return float(arg_value)
    if arg_format in STRING_FORMATS or arg_format is None:
        return str(arg_value)

    raise ValueError(
        f"Unknown argument type '{arg_format}' for argument '{arg_name}'"
    )

def _run_downlink(tid, img_path):
    """
    Background thread that runs the full image downlink state machine:
      CREATE_TRANS → wait INIT_TRANS → loop(GENERATE_X_PACKETS → wait ACK
      → wait fragments stable → CONFIRM_LAST_BATCH → wait ACK) → done
    Uses its own RPC client to avoid contention with the global rpc_client.
    """
    global downlink_state, _downlink_stop_flag

    from simple_rpc_clinet import SimpleRPCClient, address as rpc_address
    local_rpc = SimpleRPCClient(rpc_address)

    def update_state(**kwargs):
        with _downlink_lock:
            downlink_state.update(kwargs)

    def should_stop():
        return _downlink_stop_flag

    try:
        # Step 1: Send CREATE_TRANS
        update_state(step='Sending CREATE_TRANS...')
        result = local_rpc.send_command('CREATE_TRANS', {'tid': tid, 'string_command': img_path})
        if not result:
            update_state(done=True, success=False,
                         error='CREATE_TRANS rejected by backend (tid conflict or invalid path)')
            return

        # Step 2: Wait for INIT_TRANS (transaction state >= INIT = 2)
        update_state(step='Waiting for satellite INIT_TRANS...')
        deadline = time.time() + 30
        number_of_packets = 0
        while time.time() < deadline:
            if should_stop():
                update_state(done=True, success=False, error='Cancelled by user')
                return
            status = local_rpc.get_transaction_status(tid)
            if status and status.get('found') and status.get('state', 0) >= 2:
                number_of_packets = status['number_of_packets']
                update_state(total=number_of_packets,
                             step=f'Initialized: {number_of_packets} packets total')
                break
            time.sleep(1)
        else:
            update_state(done=True, success=False,
                         error='Timeout waiting for INIT_TRANS from satellite (30s)')
            return

        if number_of_packets == 0:
            update_state(done=True, success=False,
                         error='Satellite reported 0 packets — check image path on satellite')
            return

        # Steps 3-5: Batch loop until all packets received
        while True:
            if should_stop():
                update_state(done=True, success=False, error='Cancelled by user')
                return

            status = local_rpc.get_transaction_status(tid)
            if not status or not status.get('found'):
                update_state(done=True, success=False, error='Transaction disappeared from backend')
                return

            missing_count = status['missing_count']
            received = status['received_packets']
            update_state(received=received)

            if status['state'] >= 5 or missing_count == 0:
                break

            batch_size = min(30, missing_count)
            update_state(step=f'Requesting batch of {batch_size} packets '
                              f'({received}/{number_of_packets} received)...')

            # Send GENERATE_X_PACKETS
            local_rpc.send_command('GENERATE_X_PACKETS', {'tid': tid, 'x': batch_size})

            # Wait for ACK with rid=0 (up to 15s)
            ack_deadline = time.time() + 15
            while time.time() < ack_deadline:
                if should_stop():
                    update_state(done=True, success=False, error='Cancelled during ACK wait')
                    return
                ack = local_rpc.get_pending_ack()
                if ack and ack.get('rid') == 0:
                    break
                time.sleep(0.3)

            # Poll until received count stabilizes (3s with no change) or COMPLETED
            update_state(step='Receiving fragments...')
            last_received = -1
            stable_since = None
            poll_deadline = time.time() + 60
            while time.time() < poll_deadline:
                if should_stop():
                    update_state(done=True, success=False, error='Cancelled during fragment receive')
                    return
                status = local_rpc.get_transaction_status(tid)
                if not status or not status.get('found'):
                    break
                cur_received = status['received_packets']
                update_state(received=cur_received)
                if status['state'] >= 5:
                    break
                if cur_received == last_received:
                    if stable_since is None:
                        stable_since = time.time()
                    elif time.time() - stable_since >= 3:
                        break
                else:
                    last_received = cur_received
                    stable_since = None
                time.sleep(0.5)

            # Send CONFIRM_LAST_BATCH
            update_state(step='Sending CONFIRM_LAST_BATCH...')
            local_rpc.send_command('CONFIRM_LAST_BATCH', {'tid': tid, 'MSB': 0, 'LSB': 0})

            # Wait for ACK (up to 10s)
            ack_deadline = time.time() + 10
            while time.time() < ack_deadline:
                if should_stop():
                    update_state(done=True, success=False, error='Cancelled during confirm ACK wait')
                    return
                ack = local_rpc.get_pending_ack()
                if ack and ack.get('rid') == 0:
                    break
                time.sleep(0.3)

        # Final update
        final_status = local_rpc.get_transaction_status(tid)
        final_received = (final_status['received_packets']
                          if final_status and final_status.get('found') else received)
        update_state(received=final_received, done=True, success=True,
                     step='Download complete!')

    except Exception as e:
        update_state(done=True, success=False, error=f'Unexpected error: {str(e)}')
    finally:
        with _downlink_lock:
            downlink_state['running'] = False


@app.route('/')
def index():
    """Render the main interface"""
    return render_template('index.html')

@app.route('/api/commands')
def get_commands():
    """Get all available commands with their properties"""
    try:
        commands = get_rpc_command_definitions()
        # Convert to a format easier for the frontend
        command_list = []
        for cmd_name, props in commands.items():
            command_list.append({
                'name': cmd_name,
                'id': props['id'],
                'arguments': props['arguments'],
                'argument_types': props['argument_types'],
                'precondition': props['precondition'],
                'size': props['size']
            })
        return jsonify({'success': True, 'commands': command_list})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/predefined_commands')
def get_predefined_commands():
    """Get predefined commands from JSON file"""
    try:
        with open('predefined_commands.json', 'r') as f:
            predefined = json.load(f)
        return jsonify({'success': True, 'commands': predefined})
    except FileNotFoundError:
        return jsonify({'success': True, 'commands': []})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/send_command', methods=['POST'])
def send_command():
    """
    Send a command to the satellite.
    This is where you'll add your ground station communication code.
    """
    try:
        data = request.json
        cmd_name = data['command']
        arguments = data['arguments']
        command_definitions = get_rpc_command_definitions()
        command_definition = command_definitions.get(cmd_name)

        if command_definition is None:
            raise ValueError(f"Unknown command '{cmd_name}'")

        argument_types = command_definition.get('argument_types', {})
        
        # make sure that the argument has the correct type. By deafult all arguments will be string
        for arg_name, arg_value in arguments.items():
            arg_str_format = argument_types.get(arg_name)
            arguments[arg_name] = coerce_argument_value(arg_name, arg_value, arg_str_format)
            
        print(f"=== SENDING COMMAND ===")
        print(f"Command: {cmd_name}")
        print(f"Arguments: {arguments}")
        # print(f"Encoded bytes: {' '.join(f'0x{b:02X}' for b in encoded_command)}")
        print(f"======================")

        response = rpc_client.send_command(cmd_name, arguments)
        
        # if response is true, i want the command box to flash  light green
        # if the response is false I want the command box to flash light red
        
        return jsonify({
            'success': response,
            'message': f'Command {cmd_name} sent successfully',
            # 'hex': ' '.join(f'0x{b:02X}' for b in encoded_command)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/last_packet')
def get_last_packet():
    """Get the last received packet information"""
    if last_packet['timestamp']:
        seconds_ago = (datetime.now() - last_packet['timestamp']).total_seconds()
        return jsonify({
            'success': True,
            'has_packet': True,
            'timestamp': last_packet['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            'seconds_ago': int(seconds_ago),
            'hex_data': last_packet['hex_data']
        })
    else:
        return jsonify({
            'success': True,
            'has_packet': False
        })

@app.route('/api/packet_history')
def get_packet_history():
    """Get the packet history"""
    return jsonify({
        'success': True,
        'history': packet_history
    })

@app.route('/api/ground_station_status')
def get_ground_station_status():
    """Get the current ground station status"""

    ground_station_active = rpc_client.server_active
    
    return jsonify({
        'success': True,
        'active': ground_station_active
    })

@app.route('/api/toggle_ground_station', methods=['POST'])
def toggle_ground_station():
    """Toggle ground station status"""
    global ground_station_active
    data = request.json
    if 'active' in data:
        ground_station_active = data['active']
    else:
        ground_station_active = not ground_station_active
    
    return jsonify({
        'success': True,
        'active': ground_station_active
    })

@app.route('/api/update_server_address', methods=['POST'])
def update_server_address():
    """Update the XML-RPC server address"""
    try:
        data = request.json
        ip = data.get('ip')
        port = data.get('port')
        
        if not ip or not port:
            return jsonify({'success': False, 'error': 'IP and port are required'})
        
        # Update the RPC client with new address
        rpc_client.update_address(ip, port)
        
        return jsonify({
            'success': True,
            'message': f'Server address updated to {ip}:{port}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/server_control', methods=['POST'])
def server_control():
    """Control the XML-RPC server (start, stop, restart)"""
    try:
        data = request.json
        action = data.get('action')
        
        if action == 'start':
            response = rpc_client.send_command('start_server', {})
            return jsonify({
                'success': response,
                'message': 'Server start command sent'
            })
        elif action == 'stop':
            response = rpc_client.send_command('stop_server', {})
            return jsonify({
                'success': response,
                'message': 'Server stop command sent'
            })
        elif action == 'restart':
            response = rpc_client.send_command('restart_server', {})
            return jsonify({
                'success': response,
                'message': 'Server restart command sent'
            })
        else:
            return jsonify({'success': False, 'error': 'Invalid action'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def update_last_packet(packet_bytes):
    """
    Call this function when you receive a packet from the satellite.
    
    Args:
        packet_bytes: The raw bytes received from the satellite
    """
    global last_packet, packet_history
    
    hex_data = ' '.join(f'0x{b:02X}' for b in packet_bytes)
    timestamp = datetime.now()
    
    last_packet['data'] = packet_bytes
    last_packet['timestamp'] = timestamp
    last_packet['hex_data'] = hex_data
    
    # Add to history
    packet_history.insert(0, {
        'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'hex_data': hex_data
    })
    
    # Keep only last 50 packets
    if len(packet_history) > 50:
        packet_history = packet_history[:50]

@app.route('/api/received_packets')
def get_received_packets():
    """Poll the backend for new decoded packets, buffer them, and return the full buffer."""
    try:
        new_packets = rpc_client.get_new_packets()
        if new_packets:
            with _rx_buffer_lock:
                received_packets_buffer.extend(new_packets)
    except Exception:
        pass  # backend may be offline; return what we have buffered
    with _rx_buffer_lock:
        return jsonify({'success': True, 'packets': list(received_packets_buffer)})


@app.route('/api/auto_downlink/start', methods=['POST'])
def auto_downlink_start():
    """Start the automated image downlink state machine in a background thread."""
    global downlink_state, _downlink_stop_flag
    with _downlink_lock:
        if downlink_state['running']:
            return jsonify({'success': False, 'error': 'Downlink already in progress'})

    data = request.json
    tid = data.get('tid')
    img_path = (data.get('img_path') or '').strip()

    if tid is None or not isinstance(tid, int) or tid < 0 or tid > 7:
        return jsonify({'success': False, 'error': 'tid must be an integer 0-7'})
    if not img_path:
        return jsonify({'success': False, 'error': 'img_path is required'})

    with _downlink_lock:
        downlink_state.update({
            'running': True,
            'tid': tid,
            'step': 'Starting...',
            'total': 0,
            'received': 0,
            'done': False,
            'success': False,
            'error': None
        })
        _downlink_stop_flag = False

    thread = threading.Thread(target=_run_downlink, args=(tid, img_path), daemon=True)
    thread.start()
    return jsonify({'success': True})


@app.route('/api/auto_downlink/status', methods=['GET'])
def auto_downlink_status():
    """Return the current state of the automated downlink."""
    with _downlink_lock:
        return jsonify(dict(downlink_state))


@app.route('/api/auto_downlink/stop', methods=['POST'])
def auto_downlink_stop():
    """Request the running downlink thread to stop."""
    global _downlink_stop_flag
    _downlink_stop_flag = True
    return jsonify({'success': True})


def set_ground_station_active(active=True):
    """
    Set the ground station status to active or inactive.
    
    Args:
        active: True for online, False for offline
    """
    global ground_station_active
    ground_station_active = active

def toggle_ground_station_status():
    """
    Toggle the ground station status between active and inactive.
    """
    global ground_station_active
    ground_station_active = not ground_station_active
    return ground_station_active

if __name__ == '__main__':
    # pretty print the server status on startup
    print(f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║           ARGUS Satellite Command Interface               ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  Running on: http://localhost:8080                        ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
        
    app.run(debug=True, host='0.0.0.0', port=8080,)