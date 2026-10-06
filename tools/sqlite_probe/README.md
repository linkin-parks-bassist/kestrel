# Isolated carrier SQLite probe

This ESP-IDF application qualifies ordered facet queries on the ESP32-P4 carrier
SD card. It is separate from the pedal firmware and adds no production package.
It creates 100,000 generated effects, one instrument facet per effect and groups
of 256 identical names. Five page checks and a complete 25,000-result bass walk
verify IDs and names, including page boundaries inside name ties.

Enable `KT_PROBE_COMPOSED` in menuconfig for a separate 10,000-effect fixture
with descriptions and overlapping instrument/type/genre/keyword memberships.
`KT_PROBE_ROWS` changes its size; the default remains 10,000. The host checker
accepts the same count with `--rows`, for example `--rows 100000`. Larger synthetic
fixtures test scale, without establishing realistic metadata distributions.
Six Boolean predicates cover unions, intersections, nested groups, rare and
empty results. Every paged ID/name is checked against a C predicate evaluator;
eligible cases compare an ordered scan against a covering-facet seed. These
queries also compare indexed ID-set unions/intersections, with explicit nesting
to preserve Boolean grouping. Output strategies: 0 ordered EXISTS, 1 covering
seed, 2 ID sets using table rows, 3 ordered covering union (the two-branch union
case only), 4 ID sets using the covering effect(id,name) index. The last variant
tests name lookup without reading description-bearing table rows.
Strategy 5 runs the covering union as a top-level compound ordered SELECT with
cursor bounds in both branches, allowing an ordered merge instead of sorting
the wrapped union's complete candidate set.
Each strategy walks twice on the same connection: repeat 0 starts fresh, repeat
1 retains its page cache. `IO` reports first-page VFS read calls/requested bytes
and time inside the file read/seek path, excluding prepare/schema reads. This is SQLite VFS
traffic, not raw SD transaction counts or proof of cold card caches.
`HOTFIRST` immediately repeats page one before completing the walk; its IO
repeat labels are 2/3. This distinguishes immediate page reuse from repeat 1's
cache state after a complete traversal. Hot-page checks validate every ID/name.
Distributions are synthetic and do not establish realistic
library performance.
`NAV` checks 72 alternating filter visits on one connection with a 256-KiB
page-cache target, releasing cached pages once before the sequence. Every first
page is verified against the C oracle, including exhaustion for short/empty
results. Visits do not immediately repeat their page to warm it. This target
does not cap total SQLite memory; timings exclude preparation and UI work.
The first 36 visits start at the list beginning; the rest use midpoint and
near-end `(name,id)` cursors, including cursors inside tied names. `after`
identifies the cursor ID. A filter change retaining its cursor is an experiment,
not an adopted UI policy.
`PAGE` accompanies successful navigation checks with separate SQL construction,
prepare, cursor bind, step, reset and finalize timings. `query_us` sums those
phases, excluding console reporting and task yields; stepping includes the
existing row oracle. It excludes connection opening, UI rendering and queueing,
so it is not end-to-end user latency. Finalization errors fail the probe.
`CANCEL` interrupts an empty-result scan at the first progress callback (every
64 SQLite VM instructions, or one for fixtures smaller than sixteen rows).
It checks `SQLITE_INTERRUPT` from stepping and finalizing, removes the handler,
then verifies a new filter page on the same connection. This establishes bounded
query cancellation/reuse, not concurrent UI integration or a wall-clock deadline.
Enable `KT_PROBE_RAW_READ` to compare `lseek/read` with the default
`fseek/fread` VFS using the same fixture and query checks. `SD read_path` identifies
the chosen path; the comparison does not qualify a writable production VFS.
`KT_PROBE_DMA_READ` additionally reads through an aligned internal 4-KiB
copy buffer. It is not a page cache. `IO single/multiple/sd_bytes` counts SD
read commands and their bytes during the same first-page interval, including
filesystem reads; it does not measure card-internal physical operations.
`python3 tools/sqlite_probe/host_check.py` checks the same composed C code in
memory using the pinned amalgamation (C compiler and `SQLITE_AMALGAMATION_DIR`
environment variable required).
It also requires one complete `PAGE` timing record per `NAV` result and checks
that all phases are nonnegative and sum to `query_us`.
It does not exercise SD, fresh connections or carrier timing.

`library_check.py` instead imports authored descriptors through the production
host parser's `compile_eff --info`, then checks fourteen parameterized grouped
predicates and every `(name,id)` page against independent Python evaluation:

```bash
make -C kestrel_interface compile-eff
python3 tools/sqlite_probe/library_check.py --output /tmp/authored-query.json \
  effects/BASSRING.EFF effects/FLANGE.EFF effects/experimental/SWAMP.EFF
```

The optional experimental metadata-only reader imports batches of at most 64 files
without constructing DSP graphs:

```bash
make -C kestrel_interface -f Makefile -f tools/info_reader_preview.mk bin/lib/info-reader-preview
python3 tools/sqlite_probe/library_check.py \
  --info-reader kestrel_interface/bin/lib/info-reader-preview \
  --output /tmp/info-query.json effects/BASSRING.EFF effects/FLANGE.EFF
```

Use `--effects-dir DIRECTORY` instead of file arguments to import its immediate
`.eff` files (case-insensitive extension), without shell glob expansion. The two
input forms are exclusive; an empty directory is rejected. Bounded reader batches
avoid passing an entire large library as process arguments. A reader/protocol
failure rejects the import before database construction.

The default remains the full parser. The metadata-only experiment tokenizes whole
files using the shared parser arena and does not validate DSP instructions. It is
not a production scanning API or background worker.

Pass any explicit descriptor batch; `--copies 400` repeats its tags/names for
scale checks and `--page-size 50` changes the default seven-row pages. Reports
include exact retained metadata/source hashes, reader mode/binary hash, SQLite version, database bytes,
counts and maximum host page times. Repeated names test tie boundaries. Literal
values are bound parameters, including a SQL-looking absent keyword. This uses
Python's host SQLite, not the pinned carrier amalgamation. Replicated authored
tags are not a diverse huge library; timing excludes import, oracle evaluation,
SD and UI. Schema, Boolean predicates and negation are experiments, not adopted
production architecture or UI semantics.
The checker compares ordered scans with covering seeds that are necessary for
every match. For OR branches it also merges independently seeded ordered streams,
with cursor bounds in each branch and top-level UNION/ORDER BY/LIMIT. Seeds are
chosen from observed facet counts; negated branches cannot supply positive seeds.
The bounded branch experiment refuses conjunction expansion beyond 32 branches.
Indexes add storage; record costs as well as latency. A bass-only seed is not
selective in an all-bass fixture, and one branch of a union cannot safely seed
the entire query.

`skew_check.py` generates mixed/skewed records from parser-retained templates:

```bash
python3 tools/sqlite_probe/skew_check.py --rows 100000 \
  --output /tmp/skew-query.json effects/BASSRING.EFF effects/FLANGE.EFF \
  effects/WAH.EFF effects/OCTAVE.EFF effects/DRIVE.EFF \
  effects/experimental/FRACTURE.EFF effects/experimental/UNDERTOW.EFF
```

The default seed is 31; `--seed` and `--page-size` are explicit. Twenty-two
predicates verify every page against Python membership evaluation, including
unseedable negation/union branches, rare late matches and a SQL-looking keyword
with real matches. Mixed instruments/genres, repeated Unicode names, duplicate
and case-distinct keywords, empty axes and longer descriptions exercise storage
and ordering. Reports bind template/tool hashes and retain generated facet counts.
These generated distributions are controlled fixtures, not a realistic authored
library or evidence of carrier/SD/UI latency. No production dependency is added.

The experimental predicate compiler treats empty ALL as true and empty ANY as
false, including inside negation and nested groups. The independent evaluator
checks those identities on every paged result. These are query-composition
identities; the product's empty-filter editing behavior remains a UI decision.

Use pinned ESP-IDF 5.3.3. Fetch the checksum-verified SQLite 3.53.4 amalgamation
outside the repository, then build:

```bash
python3 tools/sqlite_probe/fetch.py /tmp/kestrel-sqlite-amalgamation
cd tools/sqlite_probe
export SQLITE_AMALGAMATION_DIR=/tmp/kestrel-sqlite-amalgamation
idf.py build
```

Defaults select 360-MHz P4, 200-MHz PSRAM and a 16-KiB main stack. Verify the
resolved configuration; experimental features gate the PSRAM speed in this SDK.
The assertion shim applies only to SQLite's translation unit. THREADSAFE=0 and
the read-only VFS are experimental choices, not production concurrency policy.

Flashing replaces the running MCU application. Preserve the pedal binary and
restore it afterwards; use app-only writes at 0x10000 to preserve partition/NVS
contents. There is no automatic flash command here. Use the MCU UART connection;
the carrier power restriction prohibits Tang USB-C while externally powered.

The probe requires exclusive MCU SD ownership. It mounts the carrier's existing
card without formatting, creates `/sdcard/KTPROBE.DB` exclusively, writes/syncs
the serialized database, opens it as immutable/read-only and removes only the
file it created. An existing file causes failure and is never overwritten or
deleted. Interrupted runs can leave the fixture: inspect it before manually
removing it. This VFS does not qualify writable SQLite locking, journaling or
TinyUSB handoff. No USB mass-storage service runs in the probe.

Capture serial output through `PROBE rc=0 cleanup=0`. `COVERING` timings measure
stepping only; fresh SQLite connections do not establish cold card caches.
`WALK` time includes one task yield per page. Results are single-run synthetic
evidence, excluding UI, realistic metadata, composed predicates and refresh.
The knowledge-tree query and integration owners contain measured evidence and
remaining qualification requirements.

After flashing the probe, `python3 tools/sqlite_probe/capture.py PORT LOG` resets
the MCU, captures output and checks completion/cleanup (host pyserial required).
The application waits for `g` before mounting/building; the capture script sends
it after observing readiness, avoiding a reset during fixture publication.
Composed page timings include C result verification, excluding preparation,
open/bind and inter-page task yields; they are not bare SQLite-step costs.
