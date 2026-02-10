from enum import IntEnum
from typing import Dict, Any, Optional
from dataclasses import dataclass


class TelemetryType(IntEnum):
    """Satellite telemetry message IDs"""
    SAT_HEARTBEAT = 0x01
    SAT_TM_HAL = 0x02
    SAT_TM_STORAGE = 0x03
    SAT_TM_PAYLOAD = 0x04
    SAT_TM_NOMINAL = 0x05
    SAT_ACK = 0x0F
    SAT_FILE_METADATA = 0x10
    SAT_FILE_PKT = 0x20

    @property
    def display_name(self) -> str:
        names = {
            TelemetryType.SAT_HEARTBEAT: 'Heartbeat',
            TelemetryType.SAT_TM_HAL: 'HAL Status',
            TelemetryType.SAT_TM_STORAGE: 'Storage Status',
            TelemetryType.SAT_TM_PAYLOAD: 'Payload Data',
            TelemetryType.SAT_TM_NOMINAL: 'Nominal Telemetry',
            TelemetryType.SAT_ACK: 'Acknowledgment',
            TelemetryType.SAT_FILE_METADATA: 'File Metadata',
            TelemetryType.SAT_FILE_PKT: 'File Packet'
        }
        return names.get(self, self.name)


# CDH telemetry field definitions with units and thresholds
CDH_FIELDS = {
    'TIME': {'unit': 's', 'label': 'Spacecraft Time'},
    'SC_STATE': {'unit': '', 'label': 'State'},
    'SD_USAGE': {'unit': 'bytes', 'label': 'SD Usage'},
    'CURRENT_RAM_USAGE': {'unit': '%', 'label': 'RAM Usage', 'warn': 80, 'critical': 95},
    'REBOOT_COUNT': {'unit': '', 'label': 'Reboot Count', 'warn': 5, 'critical': 10},
    'WATCHDOG_TIMER': {'unit': '', 'label': 'Watchdog'},
    'HAL_BITFLAGS': {'unit': '', 'label': 'HAL Flags'},
    'DETUMBLING_ERROR_FLAG': {'unit': '', 'label': 'Detumble Error'}
}

# EPS telemetry field definitions
EPS_FIELDS = {
    'EPS_POWER_FLAG': {'unit': '', 'label': 'Low Power Mode'},
    'MAINBOARD_TEMPERATURE': {'unit': '0.1°C', 'label': 'Mainboard Temp', 'divisor': 10,
                               'warn': 50, 'critical': 70},
    'MAINBOARD_VOLTAGE': {'unit': 'mV', 'label': 'Mainboard Voltage'},
    'MAINBOARD_CURRENT': {'unit': 'mA', 'label': 'Mainboard Current'},
    'BATTERY_PACK_TEMPERATURE': {'unit': '0.1°C', 'label': 'Battery Temp', 'divisor': 10,
                                  'warn': 40, 'critical': 55},
    'BATTERY_PACK_REPORTED_SOC': {'unit': '%', 'label': 'Battery SOC',
                                   'warn': 30, 'critical': 15},
    'BATTERY_PACK_REPORTED_CAPACITY': {'unit': 'mAh', 'label': 'Battery Capacity'},
    'BATTERY_PACK_CURRENT': {'unit': 'mA', 'label': 'Battery Current'},
    'BATTERY_PACK_VOLTAGE': {'unit': 'mV', 'label': 'Battery Voltage',
                              'warn': 7000, 'critical': 6500},
    'BATTERY_PACK_TTE': {'unit': 's', 'label': 'Time to Empty'},
    'BATTERY_PACK_TTF': {'unit': 's', 'label': 'Time to Full'},
    'RF_LDO_OUTPUT_VOLTAGE': {'unit': 'mV', 'label': 'RF LDO Voltage'},
    'RF_LDO_OUTPUT_CURRENT': {'unit': 'mA', 'label': 'RF LDO Current'}
}

# ADCS telemetry field definitions
ADCS_FIELDS = {
    'MODE': {'unit': '', 'label': 'ADCS Mode'},
    'GYRO_X': {'unit': 'rad/s', 'label': 'Gyro X'},
    'GYRO_Y': {'unit': 'rad/s', 'label': 'Gyro Y'},
    'GYRO_Z': {'unit': 'rad/s', 'label': 'Gyro Z'},
    'MAG_X': {'unit': 'μT', 'label': 'Mag X'},
    'MAG_Y': {'unit': 'μT', 'label': 'Mag Y'},
    'MAG_Z': {'unit': 'μT', 'label': 'Mag Z'},
    'SUN_STATUS': {'unit': '', 'label': 'Sun Sensor Valid'},
    'SUN_VEC_X': {'unit': '', 'label': 'Sun Vector X'},
    'SUN_VEC_Y': {'unit': '', 'label': 'Sun Vector Y'},
    'SUN_VEC_Z': {'unit': '', 'label': 'Sun Vector Z'}
}

# GPS telemetry field definitions
GPS_FIELDS = {
    'MESSAGE_ID': {'unit': '', 'label': 'Message ID'},
    'FIX_MODE': {'unit': '', 'label': 'Fix Mode'},
    'NUMBER_OF_SV': {'unit': '', 'label': 'Satellites'},
    'GNSS_WEEK': {'unit': '', 'label': 'GNSS Week'},
    'GNSS_TOW': {'unit': 'ms', 'label': 'Time of Week'},
    'LATITUDE': {'unit': '1e-7 deg', 'label': 'Latitude', 'divisor': 1e7},
    'LONGITUDE': {'unit': '1e-7 deg', 'label': 'Longitude', 'divisor': 1e7},
    'ELLIPSOID_ALT': {'unit': 'cm', 'label': 'Altitude', 'divisor': 100},
    'MEAN_SEA_LVL_ALT': {'unit': 'cm', 'label': 'MSL Altitude', 'divisor': 100}
}


def get_status_level(subsystem: str, field: str, value: Any) -> str:
    """Determine status level (nominal, warning, critical) for a telemetry value"""
    field_defs = {
        'CDH': CDH_FIELDS,
        'EPS': EPS_FIELDS,
        'ADCS': ADCS_FIELDS,
        'GPS': GPS_FIELDS
    }

    fields = field_defs.get(subsystem, {})
    field_def = fields.get(field, {})

    if value is None:
        return 'unknown'

    # Apply divisor if present
    divisor = field_def.get('divisor', 1)
    normalized_value = value / divisor if divisor != 1 else value

    # Check thresholds
    critical = field_def.get('critical')
    warn = field_def.get('warn')

    if critical is not None:
        # For battery SOC, lower is worse
        if 'SOC' in field or 'Voltage' in field:
            if normalized_value <= critical:
                return 'critical'
            if warn is not None and normalized_value <= warn:
                return 'warning'
        else:
            if normalized_value >= critical:
                return 'critical'
            if warn is not None and normalized_value >= warn:
                return 'warning'

    return 'nominal'
