"""Local UI API contracts and fixture-only product flow."""
from http.client import HTTPConnection
from http.server import HTTPServer
from pathlib import Path
import json
import tempfile
from threading import Thread
import unittest

from backend.app.application.demo import DemoService
from backend.app.ui import handler


class DemoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.service = DemoService(self.temp.name)

    def complete(self, scenario="normal", **changes):
        values = {**self.service.settings()["demo"], "scenario": scenario, **changes}
        run = self.service.create(values)
        state = self.service.get(run["run_id"])
        for _ in range(30):
            if not state["can_continue"]:
                return state
            state = self.service.advance(run["run_id"])
        self.fail("Run exceeded stage limit")

    def test_complete_five_company_flow_and_read_only_reload(self):
        state = self.complete()
        self.assertEqual(state["status"], "success")
        self.assertEqual(len(state["allocation"]["weights"]), 5)
        self.assertEqual(len(state["reports"]), 10)
        self.assertEqual(state["usage"]["model_calls_reserved"], 11)
        self.assertEqual(state["usage"]["calls_with_unknown_total_usage"], 11)
        self.assertEqual(DemoService(self.temp.name).get(state["run_id"]), state)
        self.assertEqual(self.service.list_runs()[0]["run_id"], state["run_id"])

    def test_failure_paths_never_expose_allocation(self):
        for scenario, expected in (("missing_evidence", "insufficient_candidates"), ("review_rejected", "review_rejected")):
            state = self.complete(scenario)
            self.assertEqual(state["status"], expected)
            self.assertIsNone(state["allocation"])
        state = self.complete(min_candidates=5, excluded_symbols=["XOM"])
        self.assertEqual(state["status"], "insufficient_candidates")
        self.assertIsNone(state["allocation"])

    def test_quota_requires_explicit_retry(self):
        state = self.complete("quota")
        self.assertEqual(state["status"], "awaiting_quota")
        count = state["usage"]["model_calls_reserved"]
        self.assertEqual(self.service.advance(state["run_id"])["usage"]["model_calls_reserved"], count)
        state = self.service.advance(state["run_id"], retry=True)
        self.assertEqual(state["status"], "checkpointed")
        while state["can_continue"]:
            state = self.service.advance(state["run_id"] )
        self.assertEqual(state["status"], "success")
        self.assertEqual(state["usage" ]["model_calls_reserved"], 12)

    def test_invalid_policy_and_path_rejected(self):
        values = self.service.settings()["demo"]
        for changes in ({"capital": "-1"}, {"max_asset_weight": "0.1"}, {"symbols": ["UNKNOWN"]}, {"scenario": "live"}, {"min_candidates": True}):
            with self.assertRaises((ValueError, TypeError)):
                self.service.create({**values, **changes})
        with self.assertRaises(ValueError):
            self.service.get("../secret")

    def test_excluded_company_is_visible_but_not_researched(self):
        state = self.complete(excluded_symbols=["XOM"])
        self.assertEqual(state["status"], "success")
        self.assertNotIn("XOM", state["allocation"]["weights"])
        self.assertNotIn("news:XOM", state["reports"])
        excluded = next(d for d in state["selection"]["decisions"] if d["symbol"] == "XOM")
        self.assertIn("policy:explicit_exclusion", excluded["reasons"])

    def test_http_static_api_origin_and_schema(self):
        # HTTP boundary tests do not require an npm build; browser smoke tests exercise the real bundle.
        dist = Path(self.temp.name) / "dist"
        (dist / "assets").mkdir(parents=True)
        (dist / "index.html").write_text("<title>Agent of Odds</title>", encoding="utf-8")
        (dist / "assets" / "app.js").write_text("export {};", encoding="utf-8")
        server = HTTPServer(("127.0.0.1", 0), handler(self.service, dist))
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        def call(method, path, data=None, headers=None):
            connection = HTTPConnection("127.0.0.1", server.server_port)
            connection.request(method, path, body=json.dumps(data) if data is not None else None,
                               headers=headers or ({"Content-Type": "application/json"} if data is not None else {}))
            response = connection.getresponse()
            body = response.read()
            result = response.status, body, dict(response.getheaders())
            connection.close()
            return result
        status, body, headers = call("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn(b"Agent of Odds", body)
        self.assertIn("Content-Security-Policy", headers)
        self.assertEqual(call("GET", "/assets/app.js")[0], 200)
        self.assertEqual(call("GET", "/assets/../../.env")[0], 404)
        self.assertEqual(call("GET", "/src/main.jsx")[0], 404)
        (dist / "index.html").unlink()
        self.assertEqual(call("GET", "/")[0], 503)
        self.assertEqual(call("GET", "/.env")[0], 404)
        self.assertEqual(call("POST", "/api/runs", self.service.settings()["demo"],
                              {"Content-Type": "application/json", "Origin": "https://untrusted.example"})[0], 403)
        self.assertEqual(call("POST", "/api/runs", {})[0], 400)
        status, body, _ = call("POST", "/api/runs", self.service.settings()["demo"])
        self.assertEqual(status, 201)
        run_id = json.loads(body)["run_id"]
        status, body, _ = call("POST", f"/api/runs/{run_id}/advance", {"retry": False})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["status"], "checkpointed")


if __name__ == "__main__":
    unittest.main()

