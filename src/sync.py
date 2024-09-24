import os
import time
import random
from networking import client_send_file, client_request_file
import hashlib
from utils import *

checksum_cache = {}  # Cache to store checksums of files

def calculate_checksum(filepath) -> str:
    """Calculates the MD5 checksum of a file, utilizing a cache to avoid redundant calculations."""
    
    # Check if the checksum is already cached
    if filepath in checksum_cache:
        cached_checksum, cached_mtime = checksum_cache[filepath]
        
        # Compare the modification time of the file
        current_mtime = os.path.getmtime(filepath)
        if current_mtime == cached_mtime:
            return cached_checksum

    # If not cached or file is modified, recalculate the checksum
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read(BUFFER_SIZE)
        while buf:
            hasher.update(buf)
            buf = f.read(BUFFER_SIZE)
    
    # Update the cache with the new checksum and modification time
    checksum = hasher.hexdigest()
    checksum_cache[filepath] = (checksum, os.path.getmtime(filepath))
    
    return checksum

def get_responsible_nodes(filename, replication_factor=4):
    """Determines the nodes responsible for storing a file based on the filename and the replication factor
        Args:
            filename (str): The name of the file for which to determine responsible nodes.
            replication_factor (int): The number of nodes to replicate the file across. Defaults to 4.

        Returns:
            list: A list of node IDs responsible for storing the file.
    """
    salted_filename = f"{filename}-{NODE_ID}"  # Adding a salt for better distribution

    # Sha256 hashing of the filename into a digest
    hash_object = hashlib.sha256(salted_filename.encode())
    # hex conversion
    hex_dig = hash_object.hexdigest()
    sorted_nodes = sorted(NODES.keys())
    
    # Determining primary node using the hashed value
    responsible_nodes = []
    primary_node_index = int(hex_dig, 16) % len(sorted_nodes)
    responsible_nodes.append(sorted_nodes[primary_node_index])

    # Adding a replication factor

    for i in range(1, replication_factor):
        next_node_index = (primary_node_index + i) % len(sorted_nodes)
        responsible_nodes.append(sorted_nodes[next_node_index])

    return responsible_nodes

def sync_files():
    """Synchronizes the files in the local directory with the responsible nodes. 
    If the current node is the primary responsible node, it ensures it has the latest 
    version of the files from other nodes. If not, it sends the files to the responsible nodes.
    """
    print("Syncing files...")
    for filename in os.listdir(DIRECTORY):
        print(f"Checking file: {filename}")
        responsible_nodes = get_responsible_nodes(filename)
        primary_node = responsible_nodes[0]
        print(f"Responsible node for {filename}: {primary_node}")

        if primary_node != NODE_ID:
            # Send the file to the responsible node
            target_host = NODES[primary_node]
            print(f"Sending {filename} to node {primary_node}")
            client_send_file(target_host, PORT, filename)
        else:
            # Request the latest version of the file from other nodes
            local_filepath = os.path.join(DIRECTORY, filename)
            local_checksum = calculate_checksum(local_filepath)

            for node_id in responsible_nodes:
                if node_id != NODE_ID:
                    client_request_file(NODES[node_id], PORT, filename)
                    #client_request_file(node_address, PORT, filename)
                    remote_filepath = os.path.join(DIRECTORY, filename)

                    # Checking checksum to make sure the files are not corrupted during movement
                    if os.path.exists(remote_filepath):
                        remote_checksum = calculate_checksum(remote_filepath)
                        if local_checksum != remote_checksum:
                            # Conflict detected: different contents, same name
                            print(f"Checksum mismatch for {filename}, renaming incoming file.")
                            timestamp = int(time.time())  # Current timestamp
                            name, ext = os.path.splitext(filename)
                            new_filename = f"{name}_{timestamp}{ext}"
                            new_filepath = os.path.join(DIRECTORY, new_filename)
                            
                            # Ensure that we're not overwriting any existing files with the new name
                            if not os.path.exists(new_filepath):
                                os.rename(remote_filepath, new_filepath)
                                print(f"File renamed to {new_filename} due to conflict.")
                            else:
                                print(f"File {new_filename} already exists, skipping rename.")
                        else:
                            print(f"No conflict detected for {filename}, file is consistent.")
                    else:
                        print(f"Remote file {filename} does not exist, skipping checksum check.")
                            

def scheduler():
    """Periodically triggers the file synchronization process. The synchronization occurs at intervals 
    defined by the SCHEDULER_TIMER"""
    while True:
        print("Starting file synchronization...")
        sync_files()
        print("Files synced. Waiting for next sync...")
        time.sleep(SCHEDULER_TIMER)

def send_file_to_random_node():
    """Periodically selects a random file from the local directory and sends it to a
    random node at intervals defined by FILE_SEND_TIMER"""
    while True:
        time.sleep(FILE_SEND_TIMER)  
        
        # Select a random file from the directory
        files = os.listdir(DIRECTORY)
        if not files:
            print("No files available to send.")
            continue
        filename = random.choice(files)
        
        # Select a random node
        node_id, node_address = random.choice(list(NODES.items()))
        if node_id != NODE_ID:
            print(f"Sending {filename} to random node {node_id}")
            client_send_file(node_address, PORT, filename, True)
        else:
            print(f"Selected node {node_id} is the current node, skipping send.")