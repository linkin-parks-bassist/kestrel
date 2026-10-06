---
status: green
revised_at: "2026-10-06T10:29:00+11:00"
---

effects/experimental/CHORUS.EFF is an experimental single-voice bass chorus available on carrier SD. It mixes dry input with a modulated delayed copy, without feedback, using the flanger's two-word phase accumulator and degree-seven polynomial sine.

Sweep spans 0.1–3 Hz (default 0.8); Depth spans 0.2–10 ms (default 6); Mix spans 0–0.5 (default 0.25). Base delay is 12 ms with positive modulation up to Depth; default weights are 0.75 dry/0.25 delayed. Only the final instruction writes audio channel zero.

Delay uses sample units: delay_samples=12*sample_rate/1000, declared size=1024. At 44.1 kHz, padded allocation is 1028 words and base tap 530 samples. Millisecond units also scale size, producing an unintended large allocation here. Integer taps lack fractional interpolation.

Run python3 tools/test_eff_chorus.py; --skip-build reuses builds and --case selects default, bypass, silence, dc or maximum-sweep. Five checks match 405,996 actual-core samples, with independent dry identity, silence, settled unity DC, bounded peaks and bass contrast checks. Cost is 25 blocks, at most 295 cycles/sample.

Four-second synthetic E-bass default RMS gain is 0.690675 (−3.215 dB), relative RMS change 0.416834 and peak 5715. Maximum sweep has gain 0.653601 and change 0.754419. Evidence: /tmp/kestrel-chorus-sample-buffer/results.json; each case has dry-left/RTL-right dry-wet.wav. Source/SD is 1225 bytes, SHA-256 53dfe3a947ef0e19e53859cf8da91f4035625bf00e3032a769aac8f52f913881, including discovery metadata. Its compiled default is unchanged; a fresh render matches 132300 samples (/tmp/kestrel-experimental-discovery-metadata/results.json). Exact SD bytes/loaded fields pass in /tmp/kestrel-library-metadata-deployment-result.json.

Earlier SD readback/activation qualifies the identical DSP program (/tmp/kestrel-chorus-upload.log). Discovery checks 20 descriptors/1002 expressions (/tmp/kestrel-chorus-discovery-hil.log). Ordinary UI activation uses 25 blocks; all three controls converge at endpoints and return to defaults, with changing phase readbacks (/tmp/kestrel-chorus-ui-activation-hil.log). Cleanup restores Talking Vowel and seven presets with resource/parameter/effect/preset counts 4/6/2/7. David finds 1.5-Hz/9-ms/0.45-mix nauseous and 0.3-Hz/1.5-ms/0.2-mix too mild, while accepting that the effect works. CROWD.EFF is a separate five-voice/spread/envelope prototype, owned by what/is/the/experimental/crowd/chorus.md. Its topology and sound remain unaccepted. Chorus remains on SD; it is no longer active in preset 9. These checks establish numerical behavior and control delivery; physical audio quality and listening acceptance remain open.

Sources: descriptor, production compiler/program decoder, sample model, actual-core renderer and carrier UART/UI evidence.
