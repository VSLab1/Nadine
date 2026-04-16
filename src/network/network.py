#UDP+Json
import socket
import threading
import json
import traceback


class Network:
    def __init__(self, port, on_event_callback):
        self.port = port
        self.on_event = on_event_callback
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            self.sock.bind(("", port))
        except OSError:
            raise OSError(f"Port{port} is already in use")

        self.running = True
        threading.Thread(target=self.listen, daemon=True).start()

    def send_to(self, message, addr):
        self.sock.sendto(message.encode(), addr)

    def listen(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(8192)
                event = json.loads(data.decode())

                msg_type = event["type"]
                data = event["data"]

                self.on_event(msg_type, data, addr)
            except Exception as e:
                print("Network error:", e)
                traceback.print_exc()

    def send_broadcast(self, message, recipients):
        data = message.encode()
        for addr in recipients:
            try:
                self.sock.sendto(data, addr)
            except Exception as e:
                print(f"Send error to {addr}: {e}")