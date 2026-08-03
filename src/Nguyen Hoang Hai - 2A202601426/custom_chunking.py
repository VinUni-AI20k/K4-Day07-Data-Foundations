from __future__ import annotations

import re
from typing import Callable

from .chunking import compute_similarity

DEFAULT_MAX_CHUNK_SIZE = 500
DEFAULT_SIMILARITY_THRESHOLD = 0.5


def _incremental_average(prev_avg: list[float], new_vec: list[float], new_count: int) -> list[float]:
    """Cập nhật vector trung bình (embedding đại diện cho chunk) khi thêm 1 câu mới.

    new_count là tổng số câu đã gom vào chunk SAU khi thêm câu mới này.
    """
    return [prev + (new - prev) / new_count for prev, new in zip(prev_avg, new_vec)]


class SemanticChunker:
    """Chiến lược chia nhỏ tùy chỉnh (custom) cho chủ đề chính sách TMĐT/hỗ trợ khách hàng: Semantic Chunking.

    Lý do thiết kế: các tài liệu chính sách (đổi trả, giao hàng, thanh toán, quyền
    riêng tư...) thường có nhiều câu liên tiếp cùng diễn giải một quy định, rồi mới
    chuyển sang quy định khác. Cắt cứng theo số ký tự (FixedSizeChunker) dễ cắt đứt
    giữa chừng một quy định; cắt cứng theo số câu (SentenceChunker) không biết khi
    nào nội dung đã đổi ý. SemanticChunker gom các câu liên tiếp vào cùng một chunk
    khi chúng còn "nói cùng một ý" (độ tương tự cosine giữa câu tiếp theo và embedding
    trung bình của chunk hiện tại còn >= similarity_threshold); khi độ tương tự tụt
    xuống dưới ngưỡng (dấu hiệu đổi sang quy định/ý khác) hoặc chunk đã chạm
    max_chunk_size ký tự, chunk hiện tại được chốt lại và bắt đầu chunk mới từ câu đó.

    Cần truyền vào embedding_fn (ví dụ MockEmbedder(), LocalEmbedder(), OpenAIEmbedder())
    để tính độ tương tự ngữ nghĩa giữa các câu.
    """

    def __init__(
        self,
        embedding_fn: Callable[[str], list[float]],
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
        max_chunk_size: int = DEFAULT_MAX_CHUNK_SIZE,
    ) -> None:
        self.embedding_fn = embedding_fn
        self.similarity_threshold = similarity_threshold
        self.max_chunk_size = max_chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        sentences = re.split(r'\.\s|!\s|\?\s|\.\n', text)
        sentences = [sentence.strip() for sentence in sentences if sentence.strip()]

        if not sentences:
            return []
        if len(sentences) == 1:
            return sentences

        sentence_embeddings = [self.embedding_fn(sentence) for sentence in sentences]

        chunks: list[str] = []
        current_sentences = [sentences[0]]
        current_embedding = sentence_embeddings[0]

        for sentence, embedding in zip(sentences[1:], sentence_embeddings[1:]):
            candidate_text = " ".join(current_sentences + [sentence])
            similarity = compute_similarity(current_embedding, embedding)

            fits_topic = similarity >= self.similarity_threshold
            fits_size = len(candidate_text) <= self.max_chunk_size

            if fits_topic and fits_size:
                current_sentences.append(sentence)
                current_embedding = _incremental_average(current_embedding, embedding, len(current_sentences))
            else:
                chunks.append(" ".join(current_sentences))
                current_sentences = [sentence]
                current_embedding = embedding

        if current_sentences:
            chunks.append(" ".join(current_sentences))

        return chunks


def _self_check() -> int:
    """Demo nhanh SemanticChunker (dùng MockEmbedder mặc định của src) — không cần model thật."""
    from src import MockEmbedder

    sample = (
        "Khách hàng có thể đổi trả sản phẩm trong vòng 7 ngày kể từ ngày nhận hàng. "
        "Sản phẩm đổi trả phải còn nguyên tem mác và chưa qua sử dụng. "
        "Chi phí vận chuyển đổi trả do người mua chi trả trừ khi lỗi từ người bán. "
        "Đơn hàng thường được giao trong 2-5 ngày làm việc tùy khu vực. "
        "Người mua có thể theo dõi trạng thái vận chuyển qua ứng dụng. "
        "Phương thức thanh toán hỗ trợ gồm thẻ tín dụng, ví điện tử và COD."
    )

    chunker = SemanticChunker(embedding_fn=MockEmbedder(), similarity_threshold=0.5, max_chunk_size=300)
    chunks = chunker.chunk(sample)

    print(f"SemanticChunker self-check: tạo {len(chunks)} chunk từ {len(sample)} ký tự")
    for index, piece in enumerate(chunks, start=1):
        print(f"  [{index}] ({len(piece)} ký tự) {piece}")

    assert len(chunks) > 0, "kỳ vọng ít nhất 1 chunk"
    return 0


if __name__ == "__main__":
    raise SystemExit(_self_check())
