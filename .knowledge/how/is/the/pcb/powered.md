---
status: green
revised_at: "2026-10-01T12:11:28+10:00"
---

The existing carrier uses a centre-negative 9-V pedal supply feeding an external Adafruit MPM3610 buck module for 5 V, with 3.3-V and 1.8-V rails downstream, as described by `kestrel_pcb/README.md`.

The requested Rev-B removes the breakout. Its shared KiCad project implements an onboard centre-negative jack, PTC, reverse-polarity PMOS and transient clamp feeding independent 5-V/3.3-V bucks, a fixed FPGA core regulator, supervised switched FPGA auxiliary/I/O, and audio LDOs with an isolated DAC mute reservoir. Input details belong to `what/is/the/input/power/protection/circuit.md`; buck/LDO topology to `what/is/the/integrated/power/circuit.md`; FPGA sequencing and mute to their focused circuit leaves. The separately controlled MCU HP regulator and onboard backlight boost are instantiated, owned by `what/is/the/mcu/hp/power/circuit.md` and `what/is/the/display/backlight/circuit.md`. Separate LCD and touch logic regulators plus RGB565/I2C FPC connections are instantiated, owned by `what/is/the/display/interface/circuit.md`; actual panel contact fit, loaded operation and procurement remain unresolved. Source: Rev-B generators/exported XML and display topology checks. Full power budget, placement/routing, fault/thermal/noise and hardware operation are not validated.
