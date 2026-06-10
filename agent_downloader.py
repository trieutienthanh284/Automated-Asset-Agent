import os
import csv
import requests
from urllib.parse import urlparse


def download_images(csv_file, output_dir, limit=30):
    """
    [AGENT DOWNLOADER V4.3]
    Tải ảnh nháp tốc độ cao từ file CSV. Chống treo máy và lọc file rác.
    """
    if not os.path.exists(csv_file):
        print(f"   ❌ CẢNH BÁO: Không tìm thấy file {csv_file}. Agent Scraper đã thất bại ở Giai đoạn 1!")
        return

    os.makedirs(output_dir, exist_ok=True)
    count = 0

    # Mở file CSV và tự động bỏ qua dòng tiêu đề (Header)
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader, None)  # Bỏ qua chữ 'image_url'

        for row in reader:
            if not row: continue
            img_url = row[0]
            if not img_url.startswith('http'): continue

            try:
                # Trích xuất tên file an toàn từ đường link
                parsed = urlparse(img_url)
                filename = os.path.basename(parsed.path)
                if not filename: filename = f"asset_temp_{count}.jpg"

                # Ép kiểu đuôi file an toàn
                ext = os.path.splitext(filename)[1].lower()
                if ext not in ['.jpg', '.jpeg', '.png', '.webp', '.svg']:
                    filename += '.jpg'

                file_path = os.path.join(output_dir, filename)

                # Tải ảnh với giới hạn thời gian (Timeout) để chống treo hệ thống
                response = requests.get(img_url, timeout=10)
                if response.status_code == 200:
                    with open(file_path, 'wb') as img_file:
                        img_file.write(response.content)
                    count += 1
                    print(f"   📥 Đã tải thành công: {filename}")

                if count >= limit:
                    break
            except Exception as e:
                # Bỏ qua các link chết hoặc lỗi kết nối
                continue

    if count == 0:
        print("   ❌ CẢNH BÁO: File CSV có link nhưng Agent Downloader không thể tải được bức ảnh nào!")
    else:
        print(f"   ✅ [Downloader] Đã nạp thành công {count} ảnh vào trạm trung chuyển (temp_images).")