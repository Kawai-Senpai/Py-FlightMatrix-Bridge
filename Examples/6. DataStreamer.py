import cv2
from flightmatrix.bridge import FlightMatrixBridge
from flightmatrix.utilities import DataStreamer

def left_frame_callback(left_frame_data):
    left_frame = left_frame_data['frame']
    left_timestamp = left_frame_data['timestamp']
    cv2.imshow("Left Frame", left_frame)
    print("Left Frame Timestamp:", left_timestamp)

def right_frame_callback(right_frame_data):
    right_frame = right_frame_data['frame']
    right_timestamp = right_frame_data['timestamp']
    cv2.imshow("Right Frame", right_frame)
    print("Right Frame Timestamp:", right_timestamp)

def left_zdepth_callback(left_zdepth_data):
    left_zdepth = left_zdepth_data['frame']
    left_timestamp = left_zdepth_data['timestamp']
    cv2.imshow("Left Z-Depth", left_zdepth)
    print("Left Z-Depth Timestamp:", left_timestamp)

def right_zdepth_callback(right_zdepth_data):
    right_zdepth = right_zdepth_data['frame']
    right_timestamp = right_zdepth_data['timestamp']
    cv2.imshow("Right Z-Depth", right_zdepth)
    print("Right Z-Depth Timestamp:", right_timestamp)

def left_seg_callback(left_seg_data):
    left_seg = left_seg_data['frame']
    left_timestamp = left_seg_data['timestamp']
    cv2.imshow("Left Segmentation", left_seg)
    print("Left Segmentation Timestamp:", left_timestamp)

def right_seg_callback(right_seg_data):
    right_seg = right_seg_data['frame']
    right_timestamp = right_seg_data['timestamp']
    cv2.imshow("Right Segmentation", right_seg)
    print("Right Segmentation Timestamp:", right_timestamp)

def sensor_data_callback(sensor_data):
    print("Sensor Data:", sensor_data)

# Initialize the FlightMatrixBridge
bridge = FlightMatrixBridge()

# Initialize the DataStreamer
streamer = DataStreamer(bridge)

# Subscribe to the left frame data stream
streamer.subscribe("left_frame", left_frame_callback, interval=0.1)

# Subscribe to the right frame data stream
streamer.subscribe("right_frame", right_frame_callback, interval=0.1)

# Subscribe to the left z-depth data stream
streamer.subscribe("left_zdepth", left_zdepth_callback, interval=0.1)

# Subscribe to the right z-depth data stream
streamer.subscribe("right_zdepth", right_zdepth_callback, interval=0.1)

# Subscribe to the left segmentation data stream
streamer.subscribe("left_seg", left_seg_callback, interval=0.1)

# Subscribe to the right segmentation data stream
streamer.subscribe("right_seg", right_seg_callback, interval=0.1)

# Subscribe to the sensor data stream
streamer.subscribe("sensor_data", sensor_data_callback, interval=0.1)