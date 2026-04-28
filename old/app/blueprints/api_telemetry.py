from flask import Blueprint, jsonify, request, current_app
from app.services.backend_client import BackendClient

telemetry_bp = Blueprint('telemetry', __name__)


def get_client():
    """Get backend client, with mock fallback if configured"""
    return BackendClient(
        base_url=current_app.config['BACKEND_API_URL'],
        mock_mode=current_app.config.get('MOCK_MODE', False)
    )


@telemetry_bp.route('/latest/<tm_type>')
def get_latest_telemetry(tm_type):
    """
    GET /api/telemetry/latest/<type>
    Types: heartbeat, nominal, hal, storage
    """
    valid_types = ['heartbeat', 'nominal', 'hal', 'storage']
    if tm_type not in valid_types:
        return jsonify({'error': f'Invalid type. Must be one of: {valid_types}'}), 400

    client = get_client()
    data = client.get_latest_telemetry(tm_type)
    if data is None:
        return jsonify({'error': 'Failed to fetch telemetry'}), 503
    return jsonify(data)


@telemetry_bp.route('/history')
def get_telemetry_history():
    """
    GET /api/telemetry/history?type=<type>&page=<n>&limit=<n>
    """
    tm_type = request.args.get('type', 'nominal')
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 50, type=int)

    client = get_client()
    data = client.get_telemetry_history(tm_type, page, limit)
    return jsonify(data)


@telemetry_bp.route('/subsystem/<subsystem>')
def get_subsystem_telemetry(subsystem):
    """
    GET /api/telemetry/subsystem/<CDH|EPS|ADCS|GPS>
    """
    valid_subsystems = ['CDH', 'EPS', 'ADCS', 'GPS']
    subsystem = subsystem.upper()
    if subsystem not in valid_subsystems:
        return jsonify({'error': f'Invalid subsystem. Must be one of: {valid_subsystems}'}), 400

    client = get_client()
    data = client.get_subsystem_telemetry(subsystem)
    if data is None:
        return jsonify({'error': 'Failed to fetch subsystem telemetry'}), 503
    return jsonify(data)
