from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QFrame, QListWidget, QListWidgetItem, QFormLayout, QLineEdit, \
    QPushButton, QColorDialog, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QBrush

class BattlefieldWidget(QFrame):
    def __init__(self, size=25):
        super().__init__()
        self.grid_size = size
        self.cells = {}

        # Optik des Frames
        self.setFocusPolicy(Qt.NoFocus)
        self.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.setLineWidth(2)
        self.leave_button = QPushButton("Leave Game")
        self.setMinimumSize(100, 100)

        self.init_ui()

    def init_ui(self):
        layout = QGridLayout(self)
        layout.setSpacing(1)
        layout.setContentsMargins(0, 0, 0, 0)

        for row in range(self.grid_size):
            for col in range(self.grid_size):
                cell = QLabel()
                cell.setMinimumSize(1, 1)
                cell.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                cell.setStyleSheet("background-color: #ffffff; border: 1px solid #f0f0f0;")
                cell.setAlignment(Qt.AlignCenter)
                layout.addWidget(cell, row, col)
                self.cells[(col, row)] = cell

        for i in range(self.grid_size):
            layout.setColumnStretch(i, 1)
            layout.setRowStretch(i, 1)

        self.setLayout(layout)

    def update_grid(self, players):
        """
        Zentrale Methode: Nimmt eine Liste/Dict von Spielern
        und färbt das Gitter entsprechend ein.
        """
        # 1. Alles auf Weiß zurücksetzen
        for cell in self.cells.values():
            cell.setStyleSheet("background-color: #ffffff; border: 1px solid #f0f0f0;")

        # 2. Trails und Köpfe zeichnen
        for player in players:
            # Trail zeichnen (etwas blasser)
            for (tx, ty) in player.trail:
                if (tx, ty) in self.cells:
                    self.cells[(tx, ty)].setStyleSheet(f"background-color: {player.color}; border: 1px solid {player.color};")

            if not getattr(player, 'has_left', False):
                if (player.x, player.y) in self.cells:
                    head_style = "background-color: black;" if player.alive else "background-color: darkred;"
                    self.cells[(player.x, player.y)].setStyleSheet(f"{head_style} border: 1px solid black;")

    def clear(self):
        """clear grid"""
        for cell in self.cells.values():
            cell.setStyleSheet("background-color: white; border: 1px solid #eee;")

    # In gui/widgets.py -> BattlefieldWidget

    def reset_size(self, new_size):
        """deletes old grid and builds new one with desired lengths"""
        self.grid_size = new_size

        # delete old layout
        if self.layout() is not None:
            while self.layout().count():
                item = self.layout().takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
            import sip
            sip.delete(self.layout())

        self.cells = {}
        self.init_ui()


class PlayerListWidget(QListWidget):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(200)
        self.setStyleSheet("""
            QListWidget { 
                background-color: #f8f9fa; 
                border: 1px solid #ddd;
                border-radius: 5px;
            }
        """)

    def update_scores(self, players):
        """Aktualisiert die Liste basierend auf der aktuellen Spielerliste"""
        self.clear()

        # Sortieren: Lebende Spieler zuerst, dann nach Moves
        sorted_players = sorted(players, key=lambda p: (not p.alive, -p.moves))

        for p in sorted_players:
            status_icon = "🟢" if p.alive else "💀"
            item_text = f"{status_icon} {p.name}\nMoves: {p.moves}"

            item = QListWidgetItem(item_text)

            color = QColor(p.color)

            item.setForeground(QBrush(color))
            self.addItem(item)



class ConnectionWidget(QFrame):
    start_requested = pyqtSignal(str, int, str, str, str, int)

    def __init__(self):
        super().__init__()
        self.selected_color = "#ff0000"
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout(self)

        self.name_input = QLineEdit("Player1")
        self.port_input = QLineEdit("5005")

        self.color_btn = QPushButton("Pick Color")
        self.color_btn.setStyleSheet(f"background-color: {self.selected_color}")
        self.color_btn.clicked.connect(self.pick_color)

        # Modus A: Host (start game)
        self.size_input = QLineEdit("25")
        self.host_btn = QPushButton("Start")
        self.host_btn.clicked.connect(self.on_host)

        # Modus B: Client (join)
        self.ip_input = QLineEdit("127.0.0.1")
        self.f_port_input = QLineEdit("5005")
        self.join_btn = QPushButton("join Game")
        self.join_btn.clicked.connect(self.on_join)

        layout.addRow("--- Profil ---", None)
        layout.addRow("Nickname:", self.name_input)
        layout.addRow("Your Port:", self.port_input)
        layout.addRow("Trail Color:", self.color_btn)
        layout.addRow("--- Host-Options ---", None)
        layout.addRow("Grid size:", self.size_input)
        layout.addRow(self.host_btn)
        layout.addRow("--- Join-Options ---", None)
        layout.addRow("Friend IP:", self.ip_input)
        layout.addRow("Friend Port:", self.f_port_input)
        layout.addRow(self.join_btn)

    def on_host(self):
        try:
            size = int(self.size_input.text())
        except ValueError:
            size = 25 # Fallback
        self.emit_start(target_ip=None, target_port=None, size=size)

    def on_join(self):
        self.emit_start(self.ip_input.text(), self.f_port_input.text(), size=25)

    def emit_start(self, target_ip, target_port, size):
        self.start_requested.emit(
            self.name_input.text(),
            int(self.port_input.text()),
            self.selected_color,
            target_ip,
            target_port,
            size
        )

    def pick_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.selected_color = color.name()
            self.color_btn.setStyleSheet(f"background-color: {self.selected_color}")

    def on_submit(self):
        # Daten validieren und Signal an Controller senden
        try:
            name = self.name_input.text()
            port = int(self.port_input.text())
            color = self.selected_color
            f_ip = self.ip_input.text()
            f_port = self.friend_port_input.text()

            self.start_requested.emit(name, port, color, f_ip, f_port)
        except ValueError:
            print("Invalid Port Input")