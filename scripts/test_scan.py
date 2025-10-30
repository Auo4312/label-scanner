import cv2
import pytesseract

# Tesseractのパスを指定
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("カメラが見つかりません")
        return

    print("文字認識開始（終了：'q'キー）")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 枠線を表示（中央のスキャン範囲）
        h, w, _ = frame.shape
        x1, y1 = int(w * 0.2), int(h * 0.3)
        x2, y2 = int(w * 0.8), int(h * 0.7)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # 枠内の部分をトリミング
        roi = frame[y1:y2, x1:x2]

        # OCR実行（英数字 or 日本語）
        text = pytesseract.image_to_string(roi, lang="jpn+eng")

        # 結果を画面に表示
        cv2.putText(frame, text.strip(), (30, 50), cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0, 255, 0), 2)
        cv2.imshow("文字認識スキャナ", frame)

        # コンソールにも出力
        if text.strip():
            print("認識結果:", text.strip())

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
