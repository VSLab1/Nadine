import datetime

from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QTimer
from game.game_engine import GameEngine
from network.connection import Network
from network.protocol import GameProtocol

class MainController:
    def __init__(self, gui, port, name, color, target_ip=None, target_port=None, grid_size=25):
        self.gui = gui
        self.local_name = name
        self.local_color = color
        self.port = port
        try:
            self.network = Network(port)
        except OSError:
            self.gui.show_error_and_return_to_menu("port_taken_locally")
            return
        self.network.message_received.connect(self.on_network_data)

        self.last_own_action = datetime.datetime.now()

        self.timeout_limit = 1000.0

        self.self_check_timer = QTimer()
        self.self_check_timer.timeout.connect(self.check_self_timeout)
        self.self_check_timer.start(1000)

        self.engine = GameEngine(grid_size)
        self.protocol = GameProtocol()

        if not target_ip:
            self.engine.add_player(name, port, color, "127.0.0.1", datetime.datetime.now())
            self.refresh_gui()
        else:
            req = self.protocol.wrap("join_request", {
                "name": name, "port": port, "color": color
            })
            self.network.send_to(req, (target_ip, int(target_port)))

        # connect gui signals
        self.gui.input_received.connect(self.handle_local_move)
        self.refresh_gui()


    def handle_local_move(self, direction):
        player = self.engine.players.get(self.port)
        if not player or not player.alive:
            return

        # get new coordinates
        dx, dy = {"UP": (0, -1), "DOWN": (0, 1), "LEFT": (-1, 0), "RIGHT": (1, 0)}[direction]
        new_x, new_y = player.x + dx, player.y + dy

        #update last_action for timeout
        self.last_own_action = datetime.datetime.now()

        # collision check
        collision = self.engine.check_collision(self.port, new_x, new_y)

        if collision:
            death_time = datetime.datetime.now()
            player.kill(death_time)
            # broadcast death
            timestamp_str = self.convert_datetime_to_str(death_time)
            msg = self.protocol.death(self.port, timestamp_str)
            self.broadcast(msg)
        else:
            player.move(new_x, new_y)
            # broadcast move
            msg = self.protocol.move(self.port, new_x, new_y)
            self.broadcast(msg)

        self.refresh_gui()

    def on_network_data(self, msg_type, data, addr):
        """called, when packages are received from other players"""
        if msg_type == "move":
            player_port = data["port"]
            if player_port in self.engine.players:
                self.engine.players[player_port].move(data["x"], data["y"])

        elif msg_type == "dead":
            player_port = data["port"]
            if player_port in self.engine.players:
                datetime_object = self.convert_str_to_datetime(data.get("timestamp"))
                self.engine.players[player_port].kill(datetime_object)

        elif msg_type == "join_request":
            self.handle_join_request(data, addr)

        elif msg_type == "join_accept":
            matrix = data.get("grid")

            if isinstance(matrix, list) and len(matrix) > 0:
                host_grid_size = len(matrix)
                self.engine = GameEngine(host_grid_size)
                self.gui.battlefield.reset_size(host_grid_size)
            else:
                print("warning no valid matrix received")

            for p_data in data["players"]:
                datetime_object = self.convert_str_to_datetime(p_data.get("timestamp"))
                self.engine.add_player(
                    name=p_data["name"],
                    port=p_data["port"],
                    color=p_data["color"],
                    ip_adr=p_data["ip_adr"],
                    moves=p_data["moves"],
                    x=p_data["x"],
                    y=p_data["y"],
                    trail=p_data["trail"],
                    timestamp=datetime_object
                )
            self.refresh_gui()

        elif msg_type == "join_reject":
            self.stop()
            reason = data.get("reason", "Unknown")
            self.gui.show_error_and_return_to_menu(reason)
            return

        elif msg_type == "player_joined":
            player_data = data["player"]
            if player_data["port"] not in self.engine.players:
                raw_time = player_data.get("timestamp")
                datetime_timestamp = None
                if raw_time:
                    try:
                        datetime_timestamp = datetime.datetime.strptime(raw_time, "%H:%M:%S")
                    except (ValueError, TypeError):
                        print("converting timestamp to datetime failed")


                self.engine.add_player(
                    name=player_data["name"],
                    port=player_data["port"],
                    color=player_data["color"],
                    ip_adr=player_data["ip_adr"],
                    x=player_data["x"],
                    y=player_data["y"],
                    trail=player_data["trail"],
                    timestamp=datetime_timestamp
                )
                print(f"New player joined the network: {player_data['name']}")

        elif msg_type == "leave":
            player_port = data["port"]
            if player_port in self.engine.players:
                player = self.engine.players[player_port]
                player.leave()
        self.refresh_gui()

    def broadcast(self, message_str):
        # filter players without IP or oneself
        peers = [ (p.ip_adr, p.port) for p in self.engine.players.values()
                  if p.port != self.port and p.ip_adr and not getattr(p, 'has_left', False)]

        for addr in peers:
            try:
                self.network.send_to(message_str, addr)
            except Exception as e:
                print(f"Broadcast error to {addr}: {e}")

    def refresh_gui(self):
        self.gui.update_view(self.engine.players.values())

        active_status_players = [player for player in self.engine.players.values() if not getattr(player, 'has_left', False)]
        self.gui.sidebar.update_scores(active_status_players)

        if self.engine.check_game_over():
            ranking = self.engine.get_final_ranking()
            result_text = "🏁GAME OVER\n\nRanking:\n"

            rank_emojis = {
                1: "👑",
                2: "🥈",
                3: "🥉",
                4: "💩",
            }

            for rank, player in enumerate(ranking, 1):
                emoji = rank_emojis.get(rank)
                if player.alive:
                    time_str = "Still alive"
                elif isinstance(player.timestamp, datetime.datetime):
                    time_str = player.timestamp.strftime("%H:%M:%S")
                elif isinstance(player.timestamp, str):

                    time_str = player.timestamp[:8]
                else:
                    time_str = "Unknown"

                status = "Winner" if rank == 1 and player.alive else "Loser"
                result_text += (f"{emoji} {rank}. {player.name} | "
                                f"Moves: {player.moves} | "
                                f"Died at: {time_str} ({status})\n")

            self.gui.show_final_results(result_text)

    def show_results(self):
        ranking = self.engine.get_final_ranking()
        result_text = "Game OVER\n\nRanking:\n"

        for rank, player in enumerate(ranking, 1):
            status = "Winner" if rank == 1 and player.alive else "Loser"
            result_text += f"{rank}. {player.name} - {player.moves} Moves ({status})\n"

        self.gui.show_final_results(result_text)

    def handle_join_request(self, data, addr):
        name = data["name"]
        port = data["port"]
        color = data["color"]
        ip_adr = addr[0]

        # 1. validates against other players
        for player in self.engine.players.values():
            if name.lower() == player.name.lower():
                self.network.send_to(self.protocol.wrap("join_reject", {"reason": "name_taken"}), addr)
                return
            if port == player.port:
                self.network.send_to(self.protocol.wrap("join_reject", {"reason": "port_taken"}), addr)
                return
            if color == player.color:
                self.network.send_to(self.protocol.wrap("join_reject", {"reason": "color_taken"}), addr)
                return

        # 2. add player to engine
        new_player = self.engine.add_player(name, port, color, ip_adr, datetime.datetime.now())
        if not new_player:
            self.network.send_to(self.protocol.wrap("join_reject", {"reason": "game_full"}), addr)
            return

        grid = self.engine.get_grid_matrix()

        # 3. new player gets current state (Join Accept)
        # send list of all players
        all_others_data = [
            p.to_dict() for p in self.engine.players.values()
        ]
        accept_msg = self.protocol.wrap("join_accept", {
            "players": all_others_data,
            "grid": grid
        })
        self.network.send_to(accept_msg, addr)

        # 4. inform other players about new player
        join_msg = self.protocol.wrap("player_joined", {"player": new_player.to_dict()})
        # sending to all other players except ourself and the new player
        peers = [
            (p.ip_adr, p.port) for p in self.engine.players.values()
            if p.port != self.port and p.port != port and p.ip_adr
        ]
        for peer_addr in peers:
            self.network.send_to(join_msg, peer_addr)

        self.refresh_gui()

    def handle_leave(self):
        try:
            msg = self.protocol.wrap("leave", {"port": self.port})
            self.broadcast(msg)
        except:
            pass

        if hasattr(self.network, 'sock'):
            pass

        self.gui.close()

    def check_self_timeout(self):
        player = self.engine.players.get(self.port)
        if not player or not player.alive:
            return

        elapsed = (datetime.datetime.now() - self.last_own_action).total_seconds()

        if elapsed > self.timeout_limit:
            death_time = datetime.datetime.now()
            player.kill(death_time)
            msg = self.protocol.death(self.port, death_time.strftime("%H:%M:%S"))
            self.broadcast(msg)

    def stop(self):
        """end controller and release ressources."""
        self.self_check_timer.stop()
        if hasattr(self, 'network'):
            self.network.running = False
            if hasattr(self.network, 'sock'):
                self.network.sock.close()
            try:
                self.network.message_received.disconnect(self.on_network_data)
            except:
                pass
            if hasattr(self.network, 'sock'):
                self.network.sock.close()

    def convert_datetime_to_str(self, datetime_obj):
        if isinstance(datetime_obj, datetime.datetime):
            return datetime_obj.strftime("%H:%M:%S")
        return str(datetime_obj)

    def convert_str_to_datetime(self, raw_time):
        if not raw_time or not isinstance(raw_time, str):
            return datetime.datetime.now()
        try:
            return datetime.datetime.strptime(raw_time, "%H:%M:%S").replace(
                year=datetime.datetime.now().year,
                month=datetime.datetime.now().month,
                day=datetime.datetime.now().day
            )
        except (ValueError, TypeError):
            return datetime.datetime.now()
