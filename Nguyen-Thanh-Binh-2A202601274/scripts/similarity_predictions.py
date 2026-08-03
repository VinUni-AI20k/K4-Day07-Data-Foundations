"""
Bài tập 3.3 — Dự đoán độ tương tự Cosine (phần CÁ NHÂN).

Dự đoán được ghi CỨNG trong file này TRƯỚC khi chạy (xem PREDICTIONS bên dưới),
script chỉ có nhiệm vụ tính điểm thật và đối chiếu — không sửa dự đoán sau khi biết kết quả.

Chạy:
    EMBEDDING_PROVIDER=local python scripts/similarity_predictions.py
    (Windows PowerShell: $env:EMBEDDING_PROVIDER="local"; python scripts/similarity_predictions.py)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

BUNDLE_ROOT = Path(__file__).resolve().parent.parent  # thư mục cá nhân của tôi
REPO_ROOT = BUNDLE_ROOT.parent  # repo chung của nhóm
sys.path.insert(0, str(REPO_ROOT))  # ingest.py / main.py dùng chung
sys.path.insert(0, str(BUNDLE_ROOT))  # src/ của RIÊNG tôi — ưu tiên cao hơn

from main import _select_embedder  # noqa: E402
from src import compute_similarity  # noqa: E402

# (nhãn, câu A, câu B, dự đoán, lý do dự đoán)
PREDICTIONS = [
    (
        1,
        "Người mua có thể trả lại hàng trong vòng 7 ngày kể từ khi nhận.",
        "Khách hàng được hoàn trả sản phẩm trong thời hạn một tuần sau khi nhận hàng.",
        "CAO",
        "Cùng một ý (thời hạn trả hàng), chỉ khác cách diễn đạt và đơn vị thời gian.",
    ),
    (
        2,
        "Người bán phải cung cấp mô tả sản phẩm chính xác.",
        "Thông tin sản phẩm do người bán đăng tải phải đúng sự thật.",
        "CAO",
        "Cùng nghĩa vụ của người bán, chỉ đảo cấu trúc câu và thay từ đồng nghĩa.",
    ),
    (
        3,
        "Chính sách đổi trả chỉ áp dụng cho hàng bị lỗi hoặc không đúng mô tả.",
        "Con mèo đang nằm ngủ trên mái nhà vào buổi trưa.",
        "THẤP",
        "Khác hoàn toàn chủ đề: chính sách TMĐT so với một câu tả cảnh sinh hoạt.",
    ),
    (
        4,
        "Đơn hàng này được hoàn tiền.",
        "Đơn hàng này không được hoàn tiền.",
        "CAO",
        "Bẫy phủ định: gần như trùng từ vựng nên embedding sẽ cho điểm cao dù nghĩa NGƯỢC nhau.",
    ),
    (
        5,
        "Phí vận chuyển được tính theo khối lượng đơn hàng.",
        "Thời gian giao hàng dự kiến là 3-5 ngày làm việc.",
        "TRUNG BÌNH",
        "Cùng miền giao hàng nhưng khác khía cạnh: chi phí so với thời gian.",
    ),
]


def main() -> int:
    embedder = _select_embedder()
    backend = getattr(embedder, "_backend_name", embedder.__class__.__name__)
    print(f"Backend nhúng: {backend}")
    print(f"EMBEDDING_PROVIDER={os.getenv('EMBEDDING_PROVIDER', 'mock')}\n")

    rows = []
    for index, sentence_a, sentence_b, prediction, reason in PREDICTIONS:
        score = compute_similarity(embedder(sentence_a), embedder(sentence_b))
        rows.append((index, sentence_a, sentence_b, prediction, score, reason))

    print(f"{'#':<3}{'Dự đoán':<14}{'Điểm thật':<12}Cặp câu")
    print("-" * 100)
    for index, sentence_a, sentence_b, prediction, score, _ in rows:
        print(f"{index:<3}{prediction:<14}{score:<12.4f}A: {sentence_a}")
        print(f"{'':<29}B: {sentence_b}")

    print("\n--- Xếp hạng thực tế (cao -> thấp) ---")
    for rank, (index, _, _, prediction, score, _) in enumerate(sorted(rows, key=lambda r: r[4], reverse=True), start=1):
        print(f"{rank}. Cặp {index}: {score:.4f} (dự đoán: {prediction})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
