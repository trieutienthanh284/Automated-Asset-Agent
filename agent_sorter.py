import os
import shutil
import json
import time
import re  # Thư viện Regex để bọc thép JSON
import hashlib
from google import genai
from google.genai import types
from dotenv import load_dotenv

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
        print("❌ Lỗi: Không tìm thấy GEMINI_API_KEY trong file .env. Vui lòng kiểm tra lại két sắt!")
        return

    client = genai.Client(api_key=API_KEY)
    print(f"🤖 AI Agent khởi động. Đang tiến hành lọc theo chủ đề: '{target_topic}'...\n")

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

        if ext in config.VECTOR_EXTENSIONS:
            print(f"⚠️ Từ chối đặc quyền: {filename} (AI không thể phân tích file code Vector .svg)")
            shutil.move(file_path, os.path.join(quarantine_dir, filename))
            continue

        if ext not in config.SUPPORTED_EXTENSIONS:
            print(f"⏩ Đưa vào khu cách ly: {filename} (Định dạng {ext} không hỗ trợ)")
            shutil.move(file_path, os.path.join(quarantine_dir, filename))
            continue

        print(f"👀 Đang đưa cho AI phân tích sâu: {filename}...")

        try:
            sample_file = client.files.upload(file_path=file_path)
            categories_str = ", ".join(config.ALLOWED_CATEGORIES)

            prompt = config.AGENT_PROMPT_TEMPLATE.format(
                target_topic=target_topic,
                categories=categories_str
            )

            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[sample_file, prompt],
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )

            # --- KHU VỰC BỌC THÉP JSON BẰNG REGEX ---
            raw_text = response.text
            # Tìm chính xác cấu trúc { ... } kể cả khi AI nói nhảm bên ngoài
            match = re.search(r'\{.*\}', raw_text, re.DOTALL)

            if match:
                json_str = match.group(0)
                result = json.loads(json_str)
            else:
                raise ValueError(f"AI không trả về JSON hợp lệ: {raw_text}")
            # ----------------------------------------

            is_matched = result.get("is_matched", False)
            if not is_matched:
                print(f"   ❌ Không khớp chủ đề [{target_topic}] -> Đẩy vào unprocessed.")
                shutil.move(file_path, os.path.join(quarantine_dir, filename))
                client.files.delete(name=sample_file.name)
                continue

            category = result.get("category", "others")
            if category not in config.ALLOWED_CATEGORIES:
                category = "others"

            # TRÍCH XUẤT THÔNG TIN ĐỂ ĐẶT TÊN
            main_color = result.get("main_color", "unknown").lower().replace(" ", "")
            keywords = result.get("keywords", "asset").lower().replace(" ", "_")
            short_hash = generate_short_hash(file_path)
            safe_topic = "".join([c for c in target_topic if c.isalnum()]).lower()

            # TẠO THẺ TÊN TỪ THƯ MỤC (Ví dụ: Thư mục 'logos' -> thẻ tên 'logo')
            file_tag = category[:-1] if category.endswith('s') else category

            # CÔNG THỨC TÊN MỚI: [Chủ_đề]_[Thẻ_loại]_[Màu]_[Từ_khóa]_[Mã].jpg
            new_filename = f"{safe_topic}_{file_tag}_{main_color}_{keywords}_{short_hash}{ext}"

            print(f"   -> Khớp! Đưa vào [{category}] | Tên mới: {new_filename}")

            target_dir = os.path.join(base_output_dir, category)
            os.makedirs(target_dir, exist_ok=True)

            shutil.move(file_path, os.path.join(target_dir, new_filename))
            client.files.delete(name=sample_file.name)

            print(f"   ⏳ Nghỉ {config.RATE_LIMIT_SLEEP} giây để tránh quá tải API...")
            time.sleep(config.RATE_LIMIT_SLEEP)

        except Exception as e:
            print(f"   ❌ Lỗi khi phân tích {filename}: {e}")
            shutil.move(file_path, os.path.join(quarantine_dir, filename))

    print("\n🎉 HOÀN TẤT PHÂN LOẠI!")
    sync()


def run_sorter(target_topic="logo"):
    sort_images('temp_images', 'resource', target_topic)