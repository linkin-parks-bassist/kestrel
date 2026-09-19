---
status: "unverified"
created_at: "2026-09-20T00:12:06+10:00"
scope: "local"
source: "caller-supplied answer; evidence not recorded"
---
Status: Green

Source comparison on 2026-09-20: kestrel_interface/components/fpga/kest_fpga_cmd.h and kestrel_core/include/controller.vh define the same named command IDs with equal numeric values (1–5, 10–20, 35–39). kestrel_interface/components/fpga/kest_fpga_dma.h and core/include/controller.vh define the same named DATA_REQ IDs with equal values (1–15, 33). kestrel_interface/components/core/kest_block.h and core/include/instr_dec.vh define matching BLOCK_INSTR opcode numbers 0–27. These duplicated constants are a cross-repository contract; changes require synchronized edits or generated shared definitions. Numeric agreement is a source check, not a proof of framing, timing, or live hardware interoperability.
