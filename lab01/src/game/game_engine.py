#spiellogik
import datetime
import logging
from .entities import Player, Battlefield

logger = logging.getLogger(__name__)


class GameEngine:
    def __init__(self, size=25):
        self.battlefield = Battlefield(size)
        self.players = {}

    def add_player(self, name, port, color, ip_adr, timestamp, moves=0, trail=None, x=None, y=None):
        if trail is None:
            trail = []
            if x is None or y is None:
                start_position = self.get_free_start_position()
                if not start_position:
                    return None
                x, y = start_position

        player = Player(name, port, color, x, y, ip_adr, timestamp, moves, trail)
        self.players[port] = player
        return player

    def check_collision(self, port, new_x, new_y):
        # 1. wall-collision
        if not self.battlefield.is_within_bounds(new_x, new_y):
            return "WALL"

        # 2. Trail/head-collision
        for player in self.players.values():
            if (new_x, new_y) in player.trail:
                return "TRAIL"
            if player.port != port and player.alive and (new_x, new_y) == (player.x, player.y):
                return "HEAD_ON"
        return None

    def get_free_start_position(self):
        mid = self.battlefield.size // 2
        starts = [(mid, 0), (mid, self.battlefield.size-1), (0, mid), (self.battlefield.size-1, mid)]
        taken = set()
        for player in self.players.values():
            taken.add((player.x, player.y))
            for trail_pos in player.trail:
                if isinstance(trail_pos, list):
                    taken.add(tuple(trail_pos))
                else:
                    taken.add(trail_pos)

        for s in starts:
            if s not in taken:
                return s
        return None

    def get_ranking(self):
        return sorted(self.players.values(), key=lambda p: (not p.alive, p.timestamp or datetime.datetime.max))

    def check_game_over(self):
        alive_players = [player for player in self.players.values() if player.alive]
        if len(self.players) >= 2 and len(alive_players) <= 1:
            return True
        return False

    def get_final_ranking(self):
        return sorted(self.players.values(),
                      key=lambda player: (player.alive, player.timestamp if not player.alive else datetime.datetime.max, player.moves),
                      reverse=True)

    def get_grid_matrix(self):
        size = self.battlefield.size
        grid = [[0 for _ in range(size)] for _ in range(size)]

        for player in self.players.values():
            for(tx, ty) in player.trail:
                if 0 <= tx < size and 0 <= ty < size:
                    grid[tx][ty] = player.port

            if player.alive and 0 <= player.x < size and 0 <= player.y < size:
                grid[player.x][player.y] = player.port

        return grid