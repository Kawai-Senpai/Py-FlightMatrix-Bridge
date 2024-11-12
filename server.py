import socket
import threading
import pickle
import struct
import time
import numpy as np
import select  # Add this import
import cv2  # Add this import
from flightmatrix.bridge import FlightMatrixBridge
from ultraprint.logging import logger  # Add this import for client logging

#! Server
class FlightMatrixServer:
    """
    A socket server that allows clients to subscribe to specific data streams
    from the FlightMatrixBridge and continuously broadcasts the subscribed data.
    """

    def __init__(self, host, port, bridge:FlightMatrixBridge, broadcast_interval=0.1):
        """
        Initializes the socket server.

        Args:
            host (str): Host IP address.
            port (int): Port number.
            bridge (FlightMatrixBridge): Instance of FlightMatrixBridge.
            broadcast_interval (float): Interval in seconds for broadcasting data.
        """
        self.host = host
        self.port = port
        self.bridge = bridge
        self.broadcast_interval = broadcast_interval
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = {}  # client_socket: {'subscription_list': [], 'lock': threading.Lock()}
        self.running = False
        self.log = bridge.log  # Extract the log object from the bridge

    def start(self):
        """Starts the server and begins listening for clients."""
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        self.running = True
        self.log.info(f"Server started on {self.host}:{self.port}")

        threading.Thread(target=self.accept_clients, daemon=True).start()

    def accept_clients(self):
        """Accepts new client connections."""
        while self.running:
            client_socket, addr = self.server_socket.accept()
            self.log.info(f"Client connected from {addr}")
            # Handle client in a separate thread
            threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()

    def handle_client(self, client_socket):
        """Handles communication with a client."""
        try:
            # Receive subscription list from client
            subscription_data = self.receive_data(client_socket)
            if not subscription_data:
                client_socket.close()
                return
            subscription_list = subscription_data.get('subscribe', [])
            self.clients[client_socket] = {'subscription_list': subscription_list, 'lock': threading.Lock()}

            self.log.info(f"Client subscribed to: {subscription_list}")

            # Start sending data to this client
            threading.Thread(target=self.send_data_to_client, args=(client_socket,), daemon=True).start()

            # Continuously listen for data from client without blocking
            while self.running:
                ready_to_read, _, _ = select.select([client_socket], [], [], 0.1)
                if ready_to_read:
                    client_data = self.receive_data(client_socket)
                    if client_data:
                        # Process data received from client
                        if 'movement_command' in client_data:
                            movement_command = client_data['movement_command']
                            x, y, z, roll, pitch, yaw = movement_command
                            self.bridge.send_movement_command(x, y, z, roll, pitch, yaw)
                        else:
                            # Handle other types of data if necessary
                            pass
                    else:
                        # Client has disconnected
                        break
                else:
                    # No data received; continue looping
                    continue
        except Exception as e:
            self.log.error(f"Exception handling client: {e}")
        finally:
            self.disconnect_client(client_socket)

    def send_data_to_client(self, client_socket):
        """Continuously sends subscribed data to a client."""
        subscription_list = self.clients[client_socket]['subscription_list']
        try:
            while self.running:
                data = self.collect_data(subscription_list)
                if data:
                    serialized_data = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
                    self.send_data_in_chunks(client_socket, serialized_data)
                time.sleep(self.broadcast_interval)
        except Exception as e:
            self.log.error(f"Error sending data to client: {e}")
        finally:
            self.disconnect_client(client_socket)

    def collect_data(self, subscription_list):
        """Collects data from the bridge based on the subscription list."""
        data = {}

        for item in subscription_list:
            if item == 'sensor_data':
                sensor_data = self.bridge.get_sensor_data()
                if 'error' not in sensor_data:
                    data['sensor_data'] = sensor_data
            elif item == 'left_frame':
                left_frame_data = self.bridge.get_left_frame()
                if left_frame_data['frame'] is not None:
                    # Encode frame using JPEG
                    ret, buffer = cv2.imencode('.jpg', left_frame_data['frame'])
                    if ret:
                        data['left_frame'] = {
                            'frame': buffer.tobytes(),
                            'timestamp': left_frame_data['timestamp']
                        }
            elif item == 'right_frame':
                right_frame_data = self.bridge.get_right_frame()
                if right_frame_data['frame'] is not None:
                    ret, buffer = cv2.imencode('.jpg', right_frame_data['frame'])
                    if ret:
                        data['right_frame'] = {
                            'frame': buffer.tobytes(),
                            'timestamp': right_frame_data['timestamp']
                        }
            elif item == 'left_zdepth':
                left_zdepth_data = self.bridge.get_left_zdepth()
                if left_zdepth_data['frame'] is not None:
                    frame_bytes = left_zdepth_data['frame'].tobytes()
                    data['left_zdepth'] = {
                        'frame': frame_bytes,
                        'shape': left_zdepth_data['frame'].shape,
                        'timestamp': left_zdepth_data['timestamp']
                    }
            elif item == 'right_zdepth':
                right_zdepth_data = self.bridge.get_right_zdepth()
                if right_zdepth_data['frame'] is not None:
                    frame_bytes = right_zdepth_data['frame'].tobytes()
                    data['right_zdepth'] = {
                        'frame': frame_bytes,
                        'shape': right_zdepth_data['frame'].shape,
                        'timestamp': right_zdepth_data['timestamp']
                    }
            elif item == 'left_seg':
                left_seg_data = self.bridge.get_left_seg()
                if left_seg_data['frame'] is not None:
                    frame_bytes = left_seg_data['frame'].tobytes()
                    data['left_seg'] = {
                        'frame': frame_bytes,
                        'shape': left_seg_data['frame'].shape,
                        'timestamp': left_seg_data['timestamp']
                    }
            elif item == 'right_seg':
                right_seg_data = self.bridge.get_right_seg()
                if right_seg_data['frame'] is not None:
                    frame_bytes = right_seg_data['frame'].tobytes()
                    data['right_seg'] = {
                        'frame': frame_bytes,
                        'shape': right_seg_data['frame'].shape,
                        'timestamp': right_seg_data['timestamp']
                    }
        return data

    def send_data_in_chunks(self, client_socket, data_bytes, chunk_size=4096):
        """Sends data to the client."""
        with self.clients[client_socket]['lock']:
            try:
                # Send the total size first
                client_socket.sendall(struct.pack('>I', len(data_bytes)))
                # Send the serialized data
                client_socket.sendall(data_bytes)
            except Exception as e:
                self.log.error(f"Error sending data: {e}")
                self.disconnect_client(client_socket)

    def receive_data(self, sock):
        """Receives data from a socket."""
        try:
            # Receive data length
            data_length_bytes = sock.recv(4)
            if not data_length_bytes:
                return None
            data_length = struct.unpack('>I', data_length_bytes)[0]
            # Receive data
            data = b''
            while len(data) < data_length:
                packet = sock.recv(min(data_length - len(data), 4096))
                if not packet:
                    return None
                data += packet
            # Deserialize data
            return pickle.loads(data)
        except Exception as e:
            self.log.error(f"Error receiving data: {e}")
            return None

    def disconnect_client(self, client_socket):
        """Disconnects a client and cleans up resources."""
        if client_socket in self.clients:
            del self.clients[client_socket]
        client_socket.close()
        self.log.info("Client disconnected")

    def stop(self):
        """Stops the server and closes all client connections."""
        self.running = False
        for client_socket in list(self.clients.keys()):
            client_socket.close()
        self.server_socket.close()
        self.log.info("Server stopped")

    def set_log_level(self, log_level='INFO'):
        """
        Sets the logging level for the application.

        Parameters:
            log_level (str): The desired logging level. Default is 'INFO'.
        """
        self.log.set_log_level(log_level)
        self.log.success(f"Log level set to {log_level}")

    def set_write_to_file(self, write_to_file):
        """
        Sets the logging behavior to write to a file.

        Parameters:
            write_to_file (bool): If True, logging will be written to a file.
        """
        self.log.set_write_to_file(write_to_file)
        self.log.success(f"Write to file set to {write_to_file}")

#! Client
class FlightMatrixClient:
    """
    A client that connects to the FlightMatrixSocketServer to receive subscribed data continuously
    and send movement commands when needed.
    """

    def __init__(self, host, port, subscription_list, data_callback):
        """
        Initializes the client.

        Args:
            host (str): Server IP address.
            port (int): Server port number.
            subscription_list (list): List of data types to subscribe to.
            data_callback (function): Function to handle received data.
        """
        self.host = host
        self.port = port
        self.subscription_list = subscription_list
        self.data_callback = data_callback
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = False
        self.lock = threading.Lock()
        self.log = logger('FlightMatrixClientLog', include_extra_info=False, write_to_file=False, log_level='DEBUG')  # Initialize logger for client

    def connect(self):
        """Connects to the server and starts listening for data."""
        self.socket.connect((self.host, self.port))
        self.running = True
        # Send subscription list to server
        subscription_data = {'subscribe': self.subscription_list}
        self.send_data(subscription_data)
        # Start receiving data
        threading.Thread(target=self.receive_data_loop, daemon=True).start()

    def receive_data_loop(self):
        """Continuously receives data from the server."""
        try:
            while self.running:
                data = self.receive_data()
                if data:
                    processed_data = self.process_received_data(data)
                    self.data_callback(processed_data)
                else:
                    break  # Server closed connection
        except Exception as e:
            self.log.error(f"Exception receiving data: {e}")
        finally:
            self.disconnect()

    def process_received_data(self, data):
        """Processes the received data, reconstructing frames from bytes."""
        for key, value in data.items():
            if 'frame' in value:
                frame_bytes = value['frame']
                if key in ['left_frame', 'right_frame', 'left_seg', 'right_seg']:
                    # Decode JPEG-compressed images
                    frame = cv2.imdecode(np.frombuffer(frame_bytes, np.uint8), cv2.IMREAD_COLOR)
                    value['frame'] = frame
                elif key in ['left_zdepth', 'right_zdepth']:
                    # Decode depth maps (assuming they are sent as raw float32 arrays)
                    frame_shape = value['shape']
                    frame = np.frombuffer(frame_bytes, dtype=np.float32).reshape(frame_shape)
                    value['frame'] = frame
                else:
                    # Handle other frame types if necessary
                    pass
        return data

    def send_movement_command(self, x, y, z, roll, pitch, yaw):
        """Sends a movement command to the server."""
        command_data = {'movement_command': [x, y, z, roll, pitch, yaw]}
        self.send_data(command_data)

    def send_data(self, data):
        """Sends data to the server."""
        with self.lock:
            try:
                serialized_data = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
                data_length = len(serialized_data)
                message = struct.pack('>I', data_length) + serialized_data
                self.socket.sendall(message)
            except Exception as e:
                self.log.error(f"Error sending data: {e}")

    def receive_data(self):
        """Receives data from the server."""
        try:
            # Receive data length
            data_length_bytes = self.socket.recv(4)
            if not data_length_bytes:
                return None
            data_length = struct.unpack('>I', data_length_bytes)[0]
            # Receive data in chunks
            data = b''
            while len(data) < data_length:
                chunk = self.socket.recv(min(data_length - len(data), 4096))
                if not chunk:
                    return None
                data += chunk
            # Deserialize data
            return pickle.loads(data)
        except Exception as e:
            self.log.error(f"Error receiving data: {e}")
            return None

    def disconnect(self):
        """Disconnects from the server."""
        self.running = False
        self.socket.close()
        self.log.info("Disconnected from server")

    def set_log_level(self, log_level='INFO'):
        """
        Sets the logging level for the application.

        Parameters:
            log_level (str): The desired logging level. Default is 'INFO'.
        """
        self.log.set_log_level(log_level)
        self.log.success(f"Log level set to {log_level}")

    def set_write_to_file(self, write_to_file):
        """
        Sets the logging behavior to write to a file.

        Parameters:
            write_to_file (bool): If True, logging will be written to a file.
        """
        self.log.set_write_to_file(write_to_file)
        self.log.success(f"Write to file set to {write_to_file}")