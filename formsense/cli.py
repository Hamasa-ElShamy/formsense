import argparse, json, sys
from . import core


def main(argv=None):
    ap = argparse.ArgumentParser(prog="formsense", description="Explain a web form's fields and check your planned answers.")
    ap.add_argument("source", help="an .html file or a URL (forms that need login or JavaScript are not supported)")
    ap.add_argument("--answers", help="JSON file with your planned answers: {\"field name\": \"value\"}")
    ap.add_argument("--json", action="store_true")
    o = ap.parse_args(argv)
    title, fields = core.parse(core.fetch_html(o.source))
    ex = [core.explain(f) for f in fields]
    if o.json:
        print(json.dumps(ex, ensure_ascii=False, indent=1)); return
    print(f"FORM: {title or o.source}  ({len(ex)} fields, {sum(e['required'] for e in ex)} required)\n")
    for i, e in enumerate(ex, 1):
        print(f"{i}. Field: {e['label']}   [{e['type']}]  Required: {'YES' if e['required'] else 'no'}"
              + (f" ({e['required_source']})" if e["required_source"] else ""))
        print(f"   Meaning: {e['meaning']}\n   Enter:   {e['enter']}")
        if e["document"]: print(f"   Have ready: {e['document']}")
        for n in e["limits"]: print(f"   Rule: {n}")
        if e["label_missing"]: print("   Note: the form gives this field no label.")
        print()
    if o.answers:
        ans = json.load(open(o.answers, encoding="utf-8"))
        iss = core.check(fields, ans)
        print("CHECK OF YOUR ANSWERS")
        for lv, f, m in iss: print(f"  {lv}: {f}: {m}")
        if not iss: print("  nothing found (this does not prove the form will accept it)")
        sys.exit(1 if iss else 0)


if __name__ == "__main__":
    main()
