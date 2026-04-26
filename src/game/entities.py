#entities

import logging
logger = logging.getLogger(__name__)

class Player:
    def __init__(self, name, port, color, x, y, ip_adr, timestamp, moves = 0, trail = None):
        self.name = name
        self.port = port
        self.color = color
        self.x = x
        self.y = y
        self.moves = moves if moves is not None else 0
        self.trail = trail if trail is not None else []
        self.alive = True
        self.timestamp = timestamp
        self.ip_adr = ip_adr
        self.has_left = False

    def move(self, new_x, new_y):
        if not self.alive:
            return
        self.trail.append((self.x, self.y))
        self.x = new_x
        self.y = new_y
        self.moves += 1

    def update_last_move(self, timestamp):
        logger.info(f"Player {self.port} last moved at {self.timestamp}")
        self.timestamp = timestamp

    def kill(self, timestamp):
        logger.info(f"Player {self.port} died after {self.moves} moves")
        self.alive = False
        self.timestamp = timestamp

    def leave(self):
        if (self.x, self.y) not in self.trail:
            self.trail.append((self.x, self.y))
        self.alive = False
        self.has_left = True

    def to_dict(self):
        serializable_trail = []
        for pos in self.trail:
            serializable_trail.append([int(pos[0]), int(pos[1])])
        return {
            "name": self.name,
            "port": self.port,
            "color": self.color,
            "x": int(self.x),
            "y": int(self.y),
            "trail": serializable_trail,
            "moves": self.moves,
            "alive": self.alive,
            "timestamp": self.timestamp.strftime("%H:%M:%S") if hasattr(self.timestamp, 'strftime') else self.timestamp,
            "ip_adr": self.ip_adr
        }


class Battlefield:
    def __init__(self, size):
        self.size = size

    def is_within_bounds(self, x, y):
        return 0 <= x < self.size and 0 <= y < self.size
