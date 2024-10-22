
from datetime import datetime, timezone, timedelta
import time
from flightmatrix.bridge import FlightMatrixBridge
import math

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

