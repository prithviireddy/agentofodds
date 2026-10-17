"""Loopback-only fixture UI; start with uv run --locked python -m backend.app.ui."""
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import sqlite3
from urllib.parse import urlsplit
from pathlib import Path

from backend.app.application.demo import DemoService, ROOT
from backend.app.domain.paper import PaperError


def handler(service, frontend_directory=None):
    dist = Path(frontend_directory or ROOT / "frontend" / "dist").resolve()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def reply(self, code, value, content_type="application/json"):
            body = json.dumps(value, allow_nan=False).encode() if content_type == "application/json" else value
            self.send_response(code)
            self.send_header("Content-Type", content_type + "; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(body)

        def allowed(self):
            host = self.headers.get("Host", "")
            expected = f"127.0.0.1:{self.server.server_port}"
            origin = self.headers.get("Origin")
            return host == expected and (origin is None or origin == "http://" + expected)

        def do_GET(self):
            if not self.allowed():
                return self.reply(403, {"status": "forbidden"})
            path = urlsplit(self.path).path
            try:
                requested = "index.html" if path == "/" else path.removeprefix("/")
                asset = (dist / requested).resolve()
                if path == "/" and not asset.is_file():
                    return self.reply(503, {"status": "frontend_not_built", "reason": "Run npm ci and npm run build in frontend/."})
                if path == "/" or path.startswith("/assets/"):
                    if dist.resolve() not in asset.parents:
                        return self.reply(404, {"status": "not_found"})
                    if asset.is_file():
                        kinds = {".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".svg": "image/svg+xml"}
                        return self.reply(200, asset.read_bytes(), kinds.get(asset.suffix, "application/octet-stream"))
                if path == "/api/settings":
                    return self.reply(200, service.settings())
                if path == "/api/runs":
                    return self.reply(200, service.list_runs())
                if path.startswith("/api/runs/") and path.endswith("/valuations"):
                    return self.reply(200, service.monitoring.get(path[len("/api/runs/"):-len("/valuations")]))
                if path.startswith("/api/runs/") and path.endswith("/paper"):
                    run_id = path[len("/api/runs/"):-len("/paper")]
                    receipt = service.paper.get(run_id)
                    return self.reply(200, receipt or service.paper.preview(run_id))
                if path.startswith("/api/runs/"):
                    return self.reply(200, service.get(path.removeprefix("/api/runs/")))
                return self.reply(404, {"status": "not_found"})
            except PaperError as exc:
                return self.reply(409, {"status": exc.status, "reason": str(exc)})
            except sqlite3.Error:
                return self.reply(409, {"status": "ledger_storage_error", "reason": "Paper ledger could not be read safely."})
            except FileNotFoundError:
                return self.reply(404, {"status": "not_found"})
            except (ValueError, TypeError, KeyError, OSError):
                return self.reply(400, {"status": "failed_validation", "reason": "Run unavailable, corrupt or invalid."})

        def do_POST(self):
            if not self.allowed() or self.headers.get("Content-Type") != "application/json":
                return self.reply(403, {"status": "forbidden"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 16384:
                    raise ValueError("Request must be between 1 and 16,384 bytes")
                payload = json.loads(self.rfile.read(length), parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite JSON")))
                path = urlsplit(self.path).path
                if path == "/api/runs":
                    return self.reply(201, service.create(payload))
                if path.startswith("/api/runs/") and path.endswith("/valuations"):
                    if not isinstance(payload, dict) or set(payload) != {"valuation_at"} or not isinstance(payload["valuation_at"], str):
                        raise ValueError("Supply one explicit valuation_at fixture timestamp")
                    return self.reply(200, service.monitoring.update(path[len("/api/runs/"):-len("/valuations")], payload["valuation_at"]))
                if path.startswith("/api/runs/") and path.endswith("/approve-paper"):
                    if not isinstance(payload, dict) or set(payload) != {"approved", "proposal_id"}:
                        raise PaperError("approval_required", "Submit the exact preview ID and explicit approval")
                    run_id = path[len("/api/runs/"):-len("/approve-paper")]
                    return self.reply(200, service.paper.approve(run_id, payload["proposal_id"], payload["approved"]))
                if path.startswith("/api/runs/") and path.endswith("/advance"):
                    if not isinstance(payload, dict) or set(payload) != {"retry"} or type(payload["retry"]) is not bool:
                        raise ValueError("Explicit boolean retry setting required")
                    return self.reply(200, service.advance(path[len("/api/runs/"):-len("/advance")], payload["retry"]))
                return self.reply(404, {"status": "not_found"})
            except PaperError as exc:
                return self.reply(409, {"status": exc.status, "reason": str(exc)})
            except sqlite3.Error:
                return self.reply(409, {"status": "ledger_storage_error", "reason": "Approval was not confirmed. Reload before retrying."})
            except (ValueError, TypeError, KeyError, ArithmeticError, OSError) as exc:
                return self.reply(400, {"status": "failed_validation", "reason": str(exc) if isinstance(exc, ValueError) else "Invalid or unavailable fixture input."})
    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--fixture-set", choices=("five", "twenty"), default="five")
    args = parser.parse_args()
    server = HTTPServer(("127.0.0.1", args.port), handler(DemoService(fixture_set=args.fixture_set)))
    print(f"Agent of Odds fixture UI: http://127.0.0.1:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
