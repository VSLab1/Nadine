#spiellogik
import datetime

from .entities import Player, Battlefield
import logging

logger = logging.getLogger(__name__)

timeout_seconds = 100


class GameState:
    def __init__(self, size=25, send_callback=None, add_peer_callback=None):
        self.board = Battlefield(size)
        self.players = {}

    def get_network_peers(self, exclude_ports=None):
        peers=[]
        if exclude_ports is None:
            exclude_ports = []

        if isinstance(exclude_ports, int):
            exclude_ports = [exclude_ports]

        for player in self.players.values():
            if player.port != exclude_ports and player.ip_adr:
                peers.append((player.ip_adr, player.port))
        return peers

    def add_player(self, name, port, color, ip_adr, timestamp, trail=None, x=None, y=None):
        if x is None or y is None:
            start_position = self.get_free_start_position()
            if not start_position:
                return None
            x, y = start_position

        if trail is None:
            trail = []

        new_player = Player(name, port, color, x, y, ip_adr, timestamp, trail)
        self.players[port] = new_player
        logger.info(f"new player: '{name}'; '{port}'; '{color}'; '{x, y}'; '{ip_adr}'; '{timestamp}'; trail:{trail}")
        return new_player

    def is_trail_collision(self, new_x, new_y):
        for player in self.players.values():
            if (new_x, new_y) in player.trail:
                logging.info(f"new position '{new_x, new_y} in trail'")
                return True

            if new_x == player.x and new_y == player.y:
                logging.info(f"collision with player head")
                return True
        return False


    def timeout(self, port):
        now = datetime.datetime.now()
        player = self.players.get(port)
        if not player.alive or not player.timestamp:
            return

        delta = (now - player.timestamp).total_seconds()
        if delta >= timeout_seconds:
            player.kill(now)
            logging.info(f"player '{port}' timedout")
            return True

        return False

    def get_start_positions(self):
        mid = self.board.size // 2
        return [
            (mid, 0),  # up
            (mid, self.board.size - 1),  # down
            (0, mid),  # left
            (self.board.size - 1, mid)  # right
        ]

    def get_free_start_position(self):
        positions = self.get_start_positions()

        taken = set()

        for player in self.players.values():
            taken.add((player.x, player.y))
            for position in player.trail:
                taken.add(position)

        for position in positions:
            if position not in taken:
                logger.info(f"free start position at '{position}'")
                return position

        logger.info(f"no free start position")
        return None  # no free position

    # local
    def handle_local_move(self, port, new_x, new_y):
        logger.debug(f"Player {port} moves to ({new_x},{new_y})")
        me = self.players.get(port)
        if not me or not me.alive:
            return None

        timestamp = datetime.datetime.now()

        logger.info(f"Trail: '{me.trail}'")
        logger.info(f"New: '{new_x, new_y}'")

        # collision with wall
        if not self.board.is_within_bounds(new_x, new_y):
            logger.warning(f"Player {port} hit wall at ({new_x},{new_y})")
            me.kill(timestamp)
            return {"type": "dead", "timestamp": timestamp}

        # collision with Trail
        for other_port, other_player in self.players.items():
            if (new_x, new_y) in other_player.trail:
                logger.warning(f"Player {port} hit trail of {other_port}")
                me.kill(timestamp)
                return {"type": "dead", "port": port, "timestamp": timestamp}

            if other_port != port and other_player.alive:
                if new_x == other_player.x and new_y == other_player.y:
                    logger.warning(f"Head-on collision: {port} and {other_port}")
                    me.kill(timestamp)
                    other_player.kill(timestamp)
                    return {
                        "type": "double_dead",
                        "p1": port,
                        "p2": other_port,
                        "timestamp": timestamp
                    }

        me.move(new_x, new_y)
        me.update_last_move(timestamp)

        return {
            "type": "move",
            "port": port,
            "x": new_x,
            "y": new_y
        }

    #other players
    def apply_remote_move(self, port, x, y):
        player = self.players.get(port)
        if not player:
            logger.debug("unknown player: ", port)
            return

        player.move(x, y)
        logging.info(f"player {port} moved to {x, y}")

    def apply_remote_death(self, port, timestamp):
        player = self.players.get(port)
        if isinstance(timestamp, str):
            timestamp = datetime.datetime.fromisoformat(timestamp)

        player.kill(timestamp)

    def handle_remote_event(self, msg_type, data, addr):
        if msg_type == "move":
            logger.info("move msg")
            port = data["port"]
            x = data["x"]
            y = data["y"]
            self.apply_remote_move(port, x, y)

        elif msg_type == "dead":
            logger.info("dead msg")
            port = data["port"]
            timestamp = data["timestamp"]
            self.apply_remote_death(port, timestamp)

        elif msg_type == "player_joined":
            logger.info("player_joined msg")
            self.add_player(
                name=data["name"],
                port=data["port"],
                color=data["color"],
                ip_adr=data["ip_adr"],
                moves=data["moves"],
                timestamp=datetime.datetime.now(),
                x=data["x"],
                y=data["y"]
            )

    def get_grid_matrix(self):
        size = self.board.size
        grid = [[0 for _ in range(size)] for _ in range(size)]

        for player in self.players.values():
            for (tx, ty) in player.trail:
                if self.board.is_within_bounds(tx, ty):
                    grid[ty][tx] = player.port

            if self.board.is_within_bounds(player.x, player.y):
                grid[player.y][player.x] = player.port
        return grid

    def to_dict(self):
        return {
            "grid": self.get_grid_matrix(), # Jetzt die ganze Matrix
            "players": [
                {
                    "name": p.name,
                    "port": p.port,
                    "color": p.color,
                    "moves": p.moves,
                    "x": p.x,
                    "y": p.y,
                    "timestamp": p.timestamp.strftime("%H:%M:%S"),
                    "trail": p.trail,
                    "alive": p.alive,
                    "ip_adr": p.ip_adr
                }
                for p in self.players.values()
            ]
        }

    def get_alive_players(self):
        return [player for player in self.players.values() if player.alive]

    def get_ranking(self):
        players = list(self.players.values())

        ranked = sorted(players, key=lambda p: (
            not p.alive,
            p.timestamp if p.timestamp else datetime.datetime.max
        ))

        return ranked