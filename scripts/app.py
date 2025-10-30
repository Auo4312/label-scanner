import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
import av
import cv2
import easyocr
import numpy as np
from PIL import Image
import re

st.set_page_config(page_title="ラベルスキャナ ボタン版", layout="centered")
st.title("📷 ラベルスキャナ（スキャンボタンでOCR）")

# ===== OCR誤認補正マップ =====
OCR_CORRECTION = {
    "一":"-",
    "O":"0", "0":"O", "巴":"B",
    "|":"|", "｜":"|",
    "（":"(", "）":")"
}

# ===== OCR関数 =====
def ocr_image(pil_img):
    reader = easyocr.Reader(['ja', 'en'], gpu=False)
    img = np.array(pil_img)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    # 2倍リサイズして文字強調
    h, w = gray.shape
    gray_resized = cv2.resize(gray, (w*2, h*2), interpolation=cv2.INTER_CUBIC)

    # Adaptive Threshold
    th = cv2.adaptiveThreshold(
        gray_resized, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 10
    )

    # OCR実行
    results = reader.readtext(th, detail=1)
    texts = []
    for bbox, text, conf in results:
        if conf > 0.5:
            corrected = ''.join([OCR_CORRECTION.get(c, c) for c in text])
            texts.append(corrected)

    # 文字結合＋英数字とハイフンのみ抽出
    joined = ''.join(texts)
    joined = re.sub(r'[^A-Za-z0-9\-]', '', joined)
    return joined

# ===== ラベル色判定 =====
def detect_label_color(pil_img):
    img = np.array(pil_img)
    avg_color = np.mean(img, axis=(0, 1))
    brightness = np.mean(avg_color)
    return "白" if brightness > 190 else "透明"

# ===== カメラ映像処理 =====
class FrameProcessor(VideoProcessorBase):
    latest_frame = None

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        h, w, _ = img.shape

        # 枠線サイズ（横8cm × 縦1.5cm目安）
        px_per_cm = 37.795
        rect_w = int(8 * px_per_cm)
        rect_h = int(1.5 * px_per_cm)
        rect_w = min(rect_w, w-10)
        rect_h = min(rect_h, h-10)
        x1 = (w - rect_w) // 2
        y1 = (h - rect_h) // 2
        x2 = x1 + rect_w
        y2 = y1 + rect_h

        # 枠線描画
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # 枠内画像保持
        self.latest_frame = img[y1:y2, x1:x2].copy()

        return av.VideoFrame.from_ndarray(img, format="bgr24")

# ===== Streamlit UI =====
st.info("📸 カメラ起動中：中央の枠にラベルをかざして「スキャン」ボタンを押してください")

webrtc_ctx = webrtc_streamer(
    key="label-scanner",
    video_processor_factory=FrameProcessor,
    media_stream_constraints={"video": True, "audio": False},
)

# ===== スキャンボタン =====
if webrtc_ctx.video_processor:
    if st.button("🔍 スキャン"):
        frame = webrtc_ctx.video_processor.latest_frame
        if frame is not None:
            pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

            # OCR + ラベル色判定
            texts = ocr_image(pil_img)
            color = detect_label_color(pil_img)

            st.image(pil_img, caption="スキャン対象", use_container_width=True)
            st.success("✅ スキャン完了！")
            st.write(f"🈶 OCR結果: {texts}")
            st.write(f"🎨 ラベル色: {color}")
        else:
            st.warning("❗ 枠内画像がまだ取得できていません。")
