"""
Satellite Command Interface
A simple Flask web app to build and send commands to the satellite.
"""

from flask import Flask, render_template, request, jsonify
from datetime import datetime
import json
from splat.splat.telemetry_helper import get_argument_type, list_all_commands
from splat.splat.telemetry_codec import pack, Command

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

@app.route('/')
def index():
    """Render the main interface"""
    return render_template('index.html')

@app.route('/api/commands')
def get_commands():
    """Get all available commands with their properties"""
    try:
        commands = list_all_commands()
        # Convert to a format easier for the frontend
        command_list = []
        for cmd_name, props in commands.items():
            command_list.append({
                'name': cmd_name,
                'id': props['id'],
                'arguments': props['arguments'],
                'precondition': props['precond'],
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
        
        # make sure that the argument has the correct type. By deafult all arguments will be string
        for arg_name, arg_value in arguments.items():
            # need to see if the argument is an int, string or float
            arg_str_format = get_argument_type(arg_name)
            
            # ints: b, B, ?, h, H, i, I, l, L, q, Q, n, N
            # float: e, d, F, D 
            # string: s, p          
            
            int_list = ['b', 'B', '?', 'h', 'H', 'i', 'I', 'l', 'L', 'q', 'Q', 'n', 'N']
            float_list = ['e', 'd', 'F', 'D']
            string_list = ['s', 'p']
            
            if arg_str_format in int_list:
                arg_value = int(arg_value)
            elif arg_str_format in float_list:
                arg_value = float(arg_value)
            elif arg_str_format in string_list:
                arg_value = str(arg_value)
            else:
                raise ValueError(f"Unknown argument type '{arg_str_format}' for argument '{arg_name}'")

            arguments[arg_name] = arg_value
            
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
        new_address = (ip, int(port))
        rpc_client.address = new_address
        rpc_client.server = xmlrpc.client.ServerProxy(f'http://{ip}:{port}')
        
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
    app.run(debug=True, host='0.0.0.0', port=8080, )