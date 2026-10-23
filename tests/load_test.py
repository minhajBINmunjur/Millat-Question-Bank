#!/usr/bin/env python3
import json
import math
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parent.parent


class QuietHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, format, *args):
        return

    def do_HEAD(self):
        super().do_HEAD()


def percentile(sorted_vals, p):
    if not sorted_vals:
        return 0
    idx = min(len(sorted_vals) - 1, max(0, math.ceil((p / 100) * len(sorted_vals)) - 1))
    return sorted_vals[idx]


def fetch(base, path, method="GET"):
    req = Request(base + path, method=method)
    with urlopen(req, timeout=30) as res:
        body = res.read() if method != "HEAD" else b""
        headers = {k.lower(): v for k, v in res.headers.items()}
        return res.status, headers, body


def flood(label, worker, n, concurrency):
    times = []
    errors = 0

    def one(_i):
        t0 = time.perf_counter()
        ok = worker(_i)
        ms = (time.perf_counter() - t0) * 1000
        return ok, ms

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futs = [pool.submit(one, i) for i in range(n)]
        for fut in as_completed(futs):
            ok, ms = fut.result()
            times.append(ms)
            if not ok:
                errors += 1
    times.sort()
    return {
        "label": label,
        "n": n,
        "concurrency": concurrency,
        "errors": errors,
        "errorRate": errors / n,
        "p50_ms": round(percentile(times, 50), 3),
        "p95_ms": round(percentile(times, 95), 3),
        "p99_ms": round(percentile(times, 99), 3),
        "max_ms": round(times[-1], 3) if times else 0,
    }


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    base = f"http://{host}:{port}"
    try:
        status, _, body = fetch(base, "/")
        if status != 200 or b"Millat Question Bank" not in body:
            raise SystemExit("index.html GET failed")

        pdf_path = "/pdfs/tongi_physics-2nd_test_2024.pdf"
        missing_path = "/pdfs/tongi_physics-1st_test_2021.pdf"

        status, headers, _ = fetch(base, pdf_path, method="HEAD")
        ctype = headers.get("content-type", "")
        if status != 200:
            raise SystemExit(f"existing PDF HEAD failed: {status} {ctype}")
        if ctype and "pdf" not in ctype.lower() and "octet-stream" not in ctype.lower():
            raise SystemExit(f"existing PDF HEAD unexpected type: {ctype}")

        try:
            fetch(base, missing_path, method="HEAD")
            raise SystemExit("missing PDF should 404")
        except HTTPError as exc:
            if exc.code != 404:
                raise SystemExit(f"missing PDF unexpected status {exc.code}")

        status, _, body = fetch(base, pdf_path)
        if status != 200 or not body.startswith(b"%PDF"):
            raise SystemExit("existing PDF GET failed")

        def html_ok(_i):
            st, _, _b = fetch(base, "/")
            return st == 200

        def pdf_ok(_i):
            st, hdrs, _b = fetch(base, pdf_path)
            ctype = hdrs.get("content-type", "").lower()
            return st == 200 and (not ctype or "pdf" in ctype or "octet-stream" in ctype)

        def mixed(i):
            path = "/" if i % 3 == 0 else pdf_path if i % 3 == 1 else missing_path
            method = "HEAD" if path.endswith(".pdf") and i % 2 == 0 else "GET"
            try:
                st, _, _b = fetch(base, path, method=method)
            except HTTPError as exc:
                st = exc.code
            if path == missing_path:
                return st == 404
            return st == 200

        report = {
            "environment": "local ThreadingHTTPServer (not Vercel production)",
            "base": base,
            "htmlLoad": flood("GET /index.html", html_ok, 400, 40),
            "pdfLoad": flood("GET existing PDF", pdf_ok, 80, 20),
            "mixLoad": flood("mixed HTML+HEAD PDF+404", mixed, 300, 30),
        }
        print(json.dumps(report, indent=2))
        print("\nLoad test finished against local static server (not Vercel production).")
        if any(item["errors"] for item in (report["htmlLoad"], report["pdfLoad"], report["mixLoad"])):
            raise SystemExit("load test recorded errors")
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
