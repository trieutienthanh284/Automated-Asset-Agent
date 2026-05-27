import os
import shutil
from datetime import datetime

from agent_scraper import crawl_image_links
from agent_downloader import download_images
from agent_sorter import run_sorter


def setup_environment():
    """
    Kịch bản dọn dẹp chiến trường tự động:
    1. Xóa file CSV cũ (nếu có)
    2. Dọn sạch folder temp_images (nhưng giữ lại folder gốc)
    3. Dọn sạch folder resource/unprocessed (nhưng giữ lại các folder đã phân loại khác)
    """
    print("🧹 Đang dọn dẹp dữ liệu từ phiên làm việc trước...")

    # 1. Xóa file CSV
    if os.path.exists("image_links.csv"):
        try:
            os.remove("image_links.csv")
            print("   - Đã xóa file danh sách link (image_links.csv).")
        except Exception as e:
            print(f"   - Lỗi khi xóa CSV: {e}")

    # 2. Dọn sạch folder ảnh tạm (temp_images)
    temp_dir = "temp_images"
    os.makedirs(temp_dir, exist_ok=True)  # Đảm bảo folder tồn tại
    for filename in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"   - Lỗi khi xóa file tạm {filename}: {e}")
    print("   - Đã dọn sạch kho ảnh nháp (temp_images).")

    # 3. Dọn sạch folder rác (resource/unprocessed)
    quarantine_dir = os.path.join("resource", "unprocessed")
    os.makedirs(quarantine_dir, exist_ok=True)
    for filename in os.listdir(quarantine_dir):
        file_path = os.path.join(quarantine_dir, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            pass
    print("   - Đã dọn sạch thùng rác (resource/unprocessed).")
    print("✅ Môi trường đã sẵn sàng!\n")


def main():
    print("============================================================")
    print("🚀 [HỆ THỐNG AGENT V4.2] Phân loại Hybrid (YOLO + CLIP)")
    print("============================================================")

    # GỌI HÀM DỌN DẸP TỰ ĐỘNG
    setup_environment()

    URL_MUC_TIEU = input("🔗 Nhập URL trang web muốn cào ảnh: ").strip()
    if not URL_MUC_TIEU:
        URL_MUC_TIEU = "https://vi.wikipedia.org/wiki/Giải_vô_địch_bóng_đá_thế_giới_2026"

    CHU_DE_MUC_TIEU = input("🎯 Chủ đề phụ bạn muốn tìm thêm (Enter để bỏ qua): ").strip()

    FILE_CSV = "image_links.csv"
    KHO_TAM = "temp_images"
    GIOI_HAN_TAI = 30

    start_time = datetime.now()
    print(f"\n⏰ Bắt đầu lúc: {start_time.strftime('%H:%M:%S')}")
    print("-" * 60)

    try:
        print("\n🕵️ GIAI ĐOẠN 1: Agent Scraper đang thâm nhập...")
        crawl_image_links(URL_MUC_TIEU, FILE_CSV)

        print("\n📥 GIAI ĐOẠN 2: Agent Downloader đang tải ảnh nháp...")
        download_images(FILE_CSV, KHO_TAM, limit=GIOI_HAN_TAI)

        print("\n🤖 GIAI ĐOẠN 3: AI Lai (YOLO + CLIP) phân tích Offline...")
        run_sorter(target_topic=CHU_DE_MUC_TIEU)

        end_time = datetime.now()
        duration = end_time - start_time
        print("\n" + "=" * 60)
        print(f"🎉 HOÀN TẤT THÀNH CÔNG! Đã phân loại và đồng bộ GitHub.")
        print(f"⏱️ Tổng thời gian vận hành: {duration.seconds} giây.")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n🛑 Người dùng đã dừng hệ thống.")
    except Exception as e:
        print(f"\n❌ LỖI HỆ THỐNG: {e}")


if __name__ == "__main__":
    main()