import requests
from typing import Optional, Dict, Any, List
from datetime import datetime
import random


class BackendClient:
    """HTTP client for communicating with GSW-backend API"""

    def __init__(self, base_url: str, mock_mode: bool = False):
        self.base_url = base_url.rstrip('/')
        self.mock_mode = mock_mode
        self.timeout = 5.0
        self._session = requests.Session()

    def is_connected(self) -> bool:
        """Check if backend is reachable"""
        if self.mock_mode:
            return True
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
        if self.mock_mode:
            return self._mock_telemetry(tm_type)

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
        if self.mock_mode:
            return {'data': [], 'page': page, 'total': 0}

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
        if self.mock_mode:
            return self._mock_command_queue()

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
        if self.mock_mode:
            return {'success': True, 'id': random.randint(1, 1000)}

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
        if self.mock_mode:
            return {'success': True}

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
        if self.mock_mode:
            return {'data': [], 'page': page, 'total': 0}

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
        if self.mock_mode:
            return {'success': True, 'message': 'E-STOP sent (mock)'}

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
        if self.mock_mode:
            return {
                'status': 'connected',
                'last_contact': datetime.utcnow().isoformat(),
                'last_tm_age_seconds': random.uniform(0.1, 2.0)
            }

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

    # ==================== MOCK DATA ====================

    def _mock_telemetry(self, tm_type: str) -> Dict[str, Any]:
        """Generate mock telemetry data for development"""
        now = datetime.utcnow()

        return {
            'rx_id': 0x05 if tm_type == 'nominal' else 0x01,
            'rx_name': f'SAT_TM_{tm_type.upper()}',
            'rx_type': 'telemetry',
            'timestamp': now.isoformat(),
            'rx_data': {
                'CDH': {
                    'TIME': int(now.timestamp()),
                    'SC_STATE': 2,  # NOMINAL
                    'SD_USAGE': random.randint(10000000, 100000000),
                    'CURRENT_RAM_USAGE': random.randint(30, 60),
                    'REBOOT_COUNT': random.randint(0, 3),
                    'WATCHDOG_TIMER': 0,
                    'HAL_BITFLAGS': 0,
                    'DETUMBLING_ERROR_FLAG': 0
                },
                'EPS': {
                    'EPS_POWER_FLAG': 0,
                    'MAINBOARD_TEMPERATURE': random.randint(250, 350),
                    'MAINBOARD_VOLTAGE': random.randint(7800, 8400),
                    'MAINBOARD_CURRENT': random.randint(200, 500),
                    'BATTERY_PACK_TEMPERATURE': random.randint(200, 300),
                    'BATTERY_PACK_REPORTED_SOC': random.randint(60, 95),
                    'BATTERY_PACK_REPORTED_CAPACITY': random.randint(2000, 2500),
                    'BATTERY_PACK_CURRENT': random.randint(-500, 500),
                    'BATTERY_PACK_VOLTAGE': random.randint(7200, 8200),
                    'BATTERY_PACK_MIDPOINT_VOLTAGE': random.randint(3600, 4100),
                    'BATTERY_PACK_TTE': random.randint(3600, 14400),
                    'BATTERY_PACK_TTF': random.randint(1800, 7200),
                    'XP_SOLAR_CHARGE_VOLTAGE': random.randint(4000, 5500),
                    'XP_SOLAR_CHARGE_CURRENT': random.randint(0, 500),
                    'XM_SOLAR_CHARGE_VOLTAGE': random.randint(4000, 5500),
                    'XM_SOLAR_CHARGE_CURRENT': random.randint(0, 500),
                    'YP_SOLAR_CHARGE_VOLTAGE': random.randint(4000, 5500),
                    'YP_SOLAR_CHARGE_CURRENT': random.randint(0, 500),
                    'YM_SOLAR_CHARGE_VOLTAGE': random.randint(4000, 5500),
                    'YM_SOLAR_CHARGE_CURRENT': random.randint(0, 500),
                    'ZP_SOLAR_CHARGE_VOLTAGE': random.randint(4000, 5500),
                    'ZP_SOLAR_CHARGE_CURRENT': random.randint(0, 500),
                    'ZM_SOLAR_CHARGE_VOLTAGE': random.randint(4000, 5500),
                    'ZM_SOLAR_CHARGE_CURRENT': random.randint(0, 500),
                    'RF_LDO_OUTPUT_VOLTAGE': random.randint(3200, 3400),
                    'RF_LDO_OUTPUT_CURRENT': random.randint(50, 150)
                },
                'ADCS': {
                    'MODE': random.randint(0, 3),
                    'GYRO_X': random.uniform(-0.1, 0.1),
                    'GYRO_Y': random.uniform(-0.1, 0.1),
                    'GYRO_Z': random.uniform(-0.1, 0.1),
                    'MAG_X': random.uniform(-50, 50),
                    'MAG_Y': random.uniform(-50, 50),
                    'MAG_Z': random.uniform(-50, 50),
                    'SUN_STATUS': 1,
                    'SUN_VEC_X': random.uniform(-1, 1),
                    'SUN_VEC_Y': random.uniform(-1, 1),
                    'SUN_VEC_Z': random.uniform(-1, 1),
                    'LIGHT_SENSOR_XP': random.randint(100, 4000),
                    'LIGHT_SENSOR_XM': random.randint(100, 4000),
                    'LIGHT_SENSOR_YP': random.randint(100, 4000),
                    'LIGHT_SENSOR_YM': random.randint(100, 4000),
                    'LIGHT_SENSOR_ZP1': random.randint(100, 4000),
                    'LIGHT_SENSOR_ZM': random.randint(100, 4000)
                },
                'GPS': {
                    'MESSAGE_ID': 1,
                    'FIX_MODE': 3,
                    'NUMBER_OF_SV': random.randint(6, 12),
                    'GNSS_WEEK': 2345,
                    'GNSS_TOW': random.randint(0, 604799999),
                    'LATITUDE': int(40.4433 * 1e7),
                    'LONGITUDE': int(-79.9436 * 1e7),
                    'ELLIPSOID_ALT': random.randint(40000000, 45000000),
                    'MEAN_SEA_LVL_ALT': random.randint(40000000, 45000000),
                    'ECEF_X': random.randint(-700000000, 700000000),
                    'ECEF_Y': random.randint(-700000000, 700000000),
                    'ECEF_Z': random.randint(-700000000, 700000000),
                    'ECEF_VX': random.randint(-800000, 800000),
                    'ECEF_VY': random.randint(-800000, 800000),
                    'ECEF_VZ': random.randint(-800000, 800000)
                }
            }
        }

    def _mock_command_queue(self) -> List[Dict[str, Any]]:
        """Generate mock command queue for development"""
        return [
            {
                'id': 1,
                'command_id': 0x46,
                'command_name': 'REQUEST_TM_NOMINAL',
                'args': {},
                'created_at': datetime.utcnow().isoformat()
            },
            {
                'id': 2,
                'command_id': 0x48,
                'command_name': 'REQUEST_TM_STORAGE',
                'args': {},
                'created_at': datetime.utcnow().isoformat()
            }
        ]
