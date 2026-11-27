"""FormSense: read an HTML form, explain each field, check the answers you plan to give."""
import datetime, json, re
from html.parser import HTMLParser

# Hand-made knowledge: (regex on name/label/placeholder, meaning, what to enter, document hint)
KNOWLEDGE = [
    (r"national.?id|id.?number|الرقم القومي|رقم قومي|بطاقة", "Your national ID number.", "Egyptian national ID: 14 digits, no spaces.", "National ID card"),
    (r"passport|جواز", "Your passport number.", "Exactly as printed on the passport page.", "Passport"),
    (r"e-?mail|بريد", "Your email address.", "An address you can read now. Confirmation codes and decisions are often sent here.", None),
    (r"phone|mobile|tel\b|موبايل|هاتف|تليفون|رقم الجوال", "A phone number the organisation can call or text.", "With country code if the form accepts it, for example +20 10 1234 5678.", None),
    (r"birth|dob|date.?of.?birth|تاريخ الميلاد|ميلاد", "Your date of birth.", "Same as your ID. The form may want a specific format (day/month/year).", "Birth certificate or ID"),
    (r"first.?name|given|الاسم الأول", "Your first (given) name.", "As written in your ID or passport, not a nickname.", None),
    (r"last.?name|surname|family|اسم العائلة", "Your family name.", "As written in your ID or passport.", None),
    (r"full.?name|^name$|الاسم", "Your full legal name.", "As written in your ID or passport, in the language the form asks for.", None),
    (r"employ|employer|company|current.?job|previous.?work|work.?experience|جهة العمل|الوظيفة", "Where you work or worked.", "Company name, your position and the dates (from, to).", "Experience letter or contract (if asked)"),
    (r"salary|income|الراتب|الدخل", "How much you earn.", "A number in the currency the form names; say monthly or yearly as asked.", "Payslip or income proof (often)"),
    (r"gpa|grade|معدل|تقدير", "Your academic result.", "The value on your transcript, on the scale the form states.", "Transcript"),
    (r"graduat|degree|مؤهل|تخرج", "Your qualification and when you got it.", "Degree name, university and graduation year.", "Degree certificate"),
    (r"address|عنوان", "Where you live (or receive mail).", "Street, city, governorate. Use the address that matches your documents.", "Proof of address (sometimes)"),
    (r"nationality|جنسية", "Your citizenship.", "As on your passport.", None),
    (r"gender|sex|الجنس|النوع", "Your gender as in your documents.", "Pick the option that matches your ID.", None),
    (r"password|كلمة المرور|كلمه السر", "A secret you will use to log in.", "Long and unique. Do not reuse another site's password.", None),
    (r"cv|resume|سيرة", "Your CV.", "Usually a PDF; check the size limit.", "CV file"),
    (r"statement|essay|cover.?letter|motivation|why|خطاب", "A written answer about you.", "Specific to this program or job. Check the length limit.", None),
    (r"referee|reference|recommend|توصية", "A person who can vouch for you.", "Name, relation to you, email and phone. Ask them first.", None),
    (r"terms|agree|consent|موافق|الشروط", "Your agreement to the rules.", "Read the linked terms before ticking.", None),
]
KIND_HINT = {"email": "email address", "tel": "phone number", "date": "date", "number": "number", "url": "web address",
             "file": "file upload", "password": "password", "checkbox": "tick box", "radio": "choose one", "select": "choose from a list",
             "textarea": "long text", "text": "short text"}
NEEDS_RE = re.compile(r"\*|required|إجباري|مطلوب", re.I)
OPT_RE = re.compile(r"optional|if applicable|اختياري", re.I)
HIDDEN_KINDS = {"hidden", "submit", "button", "reset", "image"}


class _F(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.fields, self.labels, self.cur_label, self.recent, self.sel = [], {}, None, "", None
        self.legend, self.in_legend, self.title, self.in_title = "", False, "", False
        self.in_ta, self.ta = False, None

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == "title": self.in_title = True
        if t == "legend": self.in_legend, self.legend = True, ""
        if t == "label":
            self.cur_label = {"for": a.get("for"), "text": ""}
        if t == "input":
            self._add(a, a.get("type", "text").lower())
        elif t == "textarea":
            self.ta = self._add(a, "textarea")
        elif t == "select":
            self.sel = self._add(a, "select"); self.sel["options"] = []
        elif t == "option" and self.sel is not None:
            self.sel["_opt"] = a.get("value", None); self.sel["options"].append("")
        elif t == "fieldset":
            self.legend = ""

    def _add(self, a, kind):
        f = {"kind": kind, "name": a.get("name") or a.get("id") or "", "id": a.get("id"), "required": "required" in a or a.get("aria-required") == "true",
             "placeholder": a.get("placeholder", ""), "aria": a.get("aria-label", ""), "maxlength": a.get("maxlength"), "minlength": a.get("minlength"),
             "pattern": a.get("pattern"), "min": a.get("min"), "max": a.get("max"), "accept": a.get("accept"), "multiple": "multiple" in a,
             "wrap_label": self.cur_label, "group": self.legend.strip(), "title": a.get("title", ""), "value": a.get("value")}
        self.fields.append(f)
        return f

    def handle_endtag(self, t):
        if t == "title": self.in_title = False
        if t == "legend": self.in_legend = False
        if t == "label" and self.cur_label:
            if self.cur_label["for"]:
                self.labels[self.cur_label["for"]] = self.cur_label["text"].strip()
            self.cur_label = None
        if t == "select": self.sel = None
        if t == "textarea": self.ta = None

    def handle_data(self, d):
        if self.in_title: self.title += d
        if self.in_legend: self.legend += d
        if self.cur_label is not None and self.sel is None: self.cur_label["text"] += d
        if self.sel is not None and self.sel["options"] and not d.isspace(): self.sel["options"][-1] += d.strip()


def parse(html):
    p = _F(); p.feed(html)
    out = []
    for f in p.fields:
        if f["kind"] in HIDDEN_KINDS: continue
        label = ""
        if f["id"] and f["id"] in p.labels: label = p.labels[f["id"]]
        elif f["wrap_label"] and f["wrap_label"]["text"].strip(): label = f["wrap_label"]["text"].strip()
        elif f["aria"]: label = f["aria"]
        elif f["title"]: label = f["title"]
        elif f["placeholder"]: label = f["placeholder"]
        label = re.sub(r"\s+", " ", label)
        f["label"] = label or f["name"] or "(no label)"
        f["label_missing"] = not label
        out.append(f)
    # radio buttons with the same name are one question
    seen, res = {}, []
    for f in out:
        if f["kind"] in ("radio",) and f["name"] in seen:
            seen[f["name"]].setdefault("choices", []).append(f.get("value") or f["label"]); continue
        if f["kind"] == "radio":
            f["choices"] = [f.get("value") or f["label"]]; f["label"] = f["group"] or f["name"]; seen[f["name"]] = f
        res.append(f)
    return p.title.strip(), res


def explain(f):
    hay = " ".join([f["name"], f["label"], f["placeholder"], f["group"]]).lower()
    meaning = enter = doc = None
    for rx, m, e, d in KNOWLEDGE:
        if re.search(rx, hay, re.I): meaning, enter, doc = m, e, d; break
    required = bool(f["required"] or (NEEDS_RE.search(f["label"]) and not OPT_RE.search(f["label"])))
    req_src = "marked required in the form" if f["required"] else ("label has a * or 'required'" if required else None)
    notes = []
    if f["maxlength"]: notes.append(f"at most {f['maxlength']} characters")
    if f["minlength"]: notes.append(f"at least {f['minlength']} characters")
    if f["min"] or f["max"]: notes.append(f"allowed range {f['min'] or '-'} to {f['max'] or '-'}")
    if f["pattern"]: notes.append(f"must match the pattern {f['pattern']}")
    if f["accept"]: notes.append(f"accepted file types: {f['accept']}")
    if f["kind"] == "select" and f.get("options"): notes.append("choose one of: " + ", ".join(o for o in f["options"] if o)[:200])
    if f["kind"] == "radio": notes.append("choose one of: " + ", ".join(f["choices"]))
    if f["kind"] == "file" and not doc: doc = "a file (see accepted types)"
    return {"label": f["label"], "name": f["name"], "type": KIND_HINT.get(f["kind"], f["kind"]),
            "required": required, "required_source": req_src,
            "meaning": meaning or "No built-in explanation for this field name. Read the label and any help text on the page.",
            "enter": enter or f"A {KIND_HINT.get(f['kind'], 'value')}.", "document": doc, "limits": notes,
            "explained": bool(meaning), "label_missing": f["label_missing"]}


def nid_info(v):
    """Egyptian national ID (14 digits): century digit, YYMMDD, governorate, serial, gender digit, check digit."""
    if not re.fullmatch(r"\d{14}", v): return None
    c = {"2": 1900, "3": 2000}.get(v[0])
    if not c: return None
    try:
        d = datetime.date(c + int(v[1:3]), int(v[3:5]), int(v[5:7]))
    except ValueError:
        return None
    return {"birth": d, "gender": "male" if int(v[12]) % 2 else "female", "gov": v[7:9]}


def check(fields, answers):
    """answers: {field name or label: value}. Returns list of (level, field, message)."""
    issues, byname = [], {}
    for f in fields:
        key = f["name"] if f["name"] in answers else (f["label"] if f["label"] in answers else None)
        if key is None:
            if explain(f)["required"] and f["kind"] not in ("checkbox",) or (f["kind"] == "checkbox" and f["required"]):
                issues.append(("MISSING", f["label"], "required field has no answer"))
            continue
        v = str(answers[key]).strip(); byname[f["name"] or f["label"]] = v
        e = explain(f)
        if e["required"] and not v: issues.append(("MISSING", f["label"], "required field is empty"))
        if v and f["maxlength"] and len(v) > int(f["maxlength"]): issues.append(("ERROR", f["label"], f"{len(v)} characters, the limit is {f['maxlength']}"))
        if v and f["minlength"] and len(v) < int(f["minlength"]): issues.append(("ERROR", f["label"], f"{len(v)} characters, the minimum is {f['minlength']}"))
        if v and f["pattern"]:
            try:
                if not re.fullmatch(f["pattern"], v): issues.append(("ERROR", f["label"], f"does not match the form's pattern {f['pattern']}"))
            except re.error: pass
        if v and f["kind"] == "email" and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", v): issues.append(("ERROR", f["label"], "does not look like an email address"))
        if v and f["kind"] in ("number",):
            try:
                n = float(v)
                if f["min"] and n < float(f["min"]): issues.append(("ERROR", f["label"], f"below the minimum {f['min']}"))
                if f["max"] and n > float(f["max"]): issues.append(("ERROR", f["label"], f"above the maximum {f['max']}"))
            except ValueError: issues.append(("ERROR", f["label"], "not a number"))
        if v and f["kind"] == "select" and f.get("options") and v not in f["options"]: issues.append(("ERROR", f["label"], "not one of the listed options"))
        if v and f["kind"] == "radio" and v not in f["choices"]: issues.append(("ERROR", f["label"], "not one of the listed choices"))
        hay = (f["name"] + " " + f["label"]).lower()
        if v and re.search(r"national.?id|الرقم القومي|رقم قومي", hay) and not re.fullmatch(r"\d{14}", v):
            issues.append(("WARNING", f["label"], "an Egyptian national ID has 14 digits"))
    # cross-field checks that do not need to understand the form
    vals = {k: v for k, v in byname.items()}
    def find(rx):
        for k, v in vals.items():
            if re.search(rx, k, re.I): return k, v
        return None, None
    _, nid = find(r"national.?id|الرقم القومي|رقم قومي")
    _, dob = find(r"birth|dob|ميلاد")
    info = nid_info(nid) if nid else None
    if nid and re.fullmatch(r"\d{14}", nid) and not info:
        issues.append(("WARNING", "national ID", "14 digits, but the century digit or the date inside is not valid"))
    if info and dob:
        try:
            d = datetime.date.fromisoformat(dob)
            if d != info["birth"]: issues.append(("CONFLICT", "date of birth vs national ID", f"the ID number encodes {info['birth']}, you wrote {dob}"))
        except ValueError: pass
    _, g = find(r"gender|sex|الجنس")
    if info and g and g.lower() in ("male", "female", "ذكر", "أنثى", "انثى"):
        gg = "male" if g.lower() in ("male", "ذكر") else "female"
        if gg != info["gender"]: issues.append(("CONFLICT", "gender vs national ID", f"the ID number encodes {info['gender']}, you wrote {g}"))
    ek, es = find(r"employment.?status|work.?status|حالة العمل")
    ck, cv = find(r"employer|company|current.?job|previous.?employ|جهة العمل")
    if es and cv and re.search(r"unemploy|student|not working|عاطل|طالب", es, re.I):
        issues.append(("CONFLICT", "employment status vs employer", f"status is '{es}' but an employer/company is filled in"))
    if es and ck is not None and not cv and re.fullmatch(r"(?i)employed|full.?time|part.?time|موظف", es):
        issues.append(("CONFLICT", "employment status vs employer", f"status is '{es}' but no employer is given"))
    sk, sv = find(r"start|from|arriv|check.?in|بداية|من تاريخ"); ek2, ev = find(r"\bend\b|\bto\b|until|depart|check.?out|نهاية|إلى تاريخ")
    try:
        if sv and ev and datetime.date.fromisoformat(ev) < datetime.date.fromisoformat(sv):
            issues.append(("CONFLICT", "dates", f"end date {ev} is before start date {sv}"))
    except ValueError: pass
    _, p1 = find(r"^password$|كلمة المرور$"); _, p2 = find(r"confirm|repeat|تأكيد")
    if p1 and p2 and p1 != p2: issues.append(("CONFLICT", "password", "the two password fields differ"))
    return issues


def fetch_html(src):
    if re.match(r"https?://", src):
        import urllib.request
        req = urllib.request.Request(src, headers={"User-Agent": "FormSense/0.1"})
        return urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "replace")
    return open(src, encoding="utf-8", errors="replace").read()
