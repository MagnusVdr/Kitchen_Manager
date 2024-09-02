import sys
import socket
import json
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSplitter, QScrollArea
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QFont, QImage, QPainter, QColor
import os
import signal

os.environ['DISPLAY'] = ':0'


class CustomerDisplay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Customer View")
        self.background = None
        self.scaled_background = None
        self.load_background()
        self.active_orders = []
        self.completed_orders = []
        self.init_ui()
        self.server_socket = None
        self.start_server()
        self.setCursor(Qt.BlankCursor)
        self.showFullScreen()

    def load_background(self):
        background_path = "Tellimuse_ekraani_taust.jpg"  # Make sure this file exists in the same directory
        self.background = QImage(background_path)
        if self.background.isNull():
            print(f"Failed to load background image: {background_path}")

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create splitter
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setStyleSheet("QSplitter::handle { background-color: rgba(50, 50, 50, 50); }")
        main_layout.addWidget(self.splitter)

        # Create active orders widget
        self.active_widget = QWidget()
        self.active_widget.setAttribute(Qt.WA_TranslucentBackground)
        self.active_layout = QVBoxLayout(self.active_widget)
        self.active_layout.setAlignment(Qt.AlignTop)
        self.active_layout.setSpacing(10)
        self.splitter.addWidget(self.active_widget)

        # Create completed orders widget
        self.completed_widget = QWidget()
        self.completed_widget.setAttribute(Qt.WA_TranslucentBackground)
        self.completed_layout = QVBoxLayout(self.completed_widget)
        self.completed_layout.setAlignment(Qt.AlignTop)
        self.completed_layout.setSpacing(10)
        self.splitter.addWidget(self.completed_widget)

        # Set initial sizes
        self.splitter.setSizes([self.width() // 2, self.width() // 2])

        # Create header labels
        self.active_header = self.create_header_label("Küpseb")
        self.completed_header = self.create_header_label("Valmis")

        # Add headers to layouts
        self.active_layout.addWidget(self.active_header)
        self.completed_layout.addWidget(self.completed_header)

        # Create scroll areas for orders
        self.active_scroll = self.create_scroll_area()
        self.completed_scroll = self.create_scroll_area()

        self.active_layout.addWidget(self.active_scroll)
        self.completed_layout.addWidget(self.completed_scroll)

    def create_header_label(self, text):
        label = QLabel(text)
        label.setFont(QFont("Bebas neue", 150, QFont.Bold))
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: white; background-color: rgba(0, 0, 0, 100); border-radius: 10px; padding: 5px;")
        label.setFixedHeight(200)
        return label

    def paintEvent(self, event):
        painter = QPainter(self)
        if not self.background.isNull():
            if self.scaled_background is None or self.scaled_background.size() != self.size():
                self.scale_background()
            painter.drawImage(self.rect(), self.scaled_background)
        else:
            painter.fillRect(self.rect(), QColor(200, 200, 200))  # Light gray background

    def create_scroll_area(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setAlignment(Qt.AlignTop)
        scroll_layout.setSpacing(5)
        scroll.setWidget(scroll_content)
        return scroll

    def scale_background(self):
        if not self.background.isNull():
            self.scaled_background = self.background.scaled(
                self.size(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )

    def update_display(self):
        self.update_orders(self.active_scroll, self.active_orders)
        self.update_orders(self.completed_scroll, self.completed_orders)

    def update_orders(self, scroll_area, numbers):
        scroll_content = scroll_area.widget()
        layout = scroll_content.layout()

        self.clear_layout(layout)

        h_layout = QHBoxLayout()
        layout.addLayout(h_layout)

        left_column = QVBoxLayout()
        middle_column = QVBoxLayout()
        right_column = QVBoxLayout()
        h_layout.addLayout(left_column)
        h_layout.addLayout(middle_column)
        h_layout.addLayout(right_column)

        for i, number in enumerate(numbers):
            order_widget = self.create_order_widget(number)
            if i < 5:
                left_column.addWidget(order_widget)
            elif i < 10:
                middle_column.addWidget(order_widget)
            elif i < 15:
                right_column.addWidget(order_widget)

        left_column.addStretch(1)
        middle_column.addStretch(1)
        right_column.addStretch(1)

    def create_order_widget(self, order_number):
        order_widget = QFrame()
        order_widget.setStyleSheet("background-color: rgba(255, 255, 255, 200); border-radius: 10px; padding: 2px;")
        order_layout = QVBoxLayout(order_widget)
        order_layout.setContentsMargins(10, 10, 10, 10)
        order_label = QLabel(f"{str(order_number).zfill(3)}")
        order_label.setFont(QFont("Bebas neue", 100))
        order_label.setAlignment(Qt.AlignCenter)
        order_layout.addWidget(order_label)
        order_widget.setFixedHeight(160)  # Set a fixed height for consistency
        return order_widget

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
                    widget.deleteLater()
                else:
                    self.clear_layout(item.layout())

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('0.0.0.0', 5000))  # Listen on all available interfaces
        self.server_socket.listen(1)
        self.server_socket.setblocking(False)

        # Use QTimer to periodically check for incoming connections
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_for_connection)
        self.timer.start(100)  # Check every 100 ms

    def check_for_connection(self):
        try:
            client_socket, address = self.server_socket.accept()
            data = client_socket.recv(1024)

            if data == b'ping':
                client_socket.sendall(b'pong')
            else:
                try:
                    orders_data = json.loads(data.decode())
                    self.active_orders = orders_data['active_orders']
                    self.completed_orders = orders_data['completed_orders']
                    self.update_display()
                except json.JSONDecodeError:
                    print(f"Received invalid JSON data: {data}")

            client_socket.close()
        except BlockingIOError:
            pass  # No incoming connection, just continue
        except Exception as e:
            print(f"Error in check_for_connection: {e}")

    def cleanup(self):
        print("Cleaning up...")
        if self.server_socket:
            self.server_socket.close()
        self.close()
        QApplication.quit()


def signal_handler(signum, frame):
    print("Ctrl+C received. Initiating cleanup...")
    window.cleanup()
    sys.exit(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CustomerDisplay()

    signal.signal(signal.SIGINT, signal_handler)

    timer = QTimer()
    timer.start(500)  # 500ms
    timer.timeout.connect(lambda: None)

    window.show()
    window.update_display()
    sys.exit(app.exec_())