import logging
import sys
from PyQt5.QtWidgets import QApplication
from gui.gui import GameGUI

def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%H:%M:%S"
    )

def main():
    setup_logging()
    app = QApplication(sys.argv)
    gui = GameGUI()
    gui.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
