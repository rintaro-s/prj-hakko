import socket
import threading
import json
import time
import traceback
import struct
from PIL import ImageGrab
import cv2
import numpy as np
import win32gui
import win32process
import psutil
import tkinter as tk
from tkinter import ttk
import ctypes

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

HOST = '192.168.0.215'
PORT = 50000

# --- 設定項目 ---
# 透過させたい背景色（今回はグリーンバック）
BACKGROUND_COLOR = (0, 255, 0)
# 色の判定の甘さ（大きいほど、背景色に近い色を透過させる）
THRESHOLD = 1
# --- ここまで ---

selected_hwnd = None
client_socket = None
crop_offset = (0, 0)
client_area_pos = (0, 0)

def get_visible_windows():
    windows = []
    def enum_windows_proc(hwnd, lParam):
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd) != "":
            try:
                _thread_id, pid = win32process.GetWindowThreadProcessId(hwnd)
                process_name = psutil.Process(pid).name()
                title = win32gui.GetWindowText(hwnd)
                windows.append((hwnd, f"[{process_name}] {title}"))
            except (psutil.NoSuchProcess, psutil.AccessDenied): pass
        return True
    win32gui.EnumWindows(enum_windows_proc, None)
    return windows

def select_window_gui():
    global selected_hwnd
    root = tk.Tk()
    root.title("Select Window to Share")
    root.attributes('-topmost', True)
    root.geometry("500x400")
    label = tk.Label(root, text="Select the application to capture:")
    label.pack(pady=10)
    windows = get_visible_windows()
    window_list = [f"{hwnd}: {title}" for hwnd, title in windows]
    listbox = tk.Listbox(root)
    for item in window_list:
        listbox.insert(tk.END, item)
    listbox.pack(expand=True, fill=tk.BOTH, padx=10)
    def on_select():
        global selected_hwnd
        selection = listbox.get(listbox.curselection())
        selected_hwnd = int(selection.split(':')[0])
        root.destroy()
    btn = tk.Button(root, text="OK", command=on_select)
    btn.pack(pady=10)
    root.mainloop()

def recv_all(sock, length):
    data = b''
    while len(data) < length:
        more = sock.recv(length - len(data))
        if not more: raise EOFError('Socket closed')
        data += more
    return data

def handle_events():
    global client_socket, selected_hwnd, client_area_pos, crop_offset
    from pynput.mouse import Controller as MouseController, Button
    from pynput.keyboard import Controller as KeyboardController, KeyCode
    mouse = MouseController()
    keyboard = KeyboardController()
    while True:
        try:
            header_data = recv_all(client_socket, 4)
            message_length = struct.unpack('>I', header_data)[0]
            message_data = recv_all(client_socket, message_length)
            event = json.loads(message_data.decode('utf-8'))
            # --- キーボードイベント処理 ---
            if event['type'] == 'key_press':
                if event.get('text'):
                    keyboard.press(event['text'])
                else:
                    keyboard.press(KeyCode.from_vk(event['key']))
                continue
            elif event['type'] == 'key_release':
                if event.get('text'):
                    keyboard.release(event['text'])
                else:
                    keyboard.release(KeyCode.from_vk(event['key']))
                continue
            # --- マウスイベント処理 ---
            # 操作座標を計算（ウィンドウ位置＋クロップ位置＋クリック位置）
            final_x = client_area_pos[0] + crop_offset[0] + event['x']
            final_y = client_area_pos[1] + crop_offset[1] + event['y']

            if win32gui.GetForegroundWindow() != selected_hwnd:
                try:
                    win32gui.SetForegroundWindow(selected_hwnd)
                    time.sleep(0.05)
                except Exception: pass
            if event['type'] == 'mouse_move':
                mouse.position = (final_x, final_y)
            elif event['type'] == 'mouse_press':
                mouse.position = (final_x, final_y)
                button = Button.left if event['button'] == 1 else Button.right
                mouse.press(button)
            elif event['type'] == 'mouse_release':
                mouse.position = (final_x, final_y)
                button = Button.left if event['button'] == 1 else Button.right
                mouse.release(button)
        except (ConnectionResetError, BrokenPipeError, EOFError):
            print("クライアントとの接続が切れました。")
            break
        except Exception as e:
            print(f"イベント処理中に予期せぬエラーが発生しました: {e}")
            traceback.print_exc()
            break
    client_socket.close()

def stream_window():
    global client_socket, selected_hwnd, client_area_pos, crop_offset
    event_thread = threading.Thread(target=handle_events, daemon=True)
    event_thread.start()
    while event_thread.is_alive():
        try:
            if not win32gui.IsWindow(selected_hwnd): break
            client_rect = win32gui.GetClientRect(selected_hwnd)
            left, top = win32gui.ClientToScreen(selected_hwnd, (client_rect[0], client_rect[1]))
            right, bottom = win32gui.ClientToScreen(selected_hwnd, (client_rect[2], client_rect[3]))
            client_area_pos = (left, top)
            bbox = (left, top, right, bottom)

            img = ImageGrab.grab(bbox=bbox, all_screens=True)
            frame = np.array(img)
            
            # --- 高速残像処理用マスク生成（cv2.inRange + Morphology） ---
            # 背景色±しきい値でマスク作成
            lower = np.clip(np.array(BACKGROUND_COLOR, np.int16) - THRESHOLD, 0, 255).astype(np.uint8)
            upper = np.clip(np.array(BACKGROUND_COLOR, np.int16) + THRESHOLD, 0, 255).astype(np.uint8)
            mask = cv2.inRange(frame, lower, upper)
            # 小型カーネルでノイズ除去（クロージング→オープニング）
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel, iterations=1)
            # RGBA変換＆透過適用
            frame_rgba = cv2.cvtColor(frame, cv2.COLOR_RGB2RGBA)
            frame_rgba[mask==255, 3] = 0
            # キャラ領域抽出
            pts = np.argwhere(frame_rgba[..., 3]>0)
            if pts.size == 0: continue
            y_min, x_min = pts.min(axis=0)
            y_max, x_max = pts.max(axis=0)
            crop_offset = (x_min, y_min)
            cropped_frame = frame_rgba[y_min:y_max+1, x_min:x_max+1]
            # --- ここまで ---

            frame_bgra = cv2.cvtColor(cropped_frame, cv2.COLOR_RGBA2BGRA)
            result, encoded_frame = cv2.imencode('.png', frame_bgra)
            if not result: continue
            
            data = encoded_frame.tobytes()
            size = len(data)
            client_socket.sendall(str(size).encode('utf-8').ljust(16))
            client_socket.sendall(data)
            time.sleep(1/30)
        except (ConnectionResetError, BrokenPipeError):
            print("クライアントとの接続が切れました（ストリーム側）。")
            break
        except Exception:
            time.sleep(0.5)
            continue
    client_socket.close()

def main():
    global client_socket
    select_window_gui()
    if selected_hwnd is None: return
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)
    print(f"サーバーが {HOST}:{PORT} で待機中...")
    client_socket, addr = server_socket.accept()
    print(f"{addr} から接続がありました。")
    stream_thread = threading.Thread(target=stream_window)
    stream_thread.start()

if __name__ == '__main__':
    main()