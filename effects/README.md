The current-image library uses arithmetic, the Chamberlin SVF, static polynomials,
scratchpad state and allocated integer delays. It needs the
paired Q15 firmware/FPGA contract and polynomial/SVF capabilities; it does not use the old
general filter engine. All filenames fit the carrier's 8.3 FAT configuration.

| File | Effect | Controls |
| --- | --- | --- |
| FLANGE.EFF | Slow swept comb filtering with delay feedback | Sweep, depth, feedback, mix |
| BASSRING.EFF | Free-running sine ring modulation in the bass range | Carrier, mix |
| GROWL.EFF | Cross-modulated bands into an audio-rate cutoff filter | Excitation, audio motion, mix |
| WAH.EFF | Swept resonant peak over dry bass | Sweep, bite |
| VOWEL.EFF | Two moving formants for a talking filter | Mouth, pronunciation |
| OCTFUZZ.EFF | Rectified octave fuzz with DC cleanup and low-pass tone | Fuzz, tone, level |
| DRIVE.EFF | Cubic drive followed by low-pass tone shaping | Drive, tone, level |
| LEVEL.EFF | Clean attenuation | Level |
| INVPHASE.EFF | Polarity inversion | Level |
| CLIP.EFF | Hard clipping | Drive, ceiling |
| CUBEDRV.EFF | Cubic soft clipping, 1.5x − 0.5x³ | Drive, level |
| OCTAVE.EFF | Full-wave rectification with DC cleanup | Level |
| SVFLP.EFF | Two-pole low-pass | Cutoff, resonance |
| SVFHP.EFF | Two-pole high-pass | Cutoff, resonance |
| SVFBP.EFF | Band-pass with damping-scaled output | Center, resonance |
| SVFNOTCH.EFF | Low + high notch | Center, width |
| SVFLP4.EFF | Two cascaded low-pass sections | Cutoff |
| SVFTONE.EFF | Blend low-pass and high-pass outputs | Split, brightness |

The tone blend reaches a notch at its middle position because low and high
outputs cancel around the split frequency. It is not a flat middle-position EQ.
The wah and vowel filter are manually controlled, without an automatic envelope
follower or LFO. Both retain dry bass and add resonant bands; they do not discard
the fundamental to produce a guitar-range band-pass output. The vowel's Mouth control moves two band-pass centers from
100/1400 Hz to 500/400 Hz; these are approximate vowel-like colors, not a voice
model. David found the earlier higher-frequency version approximately unchanged;
these lower centers target bass harmonics, but David still finds the result ultra
mild. At a fixed Mouth setting this is resonant EQ, not a demonstrated vocal effect. Octave Fuzz emphasizes rectifier harmonics by saturating the driven signal
before its tone filter; it does not pitch-shift arbitrary chords.
Cross Growl multiplies a 400-Hz low-pass component by a 1200-Hz band-pass
component, boosts the product, and filters it with a cutoff driven by the low
component on every audio sample. Audio Motion controls that modulation depth;
the coefficient is bounded to the values corresponding to 100–3000 Hz. Excitation
drives the input and Mix retains some dry attack. Its sound is input-dependent;
numeric verification is separate from listening acceptance.

Bass Ring multiplies the input by a continuous sine carrier, keeping phase in a
scratchpad word across samples. Its carrier uses the same degree-seven sine
polynomial as the flanger, avoiding the installed FPGA's missing sine ROM.
Carrier selects 20–220 Hz; Mix defaults to full wet and can retain dry attack.
The mix has RMS compensation, `1/sqrt((1-mix)^2+mix^2/2)`, to compensate the
sine carrier's inherent energy loss. This is a nominal level correction; strong
inputs can saturate.
The Q15 phase increment gives approximately 1.35-Hz frequency steps at 44.1 kHz,
so the control is nominal, not an exactly tuned or pitch-tracking oscillator.
At full wet, a single note produces sum/difference sidebands. It is an experiment
for bass; David confirms an audible effect from the repaired version. Use low fundamentals, harmonics and
playing transients when auditioning this library.

Bass Flange moves an integer delay tap from four samples up to the selected
0.2–8 ms depth, using a 0.1–3 Hz sine sweep. Feedback strengthens the comb response;
the write input is scaled by `1-feedback` to retain headroom. Output weights
retain deep cancelling notches and unity DC gain. At Mix=0.5, dry/wet weights
are `(1-feedback)/2` and `(1+feedback)/2`. David prefers this quieter watery
mix to the energy-normalized alternative, so its original weights are retained. Two scratchpad words provide the slow phase accumulator through
ordinary arithmetic; its frequency is nominal and its sine has 256 phase steps.
An odd degree-seven polynomial generates the sine: all 65,536 input codes match
RTL, with maximum analytic error below 24 signed16 codes.
The delay buffer is 516 words after compiler padding, with a silent first traversal
and subsequent fade-in. The tap has no fractional interpolation. Listening
feedback confirms audible modulation, described as a throbbing droplet; the
original quieter mix is preferred by David. Run `python3 tools/test_eff_flange.py` for
complete slow sweeps, synthetic bass transients, dry bypass and silence checks.

Run `python3 tools/test_eff_bass_levels.py` to check default ring sidebands, vowel character/control contrast and
useful RMS levels for ring/wah/vowel/flanger through actual compiled RTL. These tests
keep the first batch's severe wah/vowel attenuation from silently returning.
Ring/wah/vowel synthetic default RMS gains are +0.03/+0.11/+1.35 dB;
these are bounded checks, not a guarantee for every bass signal. The restored
flanger records its gain without enforcing that loudness target, reflecting
David's explicit sonic preference.

From the superproject root, verify the whole batch:

```bash
python3 tools/effect_library.py --output /tmp/kestrel-effect-library
```

This runs the production compiler, a sample model and the actual core/SVF/LUT/polynomial/delay RTL,
compares every output sample exactly, exercises parameter corners, and checks
default linear-filter responses. Reports include compiled blocks, maximum cycles
per sample and source/program hashes. Each render produces a WAV with dry input
on the left and RTL output on the right. The probe contains integer endpoints,
an impulse, a step and tones. These are simulation checks, not listening approval,
anti-aliasing guarantees or complete hardware qualification. Drive effects produce
harmonics without oversampling; resonant filters can clip on loud inputs.

Render your own mono, signed PCM16, 44.1-kHz recording through an effect:

```bash
python3 tools/effect_library.py --effect CUBEDRV --param drive=12 \
  --input bass.wav --output /tmp/cubic-bass
```

The current model/renderer supports MADD, ABS, MIN, MAX, CLAMP, SVF update/read,
built-in sine/tanh LUT reads and 256-word scratchpad reads/writes. Only the final
instruction may write c0. The renderer exercises full reset before programming;
scratchpad values then persist across samples. LUT modeling uses the actual ROM
words with bit-exact interpolation. Run `python3 tools/test_eff_state.py` for
exhaustive LUT input checks and an independent scratchpad recurrence test.
Allocated integer delays also run through the real delay unit using a delayed RAM
responder: `python3 tools/test_eff_delay.py` checks taps, startup gain, feedback
and isolated buffers, including negative-A clamping to zero and minimum-one taps
for zero/negative final offsets. Offset one is the latest completed write; offset
zero would read the next slot to overwrite. The responder
does not simulate the SDRAM controller, arbiter or pins.
Static polynomial allocation and coefficient writes are supported;
`python3 tools/test_eff_poly.py` checks all signed16 inputs through a compiled
quadratic/constant fixture. Power arithmetic retains signed16 truncation, including
the squared negative endpoint's wrap. Live coefficient updates, allocated LUTs
and other unsupported programming commands fail explicitly. The enclosing SPI controller, mixer
and converters are outside this loop. Full one-pipeline system verification remains planned.

To upload verified files, close other UART clients and use the ESP32 USB serial
port. The script opens one connection, checks FPGA magic/capabilities, stages each
file, publishes it and compares its complete SD readback with the source:

```bash
python3 tools/upload_effects.py --port /dev/ttyACM0 \
  --verified /tmp/kestrel-effect-library --log /tmp/effects-upload.log \
  effects/LEVEL.EFF effects/CLIP.EFF effects/CUBEDRV.EFF effects/SVFHP.EFF
```

Identical files are skipped. Differing existing files require `--replace`; that
explicitly deletes the old destination after staging the new bytes, because FAT
publication cannot overwrite it. Discovery currently happens at startup: reboot
after uploading, then add effects through the normal UI. Uploading does not
change presets or start playback. UART connection changes can reboot this carrier.

The older GAIN, TD, EF, HPF, LPF and 3BEQ examples are outside this verified batch.
In particular, effects using `filter` require the excluded general engine; they
are not suitable for the current default image. Delay modulation is accepted for
short flanging; avoid modulating long delays because of quantization. Fractional
delay is a future feature, and better results in 24-bit mode are not established.
