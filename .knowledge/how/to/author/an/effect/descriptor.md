---
status: green
revised_at: "2026-10-06T09:50:05+11:00"
---

Start with v1.0 and .INFO containing a string name; define controls/resources, then write .CODE. Optional discovery fields are description (string) and keywords/instruments/types/genres (string lists). For example, keywords: {"feedback", "rhythmic"}. Empty lists and omission are allowed. Full strings, case, order and duplicates are retained; known fields with wrong types reject. Search/filter UI remains planned.

Use .DEFS for reused formulas, square brackets around code expressions and $ before resource handles. Keep names stable because presets identify effects by cname. For carrier deployment use 8.3 filenames. Avoid the old general filter in the current library; use accepted SVF pairing and arithmetic, with future resource coverage governed by the shared verification specification.

The current model/RTL render loop requires intermediate work in c1–cF and only the final instruction writing c0; this is a harness restriction, not an ISA rule. Run how/to/verify/an/effect/descriptor.md and inspect response/WAV results before deploying.

Sources: docs/eff_guide.html, production parser and library tooling.
