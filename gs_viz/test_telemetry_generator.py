#!/usr/bin/env python3
"""
Test script to generate sample telemetry data and send to ingest server
Useful for testing the database and creating initial dashboards
"""

import time
import random
from telemetry_client import TelemetryClient


def generate_sample_telemetry():
    """Generate realistic-looking telemetry data"""
    return {
        'CDH': {
            'TIME': int(time.time()),
            'SC_STATE': random.randint(0, 3),
            'SD_USAGE': random.randint(0, 100),
            'CURRENT_RAM_USAGE': random.randint(40, 70),
            'REBOOT_COUNT': random.randint(0, 5),
            'WATCHDOG_TIMER': random.randint(0, 100),
            'HAL_BITFLAGS': random.randint(0, 255),
            'DETUMBLING_ERROR_FLAG': random.randint(0, 1)
        },
        'EPS': {
            'EPS_POWER_FLAG': random.randint(0, 1),
            'MAINBOARD_TEMPERATURE': random.randint(2500, 3000),  # ~25-30°C
            'MAINBOARD_VOLTAGE': random.randint(3200, 3400),      # ~3.3V
            'MAINBOARD_CURRENT': random.randint(50, 100),
            'BATTERY_PACK_TEMPERATURE': random.randint(2000, 2500),
            'BATTERY_PACK_REPORTED_SOC': random.randint(60, 100),
            'BATTERY_PACK_REPORTED_CAPACITY': random.randint(8000, 10000),
            'BATTERY_PACK_CURRENT': random.randint(-500, 500),
            'BATTERY_PACK_VOLTAGE': random.randint(3600, 4200),
            'BATTERY_PACK_MIDPOINT_VOLTAGE': random.randint(1800, 2100),
            'BATTERY_PACK_TTE': random.randint(0, 3600),
            'BATTERY_PACK_TTF': random.randint(0, 3600),
            'RF_LDO_OUTPUT_VOLTAGE': random.randint(4900, 5100),
            'RF_LDO_OUTPUT_CURRENT': random.randint(15, 25),
            'GPS_VOLTAGE': random.randint(3200, 3400),
            'GPS_CURRENT': random.randint(10, 15),
            # Solar panels (simulate day/night cycle)
            'XP_SOLAR_CHARGE_VOLTAGE': random.randint(0, 5000) if random.random() > 0.5 else 0,
            'XP_SOLAR_CHARGE_CURRENT': random.randint(0, 200) if random.random() > 0.5 else 0,
            'YP_SOLAR_CHARGE_VOLTAGE': random.randint(0, 5000) if random.random() > 0.5 else 0,
            'YP_SOLAR_CHARGE_CURRENT': random.randint(0, 200) if random.random() > 0.5 else 0,
            'ZP_SOLAR_CHARGE_VOLTAGE': random.randint(0, 5000) if random.random() > 0.5 else 0,
            'ZP_SOLAR_CHARGE_CURRENT': random.randint(0, 200) if random.random() > 0.5 else 0,
        },
        'ADCS': {
            'MODE': random.randint(0, 3),
            'GYRO_X': random.uniform(-0.1, 0.1),
            'GYRO_Y': random.uniform(-0.1, 0.1),
            'GYRO_Z': random.uniform(-0.1, 0.1),
            'MAG_X': random.uniform(-50, 50),
            'MAG_Y': random.uniform(-50, 50),
            'MAG_Z': random.uniform(-50, 50),
            'SUN_STATUS': random.randint(0, 255),
            'SUN_VEC_X': random.uniform(-1, 1),
            'SUN_VEC_Y': random.uniform(-1, 1),
            'SUN_VEC_Z': random.uniform(-1, 1),
            'LIGHT_SENSOR_XP': random.randint(0, 1023),
            'LIGHT_SENSOR_XM': random.randint(0, 1023),
            'LIGHT_SENSOR_YP': random.randint(0, 1023),
            'LIGHT_SENSOR_YM': random.randint(0, 1023),
            'LIGHT_SENSOR_ZP1': random.randint(0, 1023),
            'LIGHT_SENSOR_ZP2': random.randint(0, 1023),
            'LIGHT_SENSOR_ZP3': random.randint(0, 1023),
            'LIGHT_SENSOR_ZP4': random.randint(0, 1023),
            'LIGHT_SENSOR_ZM': random.randint(0, 1023),
        }
    }


if __name__ == "__main__":
    print("Starting telemetry data generator...")
    print("This will generate sample data every 5 seconds.")
    print("Press Ctrl+C to stop.")
    print()
    
    # Connect to ingest server
    client = TelemetryClient(host='localhost', port=5555)
    
    try:
        print("Connecting to ingest server...")
        client.connect()
        print("Connected!")
        print()
        
        count = 0
        while True:
            telemetry = generate_sample_telemetry()
            response = client.send_telemetry(telemetry)
            count += 1
            
            if response == "OK":
                print(f"[{count}] Sent telemetry - "
                      f"RAM: {telemetry['CDH']['CURRENT_RAM_USAGE']}%, "
                      f"Temp: {telemetry['EPS']['MAINBOARD_TEMPERATURE']/100:.1f}°C, "
                      f"Battery SOC: {telemetry['EPS']['BATTERY_PACK_REPORTED_SOC']}%")
            else:
                print(f"[{count}] Error: {response}")
            
            time.sleep(5)  # Wait 5 seconds between packets
            
    except KeyboardInterrupt:
        print(f"\n\nStopped. Sent {count} telemetry packets.")
    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure the ingest server is running: docker-compose up -d")
    finally:
        client.close()
