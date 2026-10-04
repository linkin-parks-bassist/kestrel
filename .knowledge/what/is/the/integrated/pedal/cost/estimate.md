---
status: green
revised_at: "2026-10-04T19:31:46+11:00"
checked_at: "2026-10-04T19:31:46+11:00"
expires_every: "14d"
---

Budget approximately A$300–400 per complete Rev-B pedal when sharing PCB assembly setup and freight across roughly five units, or A$450–650 for a one-off assembled prototype. These are engineering allowances, not a priced BOM, supplier quotation, approved cost ceiling or production commitment. They exclude development/final hand-assembly labour, tools, respins, paid enclosure machining and an external power adapter.

The provisional small-batch model allows A$120–160 for board electronics including the bare FPGA/MCU/audio/power circuitry, A$75–90 for the reference capacitive display, A$50–75 for the enclosure/switches/jacks/fixings, and A$55–75 for each unit's share of PCB fabrication, Standard PCBA, inspection and pooled freight/tax allowance. Only the price anchors below were checked; the rest of the BOM, procurement/overbuy quantities, setup charges, machining and Sydney delivery have not been quoted. Assembly quantity and via-in-pad finishing can change the total materially.

Checked supplier anchors as of 2026-10-04: [LCSC GW2AR-LV18QN88C8/I7 C380550](https://www.lcsc.com/product-detail/C380550.html) lists US$43.8141 at quantity one and US$41.3342 at thirty; this is the actual Rev-B U501 selection, not a GW1NR-9. [DisplayModule DM-TFT50-404](https://www.displaymodule.com/products/800x480-5-inch-visible-under-sunlight-ips-touch-display-panel-rgb) lists US$49, and remains an engineering reference rather than a final procurement choice. [DigiKey Australia Hammond 1590XX](https://www.digikey.com.au/en/products/detail/hammond-manufacturing/1590XX/2496002) lists A$28.99 excluding GST and A$31.889 including GST at quantity one. The [RBA's latest published 2026-10-02 exchange rate](https://www.rba.gov.au/statistics/frequency/exchange-rates.html) is US$0.6933 per A$1: FPGA/display conversions are approximately A$63.20/A$70.68 before tax/freight and payment conversion costs.

[JLCPCB's Standard PCBA fee table](https://jlcpcb.com/help/article/pcb-assembly-price) lists US$51.12 double-sided setup, US$16.42 double-sided stencil and US$1.53 feeder loading per basic/extended component type, plus fixture, placement, inspection, components and other applicable fees. These are fee anchors, not an order quote. The current dual-sided/0.35-mm-pitch P4 engineering layout does not have a qualified Economy assembly route; processor/assembly constraints belong to the MCU migration owner. Via-in-pad approval does not establish a fabricator's filling/tenting/stencil quote.

Source design inventory: kestrel_pcb/rev-b/generated/revb-netlist.xml; the board has 347 electrical footprints plus four mounts, with many exact passive/protection/clock/BOM selections still unresolved. Quantity-one prices for the exact ESP32-P4NRW16X v3 were not verified. No panel, assembled PCB, shipping or enclosure-machining order has been placed or requested from suppliers.

Next establish exact procurable BOM and assembler-compatible alternates, then obtain a complete quote for the requested quantity with fabrication/assembly/via treatment, necessary overbuy, Sydney freight/GST and enclosure work. The design brief owns cost-effective Sydney sourcing and the absence of a numeric ceiling or production quantity; panel/part owners retain technical selection and qualification authority.
