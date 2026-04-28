import requests
from typing import Optional, Dict, Any, List


class BackendClient:
    """HTTP client for communicating with GSW-backend API"""

    def __init__(self, base_url: str, mock_mode: bool = False):
        self.base_url = base_url.rstrip('/')
        self.mock_mode = mock_mode
        self.timeout = 5.0
        self._session = requests.Session()

    def is_connected(self) -> bool:
        """Check if backend is reachable"""
        try:
            response = self._session.get(
                f'{self.base_url}/api/system/health',
                timeout=2
            )
            return response.status_code == 200
        except requests.RequestException:
            return False

    # ==================== TELEMETRY ====================

    def get_latest_telemetry(self, tm_type: str) -> Optional[Dict[str, Any]]:
        """Get latest telemetry by type"""
        try:
            response = self._session.get(
                f'{self.base_url}/api/telemetry/latest/{tm_type}',
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return None

    def get_telemetry_history(self, tm_type: str, page: int = 1,
                              limit: int = 50) -> Dict[str, Any]:
        """Get telemetry history"""
        try:
            response = self._session.get(
                f'{self.base_url}/api/telemetry/history',
                params={'type': tm_type, 'page': page, 'limit': limit},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return {'data': [], 'page': page, 'total': 0}

    def get_subsystem_telemetry(self, subsystem: str) -> Optional[Dict[str, Any]]:
        """Get latest telemetry for a specific subsystem"""
        latest = self.get_latest_telemetry('nominal')
        if latest and subsystem in latest.get('rx_data', {}):
            return latest['rx_data'][subsystem]
        return None

    # ==================== COMMANDS ====================

    def get_command_queue(self) -> List[Dict[str, Any]]:
        """Get pending commands in queue"""
        try:
            response = self._session.get(
                f'{self.base_url}/api/commands/queue',
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return []

    def add_command(self, command_id: int, args: Dict[str, Any]) -> Dict[str, Any]:
        """Add command to queue"""
        try:
            response = self._session.post(
                f'{self.base_url}/api/commands/queue',
                json={'command_id': command_id, 'args': args},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {'success': False, 'error': str(e)}

    def delete_command(self, cmd_id: int) -> Dict[str, Any]:
        """Remove command from queue"""
        try:
            response = self._session.delete(
                f'{self.base_url}/api/commands/queue/{cmd_id}',
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {'success': False, 'error': str(e)}

    def get_command_history(self, page: int = 1,
                            limit: int = 50) -> Dict[str, Any]:
        """Get executed commands log"""
        try:
            response = self._session.get(
                f'{self.base_url}/api/commands/history',
                params={'page': page, 'limit': limit},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return {'data': [], 'page': page, 'total': 0}

    def send_estop(self) -> Dict[str, Any]:
        """Send emergency stop command"""
        try:
            response = self._session.post(
                f'{self.base_url}/api/commands/estop',
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {'success': False, 'error': str(e)}

    # ==================== SYSTEM ====================

    def get_link_status(self) -> Dict[str, Any]:
        """Get current link status"""
        try:
            response = self._session.get(
                f'{self.base_url}/api/system/link-status',
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return {
                'status': 'disconnected',
                'last_contact': None,
                'last_tm_age_seconds': None
            }
