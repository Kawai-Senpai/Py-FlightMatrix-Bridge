from flightmatrix.bridge import FlightMatrixBridge

# Initialize the bridge
bridge = FlightMatrixBridge()

# Fetch sensor data
sensor_data = bridge.get_sensor_data()

# Check for errors
if sensor_data.get('error'):
    print("Error fetching sensor data:", sensor_data['error'])
else:
    # Extract sensor readings
    location = sensor_data['location']
    orientation = sensor_data['orientation']
    gyroscope = sensor_data['gyroscope']
    accelerometer = sensor_data['accelerometer']
    magnetometer = sensor_data['magnetometer']
    lidar = sensor_data['lidar']
    collision = sensor_data['collision']
    timestamp = sensor_data['timestamp']

    # Display sensor data in a readable format
    print("Sensor Data:")
    print("-----------------------")
    print(f"Timestamp: {timestamp} ms")
    print(f"Location (cm): X={location[0]:.2f}, Y={location[1]:.2f}, Z={location[2]:.2f}")
    print(f"Orientation (degrees): Roll={orientation[0]:.2f}, Pitch={orientation[1]:.2f}, Yaw={orientation[2]:.2f}")
    print(f"Gyroscope (deg/s): X={gyroscope[0]:.2f}, Y={gyroscope[1]:.2f}, Z={gyroscope[2]:.2f}")
    print(f"Accelerometer (cm/s²): X={accelerometer[0]:.2f}, Y={accelerometer[1]:.2f}, Z={accelerometer[2]:.2f}")
    print(f"Magnetometer (unit vector): X={magnetometer[0]:.2f}, Y={magnetometer[1]:.2f}, Z={magnetometer[2]:.2f}")
    print(f"LiDAR Data (cm): Forward={lidar[0]:.2f}, Backward={lidar[1]:.2f}, Left={lidar[2]:.2f}, Right={lidar[3]:.2f}, Bottom={lidar[4]:.2f}")
    print(f"Collision Detection: Status={collision[0]}, Location (cm): X={collision[1]:.2f}, Y={collision[2]:.2f}, Z={collision[3]:.2f}")