import yaml

# Đọc cấu hình từ file YAML chuẩn mực
with open('config.yaml', 'r', encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

MIN_FILE_SIZE_KB = cfg['system']['min_file_size_kb']
SUPPORTED_EXTENSIONS = cfg['system']['supported_extensions']
VECTOR_EXTENSIONS = cfg['system']['vector_extensions']
VECTOR_DEFAULT_DIR = cfg['system']['vector_dir']

CONFIDENCE_THRESHOLD = cfg['classification']['confidence_threshold']
CATEGORIES = cfg['classification']['candidate_labels']