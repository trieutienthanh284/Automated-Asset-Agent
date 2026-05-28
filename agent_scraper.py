import os
import csv
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def save_to_csv(links, output_csv):
    """Lưu danh sách link ảnh vào file CSV một cách sạch sẽ."""
    # Lọc bỏ các link rác hoặc trùng lặp
    valid_links = list(set([link for link in links if link.startswith('http')]))

    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['image_url'])
        for link in valid_links:
            writer.writerow([link])
    return len(valid_links)


def crawl_with_stealth(url, output_csv):
    """
    [LÀN ĐƯỜNG 2 - TÀNG HÌNH]: Dùng trình duyệt giả lập để vượt Cloudflare
    và kích hoạt Javascript (Lazy-load).
    """
    print(f"   🤖 [Làn 2 - Stealth Track] Kích hoạt Trình duyệt tàng hình để phá giáp...")
    try:
        import undetected_chromedriver as uc
        from selenium.webdriver.common.by import By
    except ImportError:
        print("   ❌ Lỗi: Thiếu vũ khí. Vui lòng chạy: pip install undetected-chromedriver selenium")
        return

    # Cấu hình chạy ngầm không hiện cửa sổ để tiết kiệm tài nguyên
    options = uc.ChromeOptions()
    options.add_argument('--headless')

    driver = uc.Chrome(options=options, version_main=148)
    try:
        driver.get(url)
        print("   ⏳ Đang chờ website tải Javascript và kiểm tra bảo mật...")
        time.sleep(5)  # Đợi vượt Cloudflare

        # Cuộn trang dần dần xuống dưới để ép web nhả các ảnh ẩn (Lazy-load)
        print("   📜 Đang cuộn trang để bòn rút dữ liệu ẩn...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        for _ in range(3):  # Cuộn 3 lần
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # Thu thập toàn bộ thẻ ảnh
        images = driver.find_elements(By.TAG_NAME, 'img')
        links = []
        for img in images:
            src = img.get_attribute('src') or img.get_attribute('data-src')
            if src:
                links.append(src)

        total_saved = save_to_csv(links, output_csv)
        print(f"   ✅ [Làn 2] Đột nhập thành công! Bắt được {total_saved} link ảnh.")

    except Exception as e:
        print(f"   ❌ [Làn 2] Đột nhập thất bại: {e}")
    finally:
        driver.quit()


def crawl_image_links(url, output_csv="image_links.csv"):
    """
    Hệ thống phân luồng thông minh: Luôn thử Làn 1 trước, nếu fail tự chuyển Làn 2.
    """
    print(f"   ⚡ [Làn 1 - Fast Track] Đang cào tốc độ cao: {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)

        # 1. KIỂM TRA MÃ LỖI (Bị chặn bởi Tường lửa)
        if response.status_code in [403, 401, 429, 503]:
            print(f"   ⚠️ Bị chặn bởi Tường lửa (Mã {response.status_code}). Hệ thống tự động bẻ lái...")
            crawl_with_stealth(url, output_csv)
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        images = soup.find_all('img')

        links = []
        for img in images:
            src = img.get('src') or img.get('data-src')
            if src:
                src = urljoin(url, src)  # Xử lý các link tương đối thành tuyệt đối
                links.append(src)

        # 2. KIỂM TRA SỐ LƯỢNG (Bị chặn bởi Javascript)
        # Nếu là trang thương mại như Flaticon, HTML tĩnh thường chỉ có dưới 5 ảnh
        if len(links) < 5:
            print(f"   ⚠️ Tìm thấy quá ít ảnh ({len(links)}). Khả năng web giấu ảnh bằng Javascript. Tự động bẻ lái...")
            crawl_with_stealth(url, output_csv)
            return

        total_saved = save_to_csv(links, output_csv)
        print(f"   ✅ [Làn 1] Tốc độ tia chớp! Tìm thấy {total_saved} link ảnh.")

    except Exception as e:
        print(f"   ⚠️ Lỗi Làn 1 ({e}). Hệ thống tự động bẻ lái sang Làn 2...")
        crawl_with_stealth(url, output_csv)