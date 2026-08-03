"""
lexical_embedding.py — Embedder TF-IDF (hashing trick), khong can PyTorch.

VI SAO CAN FILE NAY
-------------------
MockEmbedder trong `src/embeddings.py` la hash MD5: deterministic nhung KHONG
mang ngu nghia, nen moi strategy deu duoc 0 diem va benchmark khong phan biet
duoc gi. LocalEmbedder (sentence-transformers) thi phai tai PyTorch ~2GB.

`LexicalEmbedder` la duong o giua: TF-IDF unigram + bigram tren chinh corpus
cua nhom, chi dung thu vien chuan Python. No do DO TRUNG TU (lexical overlap),
KHONG do ngu nghia — dong nghia khac tu van bi coi la khong lien quan. Voi van
ban phap luat thi diem yeu nay chap nhan duoc vi cau hoi thuong dung lai dung
thuat ngu cua van ban.

Gioi han nay PHAI duoc ghi trong report; khong duoc coi ket qua o day la bang
chung ve chat luong ngu nghia.

Dung chung mot embedder cho MOI strategy -> so sanh giua cac thanh vien van
cong bang (chi thay doi bien chunking).
"""
from __future__ import annotations

import math
import re
import unicodedata
import zlib
from collections import Counter
from pathlib import Path

_TOKEN = re.compile(r"[0-9a-zà-ỹ]+", re.IGNORECASE)


def tokenize(text: str) -> list[str]:
    text = unicodedata.normalize("NFC", text.lower())
    words = _TOKEN.findall(text)
    bigrams = [f"{a}_{b}" for a, b in zip(words, words[1:])]
    return words + bigrams


class LexicalEmbedder:
    """TF-IDF + hashing trick -> vector dac, da chuan hoa L2.

    Fit IDF tren toan bo file .md/.txt trong `data_dir` de trong so tu hiem
    (vd. "kiem_hang", "12", "5_ngay") duoc danh gia cao hon tu pho bien
    (vd. "thuong_mai", "dien_tu").
    """

    def __init__(self, data_dir: str | Path, dim: int = 2048) -> None:
        self.dim = dim
        self._backend_name = f"lexical tf-idf (dim={dim})"
        self._idf: dict[str, float] = {}
        self._fit(Path(data_dir))

    def _fit(self, data_dir: Path) -> None:
        document_freq: Counter[str] = Counter()
        total_docs = 0
        for path in sorted(data_dir.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in {".md", ".txt"}:
                continue
            total_docs += 1
            document_freq.update(set(tokenize(path.read_text(encoding="utf-8"))))

        total_docs = max(1, total_docs)
        self._idf = {
            token: math.log((total_docs + 1) / (freq + 1)) + 1.0
            for token, freq in document_freq.items()
        }
        self._default_idf = math.log(total_docs + 1) + 1.0

    def __call__(self, text: str) -> list[float]:
        vector = [0.0] * self.dim
        counts = Counter(tokenize(text))
        if not counts:
            return vector

        max_count = max(counts.values())
        for token, count in counts.items():
            tf = 0.5 + 0.5 * (count / max_count)
            idf = self._idf.get(token, self._default_idf)
            # crc32 thay cho hash(): hash() cua Python randomize theo process,
            # dung no thi hai lan chay cho hai ket qua khac nhau.
            vector[zlib.crc32(token.encode("utf-8")) % self.dim] += tf * idf

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0.0:
            return vector
        return [value / norm for value in vector]
