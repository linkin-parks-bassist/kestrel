---
status: green
revised_at: "2026-10-06T09:15:51+11:00"
---

Run kestrel_pcb/rev-b/tools/propose_signal_route.py with pcbnew, NumPy and Shapely; global:where/is/mechanical/cad/tooling.md owns the environment. It is read-only; candidates require electrical qualification.

Supply --board, --start REF.PAD, --end REF.PAD, reviewed --bounds XMIN YMIN XMAX YMAX and --output JSON. Endpoints must share a nonempty net. Require unique footprint references: dictionaries conceal duplicates. Repeated pad numbers within a footprint are legitimate; verify individual UUIDs when proving every return.

Topology: four copper layers and one In1.Cu /GND zone. Search uses F.Cu/In2.Cu/B.Cu; --layers restricts them. Default grid 0.05 mm; --grid-step .025 improves sampling without changing rules. Align bounds to fine-pitch coordinates. A* uses obstacle-free eight-way distance and required transitions; turn/via costs affect selection.

Mutually exclusive --start-via UUID/--start-track UUID and optional --end-via UUID require same-net, grid-aligned anchors physically connected to their pads. Through vias admit every free allowed layer; start tracks use their end/layer. End-via routes terminate there, retaining end_pad_position/existing_end_via without an implicit pad segment. Otherwise actual pad copper sides define endpoints; serialization follows the root layer. Prefer existing endpoint transitions when extending a bus: pad-to-pad proposals can add redundant tails beyond an earlier physical merge. Remove only new redundant copper under complete-group preservation guards.

Trace width 0.127 mm; vias 0.5/0.3 mm. Conservative pad boxes use local pad/footprint clearance, otherwise 0.2 mm; foreign tracks/vias use 0.2 mm. Search margin 0.01 mm. Outside-land via exclusions cover all pads, including same-net, by max(local clearance + annulus radius, hole clearance + drill radius) plus margin. New drills respect spacing against every existing hole, including same-net vias; noncircular drills use circumscribed circles. Hole clearance/spacing are 0.25 mm. U701's 0.127-mm local clearance gives 0.41-mm pad exclusion instead of 0.46 mm.

Exact-grid same-net through vias are reusable and reported separately. --via-in-pad REF.PAD permits only named endpoint SMD lands containing the entire drill; other pads/copper/hole rules remain. Narrow QFN lands cannot admit oversized drills. Builders preserve geometry and avoid duplicate vias. Count saved-board GetTracks UUIDs: connectivity proxies can represent vias as PCB_TRACK.

Successful JSON records paths, layers/widths, new/reused vias, anchors, rules and limitations. Exhaustion exits nonzero with reachable nodes, bounds and boundary contact per layer. Contact suggests revisiting bounds; no contact establishes only modeled exhaustion. Invalid endpoints/anchors may reject before search.

Edges, keepouts, custom rules, impedance and returns are unmodeled. Replay isolated copies with matching rules/refill; run native copper/drill/mask/courtyard/edge DRC and verify complete groups/unrelated geometry. Inspect reference/graphic fields: pad/footprint UUID filtering misses some silkscreen errors. Changed reports can surface existing warnings; compare unchanged native expressions/rules before calling them pre-existing. Inspect filled reference copper: native-clear via pairs can erase plane webs. Clearance does not establish timing, assembly or electrical performance.
