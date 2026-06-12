from ultralytics import YOLO
import config

if config.YOLO_ENABLED:
    print("⏳ [TRẠM YOLO V5.0] Đang nạp Mắt thần tích hợp đo lường không gian...")
    model_yolo = YOLO('yolov8n.pt')


def scan_for_objects(image_path):
    if not config.YOLO_ENABLED: return None

    results = model_yolo(image_path, verbose=False)
    best_match = None
    highest_conf = 0.0

    for r in results:
        # Lấy kích thước ảnh gốc để tính diện tích tổng
        img_height, img_width = r.orig_shape
        img_area = img_width * img_height

        for box in r.boxes:
            conf = float(box.conf[0])
            if conf >= config.YOLO_CONFIDENCE:
                # Tính diện tích của khung vật thể (Bounding Box)
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                box_area = (x2 - x1) * (y2 - y1)

                # Tỷ lệ: Diện tích vật thể / Diện tích ảnh
                area_ratio = box_area / img_area

                # Nếu vật thể đủ to (>= 10% ảnh) mới được phân loại
                if area_ratio >= config.YOLO_MIN_AREA_RATIO:
                    if conf > highest_conf:
                        cls_id = int(box.cls[0])
                        cls_name = model_yolo.names[cls_id]
                        if cls_name in config.YOLO_MAPPING:
                            highest_conf = conf
                            best_match = config.YOLO_MAPPING[cls_name]

    return best_match