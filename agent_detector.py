from ultralytics import YOLO
import config

# Khởi tạo siêu nhẹ: Tự động tải file yolov8n.pt (khoảng 6MB) vào RAM
if config.YOLO_ENABLED:
    print("⏳ [TRẠM YOLO] Đang nạp Mắt thần săn vật thể...")
    model_yolo = YOLO('yolov8n.pt')
    print("✅ Mắt thần YOLOv8 đã kích hoạt!")


def scan_for_objects(image_path):
    """
    Quét ảnh bằng YOLOv8.
    Trả về tên folder (chuỗi) nếu tìm thấy vật thể trong list mapping, ngược lại trả về None.
    """
    if not config.YOLO_ENABLED:
        return None

    # Chạy YOLO ẩn danh (verbose=False để không in rác ra màn hình)
    results = model_yolo(image_path, verbose=False)

    best_match = None
    highest_conf = 0.0

    for r in results:
        for box in r.boxes:
            conf = float(box.conf[0])
            if conf >= config.YOLO_CONFIDENCE and conf > highest_conf:
                cls_id = int(box.cls[0])
                cls_name = model_yolo.names[cls_id]  # Lấy tên tiếng anh (vd: person, car)

                # Kiểm tra xem vật thể này có nằm trong danh sách ta cần lọc không
                if cls_name in config.YOLO_MAPPING:
                    highest_conf = conf
                    best_match = config.YOLO_MAPPING[cls_name]

    return best_match