#!/usr/bin/env python3
import serial
import pynmea2
import time
from serial.tools import list_ports
import os
from datetime import datetime

def find_gps_port_windows():
    """Find the COM port for the BU-353N5 GPS receiver"""
    ports = list_ports.comports()
    print("Available COM ports:")
    gps_ports = []
    
    for port in ports:
        print(f" - {port.device}: {port.description}")
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
        print(f"\nPotential GPS devices found: {gps_ports}")
        return gps_ports[0]  # Return the first GPS device found
    
    print("\nNo GPS devices detected. Available USB devices:")
    for port in ports:
        if 'USB' in port.description.upper():
            print(f" - {port.device}: {port.description}")
    
    return None

def test_gps_windows():
    print("Testing BU-353N5 GPS connection on Windows...")
    
    # Find GPS port
    port = find_gps_port_windows()
    if not port:
        print("\nError: BU-353N5 GPS device not found!")
        print("\nTroubleshooting steps:")
        print("1. Check USB connection")
        print("2. Check Device Manager for COM port")
        print("3. Try unplugging and replugging the device")
        print("4. Make sure drivers are installed")
        
        # Offer manual port selection
        print("\nWould you like to try a specific COM port?")
        manual_port = input("Enter COM port (e.g., COM3) or press Enter to skip: ").strip()
        if manual_port:
            port = manual_port
            print(f"Trying manual port: {port}")
        else:
            return False
    
    try:
        print(f"\nFound GPS device at: {port}")
        
        # Try to connect and read data
        print("Attempting to read GPS data...")
        ser = serial.Serial(
            port=port,
            baudrate=4800,  # BU-353N5 typical baudrate
            timeout=1,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS
        )
        
        start_time = time.time()
        nmea_count = 0
        valid_fix = False
        
        while time.time() - start_time < 10:  # Try for 10 seconds
            try:
                line = ser.readline().decode('ascii', errors='replace').strip()
                
                if line.startswith('$'):
                    nmea_count += 1
                    print(f"Raw NMEA: {line}")
                    
                    if line.startswith('$GNGGA') or line.startswith('$GPGGA'):
                        msg = pynmea2.parse(line)
                        print(f"\nReceived GGA data:")
                        print(f"Timestamp: {msg.timestamp}")
                        print(f"Fix Quality: {msg.gps_qual}")
                        print(f"Satellites: {msg.num_sats}")
                        
                        if msg.gps_qual > 0:
                            valid_fix = True
                            print(f"Position: {msg.latitude}° {msg.lat_dir}, {msg.longitude}° {msg.lon_dir}")
                            print(f"Altitude: {msg.altitude} {msg.altitude_units}")
                            break
                        
            except pynmea2.ParseError as e:
                print(f"Parse error: {e}")
                continue
            except UnicodeDecodeError as e:
                print(f"Decode error: {e}")
                continue
                
        ser.close()
        
        print(f"\nNMEA sentences received: {nmea_count}")
        if nmea_count > 0:
            print("GPS is connected and sending data!")
            if valid_fix:
                print("GPS has a valid position fix!")
            else:
                print("Waiting for GPS fix - this is normal if device just started")
            return True
        else:
            print("No GPS data received - check device configuration")
            return False
            
    except serial.SerialException as e:
        print(f"\nError accessing GPS: {str(e)}")
        print("Troubleshooting:")
        print("1. Check if device is properly powered")
        print("2. Try unplugging and replugging the device")
        print("3. Check Device Manager for COM port conflicts")
        print("4. Try running as administrator")
        return False
        
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    test_gps_windows() 