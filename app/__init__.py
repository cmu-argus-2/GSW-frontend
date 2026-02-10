from flask import Flask
from flask_socketio import SocketIO
import os

socketio = SocketIO()


def create_app(config_name=None):
    """Application factory for creating Flask app instances"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(__name__,
                template_folder='../templates',
                static_folder='../static')

    # Load configuration
    from config import config
    app.config.from_object(config.get(config_name, config['default']))

    # Initialize extensions
    socketio.init_app(app, cors_allowed_origins="*", async_mode='threading')

    # Register blueprints
    from app.blueprints.main import main_bp
    from app.blueprints.api_telemetry import telemetry_bp
    from app.blueprints.api_commands import commands_bp
    from app.blueprints.api_system import system_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(telemetry_bp, url_prefix='/api/telemetry')
    app.register_blueprint(commands_bp, url_prefix='/api/commands')
    app.register_blueprint(system_bp, url_prefix='/api/system')

    # Register WebSocket handlers
    from app.services import websocket_handler  # noqa: F401

    return app
