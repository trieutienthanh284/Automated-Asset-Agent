# ==========================================
# SỔ TAY QUY CHUẨN CHO HỆ THỐNG AGENT (V2.3)
# ==========================================

SUPPORTED_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.webp']
MIN_FILE_SIZE_KB = 1  # Giữ mức 1KB để không bỏ sót thumbnail Wikipedia
VECTOR_EXTENSIONS = ['.svg']
VECTOR_DEFAULT_DIR = 'icons'
RATE_LIMIT_SLEEP = 12

# BỔ SUNG DANH MỤC CHI TIẾT ĐỂ AI PHÂN LOẠI CHUẨN XÁC HƠN
ALLOWED_CATEGORIES = [
    'logos',        # Logo, huy hiệu, biểu tượng chính thức
    'icons',        # Icon nhỏ, ký hiệu, nút bấm
    'backgrounds',  # Hình nền, họa tiết, texture
    'characters',   # Con người, nhân vật, cầu thủ, diễn viên
    'places',       # Địa điểm, kiến trúc, sân vận động, thành phố
    'animals',      # Động vật, thú cưng, sinh vật
    'nature',       # Cây cối, phong cảnh thiên nhiên, núi rừng
    'vehicles',     # Xe cộ, máy bay, tàu thuyền
    'objects',      # Đồ vật cụ thể (cup, bóng, điện thoại, máy móc)
    'others'        # Không thuộc các nhóm trên
]

AGENT_PROMPT_TEMPLATE = """
Bạn là chuyên gia phân tích và quản lý tài nguyên thiết kế hiệu năng cao.
Hãy phân tích bức ảnh được cung cấp dựa trên chủ đề mục tiêu: "{target_topic}".

Nhiệm vụ của bạn:
1. Kiểm tra xem bức ảnh này có liên quan hoặc chứa nội dung thuộc chủ đề "{target_topic}" hay không (Trả về True/False ở trường "is_matched"). Hãy linh hoạt: ví dụ chủ đề là 'thể thao' thì sân vận động, cầu thủ, hay cup đều là True.
2. Nếu "is_matched" là True, hãy phân loại nó vào MỘT trong các thư mục chính xác sau: {categories}. 
3. Phân tích nội dung để trích xuất 2-3 từ khóa ngắn gọn (bằng tiếng Anh hoặc tiếng Việt không dấu, viết thường, cách nhau bằng dấu gạch dưới).
4. Xác định 1 màu sắc chủ đạo nổi bật nhất của bức ảnh (ví dụ: red, blue, green, white, black...).

Trả về đúng 1 cấu trúc định dạng JSON duy nhất, TUYỆT ĐỐI không giải thích thêm:
{{
    "is_matched": true/false,
    "category": "tên_thư_mục_phù_hợp",
    "keywords": "tu_khoa_1_tu_khoa_2",
    "main_color": "mau_sac",
    "description": "mo_ta_ngan_gon"
}}
"""