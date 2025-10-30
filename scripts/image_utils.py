# image_utils.py
import numpy as np
from PIL import Image

def detect_label_color(pil_img):
    """白は白、白以外は透明と判定"""
    img = pil_img.convert("RGB")
    arr = np.array(img)
    avg = arr.mean(axis=(0,1))  # RGB平均
    if avg.mean() > 200:
        return "白"
    else:
        return "透明"
