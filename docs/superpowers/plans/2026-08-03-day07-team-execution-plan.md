# Lab 07 Team Execution Plan

> **For agentic workers:** Execute this plan task-by-task with focused verification after each task.

**Goal:** Complete the K4 Data Foundations lab for five members with one traceable shared corpus, five distinct personal strategies, complete personal reports, a group report, a demo, and forty-two passing tests in every personal repository.

**Architecture:** Keep the starter package contract in the root `src/` modules so `python -m pytest tests -v` continues to work.
Store each member's strategy implementation and benchmark evidence in a named subfolder under `src/` without creating a second importable package that can conflict with the starter package.
Use one integration branch for shared artifacts and one member branch per contributor.

**Tech Stack:** Python 3.11, pytest 9.1.1, python-dotenv 1.2.2, the existing in-memory `EmbeddingStore`, and the optional local multilingual embedder for benchmark measurement.

## Team Roster

| Member | Student ID | Primary group responsibility | Personal strategy |
|---|---|---|---|
| Nguyễn Đăng Long | 2A202601934 | Integration owner and corpus coordinator | Heading with recursive fallback |
| Đào Minh Chiến | 2A202601184 | Buyer-source curator | Sentence chunking |
| Lương Minh Quân | 2A202601308 | Seller-source curator | Recursive chunking |
| Lê Đăng Tấn | 2A202601916 | Metadata and validation owner | Fixed-size with overlap |
| Vũ Hữu An | 2A202601078 | Benchmark, report, and demo owner | Tuned fixed-size or FAQ-section strategy |

## Shared Branch and Contribution Rules

- `main` remains the clean integration baseline.
- `shared/data` contains the approved corpus, metadata manifest, and five benchmark queries.
- `develop/long` contains Long's personal implementation plus the current integrated shared artifacts.
- Each member works on `member/<student-id>-<name>` and opens a pull request into the integration branch.
- No branch name may contain `codex`.
- Each member commits only files they authored or materially changed.
- `README.md` and `report/REPORT_NHOM.md` contain a contribution matrix with the relevant commit or pull request.
- The root `src/chunking.py`, `src/store.py`, and `src/agent.py` remain the runnable personal implementation in each personal repository.
- Each member folder under `src/` contains that member's strategy code, notes, and benchmark evidence rather than a duplicate package that shadows the root `src` package.

## Final Repository Layout

```text
src/
├── __init__.py
├── chunking.py
├── store.py
├── agent.py
├── K4_2A202601934_NguyenDangLong/
├── K4_2A202601184_DaoMinhChien/
├── K4_2A202601308_LuongMinhQuan/
├── K4_2A202601916_LeDangTan/
└── K4_2A202601078_VuHuuAn/
```

Each member folder contains `strategy.py`, `strategy_notes.md`, and `benchmark_results.json`.
Folder names use ASCII letters and underscores so they remain portable and safe to import or package.

## Task 1: Establish the shared repository

**Owner:** Nguyễn Đăng Long.

- [ ] Add all five members and student IDs to `README.md`.
- [ ] Add the five member folders under `src/`.
- [ ] Add the contribution matrix to `README.md` and `report/REPORT_NHOM.md`.
- [ ] Push the integration branch and document the branch workflow for the team.
- [ ] Verify `git status`, branch names, and remote tracking before inviting contributions.

## Task 2: Lock the shared corpus

**Owners:** Đào Minh Chiến, Lương Minh Quân, Lê Đăng Tấn, and Nguyễn Đăng Long.

- [ ] Keep the approved niche as TikTok Shop Vietnam after-sales operations.
- [ ] Assign each source document to one curator and preserve the official source URL, retrieval date, and document version.
- [ ] Keep seven approved Markdown documents under `data/tiktok_shop_after_sales/`.
- [ ] Keep `sources.csv` one-to-one with the seven Markdown documents.
- [ ] Validate required metadata on every document, including `customer_role`, `category`, `source_url`, `retrieved_at`, and `document_version`.
- [ ] Require at least two values for `customer_role`, with both `buyer` and `seller` present.
- [ ] Do not change the corpus after benchmark execution begins without recording a new version.

## Task 3: Lock the five benchmark queries

**Owners:** One query per member, with Vũ Hữu An performing the final consistency check.

- [ ] Nguyễn Đăng Long owns Q1 about the buyer's 48-hour second request window.
- [ ] Đào Minh Chiến owns Q2 about the three return methods.
- [ ] Lương Minh Quân owns Q3 about the seller's three-business-day reimbursement documents.
- [ ] Lê Đăng Tấn owns Q4 about TikTok Shop Mall change-of-mind return shipping responsibility.
- [ ] Vũ Hữu An owns Q5 about automatic approval when a seller takes no action.
- [ ] Store all five queries, gold answers, metadata filters, expected document IDs, and evidence phrases in `benchmarks/tiktok_shop_after_sales.json`.
- [ ] Verify every evidence phrase exists in the expected document before any strategy is benchmarked.

## Task 4: Complete the personal core implementation

**Owner:** Every member in their personal repository.

- [ ] Create Python 3.11 virtual environments and install the core requirements.
- [ ] Record the expected starter baseline of 11 passing and 31 failing tests.
- [ ] Implement `SentenceChunker`, `RecursiveChunker`, `compute_similarity`, and `ChunkingStrategyComparator`.
- [ ] Implement the in-memory `EmbeddingStore` and metadata pre-filtering.
- [ ] Implement `KnowledgeBaseAgent` with numbered source context and an empty-store response.
- [ ] Run focused tests after each component and the full `python -m pytest tests -v` command.
- [ ] Do not modify tests or public class and function interfaces.

## Task 5: Implement and document personal strategies

**Owners:** Each member owns one distinct strategy.

- [ ] Nguyễn Đăng Long implements heading-aware chunks with recursive fallback and preserves headings on child chunks.
- [ ] Đào Minh Chiến implements sentence groups with a documented sentence limit.
- [ ] Lương Minh Quân tunes recursive separators and chunk size for policy sections.
- [ ] Lê Đăng Tấn tunes fixed-size chunk size and overlap.
- [ ] Vũ Hữu An implements a distinct tuned fixed-size or FAQ-section strategy after confirming it does not duplicate another member.
- [ ] Each member writes the rationale and expected trade-off in their `src/K4_.../strategy_notes.md`.

## Task 6: Run the common benchmark

**Owner:** Vũ Hữu An maintains the runner, and every member runs it with their own strategy.

- [ ] Use the same corpus, five queries, embedding model, and top-k value for every member.
- [ ] Run one unfiltered search and one metadata-filtered search for every query.
- [ ] Record top-3 score, document ID, chunk index, evidence phrase presence, and a short content preview.
- [ ] Prefer the local multilingual embedder for benchmark measurement and record its exact model name.
- [ ] Keep mock embedding results only as a technical baseline and label them as non-semantic.
- [ ] Save each member's output to their strategy folder and summarize the result in their personal report.

## Task 7: Analyze quality and failure

**Owners:** Every member analyzes their own strategy, and Vũ Hữu An consolidates the comparison.

- [ ] Compare retrieval precision, chunk coherence, metadata utility, and grounding quality.
- [ ] Identify at least one query where the top-3 is wrong or incomplete.
- [ ] Record the exact retrieved evidence, the likely cause, and one concrete improvement.
- [ ] Do not claim a strategy is better from mock scores alone.

## Task 8: Complete reports and demo

**Owners:** Nguyễn Đăng Long integrates, Vũ Hữu An coordinates the demo, and all members supply their sections.

- [ ] Complete each `REPORT_CANHAN.md` with warm-up, approach, test output, predictions, and personal benchmark results.
- [ ] Complete `REPORT_NHOM.md` with corpus inventory, metadata schema, baseline, five strategies, five queries, comparison, filter A/B, failure case, and contribution matrix.
- [ ] Prepare a six-to-eight-minute demo covering sources, strategies, comparison, filter impact, and failure analysis.
- [ ] Ensure no personal report is copied from another member's strategy or benchmark output.

## Task 9: Final verification and submission

**Owner:** Nguyễn Đăng Long runs the final checklist, and all members verify their own repositories.

- [ ] Run `python -m pytest tests -v` and confirm 42 passing tests in every personal repository.
- [ ] Run the corpus validator and confirm seven documents, matching `sources.csv`, both required roles, and five queries.
- [ ] Run each benchmark entrypoint and confirm top-3 output is reproducible.
- [ ] Run `git diff --check` and verify no `.env`, API key, `.venv`, model cache, or local database is tracked.
- [ ] Commit with descriptive messages, push each personal branch, and submit the required GitHub link on VLearn.
- [ ] Keep the final branch and repository names aligned with the instructor's naming convention.

## Definition of Done

- The five members are listed in `README.md` with correct names and student IDs.
- The shared corpus and five benchmark queries are approved and traceable.
- Every personal repository passes all 42 tests.
- Every member has a distinct strategy folder and personal report.
- The group report includes measurable comparison, metadata A/B evidence, and one failure case.
- The demo and submission links are ready.
