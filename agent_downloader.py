import os
import csv
import sqlite3
import asyncio
import aiohttp
import aiofiles
from urllib.parse import urlparse


# 1. KHỞI TẠO BỘ NHỚ LỊCH SỬ (SQLite)
def init_db():
    conn = sqlite3.connect('download_history.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history 
                 (url TEXT PRIMARY KEY, status TEXT)''')
    conn.commit()
    return conn


# 2. HÀM TẢI ẢNH BẤT ĐỒNG BỘ (Bơm dữ liệu song song)
async def fetch_and_save_image(session, url, output_dir, count, db_conn):
    # Kiểm tra xem link này hôm qua đã tải chưa
    cursor = db_conn.cursor()
    cursor.execute("SELECT url FROM history WHERE url=?", (url,))
    if cursor.fetchone():
        return False  # Đã tải rồi thì bỏ qua

    try:
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)
        if not filename: filename = f"asset_temp_{count}.jpg"
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.webp', '.svg']:
            filename += '.jpg'

        file_path = os.path.join(output_dir, filename)

        async with session.get(url, timeout=15) as response:
            if response.status == 200:
                # Ghi file với tốc độ cao
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(await response.read())

                # Lưu vào não bộ SQLite
                cursor.execute("INSERT INTO history (url, status) VALUES (?, ?)", (url, "SUCCESS"))
                db_conn.commit()
                print(f"   📥 [Async] Đã tải thần tốc: {filename}")
                return True
    except Exception as e:
        pass
    return False


# 3. TRÌNH ĐIỀU KHIỂN CHÍNH
async def process_downloads(csv_file, output_dir, limit):
    db_conn = init_db()
    os.makedirs(output_dir, exist_ok=True)

    urls = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)  # Bỏ qua header
        for row in reader:
            if row and row[0].startswith('http'):
                urls.append(row[0])

    success_count = 0
    # Mở cổng kết nối song song (Mở tối đa 20 luồng cùng lúc)
    connector = aiohttp.TCPConnector(limit=20)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        for i, url in enumerate(urls):
            tasks.append(fetch_and_save_image(session, url, output_dir, i, db_conn))

        # Kích hoạt toàn bộ luồng chạy đua cùng lúc
        for completed_task in asyncio.as_completed(tasks):
            result = await completed_task
            if result:
                success_count += 1
            if success_count >= limit:
                break

    db_conn.close()
    return success_count


def download_images(csv_file, output_dir, limit=30):
    """Hàm bọc ngoài để tương thích ngược với main.py cũ"""
    if not os.path.exists(csv_file):
        print(f"   ❌ CẢNH BÁO: Không tìm thấy {csv_file}.")
        return

    print(f"   🚀 [Downloader V5.0] Kích hoạt tải song song và tra cứu SQLite...")
    # Chạy vòng lặp sự kiện bất đồng bộ
    count = asyncio.run(process_downloads(csv_file, output_dir, limit))

    if count == 0:
        print("   ⚠️ Không có ảnh mới nào được tải (Có thể đã tải hết từ trước hoặc lỗi mạng).")
    else:
        print(f"   ✅ Đã nạp thần tốc {count} ảnh mới vào trạm trung chuyển.")