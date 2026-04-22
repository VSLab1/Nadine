from PyQt5.QtWidgets import QWidget, QHBoxLayout, QMessageBox, QVBoxLayout, QPushButton
from PyQt5.QtCore import pyqtSignal, Qt
from .widgets import ConnectionWidget, BattlefieldWidget, PlayerListWidget

class GameGUI(QWidget):
    input_received = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.grid_size = 25
        self.setWindowTitle("P2P Tron")
        self.main_layout = QHBoxLayout(self)

        self.connection_ui = ConnectionWidget()
        self.battlefield = BattlefieldWidget(self.grid_size)

        self.sidebar = PlayerListWidget()

        self.main_layout.addWidget(self.connection_ui)
        self.connection_ui.start_requested.connect(self.start_game_logic)

    def start_game_logic(self, name, port, color, ip, f_port, size):
        from controller.main_controller import MainController # Local import to avoid circularity

        if size % 2 == 0:
            size += 1
            print(f"Grid-Größe angepasst auf {size} (ungerade Zahl für Symmetrie benötigt).")
        self.grid_size = size
        self.battlefield.reset_size(size)

        self.connection_ui.hide()
        self.main_layout.removeWidget(self.connection_ui)

        self.controller = MainController(
            self, port, name, color,
            target_ip=ip if ip else None,
            target_port=f_port if f_port else None,
            grid_size=size
        )

        self.sidebar_widget = QWidget()
        self.sidebar_widget.setMinimumWidth(220)
        self.sidebar_widget.setFocusPolicy(Qt.NoFocus)

        sidebar_layout = QVBoxLayout(self.sidebar_widget)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)
        sidebar_layout.setSpacing(15)

        self.sidebar.setFocusPolicy(Qt.NoFocus)
        sidebar_layout.addWidget(self.sidebar, stretch=1)

        self.leave_button = QPushButton("Leave Game")
        self.leave_button.setFocusPolicy(Qt.NoFocus)
        self.leave_button.setMinimumHeight(45)
        self.leave_button.setStyleSheet("""
            QPushButton {
                background-color: #c0392b;
                color: white;
                font-weight: bold;
                border-radius: 4px;
                border: 1px solid #a93226;
            }
            QPushButton:hover {
                background-color: #e74c3c;
            }
        """)
        self.leave_button.clicked.connect(self.controller.handle_leave)
        sidebar_layout.addWidget(self.leave_button)

        self.main_layout.addWidget(self.battlefield, stretch=5)
        self.main_layout.addWidget(self.sidebar_widget, stretch=1)

        self.resize(1000, 800)
        self.setFocus()

    def update_view(self, players):
        """delegates the drawing to specialized Widgets"""
        self.battlefield.update_grid(players)
        self.sidebar.update_scores(players)


    def keyPressEvent(self, event):
        from PyQt5.QtCore import Qt
        keys = {Qt.Key_Up: "UP", Qt.Key_Down: "DOWN", Qt.Key_Left: "LEFT", Qt.Key_Right: "RIGHT"}
        if event.key() in keys:
            self.input_received.emit(keys[event.key()])


    def show_error_and_return_to_menu(self, reason):
        """shows error message and gets back to login"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText("Beitritt abgelehnt")
        msg.setInformativeText(f"Grund: {reason}")
        msg.setWindowTitle("Fehler")
        msg.exec_()

        # set back UI
        self.battlefield.hide()
        self.sidebar.hide()
        self.main_layout.removeWidget(self.battlefield)
        self.main_layout.removeWidget(self.sidebar)

        # show old menu
        self.connection_ui.show()
        self.main_layout.addWidget(self.connection_ui)

    def show_final_results(self, text):
        msg = QMessageBox()
        msg.setWindowTitle("Game Ranking")
        msg.setText(text)
        msg.exec_()

        import sys
        sys.exit()
