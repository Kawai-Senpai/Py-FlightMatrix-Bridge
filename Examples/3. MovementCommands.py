from flightmatrix.bridge import FlightMatrixBridge
import time

# Initialize the bridge
bridge = FlightMatrixBridge()

# Send a movement command (x, y, z, roll, pitch, yaw)
bridge.send_movement_command(0.5, 1.0, 0.8, 0.0, 0.1, 0.2)

# Wait for 2 seconds
time.sleep(2)

# Send another movement command (reset)
bridge.send_movement_command(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)