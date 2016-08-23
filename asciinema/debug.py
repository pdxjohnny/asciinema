import os
import socket


DEBUG_HOST = os.getenv('ASCIINEMA_DEBUG_HOST', 'localhost')
DEBUG_PORT = int(os.getenv('ASCIINEMA_DEBUG_PORT', 4444))

def write(d):
    try:
        if isinstance(d, str):
            d = d.encode('UTF-8')
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((DEBUG_HOST, DEBUG_PORT))
            s.sendall(d)
    except Exception:
        pass
    return len(d)
