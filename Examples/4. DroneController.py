
from flightmatrix.bridge import FlightMatrixBridge
from flightmatrix.utilities import DroneController

# Example Usage
bridge = FlightMatrixBridge()
drone = DroneController(bridge)

# Move forward by 1.0 (positive y-axis)
drone.move_forward(1.0)

# Ascend by 0.5 (positive z-axis)
drone.ascend(0.5)

# Rotate in yaw by 0.3
drone.rotate_yaw(0.3)

# Stop only rotation (keep movement intact)
drone.stop_rotation()

# Stop all movement and rotation
drone.stop()

# Hover in place and rotate at 0.5 speed for 5 seconds
drone.hover_and_rotate(0.5, 5)
