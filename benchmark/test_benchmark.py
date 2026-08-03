from benchmark.run_benchmark import score_query


class FakeStore:
    def __init__(self, doc_ids: list[str]) -> None:
        self.results = [
            {"metadata": {"doc_id": doc_id}, "content": doc_id, "score": 1.0}
            for doc_id in doc_ids
        ]

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        return self.results[:top_k]

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter=None) -> list[dict]:
        return self.search(query, top_k)


def benchmark_item(*expected_doc_ids: str) -> dict:
    return {
        "query": "test query",
        "metadata_filter": None,
        "expected_doc_ids": list(expected_doc_ids),
    }


def test_hit_below_rank_three_is_not_counted() -> None:
    result = score_query(
        FakeStore(["noise-1", "noise-2", "noise-3", "expected"]),
        benchmark_item("expected"),
        top_k=10,
    )
    assert result["outcome"] == "MISS"
    assert result["retrieval_pts"] == 0


def test_multi_result_requires_every_expected_document() -> None:
    result = score_query(
        FakeStore(["expected-a", "noise", "other-noise"]),
        benchmark_item("expected-a", "expected-b"),
        top_k=3,
    )
    assert result["outcome"] == "MISS"


def test_multi_result_passes_when_all_expected_documents_are_top_three() -> None:
    result = score_query(
        FakeStore(["expected-a", "noise", "expected-b"]),
        benchmark_item("expected-a", "expected-b"),
        top_k=3,
    )
    assert result["outcome"] == "TOP-3"
    assert result["retrieval_pts"] == 1
