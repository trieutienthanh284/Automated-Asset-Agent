import os
import shutil
import hashlib
from PIL import Image
from dotenv import load_dotenv

import config
from auto_sync import sync

try:
    import fitz
except ImportError:
    fitz = None

import torch
from transformers import CLIPProcessor, CLIPModel

print("⏳ [HỆ THỐNG V4.0] Đang nạp mô hình Trí tuệ Nhân tạo OpenAI CLIP vào bộ nhớ...")
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
print("✅ Nạp AI thành công! Sẵn sàng duyệt ảnh với tốc độ ánh sáng.")


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

        if file_size_kb == 0:
            os.remove(file_path)
            continue
        elif config.MIN_FILE_SIZE_KB > 0 and file_size_kb < config.MIN_FILE_SIZE_KB:
            os.remove(file_path)
            continue

        if ext not in config.SUPPORTED_EXTENSIONS and ext not in config.VECTOR_EXTENSIONS:
            shutil.move(file_path, os.path.join(quarantine_dir, filename))
            continue

        temp_render_path = None
        try:
            if ext in config.VECTOR_EXTENSIONS:
                if not fitz:
                    raise Exception("Thiếu PyMuPDF")
                short_hash = generate_short_hash(file_path)
                temp_render_path = os.path.join(input_dir, f"temp_vision_{short_hash}.png")
                doc = fitz.open(file_path)
                pix = doc[0].get_pixmap()
                pix.save(temp_render_path)
                target_image_path = temp_render_path
            else:
                target_image_path = file_path

            image = Image.open(target_image_path).convert("RGB")

            # TRỘN DANH SÁCH: YAML tĩnh + Từ khóa bạn vừa nhập từ bàn phím
            dynamic_labels = config.CATEGORIES.copy()
            if target_topic and target_topic.lower() not in [l.lower() for l in dynamic_labels]:
                dynamic_labels.append(target_topic.lower())

            inputs = processor(text=dynamic_labels, images=image, return_tensors="pt", padding=True)
            outputs = model(**inputs)
            logits_per_image = outputs.logits_per_image
            probs = logits_per_image.softmax(dim=1)

            best_prob = probs.max().item()
            best_idx = probs.argmax().item()
            best_category_raw = dynamic_labels[best_idx]

            if temp_render_path and os.path.exists(temp_render_path):
                os.remove(temp_render_path)

            if best_prob < config.CONFIDENCE_THRESHOLD:
                print(f"   ❌ {filename} -> Từ chối (Khớp cao nhất: {best_prob * 100:.1f}%)")
                shutil.move(file_path, os.path.join(quarantine_dir, filename))
                continue

            folder_name = best_category_raw.replace(" ", "_")
            if not folder_name.endswith('s'): folder_name += 's'

            short_hash = generate_short_hash(file_path)
            safe_topic = "".join([c for c in target_topic if c.isalnum()]).lower() if target_topic else "asset"
            new_filename = f"{safe_topic}_{folder_name}_{short_hash}{ext}"

            print(f"   ✅ {filename} -> [{folder_name}] (Độ tin cậy: {best_prob * 100:.1f}%)")

            target_dir = os.path.join(base_output_dir, folder_name)
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

    print("\n🎉 HOÀN TẤT PHÂN LOẠI NHANH!")
    sync()


def run_sorter(target_topic=""):
    sort_images('temp_images', 'resource', target_topic)