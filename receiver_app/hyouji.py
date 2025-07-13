# hyouji.py (ドラッグ＆Ctrl+C修正版)

import sys
import socket
import threading
import json
import struct
import signal # Ctrl+Cで止めるために追加
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QPixmap, QImage, QPainter
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPoint

HOST = '192.168.0.215'
PORT = 50000

class StreamReceiverThread(QThread):
    new_image = pyqtSignal(bytes)
    disconnected = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.is_running = True

    def run(self):
        try:
            self.sock.connect((HOST, PORT))
            print(f"サーバー {HOST}:{PORT} に接続しました。")
            print("Ctrl+C でプログラムを終了できます。")
        except:
            print(f"接続に失敗しました。サーバーが起動しているか確認してください。")
            self.disconnected.emit()
            return
        while self.is_running:
            try:
                size_data = self.sock.recv(16)
                if not size_data: break
                size = int(size_data.decode('utf-8').strip())
                img_data = b""
                while len(img_data) < size:
                    chunk = self.sock.recv(size - len(img_data))
                    if not chunk: break
                    img_data += chunk
                if not self.is_running: break
                self.new_image.emit(img_data)
            except:
                break
        self.is_running = False
        self.sock.close()
        self.disconnected.emit()

    def stop(self):
        self.is_running = False
        self.sock.close()

class AppWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.current_pixmap = QPixmap()
        self.drag_offset = QPoint()
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # キーボード入力を拾う
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.move(120, 0)
        
        self.thread = StreamReceiverThread()
        self.thread.new_image.connect(self.update_image)
        self.thread.disconnected.connect(self.close)
        self.thread.start()

    def update_image(self, img_data):
        image = QImage()
        image.loadFromData(img_data, "PNG")
        if image.isNull(): return
        
        pixmap = QPixmap.fromImage(image)
        self.current_pixmap = pixmap
        
        self.setFixedSize(pixmap.size())
        self.setMask(pixmap.mask())
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        # 背景を透明で塗りつぶして残像を防止
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        # 画像を上書き合成で描画
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        if not self.current_pixmap.isNull():
            painter.drawPixmap(0, 0, self.current_pixmap)
            
    def send_event(self, event_data):
        try:
            message = json.dumps(event_data).encode('utf-8')
            header = struct.pack('>I', len(message))
            self.thread.sock.sendall(header + message)
        except:
            pass

    # --- ここからがドラッグ操作の修正部分 ---
    def mousePressEvent(self, event):
        # 左クリックで掴んだ時だけ、ドラッグの準備をする
        if event.button() == Qt.MouseButton.LeftButton:
            # ウィンドウの左上からクリックした位置までの差を覚えておく
            self.drag_offset = event.globalPosition().toPoint() - self.pos()
        
        pos = event.position()
        button_map = {Qt.MouseButton.LeftButton: 1, Qt.MouseButton.RightButton: 2}
        button = button_map.get(event.button(), 1)
        event_data = {'type': 'mouse_press', 'button': button, 'x': int(pos.x()), 'y': int(pos.y())}
        self.send_event(event_data)

    def mouseMoveEvent(self, event):
        # 左ボタンが押されている間（ドラッグ中）
        if event.buttons() & Qt.MouseButton.LeftButton:
            # マウスの現在地から、さっき覚えた差を引いて、ウィンドウを動かす
            self.move(event.globalPosition().toPoint() - self.drag_offset)
        else:
            pos = event.position()
            event_data = {'type': 'mouse_move', 'x': int(pos.x()), 'y': int(pos.y())}
            self.send_event(event_data)
    # --- ここまで ---

    def mouseReleaseEvent(self, event):
        pos = event.position()
        button_map = {Qt.MouseButton.LeftButton: 1, Qt.MouseButton.RightButton: 2}
        button = button_map.get(event.button(), 1)
        event_data = {'type': 'mouse_release', 'button': button, 'x': int(pos.x()), 'y': int(pos.y())}
        self.send_event(event_data)

    # キー押下をサーバーに送信
    def keyPressEvent(self, event):
        text = event.text()
        event_data = {
            'type': 'key_press',
            'text': text,
            'key': event.key()
        }
        self.send_event(event_data)

    # キー解放をサーバーに送信
    def keyReleaseEvent(self, event):
        text = event.text()
        event_data = {
            'type': 'key_release',
            'text': text,
            'key': event.key()
        }
        self.send_event(event_data)

    def closeEvent(self, event):
        self.thread.stop()
        self.thread.wait()
        super().closeEvent(event)

if __name__ == '__main__':
    # --- ここからがCtrl+Cで止めるための修正部分 ---
    # Ctrl+Cを受け取ったら、アプリを終了するように設定
    signal.signal(signal.SIGINT, lambda *args: QApplication.instance().quit())
    # --- ここまで ---

    app = QApplication(sys.argv)
    
    window = AppWindow()
    window.show()
    
    sys.exit(app.exec())