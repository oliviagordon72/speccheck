"""Run with python app.py, then open http://127.0.0.1:3000."""
from __future__ import annotations

import argparse
import base64
import json
import os
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from core import (ROOT, SCENARIOS, Passage, demo_review, fingerprint, live_review,
                  parse_azure, parse_pdf, report)

DOCS: dict[str, dict] = {}
LOCK = threading.Lock()
SAMPLE = ROOT / "sample" / "SC100_Fictional_Datasheet.pdf"


def register(data, name, extractor, config):
    if extractor == "azure":
        passages, raw = parse_azure(data, config)
    else:
        passages, raw = parse_pdf(data), None
    entry = {"name": Path(name).name[:150], "sha256": fingerprint(data), "extractor": extractor,
             "passages": passages, "pdf": data, "azure_raw": raw}
    token = secrets.token_urlsafe(24)
    with LOCK:
        # Bound in-memory storage. No documents, keys, or answers are written to disk.
        while len(DOCS) >= 12:
            DOCS.pop(next(iter(DOCS)))
        DOCS[token] = entry
    return token, entry


class Handler(BaseHTTPRequestHandler):
    server_version = "SpecCheck/0.1"

    def log_message(self, *args):
        pass

    def respond(self, value, status=200, content_type="application/json"):
        data = json.dumps(value, ensure_ascii=False).encode() if content_type == "application/json" else value
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/":
            return self.respond((ROOT / "ui.html").read_bytes(), content_type="text/html; charset=utf-8")
        if path == "/api/info":
            return self.respond({"scenarios": [{"id": k, **v} for k,v in SCENARIOS.items()],
                "configured": {"openai": bool(os.getenv("OPENAI_API_KEY")),
                    "azure_ai": bool(os.getenv("AZURE_OPENAI_API_KEY")),
                    "azure_layout": bool(os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY"))}})
        if path == "/sample.pdf":
            return self.respond(SAMPLE.read_bytes(), content_type="application/pdf")
        if path.startswith("/pdf/"):
            with LOCK:
                entry = DOCS.get(path.removeprefix("/pdf/"))
            if entry:
                return self.respond(entry["pdf"], content_type="application/pdf")
        return self.respond({"error": "Not found"}, 404)

    def do_POST(self):
        origin = self.headers.get("Origin")
        if origin and urlsplit(origin).netloc != self.headers.get("Host"):
            return self.respond({"error": "Cross-origin requests are not allowed."}, 403)
        if "application/json" not in self.headers.get("Content-Type", ""):
            return self.respond({"error": "Expected JSON."}, 415)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 18*1024*1024:
                return self.respond({"error": "Request exceeds the prototype upload limit."}, 413)
            body = json.loads(self.rfile.read(length))
            path = urlsplit(self.path).path
            if path == "/api/sample":
                token, entry = register(SAMPLE.read_bytes(), SAMPLE.name, "local", {})
                return self.respond({"document_id": token, "name": entry["name"],
                    "extractor": "local", "passages": [p.model_dump() for p in entry["passages"]]})
            if path == "/api/upload":
                data = base64.b64decode(body.get("pdf_base64", ""), validate=True)
                extractor = body.get("extractor", "local")
                if extractor not in ("local", "azure"):
                    raise ValueError("Unknown extractor.")
                token, entry = register(data, body.get("name", "document.pdf"), extractor, body.get("config", {}))
                return self.respond({"document_id": token, "name": entry["name"], "extractor": extractor,
                    "passages": [p.model_dump() for p in entry["passages"]]})
            with LOCK:
                entry = DOCS.get(body.get("document_id"))
            if not entry:
                raise ValueError("Load a document first. If the server restarted, load it again.")
            if path == "/api/review":
                if body.get("mode") == "sample":
                    if entry["sha256"] != fingerprint(SAMPLE.read_bytes()):
                        raise ValueError("Sample rules apply only to the bundled fictional datasheet.")
                    result = demo_review(body.get("scenario", "wrong-limit"), entry["passages"])
                else:
                    result = live_review(entry["passages"], body.get("question", ""),
                        body.get("config", {}), body.get("answer", ""))
                meta = {k:entry[k] for k in ("name", "sha256", "extractor")}
                return self.respond(report(result, entry["passages"], meta))
            if path == "/api/extraction":
                return self.respond({"name": entry["name"], "extractor": entry["extractor"],
                    "sha256": entry["sha256"], "passages": [p.model_dump() for p in entry["passages"]],
                    "azure_raw": entry["azure_raw"]})
            return self.respond({"error": "Not found"}, 404)
        except (ValueError, KeyError, TypeError) as exc:
            return self.respond({"error": str(exc)}, 400)
        except Exception:
            return self.respond({"error": "This document could not be processed. Try an unencrypted PDF, or check the setup guide."}, 500)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "3000")))
    args = parser.parse_args()
    print(f"SpecCheck is running at http://{args.host}:{args.port}", flush=True)
    print("Local development app. Press Ctrl+C to stop. API keys and uploads are not written to disk.", flush=True)
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()
