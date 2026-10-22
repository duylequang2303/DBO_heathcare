#!/usr/bin/env bash
# Script dọn dẹp hệ thống chuyên sâu (yêu cầu quyền root / sudo)
set -e

if [ "$EUID" -ne 0 ]; then
  echo "Vui lòng chạy script này với sudo: sudo bash $0"
  exit 1
fi

echo "========================================="
echo "  BẮT ĐẦU DỌN DẸP HỆ THỐNG LINUX"
echo "========================================="

echo "[1/4] Dọn dẹp cache gói APT (/var/cache/apt)..."
apt-get clean
apt-get autoremove --purge -y

echo "[2/4] Dọn dẹp log hệ thống Systemd Journal (giữ lại 3 ngày gần nhất)..."
journalctl --vacuum-time=3d

echo "[3/4] Xóa các bản Snap cũ đã bị vô hiệu hóa (disabled revisions)..."
set +e
snap list --all | awk '/disabled/{print $1, $3}' | while read snapname revision; do
    echo "Đang gỡ snap $snapname bản rev $revision..."
    snap remove "$snapname" --revision="$revision"
done
snap set system refresh.retain=2
set -e

echo "[4/4] Dọn dẹp các tập tin tạm cũ..."
find /tmp -type f -atime +3 -delete 2>/dev/null || true

echo "========================================="
echo "  DỌN DẸP HOÀN TẤT! DUNG LƯỢNG Ổ ĐĨA HIỆN TẠI:"
echo "========================================="
df -h /
