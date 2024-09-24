from threading import Thread
from networking import server
from sync import scheduler, send_file_to_random_node
import time

if __name__ == "__main__":

    # Server thread
    server_thread = Thread(target=server)
    server_thread.start()

    time.sleep(1)

    # Scheduler thread
    scheduler_thread = Thread(target=scheduler)
    scheduler_thread.start()

    time.sleep(2)

    # Random send thread
    random_send_thread = Thread(target=send_file_to_random_node)
    random_send_thread.start()