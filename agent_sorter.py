import os
import shutil
import json
import time
import re
import hashlib
from google import genai
from google.genai import types
from dotenv import load_dotenv

try:
    import fitz  # Thư viện đọc SVG (PyMuPDF)
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

        if ext not in config.SUPPORTED_EXTENSIONS and ext not in config.VECTOR_EXTENSIONS:
            print(f"⏩ Đưa vào khu cách ly: {filename} (Định dạng {ext} không hỗ trợ)")
            shutil.move(file_path, os.path.join(quarantine_dir, filename))
            continue

        print(f"👀 Đang đưa cho AI phân tích sâu: {filename}...")

        upload_target = file_path
        temp_render_path = None

        try:
            if ext in config.VECTOR_EXTENSIONS:
                if not fitz:
                    raise Exception("Thiếu thư viện PyMuPDF để đọc SVG.")
                print(f"   🔄 Đang đeo 'kính phiên dịch' cho AI đọc file Vector...")
                short_hash = generate_short_hash(file_path)
                temp_render_path = os.path.join(input_dir, f"temp_vision_{short_hash}.png")

                doc = fitz.open(file_path)
                pix = doc[0].get_pixmap()
                pix.save(temp_render_path)
                upload_target = temp_render_path

            sample_file = client.files.upload(file=upload_target)
            prompt = config.AGENT_PROMPT_TEMPLATE.format(target_topic=target_topic)

            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[sample_file, prompt],
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )

            if temp_render_path and os.path.exists(temp_render_path):
                os.remove(temp_render_path)

            raw_text = response.text
            match = re.search(r'\{.*\}', raw_text, re.DOTALL)

            if match:
                json_str = match.group(0)
                json_str = json_str.replace("True", "true").replace("False", "false").replace("'", '"')
                try:
                    result = json.loads(json_str)
                except json.JSONDecodeError:
                    raise ValueError("AI trả về JSON sai cú pháp.")
            else:
                raise ValueError("AI không trả về JSON hợp lệ.")

            is_matched = result.get("is_matched", False)
            if isinstance(is_matched, str):
                is_matched = is_matched.lower() == 'true'

            if not is_matched:
                print(f"   ❌ Không khớp chủ đề [{target_topic}] -> Đẩy vào unprocessed.")
                shutil.move(file_path, os.path.join(quarantine_dir, filename))
                client.files.delete(name=sample_file.name)
                continue

            category = result.get("category", "others").lower().strip()
            category = re.sub(r'[^a-z0-9_]', '', category)
            if not category: category = "others"

            main_color = result.get("main_color", "unknown").lower().replace(" ", "")
            keywords = result.get("keywords", "asset").lower().replace(" ", "_")
            short_hash = generate_short_hash(file_path)
            safe_topic = "".join([c for c in target_topic if c.isalnum()]).lower()

            file_tag = category[:-1] if category.endswith('s') else category
            new_filename = f"{safe_topic}_{file_tag}_{main_color}_{keywords}_{short_hash}{ext}"

            print(f"   -> Khớp! Đưa vào [{category}] | Tên mới: {new_filename}")

            target_dir = os.path.join(base_output_dir, category)
            os.makedirs(target_dir, exist_ok=True)

            gitkeep_path = os.path.join(target_dir, ".gitkeep")
            if not os.path.exists(gitkeep_path):
                with open(gitkeep_path, "w") as f: pass

            shutil.move(file_path, os.path.join(target_dir, new_filename))

            try:
                client.files.delete(name=sample_file.name)
            except:
                pass

        except Exception as e:
            # Nếu sập API (Lỗi 429), nó sẽ báo ở đây nhưng VẪN PHẢI NGHỈ
            print(f"   ❌ LỖI KỸ THUẬT: {e}")
            if temp_render_path and os.path.exists(temp_render_path):
                os.remove(temp_render_path)
            shutil.move(file_path, os.path.join(quarantine_dir, filename))

        finally:
            # CHỐT CHẶN AN TOÀN: Code có lỗi hay chạy đúng thì vẫn bắt buộc dừng 15s
            print(f"   ⏳ Nghỉ {config.RATE_LIMIT_SLEEP} giây để reset Quota API...")
            time.sleep(config.RATE_LIMIT_SLEEP)

    print("\n🎉 HOÀN TẤT PHÂN LOẠI!")
    sync()


def run_sorter(target_topic="thể thao"):
    sort_images('temp_images', 'resource', target_topic)