# server_example.py

from flightmatrix.bridge import FlightMatrixBridge
from flightmatrix.server import FlightMatrixServer
import time

# Initialize the bridge with desired resolution
bridge = FlightMatrixBridge()

# Start the server
server = FlightMatrixServer(
    host='0.0.0.0',
    port=9999,
    bridge=bridge,
    broadcast_interval=0.00  # Adjusted interval for higher FPS
)
server.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    server.stop()