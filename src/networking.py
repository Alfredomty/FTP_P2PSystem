import socket
import os
import json
from threading import Thread
from datetime import datetime
from utils import *


def server() -> None: 
    """Starts a server that listens for incoming connections on the specified HOST and PORT.
    Each incoming connection is handled in a separate thread using the `handle_client` function.
    """

    # Socket initializaiton
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Listening on {HOST}:{PORT}")
        
        while True:
            conn, addr = s.accept()
            thread = Thread(target=handle_client, args=(conn, addr))
            thread.start()

def handle_client(conn, addr):
    """Handles incoming client connection depending on requested JSON action and routes to handler
        Args:
            conn (socket.socket): The socket object representing the client connection.
            addr (tuple): The address of the connected client.
    """

    print(f"Connected by {addr}")
    with conn:
        data = conn.recv(BUFFER_SIZE)
        # Desereialization
        request = json.loads(data.decode('utf-8'))
        action = request['action']
        
        #if action == 'FILE_LIST':
            #handle_file_list(conn, request['file_list'])
        if action == 'REQUEST_FILE':
            handle_file_request(conn, request)

        elif action == 'SEND_FILE':
            handle_file_receive(conn, request)

        else:
            print(f"Unknown action {action} from {addr}")



def handle_file_request(conn, request):
    """Handles client request for a file
        Args:
            conn (socket.socket): The socket object representing the client connection.
            request (dict): The client's request data containing the filename.
    """
    filename = request['filename']
    filepath = os.path.join(DIRECTORY, filename)

    if os.path.exists(filepath):
        response = {'status': 'OK', 'filename': filename, 'filesize': os.path.getsize(filepath)}
        conn.sendall(json.dumps(response).encode('utf-8'))

        with open(filepath, 'rb') as f:
            while True:
                bytes_read = f.read(BUFFER_SIZE)
                if not bytes_read:
                    break
                conn.sendall(bytes_read)
                
        print(f"Sent file {filename} to client.")

    else:
        response = {'status': 'NOT_FOUND', 'filename': filename}
        conn.sendall(json.dumps(response).encode('utf-8'))
        print(f"File {filename} not found, informed client.")

def handle_file_receive(conn, request):
    """Handles the client's request to send a file to the server. Receives the file in chunks
    and saves it to the specified directory.
        Args:
            conn (socket.socket): The socket object representing the client connection.
            request (dict): The client's request data containing the filename.
    """
    filename = request['filename']
    filesize = request['filesize']
    filepath = os.path.join(DIRECTORY, filename)

    with open(filepath, 'wb') as f:
        total_received = 0
        while total_received < filesize:
            # Grabbing files in chunks and write
            bytes_read = conn.recv(BUFFER_SIZE)
            if not bytes_read:
                break
            f.write(bytes_read)
            total_received += len(bytes_read)
    
    print(f"Received and saved file {filename} from client.")



def client_request_file(target_host, target_port, filename):
    """Sends a request to a server to download a specific file. Receives the file in chunks
    and saves it to the DIRECTORY .
        Args:
        target_host (str): The IP address or hostname of the target server.
        target_port (int): The port number of the target server.
        filename (str): The name of the file to request from the server.
    """
    request = {
        'action': 'REQUEST_FILE',
        'filename': filename
    }

    # Socket initialization
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((target_host, target_port))
        
        # Request all
        s.sendall(json.dumps(request).encode('utf-8'))

        response = json.loads(s.recv(BUFFER_SIZE).decode('utf-8'))
        if response['status'] == 'OK':
            filesize = response['filesize']
            filepath = os.path.join(DIRECTORY, filename) 
            with open(filepath, 'wb') as f:
                total_received = 0
                while total_received < filesize:
                    bytes_read = s.recv(BUFFER_SIZE)
                    if not bytes_read:
                        break
                    f.write(bytes_read)
                    total_received += len(bytes_read)
            print(f"File {filename} received successfully.")

        elif response['status'] == 'NOT_FOUND':
            print(f"File {filename} not found on server.")


def client_send_file(target_host, target_port, filename, delete_file = False):
    """Sends a file to a specified server. Optionally deletes the file from the local directory
    after successful transmission.
        Args:
            target_host (str): The IP address or hostname of the target server (Docker handles it using node1,2...etc).
            target_port (int): The port number of the target server.
            filename (str): The name of the file to send to the server.
            delete_file (bool, optional): Whether to delete the file from the local directory after sending. Defaults to False.
    """
    filepath = os.path.join(DIRECTORY, filename)
    filesize = os.path.getsize(filepath)
    request = {
        'action': 'SEND_FILE',
        'filename': filename,
        'filesize': filesize
    }

    # Socket init
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((target_host, target_port))
        s.sendall(json.dumps(request).encode('utf-8'))

        with open(filepath, 'rb') as f:
            while True:
                # Grab by bytes and send 
                bytes_read = f.read(BUFFER_SIZE)
                if not bytes_read:
                    break
                s.sendall(bytes_read)
        print(f"File {filename} sent successfully.")

        if (delete_file): 
            # REMOVE AFTER BEING SENT
            os.remove(filepath)
            print(f"File {filename} deleted from local directory.")
