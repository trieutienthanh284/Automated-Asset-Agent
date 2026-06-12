import os
import shutil
from datetime import datetime

from agent_scraper import crawl_image_links
from agent_downloader import download_images
from agent_sorter import run_sorter


def setup_environment():
    """
    Kịch bản dọn dẹp chiến trường tự động:
    Bảo vệ tuyệt đối file dữ liệu trí nhớ 'download_history.db'
    """
    print("🧹 Đang dọn dẹp dữ liệu từ phiên làm việc trước...")

    if os.path.exists("image_links.csv"):
        try:
            os.remove("image_links.csv")
        except Exception:
            pass

    # Dọn sạch kho ảnh nháp
    temp_dir = "temp_images"
    os.makedirs(temp_dir, exist_ok=True)
    for filename in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception:
            pass

    # Dọn sạch thùng rác
    quarantine_dir = os.path.join("resource", "unprocessed")
    os.makedirs(quarantine_dir, exist_ok=True)
    for filename in os.listdir(quarantine_dir):
        file_path = os.path.join(quarantine_dir, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception:
            pass

    print("   - Đã dọn sạch kho nháp và thùng rác (Trí nhớ SQLite được bảo toàn).")
    print("✅ Môi trường đã sẵn sàng!\n")


def main():
    print("============================================================")
    print("🚀 [HỆ THỐNG AGENT V5.0] Tối thượng - AsyncIO & SQLite")
    print("============================================================")

    setup_environment()

    URL_MUC_TIEU = input("🔗 Nhập URL trang web muốn cào ảnh: ").strip()
    if not URL_MUC_TIEU:
        URL_MUC_TIEU = "https://vi.wikipedia.org/wiki/Du_l%E1%BB%8Bch_Vi%E1%BB%87t_Nam"

    CHU_DE_MUC_TIEU = input("🎯 Chủ đề phụ bạn muốn tìm thêm (Enter để bỏ qua): ").strip()

    FILE_CSV = "image_links.csv"
    KHO_TAM = "temp_images"
    GIOI_HAN_TAI = 30  # Bạn có thể tăng lên 100-500 ở V5.0 vì tốc độ rất nhanh

    start_time = datetime.now()
    print(f"\n⏰ Bắt đầu lúc: {start_time.strftime('%H:%M:%S')}")
    print("-" * 60)

    try:
        print("\n🕵️ GIAI ĐOẠN 1: Agent Scraper đang thâm nhập...")
        crawl_image_links(URL_MUC_TIEU, FILE_CSV)

        print("\n📥 GIAI ĐOẠN 2: Agent Downloader đang kích hoạt tải song song...")
        download_images(FILE_CSV, KHO_TAM, limit=GIOI_HAN_TAI)

        print("\n🤖 GIAI ĐOẠN 3: AI Lai phân tích & Tự động đồng bộ GitHub...")
        run_sorter(target_topic=CHU_DE_MUC_TIEU)

        end_time = datetime.now()
        duration = end_time - start_time
        print("\n" + "=" * 60)
        print(f"🎉 HOÀN TẤT THÀNH CÔNG KIẾN TRÚC V5.0!")
        print(f"⏱️ Tổng thời gian vận hành: {duration.seconds} giây.")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n🛑 Người dùng đã dừng hệ thống.")
    except Exception as e:
        print(f"\n❌ LỖI HỆ THỐNG: {e}")


if __name__ == "__main__":
    main()