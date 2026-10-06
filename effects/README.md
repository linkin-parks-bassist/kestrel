The current-image library uses arithmetic, the Chamberlin SVF, static polynomials,
scratchpad state and allocated integer delays. It needs the
paired Q15 firmware/FPGA contract and polynomial/SVF capabilities; it does not use the old
general filter engine. All filenames fit the carrier's 8.3 FAT configuration.

The eighteen library descriptors and nine experiments carry optional
`.INFO` discovery metadata: a description, explicit keywords, `instruments: {"bass"}`,
and one or more effect types. Tags describe their implemented behavior; genre
labels remain unassigned. These are authored labels, not a fixed taxonomy. The
installed Interface retains them, and `eff-info CNAME` inspects loaded values.
The search/category/filter UI is still planned. Metadata changes leave effect
identities, controls, resources and compiled DSP programs unchanged.

`experimental/SPIRAL.EFF` is a carrier-published Spectral Spiral experiment: a fixed-Hz
frequency shifter inside a damped feedback echo. Drift, Echo, Memory, Mirror,
Dust, Drive, Ghosts and Dry expose the motion and feedback. Dry defaults to unity.
Its provisional all-pass rounding repair has signed DC, quiet-tail and selected
sideband, default feedback/tail and stressed-tail RTL checks: 11 cases match
323,497 outputs. A full-engine run matches 50,000 frames with read32 traffic.
Live controls match another 53,584 frames/read words: Drift across a filled echo
buffer, and three changes on each other dial in short fixtures. Run
`python3 tools/test_eff_engine_updates.py --effect SPIRAL --control frequency --live --read32 --samples 50000`.
References retain DSP resources/state and use observed dispatch/warmup alignment;
other populated-buffer controls and independent activation timing remain open.
Publication/readback, metadata discovery, UI activation/control and temporary-preset
cleanup pass. The active idle snapshot is 200 FPS/1% CPU; slow UART dial movement
captures 193 FPS/7%. Fast physical sweeps, waveform measurements and audition
remain open; it is not an accepted effect. Run
`python3 tools/test_eff_spiral.py` for focused verification; `--recheck --case NAME`
rechecks retained PCM and signal properties without another RTL render.

`experimental/UNDERTOW.EFF` is a deployed granular pitch-delay experiment,
awaiting audition. Eight controls shape interval, grain
size, echo time, feedback memory, damping, drive, wet return and dry signal.
Two crossfaded moving heads feed a damped echo loop, so repeats can climb or sink.
Default dry stays at unity. Integer taps lack interpolation, and short grains
produce detuned sidebands; this is not transparent pitch transposition. Run
`python3 tools/test_eff_undertow.py` for topology, tone, dry/silence/DC, bass/tail
and extreme-control model/RTL checks. Nine cases match 665,272 outputs; a separate
full-engine run matches 50,000 outputs with mapped readback. Carrier discovery,
activation and control checks pass. Numerical qualification and audition are
separate; detailed evidence and remaining limits belong to its knowledge-tree owner.

| File | Effect | Controls |
| --- | --- | --- |
| FLANGE.EFF | Slow swept comb filtering with delay feedback | Sweep, depth, feedback, mix |
| BASSRING.EFF | Free-running sine ring modulation in the bass range | Carrier, mix |
| GROWL.EFF | Cross-modulated bands into an audio-rate cutoff filter | Excitation, audio motion, mix |
| WAH.EFF | Swept resonant peak over dry bass | Sweep, bite |
| VOWEL.EFF | Two manually moved resonant bands over dry bass | Mouth, pronunciation |
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
the squared negative endpoint's wrap. The same test replays production live updates at three
parameter values, checking full coefficient-bank replacement and unaffected handles.
It also checks three successive commits without resetting the same instance.
It replays freshly compiled programming/update bodies through the actual SPI
slave, controller and filter masters at carrier cadence, with fixed-input
numerical checks across eight phases and two chip-select patterns. Audio
instructions are parsed but not executed in this transport fixture.
The script also runs `--engine`: actual compiled audio executes through the
FIFO/controller, pipelines/resources, health, gain/crossfade and mixer. Steady
outputs and eight signed-input endpoints match across three commits at 2551
clocks/sample; 4,096 changing outputs match with fixed four-frame latency.
The polynomial qualification checks eight phases/two chip-select patterns;
physical SDRAM, MISO timing and transition sound remain unqualified.
`python3 tools/test_eff_engine.py` also compares LEVEL, CLIP, CUBEDRV, SVFLP,
SVFHP and VOWEL at defaults and seven control corners through engine-level PCM
rendering: 6,656 samples match the model. Static polynomial PCM also matches all
65,536 signed inputs.
Experimental effect names are supported too. For example,
`--effect RHYTHM --setting tempo=300 --setting division=6 --samples 8192 --read32`
passes 8,192 full-engine outputs and mapped replies. Setting overrides use integer
internal values and require one selected effect. Physical delay timing remains open.
Quarter/300 also passes 20,000 outputs/replies. Independent checks locate the first
echo at sample 1,654 for Sixteenth and 6,615 for Quarter, with no earlier wet return.
Add `--read32 --effect LEVEL --effect INVPHASE --effect SVFLP` to verify mapped
magic/capability replies during every input frame: 1,536 read words and changing
audio outputs match, with independent unity/polarity checks. Replies are sampled
late in the high half-period; master-edge timing remains unqualified.
Readback also passes 6,209 outputs/words for `--effect memory-state --effect delay-feedback --effect delay-pair`.
`python3 tools/test_eff_engine_updates.py --live --read32` passes another 1,536
outputs/words while three controls commit per LEVEL/SVFLP/SVFHP fixture. Its
stateful reference uses observed register dispatch; independent activation timing
and broader resource/update interactions remain open.
The runner includes built-in LUT/scratchpad fixtures (`--resources-only`) and
settled delay/feedback/paired-buffer fixtures (`--delays-only`). Delay programs
receive 512 zero-input settling frames. Core’s PCM owner records qualification.
It uses zero-input warmup and compensates four-frame latency. These fixtures
preserve silence during warmup; arbitrary stateful programs need separate startup
qualification. PCM rendering checks one phase/continuous chip select with a
delayed RAM responder, rather than physical SDRAM.
For one authored effect, use `--effect FLANGE --param rate=3 --samples 16384`.
The runner primes its persistent model with the observed pipeline-B zero-input
execution count in `rtl.pcm.warmup`; equality is conditioned on this count,
not an independent prediction of startup timing.
`python3 tools/test_eff_engine_updates.py` sends three production register/sync
updates each to active LEVEL/SVFLP/SVFHP programs at zero input, then checks 1,536
final-value outputs against fresh models. The PCM harness settles for sixteen
frames after each body. Add `--live` to check another 1,536 continuous outputs,
including intermediate control states and retained SVF state. Its reference uses
actual dispatch register tuples and requires every compiled state in order;
it does not independently predict activation timing. General control programs
and physical transition sound still need qualification.
The polynomial runner produces `carrier-probe/results.json` for verified upload of
`kestrel_interface/tests/fixtures/KTPOLY.EFF`, checking 500 silent outputs first.
Run either carrier script with `tools/hil_interface.py` after verified fixture upload.
`tools/hil_scripts/carrier_polynomial_targets.json` checks fixed-input scratchpad
results through numerical `parameter-target` requests, the normal smoothing queue
and real SPI delivery. Its 40 steps passed on the Interface image preceding the codec-gain change
(`/tmp/kestrel-rhythm-poly-targets-retry-hil.log`).
`tools/hil_scripts/carrier_polynomial_readback.json` checks the corresponding
ordinary UI parameter changes; its 44 steps passed on the earlier parser-format image
(`/tmp/kestrel-chorus-poly-touch-hil.log`); the updated picker guard has not been
rerun through that full touch sequence.
Both restore Talking Vowel and remove the temporary preset, effect and SD fixture.
Review the guarded UI/pool baseline before reuse: these scripts assume seven
presets, temporary preset ID 8 and the specified screen coordinates. With the
previous SD collection including TREMOLO, CHORUS and RHYTHM, the probe label guard was `(242, 1051)`
and selection tapped `(360, 1065)`. SWAMP changes that collection; review both guards
and restore the seven-preset fixture before reuse. The Interface
UART and periodic-read knowledge owners govern the procedure and evidence.
These bounded checks do not qualify audible transitions or maximum load.
Allocated LUTs and other unsupported programming commands fail explicitly. The audio
renderer excludes SPI/controller, mixer and converters; the separate transport
fixture has the bounded scope above. Full one-pipeline system verification remains planned.

`experimental/SWAMP.EFF` is the Swamp Machine: three uneven echo paths feed a
signed, ring-modulated, damped feedback loop. An input envelope ducks the wet
return during attacks so it emerges between notes. Time and Scatter reshape
the echoes; Persistence controls feedback; Damping darkens each circulation;
Metal and Carrier alter its frequency content; Bloom controls attack ducking;
Mix sets the wet addition; Return boosts it by 0–24 dB, outside the feedback loop;
Dry independently controls the clean signal. Defaults retain full dry and boost
the return by 18 dB. High return settings can saturate deliberately.
Live Time/Scatter changes move integer taps and can glitch.
Run `python3 tools/test_eff_swamp.py` for compiled model/RTL comparison, dry
identity, silence, default level/contrast, feedback-tail and maximum-return
saturation checks. Eight cases match 849,700 actual-core outputs at no more than
451 cycles/sample; default synthetic-bass RMS gain is +1.099 dB with relative
change 0.498. The 2045-byte ten-control version has verified SD readback.
Musical acceptance remains open; the earlier crossfade version was quiet/subtle.

`experimental/RHYTHM.EFF` now has an integer Tempo field (30–300 BPM) and seven
Subdivision choices from Whole to Sixteenth. The second tap stays at three quarters
of the selected interval. Default 120 BPM/Quarter preserves the old quarter-note
and dotted-eighth timings. Feedback defaults to 0.5 and Mix to 0.25. Current source
adds a one-pole Damping control (80–12000 Hz, default 2500) before return/feedback
mixing, using one scratchpad word and fourteen instructions. Carrier SD has the
verified 1358-byte damped descriptor; live migration and restart preserve Preset 8,
Feedback 0.65, Mix 0, Tempo 120 and Dotted eighth, adding Damping 2500.
Its explicit `cname` preserves the older descriptor identity when the title changes.
Run `python3 tools/test_eff_rhythm.py` for model/RTL agreement, dry
identity, silence, independent echo timing/amplitudes and signed feedback recurrence.
Eleven cases pass 1,127,800 outputs at 164 cycles/sample, including both damping
endpoints; 28 configuration allocations and seven rejected overrides also pass.
Physical tempo/dropdown
UI activation, 120→90→120 BPM keyboard entry and seven-choice popup work with clean
FPGA status. `dsp` verifies Quarter (24) → Dotted eighth (18), retention through
live reload, and restoration to Quarter. Exact physical delay timing remains open. Adding
settings breaks old positional saved files: load them with the old descriptor, then
live-reload and save. That recovery preserves Preset 8 across restart. Physical echo
timing and listening acceptance remain open; the render is dry left and processed right.

`experimental/CHORUS.EFF` is an experimental single-voice bass chorus available on carrier SD.
It retains a dry path and adds a polynomial-modulated 12-ms delay without feedback.
Sweep, Depth and Mix default to 0.8 Hz, 6 ms and 0.25. Five matching-source checks
pass 405,996 samples. Complete SD readback, UI activation and control endpoints pass;
Talking Vowel and baseline instances were restored. It uses 25 blocks and at most
295 cycles/sample. Default synthetic-bass RMS is −3.215 dB relative to dry.
Run `python3 tools/test_eff_chorus.py`
for RTL comparison, bass level/change, dry identity, silence and settled DC checks.
Integer-delay modulation has no fractional interpolation; listening acceptance remains open.

`experimental/FAULT.EFF` (Fault Choir) is a local, unaccepted nonlinear feedback
prototype. Two detuned short-delay returns subtract and pass a one-pole; feedback
and driven input feed two wave-folding stages before returning to both buffers.
Cavity, Detune, Memory, Pressure, Fracture and Ash shape the feedback texture;
Choir and Dry set explicit return and dry gains. Saturating arithmetic is part of
the nonlinear behavior. `python3 tools/test_eff_fault.py` checks compiled model/RTL
agreement, signed dry identity, silence, bass level and control contrasts.
An independent exhaustive fold test exposed negative-endpoint ABS wrap despite
model/RTL agreement. The current descriptor guards each ABS input, adding four
instructions. At default and both threshold limits, the guarded fold matches all
65,536 signed inputs with zero error against an independent saturating triangle
reference. The unchanged program passes 387,800 full-effect model/RTL comparisons at 338
cycles/sample.
`tools/test_eff_fault_fold.py` checks default and endpoint thresholds exhaustively;
`tools/test_eff_fault_feedback.py` checks signed pulse/tap/feedback recurrence in
the linear fold region, with all 40,000 outputs matching independently. Carrier
continuous sweeps, physical numerical response and listening remain open.
Carrier SD publication and complete readback pass; startup discovers it. Carrier
UI activation shows all eight dials; UART endpoint/default targets converge and
active reload preserves controls. Listening is still unqualified.

`experimental/CROWD.EFF` is an unaccepted five-voice chorus prototype with verified
verified SD readback. Five polynomial-modulated taps share one delay
buffer. Sweep, Depth, Spread, Spacing and envelope-sensitive Feel shape the voices;
Voices and Dry control the mix independently. Defaults retain unity dry, adding
voices with a 150-Hz low-cut. Integer taps have no fractional interpolation.
Run `python3 tools/test_eff_crowd.py` for model/RTL, dry identity, silence, settled
DC, bass level and envelope/spread contrast checks. Seven cases match 410,092
actual-core samples at no more than 1,612 cycles/sample. Default synthetic-bass
RMS gain is 1.00133; envelope and spread control contrasts are 0.03893/0.14690.
Carrier UI activation exposes all seven dials; UART targets converge to their
endpoints and back to defaults. Out-of-range targets reject, and active reload
preserves controls. Temporary-preset cleanup restores pool counts and Swamp.
These checks observe firmware state and clean FPGA status; physical coefficient
delivery, audio response and listening acceptance remain open.

`experimental/FRACTURE.EFF` (Fracture Memory) is an unaccepted rhythmic
memory experiment. Five moving heads share a four-beat buffer; voice collisions
and envelope-shaped, damped feedback make its history interact with new playing.
Tempo controls duration. Drift, Fracture, Voices, Memory, Collision, Pressure,
Dust and Grip shape behavior; Ghosts and Dry control output independently.
Pressure drives excitation into a clamp; the feedback coefficient compensates
for Pressure so it does not amplify recurrence. A 20-Hz feedback-return high-pass
removes slow buildup while retaining unity dry. The program uses 131 blocks and
five scratchpad words. Fractional interpolation is absent. Reads enter after
buffer fill: roughly two seconds of dry startup at 120 BPM.

Run `python3 tools/test_eff_fracture.py` for the five baseline cases; add
`--case default --case fixed --case bypass --case silence --case chaos --case bright`
for all six, including sustained high-Dust stress. `--descriptor PATH` checks a
candidate without replacing source/SD. The current six-case run matches 717,400
actual-core samples at 1,455 cycles/sample. Default synthetic-bass RMS gain is
1.01763, change from dry 0.15276 and fracture contrast 0.18919. Dark/bright extreme
cases have zero rail samples and tail RMS 356.14/1,011.35 codes; bright peak is
30,488. Four wider model cases also pass 1,323,000 samples with zero rails,
including slow Drift at 30 BPM. These fixtures do not qualify the entire range.

A separate Tempo-300 full-engine run matches 50,000 samples and mapped SPI
readback words, including post-fill wet output and four malformed-program
rejections. It uses simulated RAM and observed startup executions; physical
SDRAM and independent startup prediction are excluded. Carrier readback verifies
the complete descriptor and live reload; UI activation exposes Tempo/ten dials, 131 blocks
and five periodic state words with clean FPGA status. Pressure reaches both
endpoints; temporary-preset deletion restores pools and Swamp's saved controls.
Physical coefficient delivery, audio response and listening acceptance remain open.

`experimental/TREMOLO.EFF` is an experimental bass tremolo, separate from
the eighteen-effect library. Rate spans 0.1–12 Hz and Depth spans 0–1; defaults
are 4 Hz and 0.6. It uses a polynomial oscillator and adds an attenuation delta
to the dry sample, preserving exact identity at zero depth. Run
`python3 tools/test_eff_tremolo.py` for envelope/rate, identity, silence, signed-range
attenuation and bass checks; `--slow` adds complete 0.1-Hz full-depth sweeps. Listening
acceptance remains open. The carrier SD copy has verified complete byte readback
and startup discovery; it is available for audition.

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
publication cannot overwrite it. Add `--reload` to reparse verified bytes into an
already-loaded `cname`, including identical files. This refreshes matching preset
instances and the active program, retaining compatible controls but restarting DSP
state. A rejected reload reports an error; the published SD bytes remain. New
identities require startup discovery and ordinary UI addition. Without `--reload`,
uploading leaves the running model alone. UART connection changes can reboot this carrier.

The older GAIN, TD, EF, HPF, LPF and 3BEQ examples are outside this verified batch.
In particular, effects using `filter` require the excluded general engine; they
are not suitable for the current default image. Delay modulation is accepted for
short flanging; avoid modulating long delays because of quantization. Fractional
delay is a future feature, and better results in 24-bit mode are not established.
