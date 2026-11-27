import json, pathlib
from formsense import core
D = pathlib.Path(__file__).parent.parent / "demo"
title, F = core.parse((D / "scholarship.html").read_text())
E = {e["name"]: e for e in map(core.explain, F)}

def test_fields_and_hidden_skipped():
    assert title == "Scholarship Application 2027" and len(F) == 12 and "csrf" not in E
def test_required_and_optional():
    assert E["full_name"]["required"] and E["national_id"]["required"] and not E["employer"]["required"] and not E["phone"]["required"]
def test_label_for_and_fieldset_radio():
    assert E["national_id"]["label"] == "National ID number *" and E["gender"]["label"] == "Gender *" and "female" in E["gender"]["limits"][0]
def test_knowledge_and_document():
    assert "14 digits" in E["national_id"]["enter"] and E["cv"]["document"]
def test_limits_listed():
    assert any("500" in n for n in E["statement"]["limits"]) and any(".pdf" in n for n in E["cv"]["limits"])
def test_unknown_field_is_honest():
    t, f = core.parse('<label for="x">Zorp level</label><input id="x" name="zorp">')
    assert not core.explain(f[0])["explained"] and "No built-in explanation" in core.explain(f[0])["meaning"]
def test_answers_check():
    iss = core.check(F, json.loads((D / "answers.json").read_text()))
    txt = " | ".join(f"{a}:{b}:{c}" for a, b, c in iss)
    assert "ERROR:Email" in txt.replace("Email *", "Email") or "email address" in txt
    assert "national ID" in txt and "above the maximum 4" in txt and "employer" in txt and "gender vs national ID" in txt
    assert "MISSING:CV" in txt.replace("CV (PDF only) *", "CV")
def test_dob_conflict():
    iss = core.check(F, {"full_name": "A", "national_id": "30001011234577", "dob": "2002-05-14", "email": "a@b.co", "gender": "male"})
    assert any("encodes 2000-01-01" in m for _, _, m in iss)
def test_clean_answers():
    ok = {"full_name": "A B", "national_id": "30001011234577", "dob": "2000-01-01", "email": "a@b.co", "gender": "male", "employment_status": "Student",
          "gpa": "3.5", "statement": "x", "cv": "cv.pdf", "terms": "yes"}
    assert core.check(F, ok) == []


def test_bad_inputs_exit_cleanly(tmp_path):
    import subprocess, sys
    e = tmp_path / "e.html"; e.write_text("just text")
    j = tmp_path / "a.json"; j.write_text("{bad")
    ok = tmp_path / "f.html"; ok.write_text("<form><input name=email type=email></form>")
    for args in ([str(tmp_path / "missing.html")], [str(e)], [str(ok), "--answers", str(j)]):
        r = subprocess.run([sys.executable, "run_formsense.py", *args], capture_output=True, text=True)
        assert r.returncode != 0 and "Traceback" not in r.stderr and "formsense:" in r.stderr
