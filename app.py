#!/usr/bin/env python3
"""
ARGUS Mission Control Frontend
Entry point for the Flask application
"""
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

from app import create_app, socketio

app = create_app(os.getenv('FLASK_ENV', 'development'))

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'

    print(f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║           ARGUS Mission Control Frontend                   ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  Running on: http://localhost:{port}                         ║
    ║  Debug mode: {str(debug).lower():<10}                              ║
    ║  Mock mode:  {str(app.config.get('MOCK_MODE', False)).lower():<10}                              ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

    socketio.run(app, host='0.0.0.0', port=port, debug=debug)
