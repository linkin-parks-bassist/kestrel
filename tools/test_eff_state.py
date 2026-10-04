#!/usr/bin/env python3
"""Verify compiled LUTs exhaustively and scratchpad state against actual core RTL."""
import argparse
from pathlib import Path

from dsp_model import read_pcm, saturate
from effect_library import ROOT, prepare, verify_case


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, default=Path('/tmp/kestrel-state-verification'))
args = parser.parse_args()
prepare()
fixtures = ROOT / 'kestrel_interface/tests/fixtures'
for name in ('lut-sin', 'lut-tanh'):
    dry = list(range(-32768, 32768))
    result = verify_case(fixtures / f'{name}.eff', {}, args.output / name, dry)
    wet = read_pcm(args.output / name / 'rtl.pcm')
    if name == 'lut-sin':
        assert abs(wet[32768]) <= 1
        assert wet[32768 + 8192] == 32767
        assert wet[32768 - 8192] == -32767
        assert list(wet[:32768]) == list(wet[32768:])
    else:
        assert all(a <= b for a, b in zip(wet, wet[1:]))
        assert wet[0] < -32000 and wet[-1] > 32000 and abs(wet[32768]) <= 1
    print(f'{name}: all 65536 inputs exact, {result["max_cycles"]} cycles/sample', flush=True)
dry = [8192] + [0] * 64 + [32767, -32768, 1, -1] * 1024
result = verify_case(fixtures / 'memory-state.eff', {}, args.output / 'memory', dry)
wet = read_pcm(args.output / 'memory/rtl.pcm')
state = 0
for sample, actual in zip(dry, wet):
    state = saturate(((state + 1) // 2) + sample)
    assert actual == state, (sample, actual, state)
assert list(wet[:5]) == [8192, 4096, 2048, 1024, 512]
print(f'memory: {len(dry)} exact state updates/read-after-write samples, '
      f'{result["max_cycles"]} cycles/sample', flush=True)

# An actual descriptor oscillator must wrap, not merely match the sample model.
result = verify_case(ROOT / 'effects/BASSRING.EFF', {'frequency': 55, 'mix': 1},
                     args.output / 'carrier', [8192] * 44100)
wet = read_pcm(args.output / 'carrier/rtl.pcm')
crossings = [i for i in range(1, len(wet)) if wet[i-1] <= 0 < wet[i]]
assert len(crossings) > 2 and min(wet) < -8000 and max(wet) > 8000
frequency = 44100 * (len(crossings) - 1) / (crossings[-1] - crossings[0])
assert abs(frequency - 55) < 1, frequency
print(f'Bass Ring: sustained carrier {frequency:.3f} Hz, '
      f'{result["max_cycles"]} cycles/sample', flush=True)
