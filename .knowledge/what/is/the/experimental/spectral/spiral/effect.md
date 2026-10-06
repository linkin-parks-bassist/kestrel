---
status: green
revised_at: "2026-10-06T12:42:40+11:00"
---

effects/experimental/SPIRAL.EFF is Spectral Spiral (spectral_spiral): a carrier-published fixed-Hz shifter inside a damped feedback echo, not semitone transposition. It has 149 instructions, 35 scratchpad words, one 32772-word delay allocation and one static polynomial. Publication, discovery and ordinary UI control pass; physical/sonic acceptance remains open.

Two four-stage all-pass paths form quadrature, with an extra sample delay on I. Each stage has four scratchpad words and computes a*(x[n]+y[n−2])−x[n−2], subtracting one signed code before delayed-input subtraction. This quantized bleed fixes near-unity-pole deadbands but is nonlinear near silence. The oscillator overwrites temporary c9. Polynomial carriers combine I*cos+(1−2*Mirror)*Q*sin: Mirror 0/1 selects opposing sidebands, 0.5 gives ring modulation. Damped feedback accumulates harmonic offsets. Quarter-scaled input is restored before the ±0.95 clamp/delay write; high Drive/Ghosts/Memory can saturate the final sum.

Controls (range; default): Drift −400..400 Hz;17.5, Echo 0..600 ms;130, Memory 0..0.85;0.72, Mirror 0..1;0, Dust 200..12000 Hz;8000, Drive 1..4;1.5, Ghosts 0..2;1, Dry 0..1;unity.

tools/test_eff_spiral.py checks model/core equality and independent signal properties. --recheck validates retained source/program/parameter/input identities and model equality, then recomputes signal checks. The 11 completed core fixtures total 323497 exact outputs, all at 1181 cycles/sample:

| Fixture | Outputs | Independent property |
| --- | ---: | --- |
| Four isolated tones | 65536 | Desired amplitude 7600..8400, opposite-sideband rejection>30 dB |
| Signed ±8192 zero-shift DC | 32768 | Settled output within 128 codes of unity |
| +32 quiet input/tail | 24576 | Steady error and final residual≤8 codes; observed residual 4 |
| Dry bypass | 5000 | Exact signed-edge identity |
| Cold silence | 8192 | Zero output |
| Default plucked-bass/tail | 132300 | Gain above unity, no fixture clipping, ≥6-dB tail decay |
| Extreme wet-only/tail | 55125 | Peak ≤31130, final quarter-second RMS <8 codes |

Compiled carrier: 17.4957275 Hz. Rejection: low-B upward 35.31 dB, 110-Hz upward 56.27 dB, negative Drift 61.01 dB and Mirror-down 61.50 dB. Default bass peak 20881, RMS gain 2.141, early/final quarter-second tail RMS 3330.39/523.61. Reports: /tmp/kestrel-spiral-bleed-qualified/CASE/{result,qualification}.json. Signed ±32 model error/residual ≤4 codes.

Extreme 55125-sample model/core: Drift=400/Echo=0/Memory=0.85/Mirror=1/Dust=12000/Drive=4/Ghosts=1/Dry=0; peak 31130, final RMS 4.10 (/tmp/kestrel-spiral-bleed-qualified/extreme-tail/qualification.json).

Full engine: 50000 static frames with read32 (/tmp/kestrel-spiral-engine/results.json). Live controls add 53584 exact frames/read words: Drift −200/0/+400 over 50000 frames including filled feedback; seven other dials, three changes each over 512 frames (/tmp/kestrel-spiral-engine-live-results.json). SPI/controller/mixer/delay are included. References retain resources/state and use observed complete dispatch groups/warmup1411; latency four frames. Independent activation/startup, other populated-buffer controls, physical and worst-case timing remain unqualified.

Prior-FPGA carrier publication/readback covers 4669 bytes; 18 metadata rows match host parsing. At default Echo 130 ms, normal UI activation shows 149 blocks/ 35 read-enabled words. Idle snapshot: 200 FPS/1% CPU; 36 injected Drift moves (≥250-ms spacing) capture 193 FPS/7%. Targets queue/defaults restore, and temporary preset removal restores pools/Bass Ring. Evidence: /tmp/kestrel-spiral-{upload,carrier}.log and /tmp/kestrel-spiral-{metadata,carrier-result}.json. MCU image unchanged; 27 SD descriptors. The one-sample base/nonnegative Echo avoid zero/negative taps even on the previous FPGA; Core owns the new flash-verified repair. Remaining: broader corners, physical measurements, fast gestures and audition.

Basis: [HIIR phase-split form](https://github.com/LostRobotMusic/hiir/blob/main/PolyphaseIir2Designer.h), independently evaluated; no runtime dependency. Source: 4669 bytes, SHA-256 463f4a30c66b1a80d23f399108233734fbdf4ca7ec9f5aeda8a8c03a842d9a29.
