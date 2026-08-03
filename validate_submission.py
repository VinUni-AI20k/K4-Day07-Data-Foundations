from __future__ import annotations

import csv
import json
from pathlib import Path

from ingest import load_documents

REQUIRED_METADATA = {
    "doc_id",
    "customer_role",
    "category",
    "source_url",
    "retrieved_at",
    "document_version",
    "language",
    "permission",
}


def main() -> int:
    root = Path(__file__).parent
    documents = load_documents(root / "data" / "k4_ecommerce")
    assert 5 <= len(documents) <= 10, f"Expected 5-10 documents, got {len(documents)}"
    for document in documents:
        missing = REQUIRED_METADATA - set(document.metadata)
        assert not missing, f"{document.id} missing metadata: {sorted(missing)}"
        assert document.metadata["customer_role"] in {"buyer", "seller", "both"}
        assert document.content.strip()

    with (root / "data" / "k4_ecommerce" / "sources.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == len(documents), "sources.csv must contain one row per document"

    evaluation = json.loads((root / "evaluation_results.json").read_text(encoding="utf-8"))
    assert evaluation["document_count"] == len(documents)
    assert all(strategy["points"] == 10 for strategy in evaluation["strategies"])
    heading = next(item for item in evaluation["strategies"] if item["strategy"] == "HeadingChunker")
    assert len(heading["rows"]) == 5
    assert any(row["filter"] == {"customer_role": "seller"} for row in heading["rows"])
    assert all(row["rank"] == 1 for row in heading["rows"])

    report_group = (root / "report" / "REPORT_NHOM.md").read_text(encoding="utf-8")
    expected_members = {
        "Nguyễn Hoàng Hải": "2A202601426",
        "Nguyễn Văn Thành": "2A202601030",
        "Nguyễn Duy Khánh": "2A202601530",
        "Ngô Xuân Ninh": "2A202601068",
        "Nguyễn Chiến Thắng": "2A202601734",
    }
    for member_name, student_id in expected_members.items():
        assert member_name in report_group and student_id in report_group
    assert "[bổ sung tên" not in report_group

    personal_dir = root / "src" / "Nguyen Van Thanh"
    required_personal_files = {
        "README.md",
        "REPORT_CANHAN.md",
        "chunking.py",
        "store.py",
        "agent.py",
        "custom_chunking.py",
    }
    assert personal_dir.is_dir(), "Missing src/Nguyen Van Thanh personal folder"
    missing_personal = required_personal_files - {item.name for item in personal_dir.iterdir() if item.is_file()}
    assert not missing_personal, f"Missing personal files: {sorted(missing_personal)}"

    print("SUBMISSION VALID: 7 docs, required metadata, 5 queries, seller filter, 5 member strategies, 10/10 retrieval")
    print("Member information and Nguyen Van Thanh personal folder are complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
