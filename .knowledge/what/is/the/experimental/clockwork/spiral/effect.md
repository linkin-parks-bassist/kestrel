---
status: green
revised_at: "2026-10-06T16:47:58+11:00"
---

Clockwork Spiral is an unpublished tempo-locked Spectral Spiral candidate at /tmp/kestrel-clockwork-candidate/CLOCKWRK.EFF, cname clockwork_spiral. Source SHA-256: 4bfb2fb44aa32d5660203a76d7e574ef0f995bba01d860748e7fed0ae829e10d. Original SPIRAL.EFF is unchanged; carrier SD has no Clockwork descriptor.

It retains Spiral's quadrature/polynomial fixed-Hz shifting, damped feedback and unity-default dry path. Tempo is 30–300 BPM/default 120. Subdivision uses Rhythm's Whole/Half/Quarter/Dotted eighth/Quarter triplet/Eighth/Sixteenth choices, default dotted eighth. Seven original dials remain; options replace free Echo.

Tap is ceil(sample_rate*60/Tempo*Subdivision/24). The minimal four-word size request uses firmware padding. At 44100 Hz, default/slow-whole/fast-sixteenth taps are 16538/352800/2205, allocating 16544/352808/2212 words. All 28 tested combinations of four tempos/seven subdivisions encode expected taps/allocations and 149 instructions. Candidate allocations.json/option-sweep.json hold evidence.

Default synthesized bass/tail matches 132300 model/core samples at 1181 cycles/sample. Peak 22422 codes, RMS gain 2.182; early/final quarter-second tail RMS 3859.73/2014.63 codes exceeds the checked 3-dB decay requirement. This does not establish musical acceptance. /tmp/kestrel-clockwork-bass/qualification.json and dry-wet.wav retain evidence/listening material. Signed-edge dry bypass is exact over 5000 samples; cold silence stays zero over 8192. Candidate identity-silence.json binds hashes/sample evidence.

Full-engine/read32 comparisons pass 50000 default and 8000 Tempo-300/sixteenth frames, at four-frame latency using 1411 observed warmup executions. /tmp/kestrel-clockwork-engine-{default,fast} binds settings/hashes/readbacks. Four malformed programming bodies reject before simulation. These include SPI/controller/mixer, not independent startup prediction or physical SDRAM.

Maximum-delay acceptance remains pending. Its 360000-frame Tempo-30/Whole run uses /tmp/kestrel-clockwork-engine-slow and /tmp/kestrel-clockwork-engine-slow.log; inspect the existing process/output before rerunning. Host exec handle 68649 and simulator PID 3369613 identify this run within the current session. /tmp/kestrel-clockwork-slow-qualify.py requires successful results.json, checks observed warmup against the 1411-execution zero-feedback reference and compares PCM before/after the independently calculated 352800-frame tap. The reference is ready; it shares compiler/model machinery, not an independent numerical oracle. Pending output or a live process cannot establish a pass.

Before publication/deployment qualify option rebuilding, sustained controls, physical audio/audition, maximum-delay results and other corners. Sources: SPIRAL/RHYTHM descriptors, candidate, production compiler and checked model/core/engine artifacts; allocation owner explains padding.
