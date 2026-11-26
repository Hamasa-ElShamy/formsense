# formsense design system

Read this before changing the site's UI. Do not introduce a new direction; extend this one. English only. Values below come from `docs/index.html` as of this commit.

## Concept

An annotated form: a note beside each field says what to enter, and conflicts are flagged in red.

Theme: light.

## Color tokens

| Token | Value | Role |
|---|---|---|
| `--bg` | `#f6f3ff` | page background |
| `--fg` | `#1e1b3a` | body text |
| `--mut` | `#6b6591` | secondary text (AA on bg) |
| `--card` | `#ffffff` | card and panel surface |
| `--line` | `#ddd6f5` | borders and dividers |
| `--acc` | `#7c3aed` | primary action, links, focus ring |
| `--accfg` | `#fff` | text on accent |
| `--code` | `#1e1b3a` | code block background |
| `--codefg` | `#e9e3ff` | code block text |
| `--warn` | `#d97706` | warning border and limits |

Contrast: every text node on the page is checked against WCAG AA (4.5:1, 3:1 for large text) with a script in the repo owner's QA harness. Keep it passing when you change a color.

## Type

| Token | Stack | Role |
|---|---|---|
| `--arabic` | `'IBM Plex Sans Arabic',sans-serif` | Arabic font stack |
| `--body` | `'Work Sans','IBM Plex Sans Arabic',system-ui,sans-serif` | body font stack |
| `--head` | `'Archivo','IBM Plex Sans Arabic',system-ui,sans-serif` | heading font stack |

Font sizes in use: `.86rem`, `1.5rem`, `1rem`, `.9rem`, `.72rem`, `clamp(2rem,8vw,2.8rem)`, `1.15rem`, `clamp(2.6rem,9vw,4.4rem)`, `1.3rem`.

## Spacing, radius, elevation

- Spacing values in use: `2px`, `4px`, `6px`, `7px`, `8px`, `10px`, `11px`, `12px`, `14px`, `16px`, `18px`, `26px`. Prefer these; do not add new ones.
- Radius: `--r` (6px). Use the token, not literals.
- Elevation: `5px 5px 0 var(--acc)`, `8px 8px 0 var(--acc)`

## Motion

- Durations in use: `.05s`, `.15s`, `.25s`, `.2s`, `.34s`, `.42s`, `.55s`, `.5s`, `1.2s`, `1.75s`, `1.9s`, `2.45s`.
- Curves: `cubic-bezier(.16,1,.3,1)`, `cubic-bezier(.2,.8,.2,1)`, `cubic-bezier(.22,1.36,.32,1)`.
- Every animation sits behind `prefers-reduced-motion: reduce`, which turns animation and transition off.
- Motion shows state or order. It is never decoration.

## Components and states

- Button `.btn` (filled) and `.btn.alt` (outline): min height 44px, visible `:focus-visible` outline (2px accent), hover and active states.
- Card `.card`, warning card `.card.warn` (left border in `--warn`).
- Language toggle `.langtoggle` with `aria-pressed`.
- Code block `pre`: always LTR, monospace.
- Status words use `.ok b` and `.no b` colors (AA checked).

## RTL rules

- The language toggle sets `dir` and `lang` on `<html>`. Arabic text uses the `--arabic` font and line-height 1.75.
- Use logical CSS (`margin-inline`, `inset-inline-start`, `text-align:start`). No `left` or `right` for layout.
- Letter-spacing is 0 and text-transform none in Arabic.
- Code, terminal output and demo panels stay LTR (`direction:ltr`). Install and demo output stay English.
- Arabic is Egyptian-leaning plain language. Brand names and commands stay Latin.

## Microcopy voice

Plain, specific, honest about limits. Say what it does and what it does not. No hype, no invented numbers.

Examples from the site:

1. Understand the form before you fill it.
2. Enter: 14 digits, no spaces.
3. CONFLICT: the ID number encodes 2003-01-01.
4. A field it does not know is reported as unknown.
5. Standard library only.

## Do / Don't

| Do | Don't |
|---|---|
| Report unknown fields as unknown | Invent a meaning |
| Name the conflicting fields | Say "invalid" |
| Violet for notes, red for errors | Mix both |
| Hard offset shadow, 2px ink border | Soft blurred shadows |
| Label demo data as demo data | Show it as a real person |

## Known hard-coded values (should become tokens)

These literal colors appear in the CSS outside `:root`: `#17703f`, `#2b1f5c`, `#2e9e5b`, `#4c1d95`, `#7a1710`, `#a8281b`, `#c0392b`, `#efe9ff`, `#faf8ff`, `#ffe8e4`, `#fff4f2`.
Also: status colors in `.ok b` and `.no b`, and several literal pixel sizes in component CSS. Move them into tokens next time that block is touched.
