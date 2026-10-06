---
status: green
revised_at: "2026-10-06T12:52:54+11:00"
---

effects/ contains eighteen library descriptors plus older examples. Library: LEVEL, INVPHASE, CLIP, CUBEDRV, OCTAVE, SVFLP/SVFHP/SVFBP/SVFNOTCH, SVFLP4, SVFTONE, WAH, VOWEL, OCTFUZZ, DRIVE, GROWL, BASSRING and FLANGE. Carrier experiments: TREMOLO, CHORUS, RHYTHM, SWAMP, CROWD, FAULT, FRACTURE, UNDERTOW and SPIRAL. UNDERTOW: 79-block granular pitch-delay, model/core/engine and carrier checks pass; audition open. Descriptors use arithmetic, private-state SVF, polynomial, scratchpad state and integer delays, never the old general filter. FAT8.3 filenames; effects/README.md explains use.

The original twenty-five include optional .INFO descriptions, keywords, instruments={"bass"} and type labels. Tags describe behavior, not acceptance; taxonomy/genres/normalization remain open. Interface retains fields; search/filter UI and catalogue remain planned. Identity, controls/resources and code are unchanged. All 136 compiled programs match pre-metadata bytes: 106 library defaults/corners, seven experimental defaults, 21 RHYTHM tempo/subdivision combinations and two FRACTURE tempo boundaries. Every source/SD byte and loaded field is verified; controls/pools are preserved (/tmp/kestrel-library-metadata-deployment-result.json).

FLANGE moves a four-sample base tap through 0.2–8 ms depth at nominal 0.1–3 Hz. Two scratchpad words retain phase. Its odd degree-seven sine polynomial has coefficients {0,3.1401887343,0,-5.1363218456,0,2.4271414428,0,-0.4310083315}; all 65536 inputs match model/RTL, maximum analytic error 23.642 codes and wrap endpoints 0/3, at most 37 cycles/sample. tools/test_eff_flange.py owns independent sine/wrap checking.

Feedback 0–0.85 scales writes by 1−feedback. Comb weights retain unity DC: at Mix 0.5, dry/wet=(1−feedback)/2,(1+feedback)/2. Fixed-tap notch residuals 0/31/43 codes at feedback 0/0.65/0.85 exceed 40 dB suppression across 49152 outputs. David prefers this quiet watery mix; do not normalize loudness. The nominal 512-word buffer pads to 516 with startup muting/fade, no fractional interpolation. FLANGE has 27 blocks/max 316 cycles. Eleven sustained checks match 2784208 samples, covering waveform/comb/sweeps/bass/dry identity/silence; rates 0.1/0.3/3 measure 0.105143/0.304914/2.996535 Hz (/tmp/kestrel-flange-poly-sustained/comparison.json).

Fresh verification passes 106 library programs/1514696 exact outputs and seven experimental defaults/926100 outputs. Library checks include selected response/polarity/clipping and Mix-zero dry identity for GROWL/BASSRING/FLANGE; costs span 18–316 cycles/sample. Reports: /tmp/kestrel-{library,experimental}-discovery-metadata/results.json; identities: /tmp/kestrel-library-metadata-identity/results.json. Simulation is not sonic acceptance.

The ROM-staged carrier image boots and passes fourteen physical sine/tanh targets; Core's LUT owner bounds coverage. The prior image lacked sine/tanh initialization. Core owns image identity/qualification. Polynomial ring/flange avoid ROM dependence.

BASSRING multiplies input by a free-running 20–220 Hz polynomial sine with persistent phase. Full-wet default and 1/sqrt((1−mix)^2+mix^2/2) nominal RMS compensation may saturate loud input. Q15 steps are approximately 1.35 Hz. It has 15 blocks/max 182 cycles; five default/corner programs match RTL. David confirms an audible effect; physical sidebands/response remain uninstrumented.

GROWL cross-multiplies driven 400-Hz low-pass/1200-Hz band-pass signals; the low component moves a third SVF cutoff at audio rate. David hears HPF/distortion with nonmusical gain changes. WAH/VOWEL retain dry bass with resonant bands normalized 2/Q. WAH is a manually swept peak; VOWEL moves 100/1400-Hz to 500/400-Hz formants. Both vowel revisions sound ultra mild to David; fixed Mouth gives resonant EQ, and the requested transformation remains unsuccessful. WAH audition remains open. OCTFUZZ/DRIVE are distortion flavors. David plays bass exclusively and wants arbitrary audio-rate DSP, cross-modulation, dynamic/stateful feedback and time/modulation effects.

tools/test_eff_bass_levels.py checks five compiled RTL programs/441000 outputs: ring/wah/vowel default gains +0.026/+0.107/+1.347 dB without fixture clipping; ring sidebands exceed 4000 codes. Vowel change 0.459 and Mouth contrast 1.104 still fail audition. FLANGE is exempt from the ±3-dB target; its bass audit measured −8.26 dB. Sonic preference governs.

SD has twenty-seven tagged effects, including UNDERTOW/SPIRAL. Interface owns installed runtime. David's 29 removed older SD descriptors were backed up; SVFLP stayed. Repository preset references remain, so missing references may fail. Older GAIN/TD/EF/HPF/LPF/3BEQ are outside verification; the general filter needs excluded ENABLE_FILTER. Unsupported rejection/lowering and fractional delay remain planned; long-delay modulation has quantization limitations.

TREMOLO remains experimental: eight checks/1358532 outputs qualify envelopes/rates, dry identity/silence/bass, signed attenuation/sign and complete slow sweeps. Nominal 0.1 Hz measures 0.105143 Hz; --slow reproduces 22 blocks/max 263 cycles. Prior UI activation/endpoint convergence/cleanup preserves pools; audition remains open. Other experiment qualifications have focused owners. SPIRAL: 149 blocks, 323497 core outputs/50000 engine frames; publication/discovery/UI/control/cleanup pass; physical response/fast gestures/audition open.

Evidence: source/tests/HIL, vendor warnings, David.
