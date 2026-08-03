from src.document_aware_chunker import DocumentAwareChunker


def test_empty_text_returns_empty_list():
    assert DocumentAwareChunker().chunk("") == []


def test_one_heading_and_body_produce_one_chunk():
    chunks = DocumentAwareChunker(max_chunk_size=200).chunk("# Chính sách\nNội dung chính.")
    assert len(chunks) == 1
    assert "Nội dung chính." in chunks[0]


def test_two_second_level_sections_produce_separate_chunks():
    text = "# Tài liệu\n## Mục A\nNội dung A.\n## Mục B\nNội dung B."
    chunks = DocumentAwareChunker(max_chunk_size=200).chunk(text)
    assert any("Mục A" in chunk and "Nội dung A." in chunk for chunk in chunks)
    assert any("Mục B" in chunk and "Nội dung B." in chunk for chunk in chunks)


def test_heading_path_appears_in_output():
    text = "# Chính sách\n## Thời hạn\nNội dung."
    chunks = DocumentAwareChunker(max_chunk_size=200).chunk(text)
    assert any("[Heading path: Chính sách > Thời hạn]" in chunk for chunk in chunks)


def test_bullet_items_remain_with_heading_under_limit():
    text = "# Chính sách\n## Điều kiện\n* Dòng một\n* Dòng hai"
    chunks = DocumentAwareChunker(max_chunk_size=200).chunk(text)
    target = next(chunk for chunk in chunks if "Điều kiện" in chunk)
    assert "* Dòng một" in target
    assert "* Dòng hai" in target


def test_oversized_section_is_split():
    text = "# Tài liệu\n## Dài\n" + ("nội dung " * 80)
    chunks = DocumentAwareChunker(max_chunk_size=120).chunk(text)
    assert len(chunks) > 1


def test_chunks_respect_size_when_prefix_allows():
    text = "# A\n## B\n" + ("word " * 60)
    chunks = DocumentAwareChunker(max_chunk_size=100).chunk(text)
    assert all(len(chunk) <= 100 for chunk in chunks)


def test_document_without_headings_falls_back_safely():
    chunks = DocumentAwareChunker(max_chunk_size=80).chunk("Không có heading. " * 10)
    assert chunks
    assert all("[Heading path: Document]" in chunk for chunk in chunks)


def test_no_empty_chunks_are_produced():
    text = "# A\n\n## B\n\n### C\nNội dung."
    chunks = DocumentAwareChunker(max_chunk_size=120).chunk(text)
    assert chunks
    assert all(chunk.strip() for chunk in chunks)
