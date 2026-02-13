#!/usr/bin/env python3
"""
Satellite Telemetry Ingest Server
Receives telemetry dictionaries via TCP socket and stores them in InfluxDB
"""

import socket
import json
import os
import datetime
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TelemetryIngestServer:
    def __init__(self):
        # InfluxDB configuration from environment variables
        self.influx_url = os.getenv('INFLUXDB_URL', 'http://influxdb:8086')
        self.influx_token = os.getenv('INFLUXDB_TOKEN', 'my-super-secret-auth-token')
        self.influx_org = os.getenv('INFLUXDB_ORG', 'satellite')
        self.influx_bucket = os.getenv('INFLUXDB_BUCKET', 'telemetry')
        
        # Socket configuration
        self.host = os.getenv('SOCKET_HOST', '0.0.0.0')
        self.port = int(os.getenv('SOCKET_PORT', '5555'))
        
        # Initialize InfluxDB client
        logger.info(f"Connecting to InfluxDB at {self.influx_url}")
        self.client = InfluxDBClient(
            url=self.influx_url,
            token=self.influx_token,
            org=self.influx_org
        )
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        
        # Create socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
    def store_telemetry(self, telemetry_dict):
        """
        Store a telemetry dictionary in InfluxDB
        
        Args:
            telemetry_dict: Dictionary containing satellite telemetry data
        """
        timestamp = datetime.datetime.now(datetime.timezone.utc)
        
        # Iterate through each subsystem (CDH, EPS, ADCS, etc.)
        for subsystem, fields in telemetry_dict.items():
            if not isinstance(fields, dict):
                continue
                
            # Create a point for this subsystem
            point = Point("satellite_telemetry") \
                .tag("subsystem", subsystem) \
                .time(timestamp)
            
            # Add all fields from this subsystem
            for field_name, field_value in fields.items():
                # Handle None values and ensure proper types
                if field_value is not None:
                    point = point.field(field_name, field_value)
            
            # Write to InfluxDB
            try:
                self.write_api.write(bucket=self.influx_bucket, org=self.influx_org, record=point)
            except Exception as e:
                logger.error(f"Error writing to InfluxDB: {e}")
                raise
    
    def handle_client(self, conn, addr):
        """Handle incoming client connection"""
        logger.info(f"Connected by {addr}")
        
        buffer = ""
        try:
            while True:
                data = conn.recv(4096).decode('utf-8')
                if not data:
                    break
                
                buffer += data
                
                # Process complete JSON objects (separated by newlines)
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    
                    if not line:
                        continue
                    
                    try:
                        # Parse JSON telemetry
                        telemetry = json.loads(line)
                        
                        # Store in database
                        self.store_telemetry(telemetry)
                        
                        # Send acknowledgment
                        conn.sendall(b"OK\n")
                        
                        logger.info(f"Stored telemetry from {addr}")
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON from {addr}: {e}")
                        conn.sendall(b"ERROR: Invalid JSON\n")
                    except Exception as e:
                        logger.error(f"Error processing telemetry from {addr}: {e}")
                        conn.sendall(b"ERROR: Processing failed\n")
                        
        except Exception as e:
            logger.error(f"Connection error with {addr}: {e}")
        finally:
            conn.close()
            logger.info(f"Disconnected from {addr}")
    
    def run(self):
        """Start the ingest server"""
        self.sock.bind((self.host, self.port))
        self.sock.listen(5)
        
        logger.info(f"Telemetry Ingest Server listening on {self.host}:{self.port}")
        logger.info(f"Storing data to InfluxDB bucket: {self.influx_bucket}")
        logger.info("Waiting for connections...")
        
        try:
            while True:
                conn, addr = self.sock.accept()
                self.handle_client(conn, addr)
        except KeyboardInterrupt:
            logger.info("Shutting down server...")
        finally:
            self.sock.close()
            self.client.close()


if __name__ == "__main__":
    server = TelemetryIngestServer()
    server.run()
