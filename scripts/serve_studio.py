#!/usr/bin/env python3
"""
Abyss Tattoo Studio — Byte-Range Capable Live Preview Server (0.0.0.0:8080)
Supports full HTTP 206 Partial Content for instant 60fps <video> A/B scrubbing.
"""
from __future__ import annotations

import mimetypes
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
EXTERNAL_4K_DIR = Path("/tmp/masters_4k")
RANGE_RE = re.compile(r"bytes=(\d+)-(\d*)")


class StudioHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def resolve_target(self, raw_path: str) -> Path | None:
        clean = unquote(raw_path.split("?", 1)[0]).lstrip("/")
        if clean in ("", "promos", "promos/"):
            return ROOT / "promos" / "index.html"
        cand = (ROOT / clean).resolve()
        if str(cand).startswith(str(ROOT)) and cand.is_file():
            return cand
        if clean.startswith("promos/"):
            ext_cand = (EXTERNAL_4K_DIR / Path(clean).name).resolve()
            if ext_cand.is_file():
                return ext_cand
        return None

    def do_HEAD(self) -> None:
        self._serve(send_body=False)

    def do_GET(self) -> None:
        self._serve(send_body=True)

    def _serve(self, send_body: bool) -> None:
        target = self.resolve_target(self.path)
        if target is None:
            self.send_error(404, "Not Found")
            return

        size = target.stat().st_size
        ctype, _ = mimetypes.guess_type(str(target))
        ctype = ctype or "application/octet-stream"
        range_hdr = self.headers.get("Range")

        start, end = 0, size - 1
        status = 200
        if range_hdr:
            m = RANGE_RE.match(range_hdr.strip())
            if m:
                start = int(m.group(1))
                end = int(m.group(2)) if m.group(2) else size - 1
                end = min(end, size - 1)
                if start < size:
                    status = 206

        length = end - start + 1
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "public, max-age=300")
        if status == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()

        if send_body:
            with target.open("rb") as fh:
                fh.seek(start)
                rem = length
                while rem > 0:
                    chunk = fh.read(min(262144, rem))
                    if not chunk:
                        break
                    try:
                        self.wfile.write(chunk)
                    except (BrokenPipeError, ConnectionResetError):
                        break
                    rem -= len(chunk)

    def log_message(self, fmt: str, *args) -> None:
        return


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    srv = ThreadingHTTPServer(("0.0.0.0", port), StudioHandler)
    print(f"Abyss Neural Remaster Studio listening on http://0.0.0.0:{port}", flush=True)
    srv.serve_forever()
