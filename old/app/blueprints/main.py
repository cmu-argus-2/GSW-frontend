from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def dashboard():
    """Main mission control dashboard"""
    return render_template('pages/dashboard.html')


@main_bp.route('/commands')
def commands():
    """Full command queue management page"""
    return render_template('pages/commands.html')


@main_bp.route('/trends')
def trends():
    """Historical telemetry trends page"""
    return render_template('pages/trends.html')


@main_bp.route('/subsystem/<name>')
def subsystem_detail(name):
    """Detailed view for a specific subsystem"""
    valid_subsystems = ['cdh', 'eps', 'adcs', 'gps']
    if name.lower() not in valid_subsystems:
        return render_template('pages/dashboard.html')
    return render_template(f'pages/subsystem_{name.lower()}.html')
