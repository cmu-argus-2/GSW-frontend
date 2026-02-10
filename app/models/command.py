from enum import IntEnum
from typing import Dict, Any


class CommandID(IntEnum):
    """Ground station command IDs (from gs_constants.py)"""
    FORCE_REBOOT = 0x40
    SWITCH_TO_STATE = 0x41
    UPLINK_TIME_REFERENCE = 0x42
    UPLINK_ORBIT_REFERENCE = 0x43
    TURN_OFF_PAYLOAD = 0x44
    SCHEDULE_OD_EXPERIMENT = 0x45
    REQUEST_TM_NOMINAL = 0x46
    REQUEST_TM_HAL = 0x47
    REQUEST_TM_STORAGE = 0x48
    REQUEST_TM_PAYLOAD = 0x49
    FILE_METADATA = 0x4A
    FILE_PKT = 0x4B
    DOWNLINK_ALL_FILES = 0x50

    @property
    def args_schema(self) -> Dict[str, Any]:
        """Return the expected arguments schema for this command"""
        schemas = {
            CommandID.FORCE_REBOOT: {},
            CommandID.SWITCH_TO_STATE: {
                'target_state_id': {'type': 'int', 'min': 0, 'max': 255, 'required': True},
                'time_in_state': {'type': 'int', 'min': 0, 'required': True}
            },
            CommandID.UPLINK_TIME_REFERENCE: {},  # Auto-filled at TX time
            CommandID.UPLINK_ORBIT_REFERENCE: {
                'time_reference': {'type': 'int', 'required': True},
                'position_x': {'type': 'int', 'required': True},
                'position_y': {'type': 'int', 'required': True},
                'position_z': {'type': 'int', 'required': True},
                'velocity_x': {'type': 'int', 'required': True},
                'velocity_y': {'type': 'int', 'required': True},
                'velocity_z': {'type': 'int', 'required': True}
            },
            CommandID.TURN_OFF_PAYLOAD: {},
            CommandID.SCHEDULE_OD_EXPERIMENT: {},
            CommandID.REQUEST_TM_NOMINAL: {},
            CommandID.REQUEST_TM_HAL: {},
            CommandID.REQUEST_TM_STORAGE: {},
            CommandID.REQUEST_TM_PAYLOAD: {},
            CommandID.FILE_METADATA: {
                'file_id': {'type': 'int', 'min': 1, 'max': 10, 'required': True},
                'file_time': {'type': 'int', 'required': True}
            },
            CommandID.FILE_PKT: {
                'file_id': {'type': 'int', 'min': 1, 'max': 10, 'required': True},
                'file_time': {'type': 'int', 'required': True},
                'rq_sq_cnt': {'type': 'int', 'min': 0, 'required': True}
            },
            CommandID.DOWNLINK_ALL_FILES: {
                'file_id': {'type': 'int', 'min': 1, 'max': 10, 'required': True},
                'file_time': {'type': 'int', 'required': True}
            }
        }
        return schemas.get(self, {})

    @property
    def display_name(self) -> str:
        """Human-readable name for UI display"""
        names = {
            CommandID.FORCE_REBOOT: 'Force Reboot',
            CommandID.SWITCH_TO_STATE: 'Switch State',
            CommandID.UPLINK_TIME_REFERENCE: 'Uplink Time',
            CommandID.UPLINK_ORBIT_REFERENCE: 'Uplink Orbit',
            CommandID.TURN_OFF_PAYLOAD: 'Turn Off Payload',
            CommandID.SCHEDULE_OD_EXPERIMENT: 'Schedule OD Experiment',
            CommandID.REQUEST_TM_NOMINAL: 'Request TM Nominal',
            CommandID.REQUEST_TM_HAL: 'Request TM HAL',
            CommandID.REQUEST_TM_STORAGE: 'Request TM Storage',
            CommandID.REQUEST_TM_PAYLOAD: 'Request TM Payload',
            CommandID.FILE_METADATA: 'Request File Metadata',
            CommandID.FILE_PKT: 'Request File Packet',
            CommandID.DOWNLINK_ALL_FILES: 'Downlink All Files'
        }
        return names.get(self, self.name)

    @property
    def category(self) -> str:
        """Command category for grouping in UI"""
        if self in [CommandID.FORCE_REBOOT, CommandID.SWITCH_TO_STATE,
                    CommandID.TURN_OFF_PAYLOAD]:
            return 'Control'
        elif self in [CommandID.UPLINK_TIME_REFERENCE, CommandID.UPLINK_ORBIT_REFERENCE]:
            return 'Uplink'
        elif self in [CommandID.REQUEST_TM_NOMINAL, CommandID.REQUEST_TM_HAL,
                      CommandID.REQUEST_TM_STORAGE, CommandID.REQUEST_TM_PAYLOAD]:
            return 'Telemetry'
        elif self in [CommandID.FILE_METADATA, CommandID.FILE_PKT,
                      CommandID.DOWNLINK_ALL_FILES]:
            return 'File Transfer'
        else:
            return 'Other'


# File ID to name mapping
FILE_ID_NAMES = {
    1: 'cmd_logs',
    2: 'watchdog',
    3: 'eps',
    4: 'cdh',
    5: 'comms',
    6: 'imu',
    7: 'adcs',
    8: 'thermal',
    9: 'gps',
    10: 'img'
}

# Spacecraft states
SPACECRAFT_STATES = {
    0: 'STARTUP',
    1: 'DETUMBLING',
    2: 'NOMINAL',
    3: 'EXPERIMENT',
    4: 'LOW_POWER',
    5: 'SAFE'
}
