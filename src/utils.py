import os
import hashlib

# GLOBAL VARIABLES
HOST = '0.0.0.0'
PORT = 5000
BUFFER_SIZE = 16384
DIRECTORY = 'sync_dir'
#SHARED_DIRECTORY = 'shared_dir'

# Nodes info
NODES = {'node1':'node1', 'node2':'node2', 'node3':'node3', 'node4':'node4'} 

# FOR USE IN LAN 
#NODES = {
    #"node1": "127.0.0.1.2",
    #"node2": "127.0.0.1.3",
    #"node3": "127.0.0.1.4",
    #"node4": "127.0.0.1.5"
#}
NODE_ID = os.getenv('NODE_ID')

# Timings
SCHEDULER_TIMER = 10
FILE_SEND_TIMER = 40

