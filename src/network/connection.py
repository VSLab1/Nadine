#UDP+Json
import socket
import threading
import json
import traceback
from PyQt5.QtCore import QObject, pyqtSignal


class Network(QObject):
    message_received = pyqtSignal(str, dict, tuple)
    def __init__(self, port):
        super().__init__()
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.running = True

        try:
            self.sock.bind(("", port))
        except OSError:
            raise OSError(f"Port{port} is already in use")

        self.listen_thread = threading.Thread(target=self.listen, daemon=True)
        self.listen_thread.start()

    def send_to(self, message, addr):
        try:
            self.sock.sendto(message.encode(), addr)
        except Exception as e:
            print(f"Send error to {addr}: {e}")

    def listen(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(8192)
                event = json.loads(data.decode())

                self.message_received.emit(event["type"], event["data"], addr)
            except Exception as e:
                if self.running:
                    print("Network error:", e)
                    traceback.print_exc()

    def send_broadcast(self, message, recipients):
        data = message.encode()
        for addr in recipients:
            try:
                self.sock.sendto(data, addr)
            except Exception as e:
                print(f"Send error to {addr}: {e}")