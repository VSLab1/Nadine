import datetime
import logging

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QGridLayout, QLineEdit,
    QStackedLayout, QFormLayout, QScrollArea, QColorDialog,
    QMessageBox
)

from game.game import GameState
from network.network import Network
import network.messages as msg


class GameGUI(QWidget):
    network_event_signal = pyqtSignal(str, dict, tuple)

    def __init__(self):
        super().__init__()
        self.network = None
        self.network_event_signal.connect(self.on_network_event)
        self.my_port = None
        self.game_state = None
        self.logger = logging.getLogger(__name__)
        self.setWindowTitle("P2P Grid Game GUI")
        self.setGeometry(100, 100, 900, 700)
        self.setFocusPolicy(Qt.StrongFocus)

        self.grid_size = 25
        self.cells = {}
        self.zoom_factor = 1.0
        self.selected_color = "red"

        self.init_ui()

        self.logger.debug(f"game ui instance was created")

    def init_ui(self):
        self.main_layout = QVBoxLayout()
        self.stacked_layout = QStackedLayout()

        # === START SCREEN ===
        self.start_widget = QWidget()
        start_layout = QFormLayout()

        self.name_input = QLineEdit()
        self.port_input = QLineEdit()
        self.size_input = QLineEdit()

        self.color_button = QPushButton("Choose Color")
        self.color_button.clicked.connect(self.pick_color)

        self.join_button = QPushButton("Join Game")

        self.host_button = QPushButton("Start New Game")

        self.host_button.clicked.connect(self.start_game)
        self.join_button.clicked.connect(self.join_game)

        start_layout.addRow("Nickname:", self.name_input)
        start_layout.addRow("Port:", self.port_input)
        start_layout.addRow("Color:", self.color_button)

        self.friend_ip = QLineEdit()
        self.friend_port = QLineEdit()
        start_layout.addRow("Friend IP:", self.friend_ip)
        start_layout.addRow("Friend Port:", self.friend_port)
        start_layout.addRow(self.join_button)

        start_layout.addRow("Grid Size:", self.size_input)
        start_layout.addRow(self.host_button)

        self.start_widget.setLayout(start_layout)

        # === GAME SCREEN ===
        self.game_widget = QWidget()
        game_layout = QHBoxLayout()

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(1)
        self.grid_container.setLayout(self.grid_layout)

        self.status_panel = QLabel()
        self.status_panel.setAlignment(Qt.AlignTop)
        self.status_panel.setFixedWidth(250)

        #leave button
        self.leave_button = QPushButton("Leave Game")
        self.leave_button.clicked.connect(self.leave_game)

        self.right_panel = QVBoxLayout()
        self.right_panel.addWidget(self.status_panel)
        self.right_panel.addStretch()
        self.right_panel.addWidget(self.leave_button)

        game_layout.addWidget(self.grid_container, stretch=1)
        game_layout.addWidget(self.status_panel)

        self.game_widget.setLayout(game_layout)

        self.stacked_layout.addWidget(self.start_widget)
        self.stacked_layout.addWidget(self.game_widget)

        self.main_layout.addLayout(self.stacked_layout)
        self.setLayout(self.main_layout)
        self.logger.debug(f"ui was initialised")

    def pick_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.selected_color = color.name()
            self.color_button.setStyleSheet(f"background-color: {self.selected_color};")

    def start_game(self):
        try:
            input_text = self.size_input.text()
            if input_text:
                size = int(input_text)
            else:
                size = 25
        except ValueError:
            size = 25

        if size % 2 == 0:
            size += 1
            self.logger.info(f"Grid size was even, adjusted to odd: {size}")

        self.grid_size = int(size)

        try:
            self.my_port = int(self.port_input.text())
        except ValueError:
            self.logger.error("Invalid port input")
            return

        self.logger.info(f"Starting game with player '{self.name_input.text()}' on port {self.my_port}")

        self.grid_size = size
        self.build_grid()
        self.game_state = GameState(self.grid_size)
        self.network = Network(self.my_port, self.emit_network_event)

        self.game_state.add_player(
            self.name_input.text(),
            self.my_port,
            self.selected_color,
            "127.0.0.1",
            datetime.datetime.now()
        )

        self.logger.info(
            f"new player = name: '{self.name_input.text()}'; port: '{self.my_port}'; color: '{self.selected_color}', ip_adr: '{self.friend_ip}'")

        self.timer = QTimer()
        self.timer.timeout.connect(self.game_loop)
        self.timer.start(500)

        self.render_players()
        self.update_status()
        self.stacked_layout.setCurrentWidget(self.game_widget)

        self.setFocus()

    def on_network_event(self, msg_type, data, addr):
        if msg_type == "join_request":
            self.handle_join_request(data, addr)
            return

        if msg_type == "join_accept":
            self.handle_join_accept(data)
            self.logger.debug("data in on_network_event: ", data)
            return

        if msg_type == "join_reject":
            reason = data.get("reason", "unknown")
            QMessageBox.warning(self, "Join rejected", f"Reason: {reason}")
            return

        if msg_type == "player_joined":
            self.logger.info("player_joined add peer")

        if msg_type == "leave":
            port = data["port"]
            self.game_state.remove_player(port)
            self.render_players()
            self.update_status()
            return

        if self.game_state is None:
            print("Ignoring event, game_state not ready:", msg_type)
            return

        if "port" in data and data["port"] == self.my_port:
            return

        self.game_state.handle_remote_event(msg_type, data, addr)

        self.render_players()
        self.update_status()

    def game_loop(self):
        logging.info(("in game loop"))
        died = self.game_state.timeout(self.my_port)
        if died:
            self.network.send_broadcast(
                msg.create_player_died(self.my_port, datetime.datetime.now()),
                self.game_state.get_network_peers(self.my_port)
            )

        self.render_players()
        self.update_status()

        alive_players = self.game_state.get_alive_players()

        if len(self.game_state.players) >= 2 and len(alive_players) <= 1:
            self.handle_game_over(alive_players)

    def build_grid(self):
        self.logger.debug(f"building grid")
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)

        self.cells.clear()

        base_size = max(5, int(20 * self.zoom_factor))

        for row in range(self.grid_size):
            for col in range(self.grid_size):
                cell = QLabel()
                cell.setFixedSize(base_size, base_size)
                cell.setStyleSheet("background-color: white; border: 1px solid lightgray;")
                self.grid_layout.addWidget(cell, row, col)
                self.cells[(row, col)] = cell
        self.logger.debug(f"building grid successful")

    def clear_grid(self):
        for cell in self.cells.values():
            cell.setStyleSheet("background-color: white; border: 1px solid lightgray;")

    def render_players(self):
        self.logger.debug(f"rendering players")
        if not hasattr(self, "game_state") or not self.game_state:
            return
        self.clear_grid()

        for player in self.game_state.players.values():
            color = player.color

            # Trail
            for (x, y) in player.trail:
                if (y, x) in self.cells:
                    self.cells[(y, x)].setStyleSheet(f"background-color: {color};")

            # Head
            if player.alive:
                if (player.y, player.x) in self.cells:
                    self.cells[(player.y, player.x)].setStyleSheet("background-color: black;")
            else:
                #dead head deep dark red
                if (player.y, player.x) in self.cells:
                    self.cells[(player.y, player.x)].setStyleSheet(
                        "background-color: darkred; border: 1px solid black;")

        self.logger.debug(f"rendering players successful")

    def update_status(self):
        self.logger.debug(f"updating status")
        text = "Players:\n"
        for player in self.game_state.players.values():
            ts = player.timestamp if player.timestamp else "---"
            text += f"{player.name} | Moves: {player.moves} | Time: {ts}\n"
        self.status_panel.setText(text)
        self.logger.debug(f"updating status successful")

    def handle_input(self, direction):
        self.logger.debug(f"Input received: {direction}")
        dx, dy = 0, 0
        if direction == "UP":
            dy = -1
        elif direction == "DOWN":
            dy = 1
        elif direction == "LEFT":
            dx = -1
        elif direction == "RIGHT":
            dx = 1

        player = self.game_state.players.get(self.my_port)
        if not player or not player.alive:
            return
        new_x = player.x + dx
        new_y = player.y + dy

        result = self.game_state.handle_local_move(self.my_port, new_x, new_y)

        if not result:
            return

        if result["type"] == "move":
            self.network.send_broadcast(
                msg.create_move(self.my_port, result["x"], result["y"]),
                self.game_state.get_network_peers(self.my_port)
            )
        elif result["type"] == "dead":
            self.network.send_broadcast(
                msg.create_player_died(self.my_port, result["timestamp"]),
                self.game_state.get_network_peers(self.my_port)
            )
        elif result["type"] == "double_dead":
            self.network.send_broadcast(
                msg.create_player_died(result["p1"], result["timestamp"]),
                self.game_state.get_network_peers(self.my_port)
            )
            self.network.send_broadcast(
                msg.create_player_died(result["p2"], result["timestamp"]),
                self.game_state.get_network_peers(self.my_port)
            )

        self.render_players()
        self.update_status()

    def keyPressEvent(self, event):
        if event.isAutoRepeat():
            return

        if self.stacked_layout.currentWidget() != self.game_widget:
            return

        key = event.key()

        if key == Qt.Key_Up:
            self.handle_input("UP")
        elif key == Qt.Key_Down:
            self.handle_input("DOWN")
        elif key == Qt.Key_Left:
            self.handle_input("LEFT")
        elif key == Qt.Key_Right:
            self.handle_input("RIGHT")


    def join_game(self):
        try:
            self.my_port = int(self.port_input.text())
            self.network = Network(self.my_port, self.emit_network_event)

            ip = self.friend_ip.text()
            friend_port = int(self.friend_port.text())
            message = msg.create_join_request(
                self.name_input.text(),
                self.selected_color,
                self.my_port
            )
            self.network.send_to(message, (ip, friend_port))
        except OSError as e:
            QMessageBox.critical(self, "Network error", str(e))
            self.network = None
        except ValueError:
            QMessageBox.warning(self, "input error", "Port and friend port have to be numbers!")
            return

    def handle_join_request(self, data, addr):
        name = data["name"]
        port = data["port"]
        color = data["color"]
        ip_adr = addr[0]

        for player in self.game_state.players.values():
            if name.lower() == player.name.lower():
                self.logger.warning(f"Rejecting join: Name '{name}' taken")
                self.network.send_to(
                    msg.create_join_reject(msg.RejectReason.NAME_TAKEN),
                    addr
                )
                return
            elif port == player.port:
                self.network.send_to(
                    msg.create_join_reject(msg.RejectReason.PORT_TAKEN),
                    addr
                )
                return
            elif color == player.color:
                self.network.send_to(
                    msg.create_join_reject(msg.RejectReason.COLOR_TAKEN),
                    addr
                )
                return

        player = self.game_state.add_player(name, port, color, ip_adr, datetime.datetime.now())

        snapshot = self.game_state.to_dict()
        self.network.send_to(msg.create_join_accept(snapshot["players"], snapshot["grid"]), addr)

        recipients = self.game_state.get_network_peers(exclude_ports=[self.my_port, port])
        self.network.send_broadcast(
            msg.create_player_joined(
                player.to_dict()
            ),
            recipients
        )

    def handle_join_accept(self, data):
        self.logger.info(f"Received join_accept with grid data")

        # Grid-Größe aus der Matrix berechnen
        grid_matrix = data.get("grid", [])
        if not grid_matrix:
            self.grid_size = 25 # Fallback
        else:
            self.grid_size = int(len(grid_matrix))

        self.build_grid()
        self.game_state = GameState(self.grid_size)

        for p in data["players"]:
            player = self.game_state.add_player(
                name=p["name"],
                port=p["port"],
                color=p["color"],
                ip_adr=p["ip_adr"],
                timestamp=["timestamp"],
                trail=[tuple(pos) for pos in p["trail"]],
                x=p["x"],
                y=p["y"]
            )
            player.alive = p["alive"]

        self.stacked_layout.setCurrentWidget(self.game_widget)
        self.render_players()
        self.update_status()

    def emit_network_event(self, msg_type, data, addr):
        self.network_event_signal.emit(msg_type, data, addr)

    def leave_game(self):
        if self.network and self.game_state:
            recipients = self.game_state.get_network_peers(exclude_port=self.my_port)
            leave_msg = msg.create_player_leave(self.my_port)
            self.network.send_broadcast(leave_msg, recipients)

        self.close()

    def handle_game_over(self, alive_players):
        if hasattr(self, "game_over") and self.game_over:
            return

        self.game_over = True

        ranking = self.game_state.get_ranking()

        text = "🏆 Ranking:\n\n"

        for i, player in enumerate(ranking, start=1):
            if i == 1:
                if player.alive:
                    text += f"🥇 {player.name} | Moves: {player.moves} | WINNER\n"
                else:
                    text += f"🥇 {player.name} | Moves: {player.moves} | Last survivor\n"
            elif i == 2:
                ts = player.timestamp.strftime("%H:%M:%S") if player.timestamp else "---"
                text += f"🥈 {player.name} | Moves: {player.moves} | Died at: {ts}\n"
            elif i == 3:
                ts = player.timestamp.strftime("%H:%M:%S") if player.timestamp else "---"
                text += f"🥉 {player.name} | Moves: {player.moves} | Died at: {ts}\n"
            else:
                ts = player.timestamp.strftime("%H:%M:%S") if player.timestamp else "---"
                text += f"💩 {player.name} | Moves: {player.moves} | Died at: {ts}\n"

        QMessageBox.information(self, "Game Over", text)
        self.close()

