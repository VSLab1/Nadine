import json
import datetime

class GameProtocol:
    @staticmethod
    def wrap(msg_type, data):
        return json.dumps({"type": msg_type, "data": data})

    @staticmethod
    def move(port, x, y):
        return GameProtocol.wrap("move", {"port": port, "x": x, "y": y})

    @staticmethod
    def death(port, timestamp):
        if isinstance(timestamp, datetime.datetime):
            ts_str = timestamp.strftime("%H:%M:%S")
        else:
            ts_str = str(timestamp)
        return GameProtocol.wrap("dead", {"port": port, "timestamp": ts_str})