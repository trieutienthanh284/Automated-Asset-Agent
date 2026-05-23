# ==========================================
# SỔ TAY QUY CHUẨN CHO HỆ THỐNG AGENT (V3.0)
# Định tuyến động (Dynamic Routing)
# ==========================================

SUPPORTED_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.webp']
MIN_FILE_SIZE_KB = 1
VECTOR_EXTENSIONS = ['.svg']
VECTOR_DEFAULT_DIR = 'vectors'
RATE_LIMIT_SLEEP = 12

# KHÔNG CÒN ALLOWED_CATEGORIES CỐ ĐỊNH NỮA!

AGENT_PROMPT_TEMPLATE = """
Bạn là chuyên gia phân tích và quản lý tài nguyên thiết kế hiệu năng cao.
Hãy phân tích bức ảnh được cung cấp dựa trên chủ đề mục tiêu: "{target_topic}".

Nhiệm vụ của bạn:
1. Kiểm tra xem bức ảnh này có liên quan hoặc chứa nội dung thuộc chủ đề "{target_topic}" hay không (BẮT BUỘC trả về true hoặc false viết thường).
2. Nếu "is_matched" là true, hãy TỰ NGHĨ RA MỘT tên thư mục bằng tiếng Anh, dạng số nhiều, viết thường để phân loại ảnh này (Ví dụ: stadiums, players, logos, animals, objects, nature, jerseys...).
3. Phân tích nội dung để trích xuất 2-3 từ khóa ngắn gọn (bằng tiếng Anh hoặc tiếng Việt không dấu, viết thường, cách nhau bằng dấu gạch dưới).
4. Xác định 1 màu sắc chủ đạo nổi bật nhất của bức ảnh.

Trả về đúng 1 cấu trúc định dạng JSON duy nhất, TUYỆT ĐỐI không giải thích thêm:
{{
    "is_matched": true,
    "category": "ten_thu_muc_tieng_anh_so_nhieu",
    "keywords": "tu_khoa_1_tu_khoa_2",
    "main_color": "mau_sac",
    "description": "mo_ta_ngan_gon"
}}
"""