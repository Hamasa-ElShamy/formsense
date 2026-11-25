# FormSense: technical notes / الشرح التقني

## English
- `parse(html)`: a standard-library `HTMLParser` collects `input`, `select` (with options) and `textarea`, skips hidden/submit/button, and links labels three ways: `label for=id`, a wrapping `label`, then `aria-label`, `title`, `placeholder`. Radio buttons with the same name become one question; a `fieldset legend` supplies its label.
- `explain(field)`: matches name, label, placeholder and group against a table of regular expressions (`KNOWLEDGE`, English and Arabic) giving meaning, what to enter and a document hint. Required = `required` / `aria-required`, or a `*` or "required" in the label unless the label says optional. Limits come from `maxlength`, `minlength`, `min`, `max`, `pattern`, `accept` and the option list.
- `check(fields, answers)`: per-field checks (missing required, length, range, pattern, email shape, option membership), then cross-field rules found by field name: `nid_info()` decodes the 14-digit Egyptian ID (digit 1 = century 2 or 3, digits 2 to 7 = YYMMDD, digit 13 odd = male) to compare with birth date and gender; employment status vs employer; end before start; password vs confirmation.
- `cli.py`: prints the explanation, then the check; exit code 1 if issues exist.

**Decisions**: no AI model, so every statement can be traced to a rule; unknown fields are reported as unknown; a conflict names both values.

**Limits**: static HTML only, a table of about 20 field types, a short list of conflict rules, nothing that needs JavaScript, OCR or a browser.

## بالعربي
`parse` بتطلع الحقول وتربطها بالـ labels. `explain` بتدور في جدول المعاني اليدوي وبتحدد الإجباري والحدود. `check` بتراجع إجاباتك وبتقارن الحقول ببعض (الرقم القومي مع تاريخ الميلاد والنوع، حالة العمل مع جهة العمل، تاريخ النهاية قبل البداية، كلمتين السر). مفيش نموذج ذكاء اصطناعي، فكل جملة ليها قاعدة واضحة. الحدود: HTML ثابت بس، وجدول صغير، وقواعد تناقض قليلة.
