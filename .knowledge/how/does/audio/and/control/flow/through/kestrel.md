---
status: green
revised_at: "2026-10-01T06:43:39+10:00"
---

In the existing carrier design, analogue audio enters the input circuitry and SGTL5000 ADC. Digital samples travel over I2S to the FPGA for DSP and return over I2S to the codec DAC and output circuitry. The analogue jacks do not carry I2S. The MCU loads effect descriptors, builds pipelines, and sends programming/parameter updates to the FPGA over SPI; SGTL5000 control uses I2C.

The requested integrated revision replaces the codec with a hardware-configured ADC/DAC pair while retaining the MCU/SPI/FPGA DSP division. Its converter selection and required integration work are owned by `what/is/the/audio/converter/selection.md`. The existing firmware and RTL still implement the carrier backend; they have not yet been migrated or validated against the new parts.

Sources: project READMEs, carrier schematic/exported netlist, Core `src/top.v`/`src/i2s.v`, and David's replacement request. Neither board-level implementation has established end-to-end hardware validation.
