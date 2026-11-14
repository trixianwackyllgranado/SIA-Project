"""Runs http_json against a real local HTTP server (no internet needed)."""
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from app import http_json


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/not-json":
            self._reply(200, b"<html>maintenance</html>")
        else:
            self._reply(200, json.dumps({"agent": self.headers["User-Agent"]}).encode())

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self._reply(401, json.dumps({"key": self.headers["x-api-key"], "got": body}).encode())

    def _reply(self, status, data):
        self.send_response(status)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


class HttpJsonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), Handler)
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_get_json(self):
        status, reply = http_json.request_json(self.base + "/ok")
        self.assertEqual(status, 200)
        self.assertEqual(reply["agent"], http_json.USER_AGENT)

    def test_error_status_returned_with_body(self):
        status, reply = http_json.request_json(self.base + "/send", method="POST",
                                               headers={"x-api-key": "k"}, payload={"a": 1})
        self.assertEqual((status, reply), (401, {"key": "k", "got": {"a": 1}}))

    def test_non_json_reply(self):
        with self.assertRaises(http_json.NetworkError):
            http_json.request_json(self.base + "/not-json")

    def test_unreachable_server(self):
        with self.assertRaises(http_json.NetworkError):
            http_json.request_json("http://127.0.0.1:1/", timeout=2)


if __name__ == "__main__":
    unittest.main()
