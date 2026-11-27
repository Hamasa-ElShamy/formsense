import argparse, json, sys
from . import core, ai


def main(argv=None):
    ap = argparse.ArgumentParser(prog="formsense", description="Explain a web form's fields and check your planned answers.")
    ap.add_argument("source", help="an .html file or a URL (forms that need login or JavaScript are not supported)")
    ap.add_argument("--answers", help="JSON file with your planned answers: {\"field name\": \"value\"}")
    ap.add_argument("--json", action="store_true")
    g = ap.add_argument_group("optional AI help (off by default)")
    g.add_argument("--ai", choices=["ollama", "openai-compatible"], help="explain unknown fields; ollama = local, nothing leaves your computer")
    g.add_argument("--model"); g.add_argument("--ai-url", help="base URL, e.g. https://host/v1 (required for openai-compatible)")
    g.add_argument("--ai-key-env", help="name of the environment variable that holds your API key")
    g.add_argument("--ai-with-answers", action="store_true", help="also send your (masked) answers to look for problems")
    g.add_argument("--ai-dry-run", action="store_true", help="print exactly what would be sent, send nothing")
    o = ap.parse_args(argv)
    title, fields = core.parse(core.fetch_html(o.source))
    ex = [core.explain(f) for f in fields]
    ans = json.load(open(o.answers, encoding="utf-8")) if o.answers else None
    aires = aierr = None
    if o.ai:
        payload = ai.build_payload(title, fields, ex, ans if o.ai_with_answers else None)
        if o.ai_dry_run:
            print(f"DRY RUN: this would be sent to {o.ai_url or ai.DEFAULT_URL.get(o.ai)}:")
            print(json.dumps(payload, ensure_ascii=False, indent=1)); return
        if payload["unexplained_fields"] or "answers" in payload:
            raw, aierr = ai.ask(o.ai, payload, o.model, o.ai_url, o.ai_key_env)
            aires = ai.clean(raw, payload) if raw else None
    if o.json:
        out = {"fields": ex}
        if ans is not None: out["check"] = [list(i) for i in core.check(fields, ans)]
        if o.ai: out["ai"] = {"label": "unverified AI suggestion", "backend": o.ai, "result": aires, "error": aierr}
        print(json.dumps(out if o.ai or ans is not None else ex, ensure_ascii=False, indent=1)); return
    print(f"FORM: {title or o.source}  ({len(ex)} fields, {sum(e['required'] for e in ex)} required)\n")
    for i, e in enumerate(ex, 1):
        print(f"{i}. Field: {e['label']}   [{e['type']}]  Required: {'YES' if e['required'] else 'no'}"
              + (f" ({e['required_source']})" if e["required_source"] else ""))
        print(f"   Meaning: {e['meaning']}\n   Enter:   {e['enter']}")
        if e["document"]: print(f"   Have ready: {e['document']}")
        for n in e["limits"]: print(f"   Rule: {n}")
        if e["label_missing"]: print("   Note: the form gives this field no label.")
        print()
    iss = []
    if ans is not None:
        iss = core.check(fields, ans)
        print("CHECK OF YOUR ANSWERS")
        for lv, f, m in iss: print(f"  {lv}: {f}: {m}")
        if not iss: print("  nothing found (this does not prove the form will accept it)")
    if o.ai:
        print(f"\nAI SUGGESTIONS (unverified, from {o.ai}; the rule-based results above are unchanged)")
        if aierr: print(f"  AI step skipped: {aierr}. Rules-only output is complete.")
        elif aires:
            for x in aires["fields"]: print(f"  Field: {x['label']}\n    Maybe means: {x['meaning']}\n    Kind of answer: {x['enter']}")
            for x in aires["problems"]: print(f"  Check: {', '.join(x['fields']) or 'several fields'}: {x['issue']}")
            if not aires["fields"] and not aires["problems"]: print("  nothing to add")
        else: print("  nothing to ask: every field was explained by the rules")
    if ans is not None: sys.exit(1 if iss else 0)


if __name__ == "__main__":
    main()
