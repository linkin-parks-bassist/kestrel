---
status: green
revised_at: "2026-10-06T10:27:14+11:00"
---

effects/experimental/FRACTURE.EFF is Fracture Memory, cname fracture_memory: five moving heads share a four-beat buffer. Musical acceptance remains open.

Tempo spans integer 30–300 BPM/default 120. Drift, Fracture, Voices, Memory, Collision, Pressure, Dust and Grip shape movement/feedback; Ghosts/default 1.4 and Dry independently control returns. A one-pole damps feedback and an envelope shapes gain. Pressure drives input into a clamp; feedback/pressure cancels its extra feedback-loop gain. A 20-Hz high-pass removes slow buildup from the feedback/wet return, retaining unity dry. Source uses 131 blocks/five memory words, base tap one and no LUT ROM.

Phase counters wrap across −0.25..+0.25. Prefix-model Drift measures 0.105143/0.704462/3.995410 Hz at 0.1/0.7/4; lowest-rate error is 5.14% (/tmp/kestrel-fracture-phase/results.json). Remaining DSP/RTL excluded.

Tempo 30/120/300 allocations are 352820/88220/35300 words including padding. Reads enter after buffer fill/256-write fade: approximately eight/two/0.8 seconds dry startup; Core owns behavior. Fractional interpolation is absent.

Six cases pass 717400 exact core-strobe samples at 1455 cycles/sample (/tmp/kestrel-fracture-input-pressure-verified/results.json/WAVs). Default gain/change/peak: 1.01763/0.15276/7421; fracture contrast 0.18919. Bypass/silence pass. Maximum nonlinear/feedback controls at Tempo 300 pass both dark plucked bass and bright sustained bass: zero rails, tail RMS 356.14/1011.35; bright peak30488/change 0.53975. These paths exclude SPI/controller/mixer.

Four wider model cases pass 1323000 samples with zero rails (/tmp/kestrel-fracture-input-pressure-range/results.json): slow-buffer post-fill gain/change 1.23934/0.74832, tail 3673.47; bright 1.19985/0.60191. The previous feedback blend railed sustained slow/bright inputs because Pressure amplified recurrence. Collision remains unchanged; bounding it weakened tested character unnecessarily (/tmp/kestrel-fracture-feedback-tune/results.json). Finite fixtures do not qualify every setting/input.

tools/test_eff_fracture.py defaults to five baseline cases; --case bright adds sustained high-Dust stress. Chaos/bright require zero rails and tail RMS no greater than excitation RMS. --descriptor selects a candidate independently.

Full-engine Tempo 300 passes 50000 exact outputs/readback words and four malformed-program rejections, with 14432/14444 post-fill samples changed from dry (/tmp/kestrel-fracture-input-pressure-engine). Observed startup primes the model; physical SDRAM/independent startup excluded.

Source and SD include description/keywords/instruments/types: 3987 bytes, SHA-256 920793466b2dc411bbea0175ee9b779d1c17b940819db954a95eebe80e171f24. Default and Tempo30/300 programs are byte-for-byte unchanged by metadata. Exact SD bytes and loaded fields are verified in /tmp/kestrel-library-metadata-deployment-result.json; the fresh default render matches 132300 samples (/tmp/kestrel-experimental-discovery-metadata/results.json). Earlier carrier activation exposed Tempo/ten dials and five periodic words, with Pressure endpoint convergence and clean FPGA status (/tmp/kestrel-fracture-input-pressure-ui-live.log). Temporary-preset deletion restored pools/Swamp controls. Interface owns current installed state. Physical coefficient delivery/audio and audition remain open.
