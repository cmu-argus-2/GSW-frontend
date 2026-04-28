from flask import Blueprint, jsonify, current_app
from datetime import datetime, timezone
from app.services.backend_client import BackendClient

system_bp = Blueprint('system', __name__)


def get_client():
    """Get backend client, with mock fallback if configured"""
    return BackendClient(
        base_url=current_app.config['BACKEND_API_URL'],
        mock_mode=current_app.config.get('MOCK_MODE', False)
    )


@system_bp.route('/link-status')
def get_link_status():
    """GET /api/system/link-status - Get current link status"""
    client = get_client()
    data = client.get_link_status()
    return jsonify(data)


@system_bp.route('/met')
def get_mission_elapsed_time():
    """GET /api/system/met - Get mission elapsed time"""
    mission_start = current_app.config.get('MISSION_START_TIME')
    if mission_start is None:
        return jsonify({'error': 'Mission start time not configured'}), 500

    now = datetime.now(timezone.utc)
    if mission_start.tzinfo is None:
        mission_start = mission_start.replace(tzinfo=timezone.utc)

    delta = now - mission_start
    total_seconds = int(delta.total_seconds())

    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    return jsonify({
        'total_seconds': total_seconds,
        'days': days,
        'hours': hours,
        'minutes': minutes,
        'seconds': seconds,
        'formatted': f'{days:03d}:{hours:02d}:{minutes:02d}:{seconds:02d}',
        'mission_start': mission_start.isoformat()
    })


@system_bp.route('/health')
def get_health():
    """GET /api/system/health - Frontend health check"""
    client = get_client()
    backend_connected = client.is_connected()

    return jsonify({
        'status': 'ok',
        'backend_connected': backend_connected,
        'mock_mode': current_app.config.get('MOCK_MODE', False)
    })


@system_bp.route('/config')
def get_frontend_config():
    """GET /api/system/config - Get frontend configuration for JS"""
    return jsonify({
        'backend_url': current_app.config['BACKEND_API_URL'],
        'mock_mode': current_app.config.get('MOCK_MODE', False),
        'mission_start': current_app.config.get('MISSION_START_TIME').isoformat()
            if current_app.config.get('MISSION_START_TIME') else None
    })
