# scripts/generate_labels.py
import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2
import easyocr
import re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# OCR 読み取り器（日本語・英語）
reader = easyocr.Reader(['ja', 'en'], gpu=False)

# 日本語対応フォント（Noto Sans JP推奨）
DEFAULT_FONT = os.path.join(PROJECT_ROOT, "fonts", "NotoSansJP-Regular.ttf")

# 正規表現で不要文字を削除
OCR_CLEANUP_REGEX = re.compile(r'[^0-9A-Za-z\u3000-\u30FF\u4E00-\u9FFF]')

def fix_transparent_background(pil_img):
    """透明背景を白に変換"""
    if pil_img.mode in ('RGBA', 'LA') or (pil_img.mode == 'P' and 'transparency' in pil_img.info):
        bg = Image.new("RGB", pil_img.size, (255, 255, 255))
        bg.paste(pil_img, mask=pil_img.split()[-1])
        return bg
    else:
        return pil_img.convert("RGB")

def create_label_image(text, width_mm=10, height_mm=None, bg_color=(255,255,255), font_path=None, scale=1.0):
    """ラベル画像生成"""
    dpi = 300
    width_px = int(width_mm / 25.4 * dpi)
    height_px = height_mm or int(width_px * 0.5)

    img = Image.new("RGBA", (width_px, height_px), bg_color + (255,))
    draw = ImageDraw.Draw(img)

    font_path = font_path or DEFAULT_FONT
    font_size = int(20 * scale)
    font = ImageFont.truetype(font_path, font_size)

    # 文字サイズ取得
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_w, text_h = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]

    pos = ((width_px - text_w) // 2, (height_px - text_h) // 2)
    draw.text(pos, text, fill=(0, 0, 0), font=font)

    return fix_transparent_background(img)

def preprocess_for_ocr(pil_img):
    """OCR向け前処理（白背景・グレースケール・二値化・リサイズ・膨張処理）"""
    img = fix_transparent_background(pil_img)
    img = img.convert("L")
    img = np.array(img)

    # コントラスト強調
    img = cv2.equalizeHist(img)

    # 二値化
    _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    h, w = img.shape
    # 小さい文字は2倍に拡大
    if h < 50:
        img = cv2.resize(img, (w*2, h*2), interpolation=cv2.INTER_CUBIC)

    # 膨張処理で文字を太く
    kernel = np.ones((2,2), np.uint8)
    img = cv2.dilate(img, kernel, iterations=1)

    return img

def ocr_image(pil_img):
    """OCR実行＋後処理"""
    img = preprocess_for_ocr(pil_img)
    results = reader.readtext(img)
    texts = [res[1] for res in results]
    # 不要文字削除
    texts = [OCR_CLEANUP_REGEX.sub('', t) for t in texts]
    return texts

def generate_samples(n=20):
    """サンプルラベル生成＋OCR"""
    sample_texts = ["テスト", "123", "Hello", "全角ＡＢＣ", "半角abc"]
    files = []

    print("📦 ラベル画像を生成中...")
    for i in range(n):
        text = sample_texts[i % len(sample_texts)]
        width = 10 if i % 2 == 0 else 12
        scale = 1.0 if i % 2 == 0 else 1.2
        bg = (255, 255, 255)

        img = create_label_image(text, width_mm=width, bg_color=bg, scale=scale)
        filename = f"label_{i}_{text}.png"
        path = os.path.join(OUTPUT_DIR, filename)
        img.save(path)

        texts = ocr_image(img)
        print(f"{filename} → OCR: {texts}")
        files.append(path)
    print("✅ 完了")
    return files

if __name__ == "__main__":
    generate_samples(20)

#cd C:\Users\221144\PycharmProjects\PythonProject1\project_root
#streamlit run scripts/app.py
