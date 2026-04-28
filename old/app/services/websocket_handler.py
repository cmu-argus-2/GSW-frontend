from flask import current_app
from flask_socketio import emit
from app import socketio
from app.services.backend_client import BackendClient
import time


@socketio.on('connect')
def handle_connect():
    """Client connected"""
    print('WebSocket client connected')
    emit('connection_status', {'status': 'connected'})


@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnected"""
    print('WebSocket client disconnected')


@socketio.on('subscribe_telemetry')
def handle_telemetry_subscription(data):
    """Subscribe to telemetry updates"""
    subsystems = data.get('subsystems', ['CDH', 'EPS', 'ADCS', 'GPS'])
    interval = data.get('interval', 1.0)  # Default 1 second

    emit('subscription_confirmed', {
        'subsystems': subsystems,
        'interval': interval
    })

    # Start background task to stream telemetry
    socketio.start_background_task(
        target=stream_telemetry,
        subsystems=subsystems,
        interval=interval
    )


def stream_telemetry(subsystems, interval=1.0):
    """Background task to stream telemetry data to clients"""
    from flask import current_app

    # Get app context for accessing config
    with current_app.app_context():
        client = BackendClient(
            base_url=current_app.config['BACKEND_API_URL'],
            mock_mode=current_app.config.get('MOCK_MODE', False)
        )

        while True:
            try:
                data = client.get_latest_telemetry('nominal')
                if data and 'rx_data' in data:
                    for subsystem in subsystems:
                        if subsystem in data['rx_data']:
                            socketio.emit('telemetry_update', {
                                'subsystem': subsystem,
                                'data': data['rx_data'][subsystem],
                                'timestamp': data.get('timestamp', time.time())
                            })

                # Also emit link status
                link_status = client.get_link_status()
                socketio.emit('link_status', link_status)

            except Exception as e:
                print(f'Error streaming telemetry: {e}')
                socketio.emit('telemetry_error', {'error': str(e)})

            socketio.sleep(interval)


@socketio.on('request_telemetry')
def handle_telemetry_request(data):
    """Handle one-time telemetry request"""
    tm_type = data.get('type', 'nominal')

    from flask import current_app
    client = BackendClient(
        base_url=current_app.config['BACKEND_API_URL'],
        mock_mode=current_app.config.get('MOCK_MODE', False)
    )

    telemetry = client.get_latest_telemetry(tm_type)
    emit('telemetry_response', {
        'type': tm_type,
        'data': telemetry
    })


@socketio.on('command_queue_update')
def handle_command_queue_request():
    """Handle command queue update request"""
    from flask import current_app
    client = BackendClient(
        base_url=current_app.config['BACKEND_API_URL'],
        mock_mode=current_app.config.get('MOCK_MODE', False)
    )

    queue = client.get_command_queue()
    emit('command_queue', {'queue': queue})
