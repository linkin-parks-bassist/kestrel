#!/usr/bin/env python3
"""Verify compiler-programmed polynomial coefficients through the actual core."""
import argparse
from pathlib import Path

from dsp_model import read_pcm, read_program, saturate, signed
from effect_library import ROOT, prepare, verify_case

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, default=Path('/tmp/kestrel-polynomial-state'))
args = parser.parse_args()
prepare()
dry = list(range(-32768, 32768))
result = verify_case(ROOT / 'kestrel_interface/tests/fixtures/polynomial-state.eff',
                     {}, args.output, dry)
program = read_program(args.output / 'program.bin')
assert program.polynomials == [(0, [16384, 32768, -16384]), (0, [-32768])]
expected = [saturate(((16384 * 32768 + 32768 * x -
                       16384 * signed((x*x) >> 15, 16)) >> 17) - 8192) for x in dry]
assert list(read_pcm(args.output / 'rtl.pcm')) == expected
assert expected[0] == -8192 and expected[32768] == -4096
print(f'Polynomial: all 65536 inputs exact, {result["max_cycles"]} cycles/sample', flush=True)
