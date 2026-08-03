from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, render_template, request, stream_with_context

from .services import CatalogService, ChatClient, ConfigurationError, LLMError, OpenAIChatClient

ROOT_DIR = Path(__file__).resolve().parents[1]
UI_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data" / "k4_asos_products"


def create_app(llm: ChatClient | None = None, data_dir: Path = DATA_DIR) -> Flask:
    load_dotenv(UI_DIR / ".env", override=False)
    load_dotenv(ROOT_DIR / ".env", override=False)
    app = Flask(__name__)
    startup_error = None
    try:
        active_llm = llm or OpenAIChatClient.from_environment()
    except ConfigurationError as error:
        active_llm, startup_error = None, str(error)
    service = CatalogService(data_dir, active_llm)

    @app.get("/")
    def index() -> str:
        return render_template("index.html", startup_error=startup_error, product_count=len(service.products))

    @app.get("/api/products")
    def products():
        return jsonify({"products": [product.to_dict() for product in service.products], "count": len(service.products), "catalog_path": "data/k4_asos_products"})

    @app.post("/api/chat")
    def chat():
        payload: dict[str, Any] = request.get_json(silent=True) or {}
        message, history, top_k = payload.get("message"), payload.get("history", []), payload.get("top_k", 3)
        if not isinstance(message, str) or not message.strip():
            return jsonify({"error": "message phải là chuỗi không rỗng"}), 400
        if len(message) > 1000:
            return jsonify({"error": "message tối đa 1000 ký tự"}), 400
        if not isinstance(history, list):
            return jsonify({"error": "history phải là danh sách"}), 400
        if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= 10:
            return jsonify({"error": "top_k phải là số nguyên từ 1 đến 10"}), 400
        def sse_event(event: dict[str, Any]) -> str:
            event_type = event.pop("type")
            return f"event: {event_type}\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"

        @stream_with_context
        def event_stream():
            try:
                for event in service.stream_answer(message, history, top_k):
                    yield sse_event(event)
            except (ConfigurationError, LLMError) as error:
                yield sse_event({"type": "error", "error": str(error)})

        return Response(event_stream(), mimetype="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
