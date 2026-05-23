import os
import shutil
import json
import time
import re
import hashlib
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Import thư viện "Kính phiên dịch" SVG
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

import config
from auto_sync import sync

load_dotenv()


def generate_short_hash(file_path):
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        buf = f.read(1024)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(1024)
    return hasher.hexdigest()[:4]


def sort_images(input_dir, base_output_dir, target_topic):
    API_KEY = os.environ.get("GEMINI_API_KEY")
    if not API_KEY:
        print("❌ Lỗi: Không tìm thấy GEMINI_API_KEY trong file .env.")
        return

    if not fitz:
        print("❌ HỆ THỐNG THIẾU THƯ VIỆN! Hãy mở Terminal và chạy: pip install pymupdf")
        return

    client = genai.Client(api_key=API_KEY)
    print(f"🤖 AI Agent khởi động. Lọc theo chủ đề: '{target_topic}'...\n")

    if not os.path.exists(input_dir): return

    quarantine_dir = os.path.join(base_output_dir, 'unprocessed')
    os.makedirs(quarantine_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        file_path = os.path.join(input_dir, filename)
        if not os.path.isfile(file_path): continue

        ext = os.path.splitext(filename)[1].lower()
        file_size_kb = os.path.getsize(file_path) / 1024

        if file_size_kb < config.MIN_FILE_SIZE_KB:
            print(f"🗑️ Đang xóa rác: {filename} ({file_size_kb:.1f} KB)")
            os.remove(file_path)
            continue

        # Chặn các đuôi lạ không nằm trong cả 2 danh sách
        if ext not in config.SUPPORTED_EXTENSIONS and ext not in config.VECTOR_EXTENSIONS:
            print(f"⏩ Đưa vào khu cách ly: {filename} (Định dạng {ext} không hỗ trợ)")
            shutil.move(file_path, os.path.join(quarantine_dir, filename))
            continue

        print(f"👀 Đang đưa cho AI phân tích sâu: {filename}...")

        upload_target = file_path  # Mặc định file đưa cho AI xem chính là file gốc
        temp_render_path = None  # Đường dẫn ảnh tạm (nếu là SVG)

        try:
            # ẢO THUẬT: NẾU LÀ SVG, DỰNG HÌNH THÀNH PNG TẠM THỜI
            if ext in config.VECTOR_EXTENSIONS:
                print(f"   🔄 Đang đeo 'kính phiên dịch' cho AI đọc file Vector...")
                short_hash = generate_short_hash(file_path)
                temp_render_path = os.path.join(input_dir, f"temp_vision_{short_hash}.png")

                # Dùng PyMuPDF đọc SVG và xuất ra PNG
                doc = fitz.open(file_path)
                pix = doc[0].get_pixmap()
                pix.save(temp_render_path)

                # Đổi mục tiêu đưa cho AI xem thành ảnh PNG tạm thời
                upload_target = temp_render_path

            # Gọi AI phân tích (nó sẽ nhìn thấy PNG thật hoặc PNG tạm)
            sample_file = client.files.upload(file=upload_target)

            prompt = config.AGENT_PROMPT_TEMPLATE.format(target_topic=target_topic)

            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[sample_file, prompt],
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )

            # DỌN DẸP ẢNH TẠM NGAY LẬP TỨC ĐỂ TRÁNH RÁC Ổ CỨNG
            if temp_render_path and os.path.exists(temp_render_path):
                os.remove(temp_render_path)

            # Bọc thép JSON & Sửa lỗi chính tả
            raw_text = response.text
            match = re.search(r'\{.*\}', raw_text, re.DOTALL)

            if match:
                json_str = match.group(0)
                json_str = json_str.replace("True", "true").replace("False", "false").replace("'", '"')
                try:
                    result = json.loads(json_str)
                except json.JSONDecodeError as je:
                    raise ValueError(f"AI trả về JSON sai cú pháp.")
            else:
                raise ValueError(f"AI không trả về JSON hợp lệ.")

            is_matched = result.get("is_matched", False)
            if isinstance(is_matched, str):
                is_matched = is_matched.lower() == 'true'

            if not is_matched:
                print(f"   ❌ Không khớp chủ đề [{target_topic}] -> Đẩy vào unprocessed.")
                shutil.move(file_path, os.path.join(quarantine_dir, filename))
                client.files.delete(name=sample_file.name)
                continue

            # Định tuyến động (AI tự nghĩ ra category)
            category = result.get("category", "others").lower().strip()
            category = re.sub(r'[^a-z0-9_]', '', category)
            if not category: category = "others"

            main_color = result.get("main_color", "unknown").lower().replace(" ", "")
            keywords = result.get("keywords", "asset").lower().replace(" ", "_")
            short_hash = generate_short_hash(file_path)
            safe_topic = "".join([c for c in target_topic if c.isalnum()]).lower()

            # GIỮ NGUYÊN ĐUÔI FILE GỐC (Sẽ lưu .svg chứ không phải ảnh tạm)
            file_tag = category[:-1] if category.endswith('s') else category
            new_filename = f"{safe_topic}_{file_tag}_{main_color}_{keywords}_{short_hash}{ext}"

            print(f"   -> Khớp! Đưa vào [{category}] | Tên mới: {new_filename}")

            target_dir = os.path.join(base_output_dir, category)
            os.makedirs(target_dir, exist_ok=True)

            gitkeep_path = os.path.join(target_dir, ".gitkeep")
            if not os.path.exists(gitkeep_path):
                with open(gitkeep_path, "w") as f: pass

            # Di chuyển FILE GỐC (.svg hoặc .png) sang nhà mới
            shutil.move(file_path, os.path.join(target_dir, new_filename))

            try:
                client.files.delete(name=sample_file.name)
            except:
                pass

            print(f"   ⏳ Nghỉ {config.RATE_LIMIT_SLEEP} giây để tránh quá tải API...")
            time.sleep(config.RATE_LIMIT_SLEEP)

        except Exception as e:
            print(f"   ❌ LỖI KỸ THUẬT: {e}")
            # Nếu có lỗi mà ảnh tạm vẫn còn, xóa nó đi
            if temp_render_path and os.path.exists(temp_render_path):
                os.remove(temp_render_path)
            shutil.move(file_path, os.path.join(quarantine_dir, filename))

    print("\n🎉 HOÀN TẤT PHÂN LOẠI!")
    sync()


def run_sorter(target_topic="thể thao"):
    sort_images('temp_images', 'resource', target_topic)