import os
from pathlib import Path
import PySimpleGUI as sg

from image_utils import create_label_image, detect_label_color
from ocr_utils import ocr_image
from config import PROJECT_ROOT

OUTPUT_DIR = os.path.join(PROJECT_ROOT, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_label(text, width_mm=10, scale=1.0):
    """ラベル生成＋OCR＋色判定"""
    img = create_label_image(text, width_mm=width_mm, scale=scale)
    filename = f"label_{text}_{width_mm}mm.png"
    path = os.path.join(OUTPUT_DIR, filename)
    img.save(path)
    texts = ocr_image(img)
    color = detect_label_color(img)
    return path, texts, color

def run_gui():
    sg.theme("LightBlue2")
    layout = [
        [sg.Text("ラベル文字列:"), sg.Input(key="-TEXT-", size=(20,1))],
        [sg.Text("幅:"), sg.Combo([10, 12], default_value=10, key="-WIDTH-")],
        [sg.Text("文字拡大率:"), sg.Slider(range=(0.5, 2.0), resolution=0.1, default_value=1.0, orientation='h', key="-SCALE-")],
        [sg.Button("生成"), sg.Button("終了")],
        [sg.Text("出力:"), sg.Text("", key="-OUTPUT-", size=(60,2))]
    ]

    window = sg.Window("ラベル生成＋OCR", layout)

    while True:
        event, values = window.read()
        if event in (sg.WINDOW_CLOSED, "終了"):
            break
        if event == "生成":
            text = values["-TEXT-"].strip()
            width = int(values["-WIDTH-"])
            scale = float(values["-SCALE-"])
            if not text:
                sg.popup_error("文字列を入力してください")
                continue
            path, ocr_texts, color = generate_label(text, width, scale)
            window["-OUTPUT-"].update(f"保存先: {path}\nOCR: {ocr_texts}\n色: {color}")
            sg.popup("生成完了", f"ファイル: {path}\nOCR: {ocr_texts}\n色: {color}")

    window.close()

if __name__ == "__main__":
    run_gui()

