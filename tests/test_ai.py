import json, threading, http.server, io, contextlib, os
from formsense import ai, cli, core

HTML = os.path.join(os.path.dirname(__file__), "..", "demo", "ai", "odd1.html")
SEEN = []


class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        SEEN.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
        out = {"fields": [{"label": "Port of entry", "meaning": "m", "enter": "e"}, {"label": "NOT ASKED", "meaning": "x", "enter": "y"}], "problems": []}
        b = json.dumps({"choices": [{"message": {"content": json.dumps(out)}}]}).encode()
        self.send_response(200); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def log_message(self, *a): pass


def run(argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try: cli.main(argv)
        except SystemExit: pass
    return buf.getvalue()


def test_mask():
    assert ai.mask("text", "30212345678901") == "30************"
    assert ai.mask("email", "a@b.com") == "<email>"
    assert ai.mask("password", "hunter2") == "<hidden>"
    assert ai.mask("date", "2002-05-14") == "2002-05-14"


def test_off_by_default_sends_nothing():
    SEEN.clear(); out = run([HTML])
    assert "AI SUGGESTIONS" not in out and not SEEN


def test_dry_run_sends_nothing():
    out = run([HTML, "--ai", "ollama", "--ai-dry-run"])
    assert "DRY RUN" in out and "Port of entry" in out


def test_mock_backend_and_filtering():
    srv = http.server.HTTPServer(("127.0.0.1", 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_port}/v1"
    out = run([HTML, "--ai", "openai-compatible", "--ai-url", url, "--model", "x"])
    assert "unverified" in out and "Port of entry" in out and "NOT ASKED" not in out
    assert "answers" not in SEEN[-1]["messages"][1]["content"]
    srv.shutdown()


def test_unreachable_falls_back():
    out = run([HTML, "--ai", "openai-compatible", "--ai-url", "http://127.0.0.1:9/v1"])
    assert "AI step skipped" in out and "FORM:" in out
