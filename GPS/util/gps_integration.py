#!/usr/bin/env python3
import serial
import pynmea2
import time
from serial.tools import list_ports
import os
from datetime import datetime
import json
import threading

class GPSIntegration:
    def __init__(self):
        self.port = None
        self.ser = None
        self.is_connected = False
        self.current_data = None
        self.last_fix_time = None
        self.gps_thread = None
        self.is_running = False
        
    def find_gps_port(self):
        """Find the COM port for the BU-353N5 GPS receiver"""
        ports = list_ports.comports()
        gps_ports = []
        
        for port in ports:
            # Look for specific GPS device identifiers
            description_upper = port.description.upper()
            
            # Skip Bluetooth and non-USB devices
            if any(skip_keyword in description_upper for skip_keyword in ['BLUETOOTH', 'BT', 'WIRELESS']):
                continue
                
            # Look for GPS-specific identifiers
            if any(gps_keyword in description_upper for gps_keyword in ['BU-353N5', 'GLOBALSAT', 'GPS', 'UBLOX']):
                gps_ports.append(port.device)
            # Also check for USB Serial devices that might be GPS
            elif 'USB' in description_upper and 'SERIAL' in description_upper:
                gps_ports.append(port.device)
        
        if gps_ports:
            return gps_ports[0]  # Return the first GPS device found
        
        return None
    
    def connect_gps(self):
        """Connect to GPS device"""
        if self.is_connected:
            return True
            
        self.port = self.find_gps_port()
        if not self.port:
            return False
        
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=4800,  # BU-353N5 typical baudrate
                timeout=1,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            self.is_connected = True
            return True
        except serial.SerialException as e:
            print(f"Error connecting to GPS: {e}")
            return False
    
    def disconnect_gps(self):
        """Disconnect from GPS device"""
        self.is_running = False
        if self.gps_thread and self.gps_thread.is_alive():
            self.gps_thread.join(timeout=1)
        
        if self.ser:
            self.ser.close()
            self.ser = None
        
        self.is_connected = False
        self.current_data = None
    
    def get_direction(self, degrees):
        """Convert degrees to cardinal direction"""
        if degrees is None:
            return None
        
        directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                     'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        index = round(degrees / 22.5) % 16
        return directions[index]
    
    def parse_gps_data(self, line):
        """Parse NMEA data and return user-friendly format"""
        try:
            if line.startswith('$GPRMC') or line.startswith('$GNRMC'):
                msg = pynmea2.parse(line)
                speed_knots = msg.spd_over_grnd
                speed_kmh = float(speed_knots) * 1.852 if speed_knots else None
                speed_mph = float(speed_knots) * 1.15078 if speed_knots else None
                
                return {
                    'timestamp': msg.timestamp.isoformat() if msg.timestamp else None,
                    'latitude': msg.latitude,
                    'longitude': msg.longitude,
                    'lat_dir': msg.lat_dir,
                    'lon_dir': msg.lon_dir,
                    'speed_knots': speed_knots,
                    'speed_kmh': speed_kmh,
                    'speed_mph': speed_mph,
                    'course': msg.true_course,
                    'course_direction': self.get_direction(msg.true_course) if msg.true_course else None,
                    'date': msg.datestamp.isoformat() if msg.datestamp else None,
                    'status': msg.status,
                    'type': 'RMC',
                    'has_fix': msg.status == 'A'
                }
            elif line.startswith('$GPGGA') or line.startswith('$GNGGA'):
                msg = pynmea2.parse(line)
                return {
                    'timestamp': msg.timestamp.isoformat() if msg.timestamp else None,
                    'latitude': msg.latitude,
                    'longitude': msg.longitude,
                    'lat_dir': msg.lat_dir,
                    'lon_dir': msg.lon_dir,
                    'altitude': msg.altitude,
                    'altitude_units': msg.altitude_units,
                    'satellites': msg.num_sats,
                    'fix_quality': msg.gps_qual,
                    'hdop': msg.horizontal_dil,
                    'type': 'GGA',
                    'has_fix': msg.gps_qual > 0
                }
        except pynmea2.ParseError:
            return None
        return None
    
    def start_gps_monitoring(self):
        """Start GPS data monitoring in a separate thread"""
        if not self.is_connected:
            return False
        
        self.is_running = True
        self.gps_thread = threading.Thread(target=self._gps_monitor_loop, daemon=True)
        self.gps_thread.start()
        return True
    
    def _gps_monitor_loop(self):
        """GPS monitoring loop"""
        while self.is_running and self.is_connected:
            try:
                line = self.ser.readline().decode('ascii', errors='replace').strip()
                
                if line.startswith('$'):
                    data = self.parse_gps_data(line)
                    
                    if data and data.get('has_fix'):
                        self.current_data = data
                        self.last_fix_time = time.time()
                        
            except Exception as e:
                print(f"GPS monitoring error: {e}")
                time.sleep(0.1)
    
    def get_current_gps_data(self):
        """Get current GPS data"""
        if self.current_data and self.last_fix_time:
            # Check if data is recent (within last 10 seconds)
            if time.time() - self.last_fix_time < 10:
                return self.current_data
        return None
    
    def test_gps_connection(self):
        """Test GPS connection and return status"""
        if not self.connect_gps():
            return {
                'status': 'error',
                'message': 'GPS device not found',
                'details': 'Check USB connection and drivers'
            }
        
        try:
            # Try to read data for 5 seconds
            start_time = time.time()
            nmea_count = 0
            valid_fix = False
            sample_data = None
            
            while time.time() - start_time < 5:
                try:
                    line = self.ser.readline().decode('ascii', errors='replace').strip()
                    
                    if line.startswith('$'):
                        nmea_count += 1
                        data = self.parse_gps_data(line)
                        
                        if data and data.get('has_fix'):
                            valid_fix = True
                            sample_data = data
                            # Store the data for later use
                            self.current_data = data
                            self.last_fix_time = time.time()
                            break
                            
                except Exception:
                    continue
            
            if nmea_count > 0:
                if valid_fix:
                    return {
                        'status': 'ok',
                        'message': 'GPS connected with valid fix',
                        'satellites': sample_data.get('satellites', 'N/A'),
                        'position': f"{sample_data.get('latitude', 0):.6f}° {sample_data.get('lat_dir', '')}, {sample_data.get('longitude', 0):.6f}° {sample_data.get('lon_dir', '')}",
                        'speed': f"{sample_data.get('speed_kmh', 0):.1f} km/h" if sample_data.get('speed_kmh') else 'N/A',
                        'course': f"{sample_data.get('course', 0):.1f}° {sample_data.get('course_direction', '')}" if sample_data.get('course') else 'N/A'
                    }
                else:
                    return {
                        'status': 'warning',
                        'message': 'GPS connected but waiting for fix',
                        'details': 'This is normal if device just started'
                    }
            else:
                return {
                    'status': 'error',
                    'message': 'No GPS data received',
                    'details': 'Check device configuration'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'GPS test failed: {str(e)}',
                'details': 'Check device connection'
            }
    
    def calculate_distance(self, gps1, gps2):
        """Calculate distance between two GPS coordinates using Haversine formula"""
        import math
        
        if not gps1 or not gps2:
            return 0
        
        # Extract coordinates
        lat1 = gps1.get('latitude', 0)
        lon1 = gps1.get('longitude', 0)
        lat2 = gps2.get('latitude', 0)
        lon2 = gps2.get('longitude', 0)
        
        if lat1 == 0 and lon1 == 0 and lat2 == 0 and lon2 == 0:
            return 0
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth's radius in meters
        earth_radius = 6371000
        
        # Distance in meters
        distance = earth_radius * c
        
        return distance
    
    def save_gps_data_with_image(self, image_filename, gps_data=None):
        """Save GPS data associated with an image"""
        if not gps_data:
            gps_data = self.get_current_gps_data()
        
        if not gps_data:
            print("No GPS data available to save")
            return None
        
        # Create GPS data directory if it doesn't exist
        gps_data_dir = "gps_data"
        try:
            if not os.path.exists(gps_data_dir):
                os.makedirs(gps_data_dir)
                print(f"Created GPS data directory: {gps_data_dir}")
        except Exception as e:
            print(f"Error creating GPS data directory: {e}")
            return None
        
        # Create JSON filename based on image filename
        base_name = os.path.splitext(image_filename)[0]
        json_filename = f"{base_name}_gps.json"
        json_filepath = os.path.join(gps_data_dir, json_filename)
        
        # Prepare data to save
        data_to_save = {
            'image_filename': image_filename,
            'gps_data': gps_data,
            'captured_at': datetime.now().isoformat()
        }
        
        # Save to JSON file
        try:
            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=2, ensure_ascii=False)
            print(f"GPS data saved successfully to: {json_filepath}")
            return json_filepath
        except PermissionError as e:
            print(f"Permission error saving GPS data: {e}")
            print(f"Check if you have write permissions to: {os.path.dirname(json_filepath)}")
            return None
        except Exception as e:
            print(f"Error saving GPS data: {e}")
            print(f"Attempted to save to: {json_filepath}")
            return None 