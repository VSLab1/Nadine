import json
from enum import Enum


class RejectReason(Enum):
    NAME_TAKEN = "name_taken"
    COLOR_TAKEN = "color_taken"
    GAME_FULL = "game_full"
    PORT_TAKEN = "port_taken"


def create_message(msg_type, data):
    return json.dumps({
        "type": msg_type,
        "data": data
    })


def create_join_request(name, color, port):
    return create_message("join_request", {
        "name": name,
        "color": color,
        "port": port
    })


def create_join_accept(players, grid):
    return create_message("join_accept", {
        "players": players,
        "grid": grid,
    })


def create_join_reject(reason: RejectReason):
    return create_message("join_reject", {
        "reason": reason.value,
    })


def create_player_joined(player):
    return create_message("player_joined", {
        "player": player
    })


def create_move(port, x, y):
    return create_message("move", {
        "port": port,
        "x": x,
        "y": y
    })


def create_player_died(port, timestamp):
    return create_message("dead", {
        "port": port,
        "timestamp": timestamp.isoformat()
    })
