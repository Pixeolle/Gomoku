import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QMessageBox, QSpacerItem, QSizePolicy
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QFontDatabase
from PyQt5.QtCore import Qt, QPoint
from board import Board
import random

class GomokuGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Gomoku Game')
        self.resize(800, 800)
        self.board = Board(15, 15)
        QFontDatabase.addApplicationFont("BebasNeue-Regular.ttf")
        self.current_player = random.randint(1, 2)
        self.central_widget = QWidget()
        self.central_widget.setStyleSheet('background-color: #c8b496;')
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.label = QLabel(f'Player {self.current_player}\'s turn', self)
        self.layout.addWidget(self.label, alignment=Qt.AlignCenter)
        self.canvas = GameBoard(self.board, self)
        self.layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding))
        self.layout.addWidget(self.canvas, alignment=Qt.AlignCenter)
        self.layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding))
        self.show()

    def update_status(self):
        winner = self.board.is_winning
        if winner is not None:
            self.show_winner(winner)
        else:
            self.current_player = 1 if self.current_player == 2 else 2
            self.label.setText(f'Player {self.current_player}\'s turn')

    def show_winner(self, winner):
        if winner == 1:
            QMessageBox.information(self, 'Gomoku', 'Player 1 wins!')
        elif winner == -1:
            QMessageBox.information(self, 'Gomoku', 'Player 2 wins!')
        else:
            QMessageBox.information(self, 'Gomoku', 'It\'s a draw!')
        self.close()

class GameBoard(QWidget):
    def __init__(self, board, parent):
        super().__init__(parent)
        self.board = board
        self.parent = parent
        self.cell_size = 40
        self.grid_marge = 60
        self.update_board_size()

    def update_board_size(self):
        width = self.cell_size * (self.board.width - 1) + 2 * self.grid_marge
        height = self.cell_size * (self.board.height - 1) + 2 * self.grid_marge
        self.setFixedSize(width, height)

    def resizeEvent(self, event):
        self.update_board_size()
        self.update()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        #self.paint_background(qp)
        self.draw_board(qp)
        self.draw_pieces(qp)
        self.draw_labels(qp)
        qp.end()

    def paint_background(self, qp):
        qp.setBrush(QColor(200, 180, 150))
        qp.drawRect(0, 0, self.width() - 1, self.height() - 1)

    def draw_board(self, qp):
        qp.setPen(QPen(Qt.black, 2, Qt.SolidLine))
        for i in range(self.board.height):
            y = i * self.cell_size + self.grid_marge
            qp.drawLine(self.grid_marge, y, self.width() - self.grid_marge, y)

        for j in range(self.board.width):
            x = j * self.cell_size + self.grid_marge
            qp.drawLine(x, self.grid_marge, x, self.height() - self.grid_marge)

    def draw_labels(self, qp):
        qp.setPen(QPen(Qt.black, 1, Qt.SolidLine))
        qp.setFont(QFont('Bebas Neue', 15))
        for i in range(self.board.height):
            letter = chr(ord('A') + i)
            y = i * self.cell_size + self.grid_marge
            qp.drawText(20, y + 5, letter)
            qp.drawText(self.width() - 30, y + 5, letter)

        for j in range(self.board.width):
            x = j * self.cell_size + self.grid_marge
            qp.drawText(x - 5, self.grid_marge - 25, str(j))
            qp.drawText(x - 5, self.height() - 25, str(j))

    def draw_pieces(self, qp):
        qp.setRenderHint(QPainter.Antialiasing)
        for i in range(self.board.height):
            for j in range(self.board.width):
                x0 = j * self.cell_size + self.grid_marge
                y0 = i * self.cell_size + self.grid_marge
                bit_position = self.board.get_x_y(self.board.position, i, j)
                if bit_position == 1:
                    qp.setBrush(QColor(255, 255, 255))
                    qp.setPen(Qt.NoPen)
                    qp.drawEllipse(QPoint(x0, y0), self.cell_size // 2 - 5, self.cell_size // 2 - 5)
                elif self.board.get_x_y(self.board.mask, i, j) == 1:
                    qp.setBrush(QColor(0, 0, 0))
                    qp.setPen(Qt.NoPen)
                    qp.drawEllipse(QPoint(x0, y0), self.cell_size // 2 - 5, self.cell_size // 2 - 5)
                qp.setBrush(Qt.NoBrush)

    def mousePressEvent(self, event):
        x = event.x()
        y = event.y()
        x -= self.grid_marge
        y -= self.grid_marge
        grid_x = round(x / self.cell_size)
        grid_y = round(y / self.cell_size)
        aligne_x = grid_x * self.cell_size
        aligne_y = grid_y * self.cell_size

        seuil = self.cell_size // 4
        if (abs(x - aligne_x) <= seuil and abs(y - aligne_y) <= seuil and grid_x < self.board.width and grid_y < self.board.height):
            position = chr(ord('A') + grid_y) + str(grid_x)
            try:
                self.board.play_to(self.parent.current_player, position)
                self.parent.update_status()
                self.update()
            except ValueError as e:
                print(f"Erreur : {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = GomokuGUI()
    sys.exit(app.exec_())