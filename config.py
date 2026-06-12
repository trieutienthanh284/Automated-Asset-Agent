import yaml

with open('config.yaml', 'r', encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

MIN_FILE_SIZE_KB = cfg['system']['min_file_size_kb']
SUPPORTED_EXTENSIONS = cfg['system']['supported_extensions']
VECTOR_EXTENSIONS = cfg['system']['vector_extensions']
VECTOR_DEFAULT_DIR = cfg['system']['vector_dir']

CONFIDENCE_THRESHOLD = cfg['classification']['confidence_threshold']
CATEGORIES = cfg['classification']['candidate_labels']

# --- BIẾN SỐ MỚI CHO YOLOv8 ---
YOLO_ENABLED = cfg.get('detection', {}).get('enabled', False)
YOLO_CONFIDENCE = cfg.get('detection', {}).get('confidence_threshold', 0.60)
YOLO_MAPPING = cfg.get('detection', {}).get('yolo_mapping', {})
YOLO_MIN_AREA_RATIO = cfg.get('detection', {}).get('min_area_ratio', 0.10)