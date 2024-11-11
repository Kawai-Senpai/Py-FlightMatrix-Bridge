from flightmatrix.server import FlightMatrixClient
import cv2
import time

def data_callback(data):
    # Handle received data
    if 'sensor_data' in data:
        sensor_data = data['sensor_data']
        print(f"Sensor Data: {sensor_data}")

    if 'left_frame' in data:
        left_frame_info = data['left_frame']
        frame = left_frame_info['frame']  # Frame is already decoded
        cv2.imshow('Left Frame', frame)
        cv2.waitKey(1)

    if 'right_frame' in data:
        right_frame_info = data['right_frame']
        frame = right_frame_info['frame']  # Frame is already decoded
        cv2.imshow('Right Frame', frame)
        cv2.waitKey(1)
    # Handle other data types similarly

# Specify the data types you want to subscribe to
subscription_list = ['sensor_data', 'left_frame', 'right_frame']

# Initialize the client
client = FlightMatrixClient(
    host='localhost',
    port=9999,
    subscription_list=subscription_list,
    data_callback=data_callback
)
client.connect()

# Example: Send a movement command once, if needed
time.sleep(5)
client.send_movement_command(x=0, y=0, z=0, roll=0, pitch=0, yaw=5)

time.sleep(5)
client.send_movement_command(x=0, y=0, z=0, roll=0, pitch=0, yaw=0)

# Keep the client running to receive data
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    client.disconnect()
    cv2.destroyAllWindows()