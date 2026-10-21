#!/usr/bin/env python3
"""Servidor HTTP con soporte nativo de Range Requests (HTTP 206) para streaming instantáneo MP4."""

import os
import re
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


class RangeHTTPRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/?"):
            self.path = "/reel.html"
        return super().do_GET()

    def do_HEAD(self):
        if self.path in ("/", "/?"):
            self.path = "/reel.html"
        return super().do_HEAD()

    def send_head(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path) or "Range" not in self.headers or not os.path.isfile(path):
            return super().send_head()
        m = re.match(r"bytes=(\d+)-(\d*)", self.headers["Range"])
        if not m:
            return super().send_head()
        f = open(path, "rb")
        fs = os.fstat(f.fileno())
        size = fs.st_size
        start = int(m.group(1))
        end = int(m.group(2)) if m.group(2) else size - 1
        end = min(end, size - 1)
        if start >= size:
            f.close()
            self.send_error(416, "Requested Range Not Satisfiable")
            return None
        self.send_response(206)
        self.send_header("Content-type", self.guess_type(path))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        f.seek(start)
        self._range_len = end - start + 1
        return f

    def copyfile(self, source, outputfile):
        rem = getattr(self, "_range_len", None)
        if rem is None:
            return super().copyfile(source, outputfile)
        self._range_len = None
        while rem > 0:
            buf = source.read(min(65536, rem))
            if not buf:
                break
            outputfile.write(buf)
            rem -= len(buf)


if __name__ == "__main__":
    os.chdir("/home/user/abysstattoo")
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    srv = ThreadingHTTPServer(("0.0.0.0", port), RangeHTTPRequestHandler)
    print(f"Serving Abyss preview on 0.0.0.0:{port}", flush=True)
    srv.serve_forever()
