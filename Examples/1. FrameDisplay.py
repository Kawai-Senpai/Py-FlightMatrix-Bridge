import cv2
from flightmatrix.bridge import FlightMatrixBridge
from flightmatrix.utilities import timestamp2string
import ultraprint.common as p

# Initialize the FlightMatrixBridge
bridge = FlightMatrixBridge()

# Start a loop to continuously fetch and display frames
while True:
    # Fetch the left and right frames
    left_frame_data = bridge.get_left_frame()
    right_frame_data = bridge.get_right_frame()

    # Fetch the z-depth frames for both left and right
    left_zdepth_data = bridge.get_left_zdepth()
    right_zdepth_data = bridge.get_right_zdepth()

    # Retrieve the actual frame arrays and timestamps
    left_frame = left_frame_data['frame']
    right_frame = right_frame_data['frame']

    left_zdepth = left_zdepth_data['frame']
    right_zdepth = right_zdepth_data['frame']
    
    left_timestamp = left_frame_data['timestamp']
    right_timestamp = right_frame_data['timestamp']

    # Convert timestamps to human-readable format
    left_timestamp = timestamp2string(left_timestamp)
    right_timestamp = timestamp2string(right_timestamp)

    # Display the frames in OpenCV windows
    cv2.imshow("Left Frame", left_frame)
    cv2.imshow("Right Frame", right_frame)

    cv2.imshow("Left Z-Depth", left_zdepth)
    cv2.imshow("Right Z-Depth", right_zdepth)

    # Print timestamps for each frame (optional)
    p.purple(f"Left Frame Timestamp: {left_timestamp}")
    p.purple(f"Right Frame Timestamp: {right_timestamp}")

    # Print timestamps for z-depth frames (optional)
    p.lgray(f"Left Z-Depth Timestamp: {left_timestamp}")
    p.lgray(f"Right Z-Depth Timestamp: {right_timestamp}")

    # Break the loop when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release OpenCV windows
cv2.destroyAllWindows()