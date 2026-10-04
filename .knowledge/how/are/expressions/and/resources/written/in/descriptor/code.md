---
status: green
revised_at: "2026-10-04T09:02:51+11:00"
---

In .CODE, enclose runtime register expressions in square brackets and prefix named resource handles with $. Arguments are space separated; destination channels normally appear last. Each instruction has two expression registers, so at most two value operands can be bracketed expressions; compute a third into a channel first. The compiler applies descriptor send transforms, resolves formats jointly and retains each register's conversion for later updates. Channels supply existing DSP words rather than host float expressions. arsh/lsh/rsh take a b shift dest, with integer fields 0 through 15. The Interface numeric-format owner governs precise policies, including signed-Q15 SVF cutoff.

Sources: docs/eff_guide.html; Interface kest_asm_parser.c, kest_fpga_instr.c, kest_reg_format.c and parser fixtures.
