import unittest

from .app import DATA_DIR, create_app
from .services import CatalogService, Completion, StreamChunk, Usage


class FakeLLM:
    def complete(self, messages):
        return Completion("Bershka white suit blazer in white là lựa chọn phù hợp.", Usage(120, 30, 150, 0.00021))

    def stream(self, messages):
        yield StreamChunk("**Bershka** là lựa chọn phù hợp. ")
        yield StreamChunk("Giá niêm yết là GBP 49.99.")
        yield StreamChunk(usage=Usage(120, 30, 150, 0.00021))


class ProductFinderTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(llm=FakeLLM())
        self.client = self.app.test_client()

    def test_catalog_loads_pulled_product_data(self):
        response = self.client.get("/api/products")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.json["count"], 20)
        self.assertEqual(response.json["catalog_path"], "data/k4_asos_products")

    def test_search_uses_product_metadata(self):
        service = CatalogService(DATA_DIR, FakeLLM())
        results = service.search("white blazer")
        self.assertTrue(results)
        self.assertIn("blazer", results[0].product.name.casefold())
        self.assertEqual(results[0].product.color, "white")

    def test_chat_streams_retrieval_and_usage_metrics(self):
        response = self.client.post("/api/chat", json={"message": "Tìm blazer màu trắng"})
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("event: retrieval", body)
        self.assertIn("event: delta", body)
        self.assertIn("event: done", body)
        self.assertIn('"total_tokens": 150', body)
        self.assertIn('"retrieve_where": "data/k4_asos_products"', body)

    def test_empty_chat_is_rejected(self):
        self.assertEqual(self.client.post("/api/chat", json={"message": " "}).status_code, 400)


if __name__ == "__main__":
    unittest.main()
