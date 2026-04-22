import json

class GameProtocol:
    @staticmethod
    def wrap(msg_type, data):
        return json.dumps({"type": msg_type, "data": data})

    @staticmethod
    def move(port, x, y):
        return GameProtocol.wrap("move", {"port": port, "x": x, "y": y})

    @staticmethod
    def death(port, timestamp):
        ts = timestamp.isoformat() if hasattr(timestamp, 'isoformat') else timestamp
        return GameProtocol.wrap("dead", {"port": port, "timestamp": ts})