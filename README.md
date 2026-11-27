# FormSense

[![tests](https://github.com/mohamed-elshamy-ai/formsense/actions/workflows/tests.yml/badge.svg)](https://github.com/mohamed-elshamy-ai/formsense/actions/workflows/tests.yml) ![tests: 9 passing](https://img.shields.io/badge/tests-9%20passing-brightgreen) ![license: MIT](https://img.shields.io/badge/license-MIT-blue)

Understand a web form before you fill it. FormSense reads the form's HTML, explains each field (what it means, what to enter, whether it is required, which document to have ready), and checks the answers you plan to give for mistakes and conflicts. By default everything runs on your computer and no AI is used. An optional AI helper exists and is off unless you turn it on (see [Optional AI help](#optional-ai-help-off-by-default)).

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

**Try it without installing:** [browser demo](https://mohamed-elshamy-ai.github.io/formsense/demo.html). Paste form HTML and answers; it runs the same Python in your browser via Pyodide (about 10 MB download the first time, loaded from jsDelivr). Nothing you paste is uploaded. The demo has no AI option.

**No Python?** Download a standalone file from [Releases](https://github.com/mohamed-elshamy-ai/formsense/releases/tag/v0.2.1) (Linux, Windows, macOS Apple-silicon). They are **not code-signed**: Windows SmartScreen and macOS Gatekeeper will probably warn, and you can compare the file with `SHA256SUMS.txt`. Built by GitHub Actions from the tag; only the Linux file was run by a person (it printed correct output on the demo). The Windows and macOS files passed an automatic `--help` check only.

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

## Optional AI help (off by default)

The rules only know about 20 field types. For other fields, and for problems nobody wrote a rule for, you can ask an AI model for a second opinion. Nothing is sent unless you pass `--ai` on that run. There is no config file, no stored key, and no background call.

```
formsense form.html --ai ollama                       # local model, nothing leaves your computer
formsense form.html --ai ollama --ai-dry-run          # show exactly what would be sent, send nothing
formsense form.html --answers a.json --ai ollama --ai-with-answers
formsense form.html --ai openai-compatible --ai-url https://HOST/v1 --ai-key-env MY_KEY --model NAME
```

| Backend | Where data goes | Cost |
|---|---|---|
| `ollama` (default model `qwen2.5:1.5b`) | Your own computer, `localhost:11434`. Nothing leaves it. | Free. You install [Ollama](https://ollama.com) and download a model yourself. |
| `openai-compatible` | The server you name with `--ai-url`, using the key in the environment variable you name. | Your provider's terms. A free tier may exist. |

**What is sent.** Without `--ai-with-answers`: the form title, and for fields the rules could not explain, each field's label, type, name and up to 15 option texts. With `--ai-with-answers`: also your answers, except text areas and files, which are never sent. Passwords are replaced by `<hidden>`, emails by `<email>`, and digit runs of 6 or more keep only their first two digits (an ID number becomes `30************`). Names and other plain words are sent as written, so use the local backend for anything private. Use `--ai-dry-run` to see the exact payload.

**What the AI may do.** Explain unknown fields and flag things that look odd. It is told not to suggest values to enter, and the tool prints only explanations and problem notes. It never changes a rule-based result, fills in or submits anything. Its lines are printed in a separate block marked "unverified". If the backend is unreachable or errors, you get the normal rules-only output plus one line saying the AI step was skipped.

**Limits, from real runs.** Tested on Linux with Ollama and `qwen2.5:1.5b` (a small model, CPU only, 40 to 50 seconds per run) on the demo forms in [`demo/ai/`](demo/ai/). It wrote plausible explanations of ordinary fields, sometimes guessed wrong context (it assumed a "visa holder" from a form title), and its "problems" notes were mostly noise: it missed an arrival date after the departure date and a negative distance, and invented unrelated "checks". Treat the output as a prompt to read the form again, not as a finding. Larger models will likely do better; that is untested here. Hosted providers are untested here (no key). Free tiers can use what you send to improve their products; for example the Gemini API's free tier terms say so, and the paid tier says it does not (see [Google's pricing page](https://ai.google.dev/gemini-api/docs/pricing)). Read your provider's terms before sending anything personal. The unit tests use a mock server and need no model or network.

## Limitations

- It reads static HTML. Forms built by JavaScript (many single-page sites), forms inside images or PDFs, and multi-step forms where later fields appear after you answer are not seen. There is no screenshot/OCR mode and no browser extension yet.
- The explanations come from a hand-made table of about 20 common field types (English and Arabic names). A field it does not know gets the honest line "No built-in explanation for this field name" plus its type and limits. It does not invent a meaning. There is no AI model.
- "Required" comes from the form's own `required` attribute or a `*` / "required" in the label. A site that checks requirements only on the server will look optional here.
- Conflict checks are a short list: ID number vs birth date and gender (Egyptian 14-digit layout: century digit, date, odd/even digit for gender, as publicly documented; not checked against any government system), employment status vs employer, end date before start date, two password fields that differ, plus the form's own limits (length, range, pattern, options). It cannot find a contradiction in free text.
- The conflict rules match fields by their `name` attribute and label. A form that names its dates `arr` and `dep` gets no date-order check (found in testing; the AI helper did not catch it either).
- It cannot tell you whether your answers will be accepted or are true.

## Related tools

[Form-Sherpa](https://github.com/Bipan101/Form-Sherpa) explains fields while it autofills using on-device AI. FormSense is rule-based by default: no model, so every explanation is traceable, but it knows only about 20 field types and reads static HTML.

## Technical notes

[ARCHITECTURE.md](ARCHITECTURE.md), Arabic and English. 9 pytest tests on the sample form (`pytest`): field parsing, label linking, radio groups, required detection, document hints, limits, unknown fields, the conflict checks, and a clean set of answers that passes. Output: [`demo/test-output.txt`](demo/test-output.txt).

## How it works

FormSense reads the form's HTML and extracts every field (input, select, textarea and radio groups), linking each field to its label. It then looks the field name up in a small hand-written table (national ID, email, mobile number, employer, GPA and so on) and tells you what it means, what to enter and which document you need. A field counts as required when it has the `required` attribute or a `*` mark. If a field is unknown, it says so instead of guessing. If you put your planned answers in a JSON file, it checks length, pattern and allowed choices, and compares answers with each other (for example an Egyptian national ID encodes the birth date and gender, so a mismatch is reported as a conflict). Forms built with JavaScript, and images, are not supported.
