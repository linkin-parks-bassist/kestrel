#!/usr/bin/env bash
set -euo pipefail

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT

make -C "$root/kestrel_interface" compile-eff
"$root/kestrel_interface/bin/lib/compile_eff" \
    "$root/kestrel_interface/tests/fixtures/readback.eff" "$work/program.bin"
"$root/kestrel_core/verilator/test/dsp_core/run.sh" --readback-program "$work/program.bin"
