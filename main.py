import os
from datetime import datetime

from agent_scraper import crawl_image_links
from agent_downloader import download_images
from agent_sorter import run_sorter


def setup_environment():
    os.makedirs("temp_images", exist_ok=True)
    os.makedirs("resource/unprocessed", exist_ok=True)


def main():
    print("============================================================")
    print("🚀 [HỆ THỐNG AGENT V4.0] Phân loại Offline bằng Computer Vision")
    print("============================================================")

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

        print("\n🤖 GIAI ĐOẠN 3: AI CLIP phân tích Offline...")
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