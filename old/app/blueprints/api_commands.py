from flask import Blueprint, jsonify, request, current_app
from app.services.backend_client import BackendClient
from app.models.command import CommandID

commands_bp = Blueprint('commands', __name__)


def get_client():
    """Get backend client, with mock fallback if configured"""
    return BackendClient(
        base_url=current_app.config['BACKEND_API_URL'],
        mock_mode=current_app.config.get('MOCK_MODE', False)
    )


@commands_bp.route('/queue', methods=['GET'])
def get_command_queue():
    """GET /api/commands/queue - Get scheduled commands"""
    client = get_client()
    data = client.get_command_queue()
    return jsonify(data)


@commands_bp.route('/queue', methods=['POST'])
def add_command():
    """POST /api/commands/queue - Add command to queue"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    command_id = data.get('command_id')
    args = data.get('args', {})

    # Validate command ID
    if command_id is None:
        return jsonify({'error': 'command_id required'}), 400

    try:
        CommandID(command_id)  # Validate it's a known command
    except ValueError:
        return jsonify({'error': f'Unknown command_id: {command_id}'}), 400

    client = get_client()
    result = client.add_command(command_id, args)
    if result.get('success'):
        return jsonify(result), 201
    return jsonify(result), 500


@commands_bp.route('/queue/<int:cmd_id>', methods=['DELETE'])
def delete_command(cmd_id):
    """DELETE /api/commands/queue/<id> - Remove command from queue"""
    client = get_client()
    result = client.delete_command(cmd_id)
    if result.get('success'):
        return jsonify(result)
    return jsonify(result), 404


@commands_bp.route('/history', methods=['GET'])
def get_command_history():
    """GET /api/commands/history - Get executed commands log"""
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 50, type=int)

    client = get_client()
    data = client.get_command_history(page, limit)
    return jsonify(data)


@commands_bp.route('/estop', methods=['POST'])
def emergency_stop():
    """POST /api/commands/estop - Emergency stop (sends FORCE_REBOOT)"""
    client = get_client()
    result = client.send_estop()
    return jsonify(result)


@commands_bp.route('/definitions', methods=['GET'])
def get_command_definitions():
    """GET /api/commands/definitions - Get all available command definitions"""
    definitions = []
    for cmd in CommandID:
        definitions.append({
            'id': cmd.value,
            'name': cmd.name,
            'hex': hex(cmd.value),
            'args_schema': cmd.args_schema
        })
    return jsonify(definitions)
