#entities

import datetime
import logging
logger = logging.getLogger(__name__)

class Player:
    def __init__(self, name, port, color, x, y, ip_adr, timestamp, trail = None):
        self.name = name
        self.port = port
        self.color = color
        self.x = x
        self.y = y
        self.trail = trail if trail is not None else []
        self.moves = 0
        self.alive = True
        self.timestamp = timestamp
        self.ip_adr = ip_adr

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


class Battlefield:
    def __init__(self, size):
        self.size = size

    def is_within_bounds(self, x, y):
        return 0 <= x < self.size and 0 <= y < self.size
