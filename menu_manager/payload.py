# payload.py
import struct
import time
from datetime import datetime

def get_timestamp():
    now = datetime.now()
    return now.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # trim to milliseconds

def write_log(message):
    with open('/srv/projects/editor-menu/packet_times.log', 'a') as f:
        f.write(message + '\n')

def send_message(sock, message: str, name):
    data = message.encode('utf-8')
    length = struct.pack('!I', len(data))
    sock.sendall(length + data)
    write_log(f"{name} sent packet at {get_timestamp()}")

def recv_message(sock, name):
    raw_len = sock.recv(4)
    if not raw_len:
        return None
    length = struct.unpack('!I', raw_len)[0]
    data = b''
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            raise ConnectionError("Connection closed before full message received")
        data += chunk
    write_log(f"{name} received packet at {get_timestamp()}")
    return data.decode('utf-8')
