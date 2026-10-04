The current-image library uses arithmetic and the Chamberlin SVF. It needs the
paired Q15 firmware/FPGA contract and SVF capability; it does not use the old
general filter engine. All filenames fit the carrier's 8.3 FAT configuration.

| File | Effect | Controls |
| --- | --- | --- |
| GROWL.EFF | Cross-modulated bands into an audio-rate cutoff filter | Excitation, audio motion, mix |
| WAH.EFF | Swept resonant band-pass wah | Sweep, bite |
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
follower or LFO. The vowel's Mouth control moves two band-pass centers from
350/2200 Hz to 800/1200 Hz; these are approximate vowel-like colors, not a voice
model. Octave Fuzz emphasizes rectifier harmonics by saturating the driven signal
before its tone filter; it does not pitch-shift arbitrary chords.
Cross Growl multiplies a 400-Hz low-pass component by a 1200-Hz band-pass
component, boosts the product, and filters it with a cutoff driven by the low
component on every audio sample. Audio Motion controls that modulation depth;
the coefficient is bounded to the values corresponding to 100–3000 Hz. Excitation
drives the input and Mix retains some dry attack. Its sound is input-dependent;
numeric verification is separate from listening acceptance.

From the superproject root, verify the whole batch:

```bash
python3 tools/effect_library.py --output /tmp/kestrel-effect-library
```

This runs the production compiler, a sample model and the actual core/SVF RTL,
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
  --input guitar.wav --output /tmp/cubic-guitar
```

The current model/renderer supports MADD, ABS, MIN, MAX, CLAMP and SVF update/read
programs, with only the final instruction writing c0. Other instructions and
resource programming fail explicitly. Delay, scratchpad, LUT and polynomial
effects need further model/renderer coverage; no approximation stands in for
their RTL. The enclosing SPI controller, mixer and converters are outside this
loop. Full one-pipeline system verification remains planned.

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
