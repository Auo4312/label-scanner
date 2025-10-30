# ocr_utils.py
import easyocr
import numpy as np
import cv2
from PIL import Image
import re

# 誤認補正マップ（ハイフンのみ半角化）
OCR_CORRECTION = {
    '一':'-'  # ハイフンに統一
}

# 不要文字削除（漢字も残す）
OCR_CLEANUP_REGEX = re.compile(r'[^0-9A-Za-z\u3000-\u30FF\u4E00-\u9FFF-]')

# EasyOCR reader
reader = easyocr.Reader(['ja','en'], gpu=False)

def preprocess_for_ocr(pil_img):
    """OCR精度向上前処理"""
    img = np.array(pil_img.convert("RGB"))
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    # リサイズ（文字が小さい場合）
    gray = cv2.resize(gray, (gray.shape[1]*2, gray.shape[0]*2), interpolation=cv2.INTER_CUBIC)
    # ノイズ除去
    blur = cv2.medianBlur(gray, 3)
    # アダプティブ二値化
    thresh = cv2.adaptiveThreshold(blur,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY,11,2)
    return thresh

def ocr_image(pil_img):
    """OCR実行＋後処理＋誤認補正"""
    img = preprocess_for_ocr(pil_img)
    results = reader.readtext(
        img, contrast_ths=0.05, adjust_contrast=0.7,
        allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-'
    )
    texts = [res[1] for res in results]
    # 不要文字削除
    texts = [OCR_CLEANUP_REGEX.sub('', t) for t in texts]
    # ハイフン誤認補正のみ
    corrected_texts = []
    for t in texts:
        corrected = ''.join([OCR_CORRECTION.get(c, c) for c in t])
        corrected_texts.append(corrected)
    return corrected_texts
