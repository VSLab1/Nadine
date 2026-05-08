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

        try:
            new_controller = MainController(
                self, port, name, color,
                target_ip=ip if ip else None,
                target_port=f_port if f_port else None,
                grid_size=size
            )
            if not hasattr(new_controller, 'engine') or new_controller.network is None:
                return
            self.controller = new_controller

        except OSError as e:
            print(f"DEBUG: Port Fehler abgefangen: {e}")
            self.show_error_and_return_to_menu("port_taken_locally")
            return
        except Exception as e:
            print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
            return

        self.connection_ui.hide()
        self.main_layout.removeWidget(self.connection_ui)

        if not hasattr(self, 'battlefield') or self.battlefield is None:
            from .widgets import BattlefieldWidget
            self.battlefield = BattlefieldWidget(size)
        else:
            self.battlefield.reset_size(size)

        self.battlefield.show()

        if not hasattr(self, 'sidebar') or self.sidebar is None:
            from .widgets import PlayerListWidget
            self.sidebar = PlayerListWidget()

        if not hasattr(self, 'sidebar_widget') or self.sidebar_widget is None:
            from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton
            from PyQt5.QtCore import Qt

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
                    background-color: #c0392b; color: white; font-weight: bold;
                    border-radius: 4px; border: 1px solid #a93226;
                }
                QPushButton:hover { background-color: #e74c3c; }
            """)
            self.leave_button.clicked.connect(self.controller.handle_leave)
            sidebar_layout.addWidget(self.leave_button)
        else:
            try:
                self.leave_button.clicked.disconnect()
            except: pass
            self.leave_button.clicked.connect(self.controller.handle_leave)

        self.sidebar_widget.show()
        if self.main_layout.indexOf(self.battlefield) == -1:
            self.main_layout.addWidget(self.battlefield, stretch=5)
        if self.main_layout.indexOf(self.sidebar_widget) == -1:
            self.main_layout.addWidget(self.sidebar_widget, stretch=1)

        self.controller.refresh_gui()
        self.resize(1000, 800)
        self.setFocus()

    def update_view(self, players):
        """delegates the drawing to specialized Widgets"""
        if self.battlefield and self.sidebar:
            try:
                self.battlefield.update_grid(players)
                self.sidebar.update_scores(players)
            except RuntimeError:
                pass


    def keyPressEvent(self, event):
        from PyQt5.QtCore import Qt
        keys = {Qt.Key_Up: "UP", Qt.Key_Down: "DOWN", Qt.Key_Left: "LEFT", Qt.Key_Right: "RIGHT"}
        if event.key() in keys:
            self.input_received.emit(keys[event.key()])


    def show_error_and_return_to_menu(self, reason):
        """shows error message and gets back to login"""
        if hasattr(self, 'controller') and self.controller:
            self.controller.stop()
            self.controller = None
        if hasattr(self, 'battlefield') and self.battlefield:
            self.battlefield.hide()
        if hasattr(self, 'sidebar_widget') and self.sidebar_widget:
            self.sidebar_widget.hide()

        reasons = {
            "name_taken": "Dieser Name ist bereits vergeben.",
            "port_taken": "Dieser Port wird bereits vom Host genutzt.",
            "port_taken_locally": "Dein gewählter Port ist auf deinem PC bereits belegt.",
            "color_taken": "Diese Farbe wird bereits verwendet.",
            "game_full": "Das Spiel ist leider voll."
        }

        text = reasons.get(reason, f"Unbekannter Fehler: {reason}")

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText("Verbindung fehlgeschlagen")
        msg.setInformativeText(text)
        msg.setWindowTitle("Fehler")
        msg.exec_()

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
