# FormSense

Understand a web form before you fill it. FormSense reads the form's HTML, explains each field (what it means, what to enter, whether it is required, which document to have ready), and checks the answers you plan to give for mistakes and conflicts. Everything runs on your computer. No AI service is used.

افهم الفورم قبل ما تملاه: الأداة بتقرا الفورم وبتشرحلك كل خانة (معناها، تكتب إيه، إجبارية ولا لا، محتاج أنهي مستند) وبتراجع إجاباتك على الأخطاء والتناقضات.

## Worked example

Form: [`demo/scholarship.html`](demo/scholarship.html). Planned answers: [`demo/answers.json`](demo/answers.json). Real output: [`demo/demo-output.txt`](demo/demo-output.txt).

```
$ formsense demo/scholarship.html --answers demo/answers.json
FORM: Scholarship Application 2027  (12 fields, 10 required)

2. Field: National ID number *   [short text]  Required: YES (marked required in the form)
   Meaning: Your national ID number.
   Enter:   Egyptian national ID: 14 digits, no spaces.
   Have ready: National ID card
   Rule: must match the pattern \d{14}
...
CHECK OF YOUR ANSWERS
  ERROR: Email *: does not look like an email address
  ERROR: GPA (out of 4) *: above the maximum 4
  MISSING: CV (PDF only) *: required field has no answer
  CONFLICT: date of birth vs national ID: the ID number encodes 2003-01-01, you wrote 2002-05-14
  CONFLICT: gender vs national ID: the ID number encodes female, you wrote male
  CONFLICT: employment status vs employer: status is 'Student' but an employer/company is filled in
```

## Install and use

```
git clone https://github.com/mohamed-elshamy-ai/formsense && cd formsense
pip install .
formsense form.html                          # explain every field of a saved page
formsense https://example.org/apply          # or a URL (public pages only)
formsense form.html --answers answers.json   # also check what you plan to write
```

Save a page from your browser with Ctrl+S ("HTML only") if the form is behind a login. `--json` prints the explanation as JSON.

| System | Status |
|---|---|
| Linux | Tested (Python 3.10). Standard library only. |
| Windows / macOS | Should work, not tested. |
| Android / browser extension | Not available. |

## What it does NOT do (honest)

- It reads static HTML. Forms built by JavaScript (many single-page sites), forms inside images or PDFs, and multi-step forms where later fields appear after you answer are not seen. There is no screenshot/OCR mode and no browser extension yet.
- The explanations come from a hand-made table of about 20 common field types (English and Arabic names). A field it does not know gets the honest line "No built-in explanation for this field name" plus its type and limits. It does not invent a meaning. There is no AI model.
- "Required" comes from the form's own `required` attribute or a `*` / "required" in the label. A site that checks requirements only on the server will look optional here.
- Conflict checks are a short list: ID number vs birth date and gender (Egyptian 14-digit layout: century digit, date, odd/even digit for gender, as publicly documented; not checked against any government system), employment status vs employer, end date before start date, two password fields that differ, plus the form's own limits (length, range, pattern, options). It cannot find a contradiction in free text.
- It cannot tell you whether your answers will be accepted or are true.

## Technical notes

[ARCHITECTURE.md](ARCHITECTURE.md), Arabic and English. 9 pytest tests on the sample form (`pytest`): field parsing, label linking, radio groups, required detection, document hints, limits, unknown fields, the conflict checks, and a clean set of answers that passes. Output: [`demo/test-output.txt`](demo/test-output.txt).

## How it works (بالعربي)

الأداة بتقرا كود HTML بتاع الفورم وبتطلع كل الحقول (input وselect وtextarea ومجموعات radio) وبتربط كل حقل بالـ label بتاعه. بعدين بتدور على اسم الحقل في جدول صغير مكتوب يدوي (الرقم القومي، الإيميل، الموبايل، جهة العمل، المعدل...) وبتقولك معناه وتكتب إيه ومحتاج مستند إيه. الحقل الإجباري بيتعرف من `required` أو علامة `*`. لو الحقل مش معروف بتقولك كده بصراحة ومش بتخمن. لو حطيت إجاباتك في ملف JSON بتراجع الطول والنمط والاختيارات، وبتقارن الإجابات ببعض (مثلاً الرقم القومي بيحتوي تاريخ الميلاد والنوع، فلو كتبت غيرهم بتطلع تناقض). الفورمات اللي بتتبني بـ JavaScript أو الصور مش مدعومة.

MIT License.
