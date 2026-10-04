---
status: green
revised_at: "2026-10-04T20:16:23+11:00"
---

Kestrel is a programmable digital effects pedal. An ESP32-P4 interface handles control, effect compilation and the LVGL GUI; a Gowin FPGA core executes per-sample audio DSP. The existing carrier uses modules and a codec; the integrated Rev-B bare-chip PCB is still being completed.

David describes the user-facing workflow as drag-and-drop composition: stack effects into presets and chain presets into sequences/programmes. Ordinary players need no instruction-set knowledge to use that flexibility. The low-level DSP instruction set serves effect authors and the compiler, while the GUI exposes musical organization. Stacking is configurable within available processing/resources; 'arbitrary' does not mean unlimited hardware capacity. The Interface owns UI, saved-preset/sequence and navigation implementation. Its saved-file loader reads descriptors, presets and sequences; this description does not add a claim of exhaustive GUI workflow qualification.

David intends an enormous free, open-source effects library, owned as a requirement by what/is/the/spec.md. The shipped-example owner records current library coverage and listening acceptance. Instruction-slot and daisy-chained-core experiments belong to the shared plan.

Sources: README.md, current shared spec/plan, Interface saved-preset/sequence loader owner and David's product-workflow description.
