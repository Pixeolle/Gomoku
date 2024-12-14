import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QMessageBox, QSpacerItem, QSizePolicy, QHBoxLayout, QPushButton, QStackedLayout, QStackedWidget)
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QFontDatabase
from PyQt5.QtCore import Qt, QPoint, QTimer
from board import Board
import random


class Config:
    def __init__(self):
        self.board_width = 15
        self.board_height = 15
        self.cell_size = 40
        self.grid_margin = 60
        self.window_size = (800, 800)
        self.background_color = '#c8b496'
        self.font_name = 'Bebas Neue'
        self.font_size = 20
        self.player1_color = QColor(255, 255, 255)
        self.player2_color = QColor(0, 0, 0)


class ResultWindow(QWidget):
    def __init__(self, winner, parent=None):
        super().__init__()
        self.parent = parent
        self.set_ui(winner)

    def set_ui(self, winner):
        layout = QVBoxLayout()
        title_label = QLabel("Fin de partie")
        title_label.setFont(QFont('Bebas Neue', 24))
        title_label.setAlignment(Qt.AlignCenter)
        if winner == 1:
            result_label = QLabel("Joueur 1 a gagné !")
        elif winner == -1:
            result_label = QLabel("Joueur 2 a gagné !")
        else:
            result_label = QLabel("Match nul !")

        result_label.setFont(QFont('Bebas Neue', 20))
        result_label.setAlignment(Qt.AlignCenter)

        button_layout = QHBoxLayout()
        retry_btn = QPushButton("Rejouer")
        leave_btn = QPushButton("Quitter")

        retry_btn.clicked.connect(self.retry)
        leave_btn.clicked.connect(self.leave)
        button_layout.addWidget(retry_btn)
        button_layout.addWidget(leave_btn)
        layout.addWidget(title_label)
        layout.addWidget(result_label)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def retry(self):
        if self.parent:
            self.parent.retry_game()

    def leave(self):
        if self.parent:
            self.parent.close()

class GomokuGUI(QMainWindow):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.initUI()
        self.move_history = []
        self.setWindowTitle('Gomoku Game')

    def initUI(self):
        self.resize(*self.config.window_size)
        self.board = Board(self.config.board_width, self.config.board_height)
        QFontDatabase.addApplicationFont("BebasNeue-Regular.ttf")
        self.current_player = random.randint(1, 2)

        self.central_widget = QWidget()
        self.central_widget.setStyleSheet(f'background-color: {self.config.background_color};')
        self.setCentralWidget(self.central_widget)

        self.stacked_widget = QStackedWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.addWidget(self.stacked_widget)

        self.game_widget = QWidget()
        game_layout = QVBoxLayout(self.game_widget)
        status_layout = QHBoxLayout()
        self.label = QLabel(f'Player {self.current_player}\'s turn', self)
        self.undo_button = QPushButton('Annuler')
        self.undo_button.setEnabled(False)
        self.undo_button.clicked.connect(self.undo_move)

        status_layout.addWidget(self.label)
        status_layout.addWidget(self.undo_button)

        game_layout.addLayout(status_layout)

        self.canvas = GameBoard(self.board, self, self.config)
        game_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding))
        game_layout.addWidget(self.canvas, alignment=Qt.AlignCenter)
        game_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding))
        self.stacked_widget.addWidget(self.game_widget)
        self.show()

    def resizeEvent(self, event):
        window_width = self.width()
        window_height = self.height()
        cell_size = min(window_width // (self.config.board_width + 2), window_height // (self.config.board_height + 2))
        self.config.cell_size = max(20, cell_size)
        self.config.grid_margin = max(30, cell_size)
        self.canvas.cell_size = self.config.cell_size
        self.canvas.grid_margin = self.config.grid_margin
        self.canvas.update_board_size()
        self.config.font_size = max(10, self.config.cell_size // 3)
        self.canvas.update()
        super().resizeEvent(event)

    def update_status(self, position):
        self.move_history.append(position)
        self.undo_button.setEnabled(True)
        winner = self.board.is_winning
        if winner is not None:
            QTimer.singleShot(1000, lambda: self.show_winner(winner))
            self.undo_button.setEnabled(False)
        else:
            self.current_player = 1 if self.current_player == 2 else 2
            self.label.setText(f'Player {self.current_player}\'s turn')

    def show_winner(self, winner):
        result_screen = ResultWindow(winner, self)
        self.stacked_widget.addWidget(result_screen)
        self.stacked_widget.setCurrentWidget(result_screen)

    def retry_game(self):
        self.board = Board(self.config.board_width, self.config.board_height)
        self.canvas.board = self.board
        self.move_history = []
        self.current_player = random.randint(1, 2)
        self.label.setText(f'Player {self.current_player}\'s turn')
        self.undo_button.setEnabled(False)
        self.canvas.update()
        self.stacked_widget.setCurrentWidget(self.game_widget)

    def undo_move(self):
        if not self.move_history:
            return
        try:
            last_move = self.move_history.pop()
            self.board.undo_to(last_move)
            self.current_player = 1 if self.current_player == 2 else 2
            self.label.setText(f'Player {self.current_player}\'s turn')
            if not self.move_history:
                self.undo_button.setEnabled(False)
            self.canvas.update()
        except ValueError as e:
            print(f"Erreur : {e}")



class GameBoard(QWidget):
    def __init__(self, board, parent, config):
        super().__init__(parent)
        self.board = board
        self.parent = parent
        self.config = config
        self.cell_size = config.cell_size
        self.grid_margin = config.grid_margin
        self.update_board_size()

    def update_board_size(self):
        width = self.cell_size * (self.board.width - 1) + 2 * self.grid_margin
        height = self.cell_size * (self.board.height - 1) + 2 * self.grid_margin
        self.setFixedSize(width, height)

    def resizeEvent(self, event):
        self.update_board_size()
        self.update()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        self.draw_board(qp)
        self.draw_pieces(qp)
        self.draw_labels(qp)
        qp.end()

    def draw_board(self, qp):
        qp.setPen(QPen(Qt.black, 2, Qt.SolidLine))
        for i in range(self.board.height):
            y = i * self.cell_size + self.grid_margin
            qp.drawLine(self.grid_margin, y, self.width() - self.grid_margin, y)

        for j in range(self.board.width):
            x = j * self.cell_size + self.grid_margin
            qp.drawLine(x, self.grid_margin, x, self.height() - self.grid_margin)

    def draw_labels(self, qp):
        qp.setPen(QPen(Qt.black, 1, Qt.SolidLine))
        qp.setFont(QFont(self.config.font_name, self.config.font_size))
        for i in range(self.board.height):
            letter = chr(ord('A') + i)
            y = i * self.cell_size + self.grid_margin
            qp.drawText(10, y + 5, letter)
            qp.drawText(self.width() - 20, y + 5, letter)

        for j in range(self.board.width):
            x = j * self.cell_size + self.grid_margin
            qp.drawText(x - 5, self.grid_margin - 40, str(j))
            qp.drawText(x - 5, self.height() - 10, str(j))

    def draw_pieces(self, qp):
        qp.setRenderHint(QPainter.Antialiasing)
        for i in range(self.board.height):
            for j in range(self.board.width):
                x0 = j * self.cell_size + self.grid_margin
                y0 = i * self.cell_size + self.grid_margin
                bit_position = self.board.get_x_y(self.board.position, i, j)
                if bit_position == 1:
                    qp.setBrush(self.config.player1_color)
                    qp.setPen(Qt.NoPen)
                    qp.drawEllipse(QPoint(x0, y0), self.cell_size // 2 - 5, self.cell_size // 2 - 5)
                elif self.board.get_x_y(self.board.mask, i, j) == 1:
                    qp.setBrush(self.config.player2_color)
                    qp.setPen(Qt.NoPen)
                    qp.drawEllipse(QPoint(x0, y0), self.cell_size // 2 - 5, self.cell_size // 2 - 5)
                qp.setBrush(Qt.NoBrush)

    def mousePressEvent(self, event):
        x = event.x()
        y = event.y()
        x -= self.grid_margin
        y -= self.grid_margin
        grid_x = round(x / self.cell_size)
        grid_y = round(y / self.cell_size)
        aligne_x = grid_x * self.cell_size
        aligne_y = grid_y * self.cell_size

        seuil = self.cell_size // 3
        if (abs(x - aligne_x) <= seuil and abs(y - aligne_y) <= seuil and grid_x < self.board.width and grid_y < self.board.height):
            position = chr(ord('A') + grid_y) + str(grid_x)
            try:
                self.board.play_to(self.parent.current_player, position)
                self.parent.update_status(position)
                self.update()
            except ValueError as e:
                print(f"Erreur : {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    config = Config()
    ex = GomokuGUI(config)
    sys.exit(app.exec_())