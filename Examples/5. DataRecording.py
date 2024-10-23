
from flightmatrix.bridge import FlightMatrixBridge
from flightmatrix.utilities import DataRecorder
import time

# Example usage (Record data each second for 120 seconds)
if __name__ == "__main__":
    bridge = FlightMatrixBridge()
    recorder = DataRecorder(bridge, base_dir="Sample_Recordings", 
                            record_left_frame=True, 
                            record_right_frame=True, 
                            record_left_zdepth=True, 
                            record_right_zdepth=True, 
                            record_left_seg=True, 
                            record_right_seg=True, 
                            record_sensor_data=True,
                            record_sensor_data_interval=1)
    
    recorder.start_recording()

    time.sleep(120)  # Record for 120 seconds

    recorder.stop_recording()