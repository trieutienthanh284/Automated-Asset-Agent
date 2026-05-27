import os
import shutil
import hashlib
from PIL import Image

import config
from auto_sync import sync

# Nhúng não trái (YOLO)
from agent_detector import scan_for_objects

try:
    import fitz
except ImportError:
    fitz = None

import torch
from transformers import CLIPProcessor, CLIPModel

print("⏳ [TRẠM CLIP] Đang nạp não phải phân tích bối cảnh...")
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
print("✅ Não phải CLIP đã kích hoạt!")


def generate_short_hash(file_path):
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        buf = f.read(1024)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(1024)
    return hasher.hexdigest()[:4]


def sort_images(input_dir, base_output_dir, target_topic):
    if not os.path.exists(input_dir): return

    quarantine_dir = os.path.join(base_output_dir, 'unprocessed')
    os.makedirs(quarantine_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        file_path = os.path.join(input_dir, filename)
        if not os.path.isfile(file_path): continue

        ext = os.path.splitext(filename)[1].lower()
        file_size_kb = os.path.getsize(file_path) / 1024

        if file_size_kb == 0 or (config.MIN_FILE_SIZE_KB > 0 and file_size_kb < config.MIN_FILE_SIZE_KB):
            os.remove(file_path)
            continue

        if ext not in config.SUPPORTED_EXTENSIONS and ext not in config.VECTOR_EXTENSIONS:
            shutil.move(file_path, os.path.join(quarantine_dir, filename))
            continue

        temp_render_path = None
        try:
            # 1. TIỀN XỬ LÝ
            if ext in config.VECTOR_EXTENSIONS:
                if not fitz: raise Exception("Thiếu PyMuPDF")
                short_hash = generate_short_hash(file_path)
                temp_render_path = os.path.join(input_dir, f"temp_vision_{short_hash}.png")
                doc = fitz.open(file_path)
                pix = doc[0].get_pixmap()
                pix.save(temp_render_path)
                target_image_path = temp_render_path
            else:
                target_image_path = file_path

            # 2. KIỂM DUYỆT TẦNG 1: YOLO SĂN VẬT THỂ CỨNG
            target_folder = scan_for_objects(target_image_path)
            ai_source = "YOLO"

            # 3. KIỂM DUYỆT TẦNG 2: CLIP ĐÁNH GIÁ BỐI CẢNH (Chỉ chạy khi YOLO bó tay)
            if not target_folder:
                ai_source = "CLIP"
                raw_image = Image.open(target_image_path)

                # Lót nền trắng
                if raw_image.mode in ('RGBA', 'LA') or (raw_image.mode == 'P' and 'transparency' in raw_image.info):
                    background = Image.new("RGB", raw_image.size, (255, 255, 255))
                    raw_image = raw_image.convert("RGBA")
                    background.paste(raw_image, mask=raw_image.split()[3])
                    image = background
                else:
                    image = raw_image.convert("RGB")

                cat_keys = list(config.CATEGORIES.keys())
                cat_prompts = list(config.CATEGORIES.values())

                if target_topic and target_topic.lower() not in cat_keys:
                    topic_clean = target_topic.lower()
                    cat_keys.append(topic_clean)
                    cat_prompts.append(f"a high quality photo or digital image of {topic_clean}")

                inputs = processor(text=cat_prompts, images=image, return_tensors="pt", padding=True)
                outputs = model(**inputs)
                probs = outputs.logits_per_image.softmax(dim=1)

                best_prob = probs.max().item()

                if best_prob < config.CONFIDENCE_THRESHOLD:
                    print(f"   ❌ {filename} -> Từ chối (CLIP Khớp: {best_prob * 100:.1f}%)")
                    if temp_render_path and os.path.exists(temp_render_path): os.remove(temp_render_path)
                    shutil.move(file_path, os.path.join(quarantine_dir, filename))
                    continue

                best_idx = probs.argmax().item()
                raw_key = cat_keys[best_idx]

                # Ép tên chuẩn
                target_folder = raw_key.replace(" ", "_")
                if not target_folder.endswith('s'): target_folder += 's'

            # 4. HOÀN TẤT VÀ LƯU FILE
            if temp_render_path and os.path.exists(temp_render_path):
                os.remove(temp_render_path)

            short_hash = generate_short_hash(file_path)
            safe_topic = "".join([c for c in target_topic if c.isalnum()]).lower() if target_topic else "asset"
            new_filename = f"{safe_topic}_{target_folder}_{short_hash}{ext}"

            print(f"   ✅ {filename} -> [{target_folder}] (Xử lý bởi: {ai_source})")

            target_dir = os.path.join(base_output_dir, target_folder)
            os.makedirs(target_dir, exist_ok=True)

            gitkeep_path = os.path.join(target_dir, ".gitkeep")
            if not os.path.exists(gitkeep_path):
                with open(gitkeep_path, "w") as f: pass

            shutil.move(file_path, os.path.join(target_dir, new_filename))

        except Exception as e:
            print(f"   ❌ LỖI XỬ LÝ {filename}: {e}")
            if temp_render_path and os.path.exists(temp_render_path):
                os.remove(temp_render_path)
            shutil.move(file_path, os.path.join(quarantine_dir, filename))

    print("\n🎉 HOÀN TẤT PHÂN LOẠI NHANH QUA 2 TẦNG AI!")
    sync()


def run_sorter(target_topic=""):
    sort_images('temp_images', 'resource', target_topic)