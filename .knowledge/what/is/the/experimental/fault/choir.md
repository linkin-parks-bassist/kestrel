---
status: green
revised_at: "2026-10-06T10:29:01+11:00"
---

effects/experimental/FAULT.EFF is a local, unaccepted nonlinear two-delay feedback prototype, cname fault_choir. Detuned returns subtract and pass a one-pole; feedback plus driven input feeds two folding stages. Both buffers receive the folded signal. Output retains explicit dry gain and adds the filtered difference.

Controls: Cavity 2–100 ms/default 17; Detune 0–1/default 0.37; Memory 0–0.9/default 0.72; Pressure 1–12/default 3; Fracture 0.05–0.5/default 0.22; Ash 100–12000 Hz/default 3500 logarithmic; Choir 0–2/default 0.8; Dry 0–1/default 1.

Source/SD includes discovery metadata: 1621 bytes, SHA-256 4fbc95589e1ee8879ba449b55243fd0374d18019c1d3d1328dd47ade47722e12. Exact SD bytes/loaded fields pass in /tmp/kestrel-library-metadata-deployment-result.json. The unchanged default program matches a fresh 132300-sample render (/tmp/kestrel-experimental-discovery-metadata/results.json). It has 31 instructions at 338 cycles/sample. Each ABS input is floored at −32767 to prevent signed16 wrap; model/RTL agreement alone concealed that endpoint shape error.

tools/test_eff_fault_fold.py extracts the authored stages into a compiled probe. Default and both threshold endpoints each match all 65536 signed inputs with zero error against an independent saturating-triangle reference. Evidence: /tmp/kestrel-fault-fold-fixed-tests.log and /tmp/kestrel-fault-fold-endpoints-tests.log.

tools/test_eff_fault.py qualifies the unchanged program across bass, signed dry identity, silence, memory/pressure contrasts and extreme controls: 387800 exact outputs. Topology checks cover allocations/taps, handles/opcodes, thresholds, guards and pole. Default allocations are 756/750 and 508/500 words/taps. Synthetic default RMS gain is 1.98045, relative change 1.68138 and peak 12251; memory and pressure contrasts are 1.90934 and 1.65061. Extreme controls reach saturation. Manifest: /tmp/kestrel-fault-guarded/results.json.

tools/test_eff_fault_feedback.py independently derives both delay histories, signed half-return difference and rounded one-pole/feedback recurrence for two signed pulses after startup ramps, with folds constrained to their identity region. All 40000 outputs match, including the first negative echo at sample 30500 (/tmp/kestrel-fault-feedback-tests.log).

Earlier carrier publication/readback qualified the identical DSP program (/tmp/kestrel-fault-upload.log). Normal UI activation of temporary Preset 10 produces 31 blocks and all eight named dials. UART minimum, maximum and restored-default targets converge for all controls; active reload affects one instance and preserves defaults. Signed scratchpad readback is live and FPGA status has no reported error. Cleanup restores active Swamp, nine presets and baseline pools: 24 descriptors, 2086 expressions, 14 resources, 19 parameters, 2 settings, 4 effects (/tmp/kestrel-fault-controls-live.log).

Listening, physical numerical response and continuous sweeps remain unqualified. Core-strobe excludes physical SDRAM/SPI/mixer/audio; UART values establish control convergence, not numerical coefficient delivery or sound.
