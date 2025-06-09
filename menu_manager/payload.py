
import struct
def send_message(sock, message: str):
    data = message.encode('utf-8')
    length = struct.pack('!I', len(data))  # 4-byte big-endian length prefix
    sock.sendall(length + data)

def recv_message(sock):
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
    return data.decode('utf-8')
