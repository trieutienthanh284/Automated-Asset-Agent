# ==========================================
# SỔ TAY QUY CHUẨN CHO HỆ THỐNG AGENT (V2.2)
# Tối ưu hóa phân tích dữ liệu Wikipedia & Cảnh quan
# ==========================================

# 1. QUY CHUẨN ĐẦU VÀO
SUPPORTED_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.webp']

# 2. QUY CHUẨN LỌC RÁC (Đã điều chỉnh cho Thumbnail)
# Hạ từ 15KB xuống 5KB để bắt được các ảnh thu nhỏ chất lượng của Wikipedia
MIN_FILE_SIZE_KB = 5

# 3. QUY CHUẨN XỬ LÝ NGOẠI LỆ (.SVG)
VECTOR_EXTENSIONS = ['.svg']
VECTOR_DEFAULT_DIR = 'icons'

# 4. QUY CHUẨN NHỊP ĐỘ (Tránh sập API)
RATE_LIMIT_SLEEP = 12

# 5. QUY CHUẨN CẤU TRÚC KHO TÀI NGUYÊN
# Đã thêm 'places' để chứa Sân vận động, Tòa nhà, Phong cảnh
ALLOWED_CATEGORIES = ['logos', 'icons', 'backgrounds', 'characters', 'places', 'others']

# 6. BỘ PROMPT NÂNG CẤP ĐỂ ĐẶT TÊN VÀ LỌC THEO CHỦ ĐỀ
AGENT_PROMPT_TEMPLATE = """
Bạn là chuyên gia phân tích và quản lý tài nguyên thiết kế hiệu năng cao.
Hãy phân tích bức ảnh được cung cấp dựa trên chủ đề mục tiêu: "{target_topic}".

Nhiệm vụ của bạn:
1. Kiểm tra xem bức ảnh này có liên quan hoặc chứa nội dung thuộc chủ đề "{target_topic}" hay không (Trả về True/False ở trường "is_matched"). (Ví dụ: Nếu chủ đề là "sân vận động", ảnh khán đài, mặt cỏ, hoặc toàn cảnh sân đều được tính là True).
2. Nếu "is_matched" là True, hãy phân loại nó vào một trong các thư mục sau: {categories}. (Gợi ý: Sân vận động/cảnh quan chọn 'places', người/cầu thủ chọn 'characters', biểu tượng chọn 'logos').
3. Phân tích nội dung để trích xuất 2-3 từ khóa ngắn gọn mô tả bức ảnh (bằng tiếng Anh hoặc tiếng Việt không dấu, viết thường, cách nhau bằng dấu gạch dưới).
4. Xác định 1 màu sắc chủ đạo nổi bật nhất của bức ảnh (ví dụ: red, blue, green, white, black...).

Trả về đúng 1 cấu trúc định dạng JSON duy nhất không kèm từ ngữ giải thích nào khác ở ngoài:
{{
    "is_matched": true/false,
    "category": "tên_thư_mục_phù_hợp",
    "keywords": "tu_khoa_1_tu_khoa_2",
    "main_color": "mau_sac",
    "description": "mo_ta_ngan_gon"
}}
"""