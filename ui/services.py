from __future__ import annotations

import os
import re
import time
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterator, Protocol


class ConfigurationError(RuntimeError):
    """Raised when server-side LLM configuration is unavailable."""


class LLMError(RuntimeError):
    """Raised when a provider request fails."""


@dataclass(frozen=True)
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float | None = None


@dataclass(frozen=True)
class Completion:
    text: str
    usage: Usage


@dataclass(frozen=True)
class StreamChunk:
    text: str = ""
    usage: Usage | None = None


@dataclass(frozen=True)
class Product:
    id: str
    name: str
    brand: str
    category: str
    category_group: str
    price_gbp: float | None
    price_basis: str
    color: str
    features: list[str]
    sizes_in_stock: list[str]
    in_stock: bool
    source_url: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RetrievedProduct:
    product: Product
    score: int
    matched_fields: list[str]

    def to_dict(self) -> dict[str, Any]:
        data = self.product.to_dict()
        data.update({"score": self.score, "matched_fields": self.matched_fields})
        return data


@dataclass(frozen=True)
class ChatResult:
    answer: str
    retrieved: list[RetrievedProduct]
    metrics: dict[str, Any]


class ChatClient(Protocol):
    def complete(self, messages: list[dict[str, str]]) -> Completion: ...
    def stream(self, messages: list[dict[str, str]]) -> Iterator[StreamChunk]: ...


class OpenAIChatClient:
    """Server-side OpenAI-compatible client exposing provider usage metrics."""

    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        if not api_key or not base_url or not model:
            raise ConfigurationError("Cần OPENAI_API_KEY, OPENAI_BASE_URL và OPENAI_MODEL trong .env")
        try:
            from openai import OpenAI
        except ImportError as error:
            raise ConfigurationError("Chưa cài gói openai; hãy cài ui/requirements.txt") from error
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self._input_cost_per_million = _optional_float("OPENAI_INPUT_COST_PER_1M")
        self._output_cost_per_million = _optional_float("OPENAI_OUTPUT_COST_PER_1M")

    @classmethod
    def from_environment(cls) -> "OpenAIChatClient":
        return cls(os.getenv("OPENAI_API_KEY", "").strip(), os.getenv("OPENAI_BASE_URL", "").strip(), os.getenv("OPENAI_MODEL", "").strip())

    def complete(self, messages: list[dict[str, str]]) -> Completion:
        try:
            response = self._client.chat.completions.create(model=self._model, messages=messages)
            text = response.choices[0].message.content
        except Exception as error:  # provider-specific exception types vary
            raise LLMError("Không thể gọi dịch vụ LLM. Hãy kiểm tra base URL, API key và model.") from error
        if not text or not text.strip():
            raise LLMError("LLM không trả về nội dung")
        usage_object = getattr(response, "usage", None)
        prompt_tokens = int(getattr(usage_object, "prompt_tokens", 0) or 0)
        completion_tokens = int(getattr(usage_object, "completion_tokens", 0) or 0)
        total_tokens = int(getattr(usage_object, "total_tokens", prompt_tokens + completion_tokens) or 0)
        cost = None
        if self._input_cost_per_million is not None and self._output_cost_per_million is not None:
            cost = (prompt_tokens * self._input_cost_per_million + completion_tokens * self._output_cost_per_million) / 1_000_000
        return Completion(text.strip(), Usage(prompt_tokens, completion_tokens, total_tokens, cost))

    def stream(self, messages: list[dict[str, str]]) -> Iterator[StreamChunk]:
        kwargs: dict[str, Any] = {"model": self._model, "messages": messages, "stream": True}
        try:
            stream = self._client.chat.completions.create(**kwargs, stream_options={"include_usage": True})
        except Exception:
            try:
                stream = self._client.chat.completions.create(**kwargs)
            except Exception as error:
                raise LLMError("Không thể gọi dịch vụ LLM. Hãy kiểm tra base URL, API key và model.") from error
        try:
            for chunk in stream:
                usage_object = getattr(chunk, "usage", None)
                if usage_object:
                    prompt = int(getattr(usage_object, "prompt_tokens", 0) or 0)
                    completion = int(getattr(usage_object, "completion_tokens", 0) or 0)
                    total = int(getattr(usage_object, "total_tokens", prompt + completion) or 0)
                    cost = None
                    if self._input_cost_per_million is not None and self._output_cost_per_million is not None:
                        cost = (prompt * self._input_cost_per_million + completion * self._output_cost_per_million) / 1_000_000
                    yield StreamChunk(usage=Usage(prompt, completion, total, cost))
                choices = getattr(chunk, "choices", [])
                if choices:
                    text = getattr(getattr(choices[0], "delta", None), "content", None)
                    if text:
                        yield StreamChunk(text=text)
        except LLMError:
            raise
        except Exception as error:
            raise LLMError("Luồng phản hồi từ LLM đã bị gián đoạn.") from error


def _optional_float(name: str) -> float | None:
    raw = os.getenv(name, "").strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _normalise(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.casefold())
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn").replace("đ", "d")


def _parse_front_matter(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.DOTALL)
    if not match:
        raise ValueError(f"{path.name} không có front matter")
    metadata: dict[str, str] = {}
    for line in match.group(1).splitlines():
        key, separator, value = line.partition(":")
        if separator:
            metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata, match.group(2)


def _section_bullets(body: str, heading: str) -> list[str]:
    match = re.search(rf"^### {re.escape(heading)}\s*\n(.*?)(?=^### |^---|\Z)", body, re.MULTILINE | re.DOTALL)
    if not match:
        return []
    return [line.removeprefix("- ").strip() for line in match.group(1).splitlines() if line.startswith("-")]


def load_products(data_dir: str | Path) -> list[Product]:
    """Read the supplied ASOS Markdown corpus; no product catalog is invented."""
    records: list[Product] = []
    for path in sorted(Path(data_dir).glob("*.md")):
        metadata, body = _parse_front_matter(path)
        try:
            price = float(metadata["price_gbp"])
        except (KeyError, ValueError):
            price = None
        sizes = _section_bullets(body, "Kich co (size)")
        stock_values = []
        for value in sizes:
            if value.lower().startswith("con hang:"):
                stock_values.extend(part.strip() for part in value.split(":", 1)[1].split(",") if part.strip())
        records.append(Product(
            id=metadata.get("doc_id", path.stem), name=metadata.get("title", path.stem),
            brand=metadata.get("brand", "not-stated").replace("-", " ").title(),
            category=metadata.get("category", "uncategorised").replace("-", " ").title(),
            category_group=metadata.get("category_group", "other"), price_gbp=price,
            price_basis=metadata.get("price_basis", "standard"), color=metadata.get("color", "not-stated"),
            features=_section_bullets(body, "Dac diem"), sizes_in_stock=stock_values,
            in_stock=bool(stock_values), source_url=metadata.get("source_url", ""),
        ))
    if not records:
        raise ConfigurationError(f"Không tìm thấy product listing trong {data_dir}")
    return records


class CatalogService:
    """Searches the pulled product corpus and grounds LLM answers in its matches."""

    CHAT_PROMPT = """Bạn là trợ lý tư vấn sản phẩm ASOS bằng tiếng Việt. Chỉ dùng thông tin
trong SẢN PHẨM ĐÃ TRUY XUẤT, gồm giá GBP, màu, sizes, tình trạng và đặc điểm. Không tự
bịa sản phẩm hay thông tin. Khi không có kết quả, nói rõ không tìm thấy trong catalog.
Trả lời ngắn, trực tiếp và nêu các sản phẩm phù hợp nhất."""

    def __init__(self, data_dir: str | Path, llm: ChatClient | None = None) -> None:
        self._products = load_products(data_dir)
        self._llm = llm

    @property
    def products(self) -> list[Product]:
        return list(self._products)

    def search(self, query: str, top_k: int = 3) -> list[RetrievedProduct]:
        tokens = [token for token in re.findall(r"[a-z0-9]+", _normalise(query)) if len(token) > 1]
        results: list[RetrievedProduct] = []
        for product in self._products:
            fields = {
                "Tên": _normalise(product.name), "Thương hiệu": _normalise(product.brand),
                "Danh mục": _normalise(product.category), "Nhóm": _normalise(product.category_group),
                "Màu": _normalise(product.color), "Đặc điểm": _normalise(" ".join(product.features)),
            }
            weights = {"Tên": 5, "Thương hiệu": 4, "Danh mục": 4, "Nhóm": 3, "Màu": 3, "Đặc điểm": 1}
            matched = [label for label, content in fields.items() if any(token in content for token in tokens)]
            score = sum(weights[label] for label in matched)
            if score:
                results.append(RetrievedProduct(product, score, matched))
        results.sort(key=lambda item: (-item.score, item.product.name.casefold()))
        return results[:max(0, top_k)]

    def answer(self, message: str, history: list[dict[str, str]] | None = None) -> ChatResult:
        if self._llm is None:
            raise ConfigurationError("LLM chưa được cấu hình. Catalog vẫn có thể xem, nhưng chưa thể chat.")
        started = time.perf_counter()
        retrieved = self.search(message)
        context = "\n\n".join(_product_context(item.product) for item in retrieved) or "Không có sản phẩm phù hợp."
        messages = [{"role": "system", "content": self.CHAT_PROMPT}, *_clean_history(history or []), {
            "role": "user", "content": f"SẢN PHẨM ĐÃ TRUY XUẤT:\n{context}\n\nCÂU HỎI: {message.strip()}"
        }]
        completion = self._llm.complete(messages)
        latency_ms = round((time.perf_counter() - started) * 1000)
        return ChatResult(completion.text, retrieved, {
            "latency_ms": latency_ms, "prompt_tokens": completion.usage.prompt_tokens,
            "completion_tokens": completion.usage.completion_tokens, "total_tokens": completion.usage.total_tokens,
            "cost_usd": completion.usage.cost_usd, "retrieve_count": len(retrieved),
            "retrieve_where": "data/k4_asos_products", "retrieval_strategy": "weighted lexical metadata search",
            "retrieved_doc_ids": [item.product.id for item in retrieved],
        })

    def stream_answer(self, message: str, history: list[dict[str, str]] | None = None) -> Iterator[dict[str, Any]]:
        """Yield retrieval evidence, text deltas, then final observability metrics."""
        if self._llm is None:
            raise ConfigurationError("LLM chưa được cấu hình. Catalog vẫn có thể xem, nhưng chưa thể chat.")
        started = time.perf_counter()
        retrieved = self.search(message)
        context = "\n\n".join(_product_context(item.product) for item in retrieved) or "Không có sản phẩm phù hợp."
        messages = [{"role": "system", "content": self.CHAT_PROMPT}, *_clean_history(history or []), {
            "role": "user", "content": f"SẢN PHẨM ĐÃ TRUY XUẤT:\n{context}\n\nCÂU HỎI: {message.strip()}"
        }]
        yield {"type": "retrieval", "products": [item.to_dict() for item in retrieved]}
        usage = Usage()
        for chunk in self._llm.stream(messages):
            if chunk.text:
                yield {"type": "delta", "text": chunk.text}
            if chunk.usage is not None:
                usage = chunk.usage
        latency_ms = round((time.perf_counter() - started) * 1000)
        yield {"type": "done", "metrics": {
            "latency_ms": latency_ms, "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens, "total_tokens": usage.total_tokens,
            "cost_usd": usage.cost_usd, "retrieve_count": len(retrieved),
            "retrieve_where": "data/k4_asos_products", "retrieval_strategy": "weighted lexical metadata search",
            "retrieved_doc_ids": [item.product.id for item in retrieved],
        }}


def _product_context(product: Product) -> str:
    price = f"GBP {product.price_gbp:.2f}" if product.price_gbp is not None else "not-stated"
    return f"{product.name}\nBrand: {product.brand}; Category: {product.category}; Price: {price}; Color: {product.color}; In stock: {product.in_stock}; Sizes: {', '.join(product.sizes_in_stock) or 'not-stated'}; Features: {'; '.join(product.features)}"


def _clean_history(history: list[dict[str, str]]) -> list[dict[str, str]]:
    cleaned = []
    for item in history[-6:]:
        if isinstance(item, dict) and item.get("role") in {"user", "assistant"} and isinstance(item.get("content"), str) and item["content"].strip():
            cleaned.append({"role": item["role"], "content": item["content"].strip()[:2000]})
    return cleaned
