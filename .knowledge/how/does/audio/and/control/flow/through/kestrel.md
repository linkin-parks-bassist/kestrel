---
status: "unverified"
created_at: "2026-09-19T23:57:05+10:00"
scope: "local"
source: "README.md; kestrel_core/README.md; kestrel_interface/README.md"
---
Status: Green

Audio enters the SGTL5000 codec over I2S, the FPGA executes the DSP pipeline per sample, and processed audio returns over I2S. The MCU loads effect descriptors, builds pipelines, and sends programming and parameter updates to the FPGA over SPI.

Source: README.md; kestrel_core/README.md; kestrel_interface/README.md
