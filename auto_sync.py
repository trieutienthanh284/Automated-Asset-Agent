import os
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

COMMIT_MESSAGES = {
    "agent_scraper.py": "Agent thu thập dữ liệu",
    "agent_downloader.py": "Agent tải dữ liệu",
    "agent_sorter.py": "Agent phân loại và sắp xếp ảnh",
    "config.py": "Bộ quy tắc cho Agent",
    "main.py": "Cấu hình phòng điều hành trung tâm",
    "auto_sync.py": "Agent tự động push lên Github",
    "resource/": "Update resource"
}


def run_git(args):
    # Thêm encoding="utf-8" và errors="replace" để chống vỡ font trên Windows
    return subprocess.run(["git"] + args, cwd=PROJECT_ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")


def sync():
    print("🚚 Agent Giao Hàng đang kiểm tra kho...")
    status = run_git(["status", "--porcelain"])

    if not status.stdout.strip():
        print("Mọi thứ đã đồng bộ. Không có dữ liệu mới.")
        return

    changed_paths = [line[3:] for line in status.stdout.splitlines()]
    commits_to_make = {}

    for path in changed_paths:
        path = path.strip('"')

        if path.startswith("resource/"):
            msg = COMMIT_MESSAGES["resource/"]
            commits_to_make.setdefault(msg, []).append(path)
        else:
            matched = False
            for key, msg in COMMIT_MESSAGES.items():
                if path == key:
                    commits_to_make.setdefault(msg, []).append(path)
                    matched = True
                    break
            if not matched:
                commits_to_make.setdefault(f"Cập nhật file: {path}", []).append(path)

    for msg, files in commits_to_make.items():
        print(f"📦 Đang đóng gói ({len(files)} file) với lời nhắn: '{msg}'")
        run_git(["add"] + files)
        run_git(["commit", "-m", msg])

    print("🚀 Đang đẩy dữ liệu lên GitHub...")
    result = run_git(["push", "origin", "HEAD"])

    if result.returncode == 0:
        print("🎉 Đã đồng bộ lên GitHub thành công với các commit chuyên nghiệp!")
    else:
        print(f"❌ Lỗi khi Push: {result.stderr}")


if __name__ == "__main__":
    sync()