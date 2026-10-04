---
status: green
revised_at: "2026-10-01T09:41:41+10:00"
---

The next Kestrel hardware revision integrates bare GW2AR-18 FPGA and supporting circuitry, control/UI MCU, audio conversion/peripherals and power conversion on one PCB. No Tang Nano 20K, MCU development board or buck breakout. Audio jacks mount underneath and may be through-hole parts soldered after SMD assembly; op-amps and suitable electronics use SMD. Audio remains mono in/out with two footswitches.

Replace SGTL5000: David reports poor availability, high cost and lead time, and delegates selection of an inexpensive, readily available, good-quality alternative. A separate ADC/DAC pair with hardware configuration rather than I2C setup is preferred. Both audio converters must remain slaves; the FPGA drives MCLK as on the carrier, and owns BCLK/LRCLK. Design work includes biasing, level matching, supplies, clocks and software/FPGA integration; David delegates those analogue details.

David delegates selection of an existing 5-inch capacitive touchscreen balancing price, availability and connector complexity at no more than 720p. Parallel RGB with I2C touch and 800x480 is the working target. His MIPI-only screen is excluded. Sourcing must account for delivery to Sydney: landed AUD cost, shipping, applicable tax and lead time. Cost-effectiveness governs the whole product; no numeric BOM ceiling or production quantity is supplied.

An enclosure is part of the design, coordinated with PCB shape/mounting, jack clearances, screen retention and foot operation. Engineering evaluation retains ESP32-P4, targeting NRW16X v3.x; processor rationale, revision migration and procurement limits belong to what/is/the/mcu/migration/decision.md. Exact panel, enclosure, jacks, switches, power budget and manufacturing constraints need engineering selection before final layout. Converter selection and validation are owned by what/is/the/audio/converter/selection.md.

Source: David's hardware instructions, explicit mono/footswitch and slave-clock selections, panel clarification, Sydney requirement and SGTL5000 replacement request. The desired revision differs from the current carrier, owned by what/is/the/pcb/design/status.md and how/is/the/pcb/powered.md.
