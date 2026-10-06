---
status: green
revised_at: "2026-10-01T07:18:08+10:00"
---

The existing carrier implements mono analogue I/O through two Neutrik NMJ4HCD2 6.35 mm switched mono jacks and SGTL5000's left channel. Right line input is grounded through R7; right line output and headphone outputs are unused. J10/J11 are on B.Cu. U2/U3 are TL072 DIP-8, which does not meet the requested SMD revision.

The carrier uses AudioJack3_Ground symbols with S/R/T/G pins, while the actual embedded NMJ4HCD2 footprints have S/SN/T/TN. Tip and sleeve pads are connected in the PCB, but both normal contacts are unconnected and R/G have no matching physical pads. This symbol/footprint mismatch must not be propagated. The stock AudioJack2_Switch symbol matches the switched mono socket's S/SN/T/TN contacts. Evidence: carrier schematic/PCB, installed KiCad 10 libraries and [Neutrik drawing/circuit links](https://www.neutrik.com/en/product/nmj4hcd2).

U2A is the input follower; U2B buffers the 9 V midrail. U3A is output gain; U3B signal pins are unconnected. The exported netlist connects SGTL5000 LINEOUT_L directly to U3A's positive input and R8/R9 100k divider between 9 V and ground, without a coupling capacitor. This needs bias/headroom review before reuse and is not endorsed as correct.

The carrier Edge.Cuts bounding box is 142.29 by 134.67 mm, not an approved integrated-board size. Its two front 3PDT switch footprints connect two poles each in parallel as MCU inputs, not analogue bypass.

Evidence: kestrel_pcb/kestrel_pcb.kicad_sch and kestrel_pcb.kicad_pcb, exported XML netlist and pcbnew inspection.
