# Simple example: server manages workspace state, broadcasts updates via UNIX socket.
# Client connects, receives updates, sends commands.
# Plugins can run on server or client side.

import os
import socket
import selectors
import threading
import json
from pathlib import Path

SOCKET_PATH = "/tmp/workspace_manager.sock"

# --- Server Side ---

class WorkspaceServer:
    def __init__(self, socket_path):
        self.socket_path = socket_path
        self.sel = selectors.DefaultSelector()
        self.clients = {}
        self.workspace = set()  # current files in workspace

    def start(self):
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.bind(self.socket_path)
        self.sock.listen()
        self.sock.setblocking(False)
        self.sel.register(self.sock, selectors.EVENT_READ, self.accept)
        threading.Thread(target=self.event_loop, daemon=True).start()
        print("Server started")

    def accept(self, sock):
        conn, _ = sock.accept()
        conn.setblocking(False)
        self.sel.register(conn, selectors.EVENT_READ, self.read)
        self.clients[conn] = b""
        self.send_state(conn)

    def read(self, conn):
        try:
            data = conn.recv(4096)
            if not data:
                self.disconnect(conn)
                return
            self.clients[conn] += data
            while b"\n" in self.clients[conn]:
                line, rest = self.clients[conn].split(b"\n", 1)
                self.clients[conn] = rest
                self.handle_message(conn, line)
        except ConnectionResetError:
            self.disconnect(conn)

    def handle_message(self, conn, line):
        try:
            msg = json.loads(line.decode())
        except Exception:
            return
        if msg.get("action") == "add_file":
            f = msg.get("file")
            if f:
                self.workspace.add(f)
                self.broadcast_state()
        elif msg.get("action") == "remove_file":
            f = msg.get("file")
            if f and f in self.workspace:
                self.workspace.remove(f)
                self.broadcast_state()

    def send_state(self, conn):
        state = json.dumps({"type": "state", "workspace": list(self.workspace)}) + "\n"
        conn.send(state.encode())

    def broadcast_state(self):
        state = json.dumps({"type": "state", "workspace": list(self.workspace)}) + "\n"
        for c in list(self.clients):
            try:
                c.send(state.encode())
            except Exception:
                self.disconnect(c)

    def disconnect(self, conn):
        self.sel.unregister(conn)
        conn.close()
        del self.clients[conn]

    def event_loop(self):
        while True:
            events = self.sel.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj)

# --- Client Side ---

class WorkspaceClient:
    def __init__(self, socket_path):
        self.socket_path = socket_path
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(socket_path)
        self.buffer = b""
        threading.Thread(target=self.listen, daemon=True).start()
        self.workspace = set()

    def listen(self):
        while True:
            data = self.sock.recv(4096)
            if not data:
                break
            self.buffer += data
            while b"\n" in self.buffer:
                line, rest = self.buffer.split(b"\n", 1)
                self.buffer = rest
                self.handle_message(line)

    def handle_message(self, line):
        try:
            msg = json.loads(line.decode())
        except Exception:
            return
        if msg.get("type") == "state":
            self.workspace = set(msg.get("workspace", []))
            print("Workspace updated:", self.workspace)

    def add_file(self, filepath):
        msg = {"action": "add_file", "file": filepath}
        self.sock.send((json.dumps(msg) + "\n").encode())

    def remove_file(self, filepath):
        msg = {"action": "remove_file", "file": filepath}
        self.sock.send((json.dumps(msg) + "\n").encode())

# --- Usage Example ---

if __name__ == "__main__":
    import sys
    import time

    if sys.argv[1] == "server":
        server = WorkspaceServer(SOCKET_PATH)
        server.start()
        while True:
            time.sleep(1)

    elif sys.argv[1] == "client":
        client = WorkspaceClient(SOCKET_PATH)
        time.sleep(1)  # wait for initial state

        # Example interaction: add and remove file
        client.add_file("/path/to/file1")
        time.sleep(0.5)
        client.add_file("/path/to/file2")
        time.sleep(0.5)
        client.remove_file("/path/to/file1")
        time.sleep(2)

