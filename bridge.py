from multiprocessing import shared_memory
import numpy as np
from ultraprint.logging import logger
import struct

class FlightMatrixBridge:
    """
    A class to interface with the Flight Matrix system using shared memory for inter-process communication.
    Attributes:
        width (int): The width of the frame.
        height (int): The height of the frame.
        frame_shape (tuple): The shape of the frame (height, width).
        frame_shape_3ch (tuple): The shape of the frame with 3 channels (height, width, 3).
        noise_level (float): The level of noise to be applied.
        apply_noise (bool): Flag to determine if noise should be applied.
        memory_names (dict): Dictionary containing shared memory names.
        log (Logger): Logger object for logging messages.
        shm (dict): Dictionary to store shared memory blocks.
        shm_timestamps (dict): Dictionary to store shared memory blocks for timestamps.
        num_floats (int): Number of float values for movement commands.
    Methods:
        set_log_level(log_level='INFO'):
            Sets the log level for the logger.
        set_write_to_file(write_to_file):
            Sets whether to write logs to a file.
        _initialize_shared_memory():
            Initializes the shared memory blocks for frames and timestamps.
        _initialize_movement_command_memory():
            Initializes the shared memory block for movement commands.
        _get_frame(key, channels=3):
            Retrieves a frame from shared memory.
        _get_timestamp(key):
            Retrieves the timestamp from shared memory.
        get_right_frame():
            Retrieves the right frame from shared memory.
        get_left_frame():
            Retrieves the left frame from shared memory.
        get_right_zdepth():
            Retrieves the right depth frame from shared memory.
        get_left_zdepth():
            Retrieves the left depth frame from shared memory.
        get_right_seg():
            Retrieves the right segmentation frame from shared memory.
        get_left_seg():
            Retrieves the left segmentation frame from shared memory.
        add_noise(data):
            Adds noise to the given data.
        get_sensor_data():
            Retrieves sensor data from shared memory.
        send_movement_command(x, y, z, roll, pitch, yaw):
            Sends a movement command to shared memory.
        _write_movement_command(commands):
            Writes movement command data to shared memory.
        set_resolution(width, height):
            Sets the resolution for the frames.
        set_noise_level(noise_level):
            Sets the noise level.
        set_apply_noise(apply_noise):
            Sets whether to apply noise.
    """
    
    def __init__(self, resolution=(1226, 370), noise_level=0.01, apply_noise=False):
        """
        Initialize the FlightMatrix bridge.
        Args:
            resolution (tuple): A tuple specifying the width and height of the frame. Default is (1226, 370).
            noise_level (float): The level of noise to apply. Default is 0.01.
            apply_noise (bool): Flag to determine whether to apply noise. Default is False.
        Attributes:
            width (int): The width of the frame.
            height (int): The height of the frame.
            frame_shape (tuple): The shape of the frame as (height, width).
            frame_shape_3ch (tuple): The shape of the frame with 3 channels as (height, width, 3).
            noise_level (float): The level of noise to apply.
            apply_noise (bool): Flag to determine whether to apply noise.
            memory_names (dict): Dictionary containing shared memory names.
            log (logger): Logger object for FlightMatrix.
            shm (dict): Dictionary to store shared memory blocks.
            shm_timestamps (dict): Dictionary to store shared memory blocks for timestamps.
            num_floats (int): Number of floats for movement command handler. Do not change this value.
        Methods:
            _initialize_shared_memory: Initializes the shared memory blocks.
            _initialize_movement_command_memory: Initializes the movement command handler.
        """

        self.width, self.height = resolution
        self.frame_shape = (self.height, self.width)
        self.frame_shape_3ch = (self.height, self.width, 3)
        
        # Noise
        self.noise_level = noise_level
        self.apply_noise = apply_noise

        # Shared memory names
        self.memory_names = {
            'right_frame': 'RightFrame',
            'left_frame': 'LeftFrame',
            'right_zdepth': 'RightZFrame',
            'left_zdepth': 'LeftZFrame',
            'right_seg': 'RightSegFrame',
            'left_seg': 'LeftSegFrame',
            'sensor_data': 'SensorData',
            'movement_command': 'MovementCommandMemory'
        }

        # Create a logger object
        self.log = logger('FlightMatrixLog', include_extra_info=False, write_to_file=False, log_level='DEBUG')

        # Initialize the shared memory blocks
        self.shm = {} # To store shared memory blocks
        self.shm_timestamps = {}  # To store shared memory blocks for timestamps
        self._initialize_shared_memory()

        # Initialize the movement command handler
        self.num_floats = 6 #! Do not change this value
        self._initialize_movement_command_memory()

    #! Logging Functions -----------------------------------------------------

    def set_log_level(self, log_level='INFO'):
        """
        Sets the logging level for the application.

        Parameters:
        log_level (str): The desired logging level. Default is 'INFO'.

        Returns:
        None
        """
        self.log.set_log_level(log_level)
        self.log.success(f"Log level set to {log_level}")

    def set_write_to_file(self, write_to_file):
        """
        Sets the logging behavior to write to a file.

        Parameters:
        write_to_file (bool): If True, logging will be written to a file. If False, logging will not be written to a file.
        """
        self.log.set_write_to_file(write_to_file)
        self.log.success(f"Write to file set to {write_to_file}")

    #! Flight Matrix API -----------------------------------------------------

    def _initialize_shared_memory(self):
        """
        Initializes shared memory blocks for various keys except 'movement_command'.

        This method iterates over the `memory_names` dictionary and attempts to connect to 
        existing shared memory blocks for each key. If the shared memory block for a key 
        does not exist, it logs a warning and sets the corresponding shared memory attributes 
        to None.

        Attributes:
            self.memory_names (dict): A dictionary where keys are identifiers and values are 
                                    the names of the shared memory blocks.
            self.shm (dict): A dictionary to store the connected shared memory blocks.
            self.shm_timestamps (dict): A dictionary to store the connected timestamp shared 
                                        memory blocks.
            self.log (Logger): Logger instance for logging information and warnings.

        Raises:
            FileNotFoundError: If the shared memory block for a key does not exist.
        """

        for key, name in self.memory_names.items():
            if key == 'movement_command':
                continue  # Skip 'movement_command' since it's initialized separately
            try:
                # Initialize frame memory
                self.shm[key] = shared_memory.SharedMemory(name=name, create=False)
                # Initialize timestamp memory
                timestamp_name = f"{name}_time"
                self.shm_timestamps[key] = shared_memory.SharedMemory(name=timestamp_name, create=False)
                self.log.info(f"Connected to shared memory block for '{key}'")
            except FileNotFoundError:
                self.shm[key] = None
                self.shm_timestamps[key] = None  # Timestamp memory may also not exist
                self.log.warning(f"'{key}' is not being broadcasted or shared memory is not available")

    def _initialize_movement_command_memory(self):
        """
        Initializes the shared memory block for movement commands.
        This method sets up a shared memory block to store movement command values
        (x, y, z, r, p, y) and an availability flag. If the shared memory block already
        exists, it attaches to the existing block; otherwise, it creates a new one.
        The shared memory block structure:
        - 1 byte for the availability flag
        - 6 floats (each 4 bytes) for the movement command values
        Raises:
            FileExistsError: If the shared memory block already exists when attempting to create it.
        """
        # Define the size for the movement command shared memory
        num_floats = 6  # As expected, there are 6 movement command values (x, y, z, r, p, y)
        data_size = np.dtype(np.float32).itemsize * num_floats  # Each float is 4 bytes
        total_size = 1 + data_size  # 1 byte for availability flag + space for 6 floats

        try:
            # Try to create the shared memory block
            self.shm['movement_command'] = shared_memory.SharedMemory(name=self.memory_names['movement_command'], create=True, size=total_size)
            self.log.info(f"Created new shared memory block '{self.memory_names['movement_command']}'")
        except FileExistsError:
            # If it exists, attach to the existing shared memory block
            self.shm['movement_command'] = shared_memory.SharedMemory(name=self.memory_names['movement_command'], create=False)
            self.log.info(f"Attached to existing shared memory block '{self.memory_names['movement_command']}'")

    def _connect_shared_memory_for_key(self, key):
        """
        Attempts to connect to shared memory for a specific key.
        """
        name = self.memory_names.get(key)
        if not name:
            self.log.warning(f"No shared memory name for key '{key}'")
            return
        try:
            # Attempt to connect to shared memory
            self.shm[key] = shared_memory.SharedMemory(name=name, create=False)
            timestamp_name = f"{name}_time"
            self.shm_timestamps[key] = shared_memory.SharedMemory(name=timestamp_name, create=False)
            self.log.info(f"Connected to shared memory block for '{key}'")
        except FileNotFoundError:
            self.shm[key] = None
            self.shm_timestamps[key] = None
            self.log.warning(f"'{key}' shared memory not available")

    def _get_frame(self, key, channels=3):
        """
        Retrieve a frame from shared memory.
        Args:
            key (str): The key identifying the shared memory segment.
            channels (int, optional): The number of channels in the frame. Defaults to 3.
        Returns:
            dict: A dictionary containing:
                - 'frame' (np.ndarray or None): The retrieved frame, or None if an error occurred.
                - 'timestamp' (any or None): The timestamp associated with the frame, or None if an error occurred.
                - 'error' (str or None): An error message if an error occurred, otherwise None.
        Raises:
            Warning: Logs a warning if the shared memory is not available or if there is a resolution mismatch.
        """

        if self.shm.get(key) is None:
            self.log.warning(f"'{key}' shared memory not available, attempting to reconnect...")
            # Try to reconnect to shared memory
            self._connect_shared_memory_for_key(key)
            if self.shm.get(key) is None:
                # Warn if the shared memory is still not available
                self.log.warning(f"'{key}' is not being broadcasted or shared memory not available")
                return {'frame': None, 'timestamp': None, 'error': 'Shared memory not available'}

        expected_size = self.width * self.height * channels if channels == 3 else self.width * self.height
        if self.shm[key].size < expected_size:
            self.log.warning(f"'{key}' Resolution mismatch")
            return {'frame': None, 'timestamp': None, 'error': 'Resolution mismatch'}

        # Fetch the frame from shared memory
        buffer = self.shm[key].buf[:expected_size]
        frame = np.ndarray(self.frame_shape_3ch if channels == 3 else self.frame_shape, dtype=np.uint8, buffer=buffer)

        # Get the timestamp from shared memory
        timestamp = self._get_timestamp(key)

        return {'frame': frame, 'timestamp': timestamp}

    def _get_timestamp(self, key):
        """
        Retrieve a timestamp associated with a given key from shared memory.
        Args:
            key (str): The key for which to retrieve the timestamp.
        Returns:
            int or None: The timestamp as a long long integer if the key exists in shared memory,
                        otherwise None.
        """

        if self.shm_timestamps.get(key) is None:
            return None

        # Read the bytes corresponding to the long long (8 bytes)
        time_buf = self.shm_timestamps[key].buf[:8]  # 8 bytes for long long
        timestamp_bytes = time_buf.tobytes()

        # Unpack the bytes to get the long long value
        timestamp = struct.unpack('q', timestamp_bytes)[0]  # 'q' is the format for long long (8 bytes)

        return timestamp  # Return the timestamp as a long long integer

    def get_right_frame(self):
        return self._get_frame('right_frame')

    def get_left_frame(self):
        return self._get_frame('left_frame')

    def get_right_zdepth(self):
        return self._get_frame('right_zdepth', channels=1)

    def get_left_zdepth(self):
        return self._get_frame('left_zdepth', channels=1)

    def get_right_seg(self):
        return self._get_frame('right_seg')

    def get_left_seg(self):
        return self._get_frame('left_seg')

    def add_noise(self, data):
        noise = np.random.normal(0, self.noise_level, data.shape)
        return data + noise

    def get_sensor_data(self):
        """
        Retrieves sensor data from shared memory and returns it as a dictionary.
        If the sensor data is not available in shared memory, a warning is logged,
        and a dictionary with all sensor fields set to None and an error message is returned.
        The sensor data includes:
        - location: 3 floats representing the location coordinates.
        - orientation: 3 floats representing the orientation.
        - gyroscope: 3 floats representing the gyroscope readings.
        - accelerometer: 3 floats representing the accelerometer readings.
        - magnetometer: 3 floats representing the magnetometer readings.
        - lidar: 5 floats representing the lidar readings.
        - collision: 4 floats representing the collision data.
        - timestamp: The timestamp of the sensor data.
        If noise application is enabled, noise is added to the gyroscope, accelerometer,
        magnetometer, and lidar data.
        Returns:
            dict: A dictionary containing the sensor data or an error message if the data is not available.
        """

        if self.shm.get('sensor_data') is None:
            self.log.warning("Sensor data memory not available, attempting to reconnect...")
            # Try to reconnect to shared memory
            self._connect_shared_memory_for_key('sensor_data')
            if self.shm.get('sensor_data') is None:
                self.log.warning("Sensor data memory still not available")
                return dict(
                    location=None,
                    orientation=None,
                    gyroscope=None,
                    accelerometer=None,
                    magnetometer=None,
                    lidar=None,
                    collision=None,
                    timestamp=None,
                    error='Sensor data memory not available'
                )

        # Assuming 24 floats in the sensor data (as per your mapping)
        sensor_array = np.ndarray((24,), dtype=np.float32, buffer=self.shm['sensor_data'].buf[:96])
        # Get the timestamp from shared memory
        timestamp = self._get_timestamp('sensor_data')

        if self.apply_noise:
            sensor_array[6:20] = self.add_noise(sensor_array[6:20])

        return dict(
            location=sensor_array[:3].tolist(),
            orientation=sensor_array[3:6].tolist(),
            gyroscope=sensor_array[6:9].tolist(),
            accelerometer=sensor_array[9:12].tolist(),
            magnetometer=sensor_array[12:15].tolist(),
            lidar=sensor_array[15:20].tolist(),
            collision=sensor_array[20:24].tolist(),
            timestamp=timestamp
        )

    def send_movement_command(self, x, y, z, roll, pitch, yaw):
        """
        Sends a movement command to the shared memory.
        Parameters:
        x (float): The x-coordinate for thct command.
        roll (float): The roll angle for the movement command.
        pitch (float): The pitch angle for the movement command.
        yaw (float): The yaw angle for the movement command.
        Returns:
        None
        """

        if self.shm.get('movement_command') is None:
            self.log.warning("Movement command memory not available, attempting to reconnect...")
            # Try to reconnect to shared memory
            self._initialize_movement_command_memory()
            if self.shm.get('movement_command') is None:
                self.log.warning("Movement command memory still not available")
                return

        command = np.array([x, y, z, roll, pitch, yaw], dtype=np.float32)
        self._write_movement_command(command)

    def _write_movement_command(self, commands):
        """
        Writes movement commands to the shared memory buffer.
        This method writes a list of float values representing movement commands
        to a shared memory buffer. The first byte of the buffer is used as an 
        availability flag, which is set to 1 to indicate that new data is available.
        Args:
            commands (list of float): A list of float values representing the movement commands.
        Raises:
            ValueError: If the length of the `commands` list does not match `self.num_floats`.
        Notes:
            - The shared memory buffer is expected to be a NumPy array with a specific 
              structure, where the first byte is an availability flag and the rest is 
              used for the float values.
            - The method assumes that `self.shm['movement_command']` is a dictionary 
              containing the shared memory buffer.
        """
        
        if len(commands) != self.num_floats:
            self.log.error(f"Expected {self.num_floats} float values, but got {len(commands)}")
            raise ValueError(f"Expected {self.num_floats} float values, but got {len(commands)}")

        # Create a NumPy array backed by the shared memory buffer (for the 6 float values)
        buffer = self.shm['movement_command'].buf[1:]  # Skip the first byte (availability flag)
        command_array = np.ndarray((self.num_floats,), dtype=np.float32, buffer=buffer)

        # Write the new command data
        command_array[:] = commands

        # Set the availability flag (first byte) to 1 (new data available)
        self.shm['movement_command'].buf[0] = 1

    def set_resolution(self, width, height):
        """
        Set the resolution of the frame.

        Parameters:
        width (int): The width of the frame.
        height (int): The height of the frame.

        Sets the following attributes:
        - self.width: The width of the frame.
        - self.height: The height of the frame.
        - self.frame_shape: A tuple representing the shape of the frame (height, width).
        - self.frame_shape_3ch: A tuple representing the shape of the frame with 3 channels (height, width, 3).

        Logs a success message with the new resolution.
        """

        self.width, self.height = width, height
        self.frame_shape = (self.height, self.width)
        self.frame_shape_3ch = (self.height, self.width, 3)
        self.log.success(f"Resolution set to {width}x{height}")

    def set_noise_level(self, noise_level):
        """
        Set the noise level for the system.

        Parameters:
        noise_level (float): The desired noise level to be set.

        Returns:
        None
        """

        self.noise_level = noise_level
        self.log.success(f"Noise level set to {noise_level}")

    def set_apply_noise(self, apply_noise):
        """
        Sets the apply_noise attribute and logs the change.

        Parameters:
        apply_noise (bool): A boolean indicating whether to apply noise.
        """
        
        self.apply_noise = apply_noise
        self.log.success(f"Noise set to {apply_noise}")