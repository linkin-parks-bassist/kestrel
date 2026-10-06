---
status: green
revised_at: "2026-10-05T05:51:18+11:00"
---

Interface kest_fpga_cmd.h and Core controller.vh define equal command IDs (1–5, 10–20, 35–40); kest_fpga_defs.h/controller.vh DATA_REQ IDs match (1–15, 33); kest_block.h/instr_dec.vh BLOCK_INSTR IDs match (0–27). Synchronize duplicated constants or generate shared definitions. Source agreement does not prove framing/timing/interoperability.

Command 40 is read32: three MSB-first address bytes, then four result bytes through data-ready/READOUT. Aligned address 0 returns magic 0x4b455354; address 4 reports ENABLE_FILTER/POLYNOMIAL/SVF in bits 0/1/2. Default Core mask is 6, computed from build macros. The controller forwards the address to engine.v's external build_registers responder. Unmapped addresses have no responder. Interface kest_fpga_read32 uses the asynchronous read callback and UART fpga-read32.

The matching pair is installed. /tmp/kestrel-timing-read32-hil.log qualifies exact addressed reads 0/4 through physical SPI. /tmp/kestrel-active-capability-reads-hil.log verifies eight repeated magic/capability pairs and clean final health on the current carrier; /tmp/kestrel-capability-dsp-hil.log confirms normal pools, Talking Vowel activation and seven smoke checks afterward. Installed identity belongs to Interface's carrier owner. Core's engine harness separately verifies mapped reply bytes over eight phases/two request CS patterns; its full-core PCM owner governs audio interaction and late-half-period sampling limits. These checks do not establish all addresses/framing, master-edge timing or clock-domain cases. read24/read16/read8, automatic boot discovery and unsupported-instruction rejection/lowering remain future work.

Argument encoding is a paired compiler/RTL contract. Interface's descriptor/resolver owner governs joint format selection and persisted conversion; Core's filter-engine owner governs SVF normalization. SVF cutoff uses nonnegative signed Q15 and damping an independently compensated signed format, without the former extra coefficient shifts. Deploy matching firmware/FPGA together: an old FPGA does not interpret these words with that scale. Compiled readback/SVF simulations qualify their tested paths; full sound/hardware acceptance remains separate.
