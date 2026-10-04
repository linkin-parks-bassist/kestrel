#!/usr/bin/env bash
set -euo pipefail
if (( $# > 1 )); then
    echo "usage: $0 [dry-wet.wav]" >&2
    exit 2
fi
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
make -C "$root/kestrel_interface" compile-eff
"$root/kestrel_interface/bin/lib/compile_eff" \
    "$root/kestrel_interface/tests/fixtures/svf.eff" "$work/program.bin"
"$root/kestrel_core/verilator/test/dsp_core/run.sh" --svf-program "$work/program.bin"
"$root/kestrel_interface/bin/lib/compile_eff" \
    "$root/effects/SVFLP.EFF" "$work/lowpass.bin"
"$root/kestrel_core/verilator/test/dsp_core/run.sh" \
    --svf-audio-program "$work/lowpass.bin" "${1:-$work/dry-wet.wav}"
