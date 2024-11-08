import time
import os
import cv2
import csv
import threading
import math
import numpy as np
from datetime import datetime, timezone
from flightmatrix.bridge import FlightMatrixBridge

#* Function to convert timestamp(int) to string(Human readable format)
def timestamp2string(timestamp):
    """
    Convert a timestamp in milliseconds to a formatted string.
    Args:
        timestamp (int): The timestamp in milliseconds.
    Returns:
        str: The formatted timestamp as a string in the format 'YYYY-MM-DD HH:MM:SS:fff'.
    """
    # Convert milliseconds to seconds for datetime
    timestamp_seconds = timestamp / 1000.0

    # Create a datetime object from the timestamp
    dt = datetime.fromtimestamp(timestamp_seconds, tz=timezone.utc)

    # Format the datetime object as a string
    formatted_timestamp = dt.strftime('%Y-%m-%d %H:%M:%S:%f')[:-3]  # Keep only milliseconds
    
    return formatted_timestamp

#* Function to convert timestamp(int) to datetime object
def timestamp2datetime(timestamp):
    """
    Convert a timestamp in milliseconds to a datetime object in UTC.
    Args:
        timestamp (int): The timestamp in milliseconds.
    Returns:
        datetime: A datetime object representing the given timestamp in UTC.
    """
    # Convert milliseconds to seconds for datetime
    timestamp_seconds = timestamp / 1000.0

    # Create a datetime object from the timestamp
    dt = datetime.fromtimestamp(timestamp_seconds, tz=timezone.utc)
    
    return dt

#* Function to convert Cartesian coordinates to GPS coordinates
def cartesian_to_gps(x, y, z, origin_lat=22.583047, origin_lon=88.45859783333334, origin_alt=0, add_noise=False, lat_long_noise_amt=0.0001, alt_noise_amt=0.1, earth_radius=6378137):
    
    """
    Converts Cartesian coordinates to GPS coordinates (latitude, longitude, altitude).
    Args:
        x (float): X coordinate in centimeters.
        y (float): Y coordinate in centimeters.
        z (float): Z coordinate in centimeters.
        origin_lat (float, optional): Latitude of the origin point in degrees. Defaults to 22.583047.
        origin_lon (float, optional): Longitude of the origin point in degrees. Defaults to 88.45859783333334.
        origin_alt (float, optional): Altitude of the origin point in meters. Defaults to 0.
        add_noise (bool, optional): Whether to add noise to the GPS coordinates. Defaults to False.
        lat_long_noise_amt (float, optional): Amount of noise to add to latitude and longitude. Defaults to 0.0001.
        alt_noise_amt (float, optional): Amount of noise to add to altitude. Defaults to 0.1.
        earth_radius (float, optional): Radius of the Earth in meters. Defaults to 6378137 (meters).
    Returns:
        tuple: A tuple containing the latitude, longitude, and altitude in meters.
    """

    # Convert cm to meters
    x = x / 100
    y = y / 100
    z = z / 100
    
    # Assuming a simple flat Earth model for small distances
    R = earth_radius  # Radius of Earth in meters
    d_lat = y / R
    d_lon = x / (R * math.cos(math.pi * origin_lat / 180))
    
    lat = origin_lat + d_lat * 180 / math.pi
    lon = origin_lon + d_lon * 180 / math.pi
    alt = origin_alt + z  # Altitude in meters

    if add_noise:
        # Add noise to the GPS coordinates
        lat += np.random.normal(0, lat_long_noise_amt)
        lon += np.random.normal(0, lat_long_noise_amt)
        alt += np.random.normal(0, alt_noise_amt)
    
    return lat, lon, alt

#* Class to control the drone movements and rotations
class DroneController:

    """
    DroneController class to manage drone movements and rotations.
    Attributes:
        bridge (FlightMatrixBridge): The bridge object to communicate with the drone.
        current_x (float): Current position on the x-axis.
        current_y (float): Current position on the y-axis.
        current_z (float): Current position on the z-axis.
        current_roll (float): Current roll angle.
        current_pitch (float): Current pitch angle.
        current_yaw (float): Current yaw angle.
    Methods:
        _send_command(): Send the current state as a movement command to the drone.
        move_x(value): Move the drone in the x-axis (forward/backward).
        move_y(value): Move the drone in the y-axis (left/right).
        move_z(value): Move the drone in the z-axis (up/down).
        rotate_roll(value): Rotate the drone in roll.
        rotate_pitch(value): Rotate the drone in pitch.
        rotate_yaw(value): Rotate the drone in yaw.
        ascend(value): Increase the drone's altitude.
        descend(value): Decrease the drone's altitude.
        move_forward(value): Move the drone forward (positive y-axis).
        move_backward(value): Move the drone backward (negative y-axis).
        stop_movement(): Stop all movement (x, y, z).
        stop_rotation(): Stop all rotation (roll, pitch, yaw).
        stop(): Stop all movement and rotation.
        hover(): Keep the current position (x, y, z) but stop rotation.
        reset_axis(axis): Reset a specific axis (x, y, z, roll, pitch, yaw) to zero.
        hover_and_rotate(yaw_speed, duration): Keep the drone in place while continuously rotating (hover and spin).
    """

    def __init__(self, bridge_object: FlightMatrixBridge):
        """
        Initializes the FlightMatrix object with a bridge object and sets initial movement parameters to zero.
        Args:
            bridge_object (FlightMatrixBridge): An instance of the FlightMatrixBridge class used to interface with the flight matrix system.
        Attributes:
            bridge (FlightMatrixBridge): The bridge object for interfacing with the flight matrix system.
            current_x (float): The current x-coordinate position, initialized to 0.0.
            current_y (float): The current y-coordinate position, initialized to 0.0.
            current_z (float): The current z-coordinate position, initialized to 0.0.
            current_roll (float): The current roll angle, initialized to 0.0.
            current_pitch (float): The current pitch angle, initialized to 0.0.
            current_yaw (float): The current yaw angle, initialized to 0.0.
        """
        self.bridge = bridge_object
        self.log = bridge_object.log  # Extract logger from bridge_object
        
        # Initialize movement parameters to zero
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_z = 0.0
        self.current_roll = 0.0
        self.current_pitch = 0.0
        self.current_yaw = 0.0

    def _send_command(self):
        """
        Send the current state as a movement command to the drone.

        This method sends the current positional and orientation state 
        (x, y, z coordinates and roll, pitch, yaw angles) to the drone 
        using the bridge's send_movement_command method.

        Returns:
            None
        """
        """Send the current state as a movement command to the drone."""
        self.bridge.send_movement_command(
            self.current_x, self.current_y, self.current_z, 
            self.current_roll, self.current_pitch, self.current_yaw
        )

    # Function to move in the x-axis (forward/backward)
    def move_x(self, value):
        """
        Moves the object to a new x-coordinate.

        Parameters:
        value (int or float): The new x-coordinate to move to.

        Returns:
        None
        """
        self.current_x = value
        self._send_command()

    # Function to move in the y-axis (left/right)
    def move_y(self, value):
        """
        Updates the current y-coordinate and sends the corresponding command.

        Parameters:
        value (int or float): The new y-coordinate value to set.
        """
        self.current_y = value
        self._send_command()

    # Function to move in the z-axis (up/down)
    def move_z(self, value):
        """
        Moves the object to a specified Z-coordinate.

        Parameters:
        value (float): The target Z-coordinate to move to.

        Returns:
        None
        """
        self.current_z = value
        self._send_command()

    # Function to rotate in roll
    def rotate_roll(self, value):
        """
        Sets the current roll to the specified value and sends the corresponding command.

        Args:
            value (float): The new roll value to set.
        """
        self.current_roll = value
        self._send_command()

    # Function to rotate in pitch
    def rotate_pitch(self, value):
        """
        Sets the current pitch to the specified value and sends the corresponding command.

        Args:
            value (float): The new pitch value to set.
        """
        self.current_pitch = value
        self._send_command()

    # Function to rotate in yaw
    def rotate_yaw(self, value):
        """
        Rotates the object to a specified yaw angle.

        Parameters:
        value (float): The yaw angle to rotate to, in degrees.

        Returns:
        None
        """
        self.current_yaw = value
        self._send_command()

    # Function to ascend (increase altitude)
    def ascend(self, value):
        """
        Ascends the object by a specified value.

        Parameters:
        value (float): The amount to increase the current altitude.

        Returns:
        None
        """
        self.current_z += value
        self._send_command()

    # Function to descend (decrease altitude)
    def descend(self, value):
        """
        Decreases the current altitude by the specified value and sends the command.

        Args:
            value (float): The amount to decrease the current altitude by.
        """
        self.current_z -= value
        self._send_command()

    # Function to move forward (positive y-axis)
    def move_forward(self, value):
        """
        Moves the current position forward by a specified value.

        Parameters:
        value (int or float): The amount to move forward. This value is added to the current y-coordinate.

        Returns:
        None
        """
        self.current_y += value
        self._send_command()

    # Function to move backward (negative y-axis)
    def move_backward(self, value):
        """
        Moves the current position backward by a specified value.

        Parameters:
        value (int or float): The amount to move backward. This value will be subtracted from the current y-coordinate.
        """
        self.current_y -= value
        self._send_command()

    # Stop only movement (x, y, z)
    def stop_movement(self):
        """
        Stops the movement by setting the current x, y, and z coordinates to 0.0 
        and sends a command to update the state.

        This method is typically used to halt any ongoing movement and reset the 
        position to the origin.
        """
        self.current_x = self.current_y = self.current_z = 0.0
        self._send_command()

    # Stop only rotation (roll, pitch, yaw)
    def stop_rotation(self):
        """
        Stops the rotation of the object by resetting the current roll, pitch, and yaw to zero.

        This method sets the `current_roll`, `current_pitch`, and `current_yaw` attributes to 0.0
        and sends a command to apply these changes.

        Returns:
            None
        """
        self.current_roll = self.current_pitch = self.current_yaw = 0.0
        self._send_command()

    # Stop all movement and rotation
    def stop(self):
        """
        Stops the current movement by resetting all positional and rotational coordinates to zero.

        This method sets the current x, y, z coordinates and roll, pitch, yaw angles to 0.0,
        effectively stopping any ongoing movement. It then sends a command to apply these changes.
        """
        self.current_x = self.current_y = self.current_z = 0.0
        self.current_roll = self.current_pitch = self.current_yaw = 0.0
        self._send_command()

    # Utility function to hover (keep current x, y, z but stop rotation)
    def hover(self):
        """
        Sets the current roll, pitch, and yaw to zero, effectively putting the flight matrix into a hover state.
        
        This method resets the orientation of the flight matrix to a neutral position and sends the corresponding command to the flight control system.
        
        Returns:
            None
        """
        self.current_roll = self.current_pitch = self.current_yaw = 0.0
        self._send_command()

    # Function to reset specific axis (x, y, z, roll, pitch, yaw)
    def reset_axis(self, axis):
        """
        Resets the specified axis to its default value (0.0).

        Parameters:
        axis (str): The axis to reset. Valid values are 'x', 'y', 'z', 'roll', 'pitch', and 'yaw'.

        Returns:
        None
        """
        if axis == 'x':
            self.current_x = 0.0
        elif axis == 'y':
            self.current_y = 0.0
        elif axis == 'z':
            self.current_z = 0.0
        elif axis == 'roll':
            self.current_roll = 0.0
        elif axis == 'pitch':
            self.current_pitch = 0.0
        elif axis == 'yaw':
            self.current_yaw = 0.0
        self._send_command()

    def hover_and_rotate(self, yaw_speed, duration):
        """
        Keep the drone in place while continuously rotating (hover and spin).
        Args:
            yaw_speed (float): The speed at which the drone should rotate around its yaw axis.
            duration (float): The duration in seconds for which the drone should keep rotating.
        Returns:
            None
        """
        """Keep the drone in place while continuously rotating (hover and spin)."""
        start_time = time.time()

        while time.time() - start_time < duration:

            # Set yaw to rotate continuously
            self.current_yaw = yaw_speed
            self._send_command()

            time.sleep(0.1)  # Adjust for smoother rotation

        # Stop rotation after the specified duration
        self.current_yaw = 0.0
        self._send_command()

#* Class to record data from the drone
class DataRecorder:
    def __init__(self, bridge: FlightMatrixBridge,
                base_dir, record_left_frame=False, record_right_frame=False, 
                record_left_zdepth=False, record_right_zdepth=False, record_left_seg=False, 
                record_right_seg=False, record_sensor_data=False, record_sensor_data_interval=0.1):
        """
                Initializes the recording utility with the specified parameters and sets up the necessary directories.
                Args:
                    bridge: The bridge object to interface with the recording system.
                    base_dir (str): The base directory where recordings will be stored.
                    record_left_frame (bool, optional): Whether to record the left frame. Defaults to False.
                    record_right_frame (bool, optional): Whether to record the right frame. Defaults to False.
                    record_left_zdepth (bool, optional): Whether to record the left z-depth. Defaults to False.
                    record_right_zdepth (bool, optional): Whether to record the right z-depth. Defaults to False.
                    record_left_seg (bool, optional): Whether to record the left segmentation. Defaults to False.
                    record_right_seg (bool, optional): Whether to record the right segmentation. Defaults to False.
                    record_sensor_data (bool, optional): Whether to record sensor data. Defaults to False.
                    record_sensor_data_interval (float, optional): The interval at which to record sensor data. Defaults to 0.1.
                    is_recording (bool): Flag to indicate if the recording is currently active.
                Attributes:
                    bridge: The bridge object to interface with the recording system.
                    base_dir (str): The base directory where recordings will be stored.
                    record_left_frame (bool): Whether to record the left frame.
                    record_right_frame (bool): Whether to record the right frame.
                    record_left_zdepth (bool): Whether to record the left z-depth.
                    record_right_zdepth (bool): Whether to record the right z-depth.
                    record_left_seg (bool): Whether to record the left segmentation.
                    record_right_seg (bool): Whether to record the right segmentation.
                    record_sensor_data (bool): Whether to record sensor data.
                    sensor_data_interval (float): The interval at which to record sensor data.
                    threads (list): A list to keep track of threads.
                    stop_event (threading.Event): An event to signal stopping of threads.
                    left_frame_dir (str): Directory for left frame recordings.
                    right_frame_dir (str): Directory for right frame recordings.
                    left_zdepth_dir (str): Directory for left z-depth recordings.
                    right_zdepth_dir (str): Directory for right z-depth recordings.
                    left_seg_dir (str): Directory for left segmentation recordings.
                    right_seg_dir (str): Directory for right segmentation recordings.
                    sensor_data_file (str): File path for storing sensor data.
                    sensor_data (list): A list to accumulate sensor data.
                """

        self.bridge = bridge
        self.base_dir = base_dir
        self.record_left_frame = record_left_frame
        self.record_right_frame = record_right_frame
        self.record_left_zdepth = record_left_zdepth
        self.record_right_zdepth = record_right_zdepth
        self.record_left_seg = record_left_seg
        self.record_right_seg = record_right_seg
        self.record_sensor_data = record_sensor_data

        self.sensor_data_interval = record_sensor_data_interval
        self.is_recording = False

        self.threads = []
        self.stop_event = threading.Event()
        self.log = bridge.log  # Extract logger from bridge

        # Dynamically create folders based on the user's choices
        if self.record_left_frame:
            self.left_frame_dir = os.path.join(self.base_dir, "left_frame")
            os.makedirs(self.left_frame_dir, exist_ok=True)
            self.bridge.log.info(f"Left frame will be recorded in {self.left_frame_dir}")

        if self.record_right_frame:
            self.right_frame_dir = os.path.join(self.base_dir, "right_frame")
            os.makedirs(self.right_frame_dir, exist_ok=True)
            self.bridge.log.info(f"Right frame will be recorded in {self.right_frame_dir}")

        if self.record_left_zdepth:
            self.left_zdepth_dir = os.path.join(self.base_dir, "left_zdepth")
            os.makedirs(self.left_zdepth_dir, exist_ok=True)
            self.bridge.log.info(f"Left z-depth will be recorded in {self.left_zdepth_dir}")

        if self.record_right_zdepth:
            self.right_zdepth_dir = os.path.join(self.base_dir, "right_zdepth")
            os.makedirs(self.right_zdepth_dir, exist_ok=True)
            self.bridge.log.info(f"Right z-depth will be recorded in {self.right_zdepth_dir}")

        if self.record_left_seg:
            self.left_seg_dir = os.path.join(self.base_dir, "left_seg")
            os.makedirs(self.left_seg_dir, exist_ok=True)
            self.bridge.log.info(f"Left segmentation will be recorded in {self.left_seg_dir}")

        if self.record_right_seg:
            self.right_seg_dir = os.path.join(self.base_dir, "right_seg")
            os.makedirs(self.right_seg_dir, exist_ok=True)
            self.bridge.log.info(f"Right segmentation will be recorded in {self.right_seg_dir}")

        if self.record_sensor_data:
            self.sensor_data_file = os.path.join(self.base_dir, "sensor_data.csv")
            self.sensor_data = []  # We'll accumulate sensor data to store it in a JSON file.
            self.bridge.log.info(f"Sensor data will be recorded in {self.sensor_data_file}")

    def record_frames(self):
        """
        Continuously records frames from various sensors and saves them as image files.
        This method runs in a loop until the `stop_event` is set. It records frames from
        left and right cameras, z-depth sensors, and segmentation sensors. The frames are
        saved as JPEG files with timestamps in their filenames. The colons in the timestamps
        are replaced with hyphens to avoid issues with filenames.
        The following frames are recorded if their respective flags are set:
        - Left frame
        - Right frame
        - Left z-depth
        - Right z-depth
        - Left segmentation frame
        - Right segmentation frame
        The method sleeps for `sensor_data_interval` seconds between each iteration to prevent
        overloading the system by fetching frames too frequently.
        Attributes:
            stop_event (threading.Event): Event to signal stopping the recording loop.
            record_left_frame (bool): Flag to record left camera frames.
            record_right_frame (bool): Flag to record right camera frames.
            record_left_zdepth (bool): Flag to record left z-depth frames.
            record_right_zdepth (bool): Flag to record right z-depth frames.
            record_left_seg (bool): Flag to record left segmentation frames.
            record_right_seg (bool): Flag to record right segmentation frames.
            bridge (object): Object to interface with the sensors and get frame data.
            left_frame_dir (str): Directory to save left camera frames.
            right_frame_dir (str): Directory to save right camera frames.
            left_zdepth_dir (str): Directory to save left z-depth frames.
            right_zdepth_dir (str): Directory to save right z-depth frames.
            left_seg_dir (str): Directory to save left segmentation frames.
            right_seg_dir (str): Directory to save right segmentation frames.
            sensor_data_interval (float): Interval in seconds between fetching frames.
        """

        # Continuously record frames
        while not self.stop_event.is_set():
            # Record left frame
            if self.record_left_frame:
                left_frame_data = self.bridge.get_left_frame()
                left_frame = left_frame_data['frame']
                left_timestamp = timestamp2string(left_frame_data['timestamp'])
                left_timestamp = left_timestamp.replace(':', '-')  # Replace ':' with '-' to avoid issues with filenames
                filename = f"left_{left_timestamp}.jpeg"
                filepath = os.path.join(self.left_frame_dir, filename)
                cv2.imwrite(filepath, left_frame)
            
            # Record right frame
            if self.record_right_frame:
                right_frame_data = self.bridge.get_right_frame()
                right_frame = right_frame_data['frame']
                right_timestamp = timestamp2string(right_frame_data['timestamp'])
                right_timestamp = right_timestamp.replace(':', '-')  # Replace ':' with '-' to avoid issues with filenames
                filename = f"right_{right_timestamp}.jpeg"
                filepath = os.path.join(self.right_frame_dir, filename)
                cv2.imwrite(filepath, right_frame)

            # Record left z-depth
            if self.record_left_zdepth:
                left_zdepth_data = self.bridge.get_left_zdepth()
                left_zdepth = left_zdepth_data['frame']
                left_zdepth_timestamp = timestamp2string(left_zdepth_data['timestamp'])
                left_zdepth_timestamp = left_zdepth_timestamp.replace(':', '-')  # Replace ':' with '-' to avoid issues with filenames
                filename = f"left_zdepth_{left_zdepth_timestamp}.jpeg"
                filepath = os.path.join(self.left_zdepth_dir, filename)
                cv2.imwrite(filepath, left_zdepth)

            # Record right z-depth
            if self.record_right_zdepth:
                right_zdepth_data = self.bridge.get_right_zdepth()
                right_zdepth = right_zdepth_data['frame']
                right_zdepth_timestamp = timestamp2string(right_zdepth_data['timestamp'])
                right_zdepth_timestamp = right_zdepth_timestamp.replace(':', '-')  # Replace ':' with '-' to avoid issues with filenames
                filename = f"right_zdepth_{right_zdepth_timestamp}.jpeg"
                filepath = os.path.join(self.right_zdepth_dir, filename)
                cv2.imwrite(filepath, right_zdepth)

            # Record left segmentation frame
            if self.record_left_seg:
                left_seg_data = self.bridge.get_left_seg()
                left_seg = left_seg_data['frame']
                left_seg_timestamp = timestamp2string(left_seg_data['timestamp'])
                left_seg_timestamp = left_seg_timestamp.replace(':', '-')  # Replace ':' with '-' to avoid issues with filenames
                filename = f"left_seg_{left_seg_timestamp}.jpeg"
                filepath = os.path.join(self.left_seg_dir, filename)
                cv2.imwrite(filepath, left_seg)

            # Record right segmentation frame
            if self.record_right_seg:
                right_seg_data = self.bridge.get_right_seg()
                right_seg = right_seg_data['frame']
                right_seg_timestamp = timestamp2string(right_seg_data['timestamp'])
                right_seg_timestamp = right_seg_timestamp.replace(':', '-')  # Replace ':' with '-' to avoid issues with filenames
                filename = f"right_seg_{right_seg_timestamp}.jpeg"
                filepath = os.path.join(self.right_seg_dir, filename)
                cv2.imwrite(filepath, right_seg)

            time.sleep(self.sensor_data_interval)  # Prevent overloading the system by fetching frames too frequently

    def record_sensors(self):
        """
        Records sensor data to a CSV file at regular intervals.
        This method opens a CSV file in append mode and writes sensor data
        retrieved from the `self.bridge.get_sensor_data()` method. The data
        includes timestamp, location, orientation, gyroscope, accelerometer,
        magnetometer, lidar, and collision information. The method continues
        to record data until `self.stop_event` is set.
        The CSV file header is written only if the file is empty. Each row of
        data is written immediately and the buffer is flushed to ensure data
        is saved.
        Attributes:
            self.sensor_data_file (str): Path to the CSV file where sensor data is recorded.
            self.stop_event (threading.Event): Event to signal the stopping of data recording.
            self.record_sensor_data (bool): Flag to control whether sensor data should be recorded.
            self.bridge (object): Object that provides the `get_sensor_data` method to fetch sensor data.
            self.sensor_data_interval (float): Time interval (in seconds) between consecutive sensor data recordings.
        Sensor Data Structure:
            - timestamp (float): The timestamp of the sensor data.
            - location (list of float): The x, y, z coordinates of the location.
            - orientation (list of float): The roll, pitch, yaw orientation values.
            - gyroscope (list of float): The x, y, z values from the gyroscope.
            - accelerometer (list of float): The x, y, z values from the accelerometer.
            - magnetometer (list of float): The x, y, z values from the magnetometer.
            - lidar (list of float): The forward, backward, left, right, bottom lidar readings.
            - collision (list of float): The status and x, y, z coordinates of the collision location.
        Raises:
            KeyError: If any expected key is missing from the sensor data.
        """
        
        # Open the CSV file in append mode
        with open(self.sensor_data_file, 'a', newline='') as csvfile:
            fieldnames = ['timestamp', 'location_x', 'location_y', 'location_z', 
                        'orientation_roll', 'orientation_pitch', 'orientation_yaw', 
                        'gyroscope_x', 'gyroscope_y', 'gyroscope_z', 
                        'accelerometer_x', 'accelerometer_y', 'accelerometer_z', 
                        'magnetometer_x', 'magnetometer_y', 'magnetometer_z', 
                        'lidar_forward', 'lidar_backward', 'lidar_left', 
                        'lidar_right', 'lidar_bottom', 
                        'collision_status', 'collision_location_x', 
                        'collision_location_y', 'collision_location_z']
            
            # Create a CSV writer
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Write the header only if the file is empty
            if csvfile.tell() == 0:
                writer.writeheader()

            while not self.stop_event.is_set():
                if self.record_sensor_data:
                    sensor_data = self.bridge.get_sensor_data()

                    # Check for errors
                    if sensor_data.get('error'):
                        self.log.error(f"Error fetching sensor data: {sensor_data['error']}")
                        continue
                    
                    # Extract sensor readings
                    location = sensor_data['location']
                    orientation = sensor_data['orientation']
                    gyroscope = sensor_data['gyroscope']
                    accelerometer = sensor_data['accelerometer']
                    magnetometer = sensor_data['magnetometer']
                    lidar = sensor_data['lidar']
                    collision = sensor_data['collision']
                    timestamp = sensor_data['timestamp']

                    # Prepare data to be written to the CSV file
                    data_row = {
                        'timestamp': timestamp,
                        'location_x': location[0],
                        'location_y': location[1],
                        'location_z': location[2],
                        'orientation_roll': orientation[0],
                        'orientation_pitch': orientation[1],
                        'orientation_yaw': orientation[2],
                        'gyroscope_x': gyroscope[0],
                        'gyroscope_y': gyroscope[1],
                        'gyroscope_z': gyroscope[2],
                        'accelerometer_x': accelerometer[0],
                        'accelerometer_y': accelerometer[1],
                        'accelerometer_z': accelerometer[2],
                        'magnetometer_x': magnetometer[0],
                        'magnetometer_y': magnetometer[1],
                        'magnetometer_z': magnetometer[2],
                        'lidar_forward': lidar[0],
                        'lidar_backward': lidar[1],
                        'lidar_left': lidar[2],
                        'lidar_right': lidar[3],
                        'lidar_bottom': lidar[4],
                        'collision_status': collision[0],
                        'collision_location_x': collision[1],
                        'collision_location_y': collision[2],
                        'collision_location_z': collision[3],
                    }

                    # Write the data row to the CSV file
                    writer.writerow(data_row)
                    csvfile.flush()  # Flush the buffer to write the data to the file

                time.sleep(self.sensor_data_interval)  # Prevent overloading the system by fetching sensor data too frequently

    def start_recording(self):
        """
        Starts the recording process by initializing and starting the necessary threads.
        This method performs the following actions:
        1. Clears the stop event to ensure recording can proceed.
        2. Initializes an empty list to hold the threads.
        3. Creates and starts a thread for recording frames.
        4. If sensor data recording is enabled, creates and starts a thread for recording sensor data.
        5. Starts all initialized threads.
        Note:
            - The `record_frames` method is expected to handle the frame recording process.
            - The `record_sensors` method is expected to handle the sensor data recording process.
            - The `record_sensor_data` attribute should be a boolean indicating whether sensor data recording is enabled.
        """

        if self.is_recording:
            self.log.warning("Recording is already in progress.")
            return

        self.stop_event.clear()
        self.threads = []

        # Start the frame recording thread
        frame_thread = threading.Thread(target=self.record_frames)
        self.threads.append(frame_thread)

        # Start the sensor data recording thread if enabled
        if self.record_sensor_data:
            sensor_thread = threading.Thread(target=self.record_sensors)
            self.threads.append(sensor_thread)

        # Start all threads
        for thread in self.threads:
            thread.start()

        self.is_recording = True
        self.bridge.log.success("Recording started.")

    def stop_recording(self):
        """
        Stops the recording process by setting the stop event and joining all threads.

        This method sets the `stop_event` to signal all running threads to stop their execution.
        It then waits for each thread in the `threads` list to complete by calling `join()` on them.
        """
        self.stop_event.set()
        for thread in self.threads:
            thread.join()
        
        self.is_recording = False
        self.bridge.log.success("Recording stopped.")

    def is_recording_on(self):
        """
        Checks if the recording process is currently active.
        Returns:
        bool: True if the recording process is active, False otherwise.
        """
        return self.is_recording

#* Class to stream data from the drone
class DataStreamer:
    """
    A class to stream data from the Flight Matrix system using callbacks.
    Allows users to subscribe to specific data streams and provides mechanisms
    to fetch data in parallel using threads.
    """

    def __init__(self, bridge):
        """
        Initialize the DataStreamer with a FlightMatrixBridge instance.
        Args:
            bridge (FlightMatrixBridge): An instance of FlightMatrixBridge to interact with the shared memory.
        """
        self.bridge = bridge
        self.subscriptions = {}
        self.threads = {}
        self.stop_events = {}
        self.log = bridge.log  # Extract logger from bridge

    def subscribe(self, data_type, callback, interval=0):
        """
        Subscribe to a specific data stream.
        Args:
            data_type (str): The type of data to subscribe to (e.g., 'left_frame', 'sensor_data').
            callback (function): The function to call when new data is available.
            interval (float): The interval in seconds at which to fetch data (set to 0 for as fast as possible).
        """
        if data_type in self.subscriptions:
            self.log.warning(f"Already subscribed to {data_type}")
            return

        stop_event = threading.Event()
        self.stop_events[data_type] = stop_event

        thread = threading.Thread(target=self._stream_data, args=(data_type, callback, interval, stop_event))
        thread.start()
        self.threads[data_type] = thread
        self.subscriptions[data_type] = {
            'callback': callback,
            'interval': interval
        }

    def unsubscribe(self, data_type):
        """
        Unsubscribe from a specific data stream.
        Args:
            data_type (str): The type of data to unsubscribe from.
        """
        if data_type in self.subscriptions:
            self.stop_events[data_type].set()
            self.threads[data_type].join()
            del self.subscriptions[data_type]
            del self.threads[data_type]
            del self.stop_events[data_type]
        else:
            self.log.warning(f"Not subscribed to {data_type}")

    def _stream_data(self, data_type, callback, interval, stop_event):
        """
        Internal method to fetch data and call the callback function.
        Args:
            data_type (str): The type of data to fetch.
            callback (function): The callback function to call with the data.
            interval (float): The interval in seconds at which to fetch data.
            stop_event (threading.Event): Event to signal when to stop streaming.
        """
        data_fetcher = self._get_data_fetcher(data_type)
        if not data_fetcher:
            self.log.error(f"Invalid data type: {data_type}. Available types: 'left_frame', 'right_frame', 'left_zdepth', 'right_zdepth', 'left_seg', 'right_seg', 'sensor_data'")
            return

        while not stop_event.is_set():
            data = data_fetcher()
            callback(data)
            if interval > 0:
                time.sleep(interval)

    def _get_data_fetcher(self, data_type):
        """
        Get the appropriate data fetching function from the bridge based on data type.
        Args:
            data_type (str): The type of data.
        Returns:
            function: The data fetching function.
        """
        fetcher_mapping = {
            'left_frame': self.bridge.get_left_frame,
            'right_frame': self.bridge.get_right_frame,
            'left_zdepth': self.bridge.get_left_zdepth,
            'right_zdepth': self.bridge.get_right_zdepth,
            'left_seg': self.bridge.get_left_seg,
            'right_seg': self.bridge.get_right_seg,
            'sensor_data': self.bridge.get_sensor_data,
        }
        return fetcher_mapping.get(data_type)

    def stop_all(self):
        """
        Stop all data streams and threads.
        """
        data_types = list(self.subscriptions.keys())
        for data_type in data_types:
            self.unsubscribe(data_type)


