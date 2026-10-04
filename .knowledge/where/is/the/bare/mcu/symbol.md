---
status: green
revised_at: "2026-10-01T13:42:22+10:00"
---

The portable ESP32-P4NRW16X v3 symbol is kestrel_pcb/rev-b/electrical/KestrelMCU.kicad_sym. The assigned engineering footprint is KestrelMCU:ESP32_P4_QFN104_10x10_P0.35_EP7.5 in electrical/KestrelMCU.pretty. tools/build_mcu_library.py generates both and registers them in project symbol/footprint tables. Run after build_audio.py recreates the tables.

Pin data is tools/data/esp32_p4_qfn104_v3.json: 104 perimeter pins plus exposed ground 105, extracted from Espressif datasheet v0.7 Table 2-1, pages 14–16, with source URL/PDF SHA-256. Pin 54 is VDD_HP_1; VDDO_FLASH/PSRAM/3/4 are power outputs. Five units separate support/power from GPIO groups; EN_DCDC is an output; other analog control/crystal pins remain passive pending circuit-role review. All 105 symbol names/numbers were compared with the extracted table using the project library loader.

Figure 6-1, page 93 specifies 10-mm body, 0.35-mm pitch, 7.5-mm nominal exposed pad (7.4–7.6), lead width 0.18 mm nominal (0.13–0.23), length 0.4 mm nominal (0.3–0.5) and nominal height 0.85 mm (0.8–0.9). The figure is a package drawing, not a recommended land pattern. Rev-B engineering lands are 0.60×0.18 mm centered 4.90 mm from package center, with 7.5×7.5-mm exposed ground, 0.025-mm mask expansion and a 10.90-mm square courtyard. Numbering is top-view counterclockwise: pin 1 upper-left, 26 lower-left, 27 bottom-left, 52 bottom-right, 53 lower-right, 78 upper-right, 79 top-right, 104 top-left. KiCad loaded all 105 numbered pads and those corner coordinates were checked.

Thirty-six 0.9-mm square exposed-pad paste windows on 1.2-mm pitch give 51.84% paste area. The generator and placed U701 use this pattern, coordinated with the board's twenty-five 0.6/0.3-mm EP through vias on 1.2-mm pitch, with bottom tenting requested. tools/check_mcu_exposed_ground.py verifies direct ground connections, serialized via settings and at least 0.062132-mm nominal clearance between each drill edge and the paste apertures. Thermal vias are board objects, not footprint pads. Array procedure and unresolved tenting/stencil/reflow/thermal qualification belong to what/is/the/bare/mcu/support/circuit.md. This geometry is not proof against solder wicking or voiding.

The nominal copper gap between adjacent leads is 0.17 mm; nominal expanded-mask gap is 0.12 mm. The generated and placed footprint use 0.127 mm local clearance. tools/check_mcu_bypass_layout.py independently checks all 100 adjacent perimeter gaps against 0.15 mm; nominal geometry passes. This is an engineering spacing constraint, not manufacturer-approved lands. Manufacturing tolerances, lead-width extremes and solder-joint suitability remain unqualified.

JLCPCB lists minimum lead pitch 0.35 mm for Standard PCBA and 0.40 mm for Economy: https://jlcpcb.com/capabilities/pcb-assembly-capabilities. This P4 requires Standard at that assembler; qualify stencil, lands, mask, thermal vias and total Sydney assembled cost before committing the process. A different assembler requires its own qualification.

Source: https://www.espressif.com/sites/default/files/documentation/esp32-p4_datasheet_en.pdf. tools/build_mcu.py instantiates U701 and support in kestrel-revb-mcu.kicad_sch. Implementation and unresolved crystal/boot/flash/interface qualification belong to what/is/the/bare/mcu/support/circuit.md. Complete GPIO/domain and whole-circuit qualification before fabrication. Processor rationale belongs to what/is/the/mcu/migration/decision.md.
