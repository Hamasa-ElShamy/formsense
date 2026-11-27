"""Optional AI help. Off unless --ai is given. Standard library only.

Sends only what build_payload() returns (see --ai-dry-run). Output is always
labelled as an unverified suggestion and never changes a rule-based result.
"""
import json, os, re, urllib.request, urllib.error

DEFAULT_URL = {"ollama": "http://localhost:11434/v1"}
TIMEOUT = 15
SYSTEM = ("You help a person understand a web form before they fill it in. "
          "Reply with JSON only. Never suggest values to enter. Never invent facts about the "
          "organisation behind the form. If unsure, say you are unsure. In \"meaning\" explain what the field is for in general; never repeat the person's answer.")


def mask(kind, value):
    """Hide the parts of an answer that identify a person. Dates and plain words are kept."""
    if kind == "password": return "<hidden>"
    v = re.sub(r"[^@\s]+@[^@\s]+\.[^@\s]+", "<email>", str(value))
    return re.sub(r"\d{6,}", lambda m: m.group(0)[:2] + "*" * (len(m.group(0)) - 2), v)


def build_payload(title, fields, explained, answers=None):
    """explained: list from core.explain (same order as fields)."""
    unknown = [{"label": f["label"], "type": f["kind"], "name": f["name"],
                "options": (f.get("options") or f.get("choices") or [])[:15]}
               for f, e in zip(fields, explained) if not e["explained"]]
    p = {"form_title": title, "unexplained_fields": unknown}
    if answers is not None:
        given = []
        for f in fields:
            k = f["name"] if f["name"] in answers else (f["label"] if f["label"] in answers else None)
            if k is not None and f["kind"] not in ("textarea", "file"): given.append({"label": f["label"], "type": f["kind"], "answer": mask(f["kind"], answers[k])})
        p["answers"] = given
    return p


def prompt(payload):
    ask = ['Return {"fields":[{"label":"...","meaning":"one or two sentences","enter":"what kind of thing to write"}]} for "unexplained_fields".']
    if "answers" in payload:
        ask.append('Also return "problems":[{"fields":["label",...],"issue":"one sentence"}] for things in "answers" that look inconsistent with each other or odd for the field. Use [] if none. Digits may be masked with *; do not complain about masking.')
    return "FORM DATA:\n" + json.dumps(payload, ensure_ascii=False, indent=1) + "\n\n" + " ".join(ask)


def ask(backend, payload, model=None, url=None, key_env=None):
    """Returns (result_dict, None) or (None, error_text)."""
    base = (url or DEFAULT_URL.get(backend) or "").rstrip("/")
    if not base: return None, "no --ai-url given"
    headers = {"Content-Type": "application/json"}
    if key_env:
        key = os.environ.get(key_env)
        if not key: return None, f"environment variable {key_env} is empty"
        headers["Authorization"] = "Bearer " + key
    body = {"model": model or ("qwen2.5:1.5b" if backend == "ollama" else ""), "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt(payload)}]}
    req = urllib.request.Request(base + "/chat/completions", json.dumps(body).encode(), headers)
    try:
        raw = json.load(urllib.request.urlopen(req, timeout=TIMEOUT if backend != "ollama" else 120))
        txt = raw["choices"][0]["message"]["content"]
        m = re.search(r"\{.*\}", txt, re.S)
        return json.loads(m.group(0)), None
    except urllib.error.HTTPError as e: return None, f"provider answered HTTP {e.code}"
    except Exception as e: return None, f"{type(e).__name__}: {e}"[:160]


def clean(res, payload):
    """Keep only well-formed text, only for labels we asked about."""
    asked = {f["label"] for f in payload["unexplained_fields"]}
    labels = {a["label"] for a in payload.get("answers", [])}
    s = lambda x: x.strip()[:300] if isinstance(x, str) else ""
    fl = [{"label": s(x.get("label")), "meaning": s(x.get("meaning")), "enter": s(x.get("enter"))}
          for x in res.get("fields", []) if isinstance(x, dict) and x.get("label") in asked]
    pr = [{"fields": [s(l) for l in x.get("fields", []) if isinstance(l, str) and l in labels],
           "issue": s(x.get("issue"))}
          for x in res.get("problems", []) if isinstance(x, dict) and x.get("issue")] if "answers" in payload else []
    return {"fields": fl, "problems": pr}
