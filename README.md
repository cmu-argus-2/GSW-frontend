# ARGUS Mission Control Frontend

A modern, dark-themed mission control dashboard for the ARGUS CubeSat ground station.

## Quick Start

1. **Install dependencies:**
   ```bash
   cd GSW-Frontend
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

4. **Open browser:**
   Navigate to `http://localhost:5001`

## Configuration

Edit `.env` to configure:

| Variable | Description | Default |
|----------|-------------|---------|
| `BACKEND_API_URL` | URL of GSW-backend API | `http://localhost:5000` |
| `SECRET_KEY` | Flask secret key | (change in production) |
| `FLASK_ENV` | Environment mode | `development` |
| `MISSION_START_TIME` | ISO timestamp for MET | `2025-01-01T00:00:00Z` |

## Development Mode

In development mode (`FLASK_ENV=development`), the frontend uses **mock data** when the backend is unavailable. This allows UI development without a running backend.

## Project Structure

```
GSW-Frontend/
├── app.py                  # Flask entry point
├── config.py               # Configuration classes
├── app/
│   ├── __init__.py         # App factory
│   ├── blueprints/         # Route handlers
│   ├── services/           # Backend client, WebSocket
│   └── models/             # Data models
├── templates/              # Jinja2 templates
│   ├── base.html
│   ├── pages/
│   ├── components/
│   └── cards/
└── static/
    ├── css/                # Styles
    ├── js/                 # JavaScript modules
    └── images/             # Assets
```

## Features

- **Real-time telemetry display** via WebSocket
- **Command queue management** with validation
- **Mission Elapsed Time (MET)** clock
- **Dark theme** optimized for mission control
- **Responsive layout** for different screen sizes
- **E-STOP** with confirmation dialog

## Backend API Requirements

This frontend requires the GSW-backend to implement the following API endpoints. See `BACKEND_API_SPEC.md` for details.

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+E` | Open E-STOP dialog |
| `Escape` | Close modal dialogs |
