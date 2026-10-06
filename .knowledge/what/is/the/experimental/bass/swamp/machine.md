---
status: green
revised_at: "2026-10-06T10:27:13+11:00"
---

effects/experimental/SWAMP.EFF composes three uneven signed-summed echoes, polynomial ring modulation, a one-pole-damped feedback return and envelope ducking. Ten controls: Time20–600ms, Scatter, Persistence0–0.85, Damping80–6000Hz, Metal, Carrier20–400Hz, Bloom, Mix0–0.8, Return0–24dB and Dry0–1. Dry and amplified wet are independently added; defaults retain unity dry and an18-dB boosted return. High wet settings deliberately allow output saturation. David finds the amplified version “kind of fun”; this is tentative positive audition feedback, not broad musical acceptance.

The 41-block program allocates three32772-word delays from nominal32768, each with one-sample base taps, plus scratchpad phase/envelope/damping state and a polynomial carrier. Time/Scatter move integer taps and may glitch. Signed averaging/ring/damping is nonexpansive before feedback≤0.85, subject to rounding; Return amplification is outside the loop.

tools/test_eff_swamp.py qualifies eight cases/849700 exact model/actual-core outputs at451 cycles/sample: defaults, bypass, silence, Metal/Bloom contrasts, extreme controls, feedback decay and maximum-return wet-only saturation after startup. Default synthetic-bass RMS gain is +1.0993dB, change0.49837 of input RMS and peak8102. Metal/Bloom contrast differences are0.75565/0.07698 of input RMS. The impulse tail decays below32 codes in its last second. Evidence: /tmp/kestrel-swamp-v3/results.json and /tmp/kestrel-swamp-v3-{verification,overdrive-ready}.log; per-case program/PCM/WAVs. Renderer excludes SPI/controller/mixer, physical SDRAM/audio and broad dynamic sweeps.

Source and SD include optional discovery description/keywords/instruments/types: 2312 bytes, SHA-256 3ac101dc3ca485a51dda24b198a5e8751740a8fd557e7e5f725ab2fd2f7f2e12. Its default program is byte-for-byte unchanged by metadata. Exact SD bytes and loaded fields are verified in /tmp/kestrel-library-metadata-deployment-result.json; the fresh default render matches 132300 samples (/tmp/kestrel-experimental-discovery-metadata/results.json).

Existing DSP qualifications use the same unchanged program. Ordinary UI activation exposed ten controls, including Return/Dry by scrolling, with clean FPGA status (/tmp/kestrel-swamp-v3-live.log). Current running selection, pool usage and installed image belong to the Interface carrier owner. UART target nominal labels may lag. Preserve user gains and controls; refine from David's audition.
