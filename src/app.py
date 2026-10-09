import sys

from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow

from jarvisUI import Ui_jarvisUI

from .assistant import AssistantWorker, create_agent
from .config import asset_path
from .speech import SpeechService


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.ui = Ui_jarvisUI()
        self.ui.setupUi(self)
        self.speech_service = SpeechService()
        self.worker = AssistantWorker(create_agent(), self.speech_service)
        self.ui.pushButton.clicked.connect(self.start_task)

    def start_task(self) -> None:
        self.ui.circle_movie = QtGui.QMovie(asset_path("circle.gif"))
        self.ui.label_2.setMovie(self.ui.circle_movie)
        self.ui.circle_movie.start()
        self.ui.load_movie = QtGui.QMovie(asset_path("load.gif"))
        self.ui.label_3.setMovie(self.ui.load_movie)
        self.ui.load_movie.start()
        if not self.worker.is_alive():
            self.worker.start()


def run() -> int:
    application = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return application.exec_()