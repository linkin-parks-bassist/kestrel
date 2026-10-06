---
status: green
revised_at: "2026-10-06T03:13:52+11:00"
checked_at: "2026-10-06T03:13:52+11:00"
expires_every: "1 day"
---

No connected, qualified physical audio stimulus/capture fixture is established for the carrier. RHYTHM's model and full-engine delay checks do not measure physical SDRAM/audio timing; its effect owner holds those results.

The current workstation ALSA inventory exposes ALC245 Analog and the internal DMIC for capture, with HDMI/ALC245 playback. It does not expose the Audiobox David used for listening. Evidence: arecord -l and aplay -l on DDRiver. Device visibility is transient and does not establish cable routing, channel mapping or safe calibrated levels.

Before physical timing tests, identify the attached interface and actual pedal input/output route with David, select channels/levels, and measure the dry-path latency. Then capture a known stimulus through RHYTHM at multiple tempo/subdivision settings and compare echo intervals independently, accounting for capture latency. Preserve the existing sound configuration and restore settings afterward. Do not infer echo timing from UART settings or host-generated programming bytes.

The shared effect-verification specification owns acceptance requirements; no complete physical fixture design or test matrix is selected.

Blocker: No verified connected stimulus/capture route.

Next check: Recheck ALSA devices and confirm actual pedal audio routing with David before physical stimulus/capture.
