#!/usr/bin/env python3
"""Verify compiler-programmed polynomial coefficients through the actual core."""
import argparse
import json
import os
from pathlib import Path

from dsp_model import DSP, read_pcm, read_program, saturate, signed
from effect_library import ROOT, command, prepare, verify_case
from dsp_model import write_pcm

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, default=Path('/tmp/kestrel-polynomial-state'))
args = parser.parse_args()
args.output = args.output.resolve()
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

for shape in (-0.25, 0.0, 0.5):
    directory = args.output / f'live-{shape}'
    directory.mkdir(parents=True, exist_ok=True)
    initial, update = directory / 'program.bin', directory / 'update.bin'
    command([ROOT / 'kestrel_interface/bin/lib/compile_eff',
             ROOT / 'kestrel_interface/tests/fixtures/polynomial-live.eff', initial,
             '--update', update, f'shape={shape}'])
    coefficient = int(shape * 131072)
    wire = lambda x: (x & 0xffffff).to_bytes(3, 'big')
    assert update.read_bytes() == (b'\x12\x00\x00\x00' + wire(coefficient) +
                                   b'\x12\x00\x00\x01' + wire(32768) +
                                   b'\x12\x00\x00\x02' + wire(-coefficient) + b'\x13\x00')
    write_pcm(directory / 'dry.pcm', dry + dry)
    command([ROOT / 'kestrel_core/verilator/test/dsp_core' /
             os.environ.get('CORE_TEST_BUILD', 'obj_dir') / 'Vcore_test',
             '--render-polynomial-update', initial, directory / 'dry.pcm',
             directory / 'rtl.pcm', update, len(dry)], cwd=ROOT / 'kestrel_core')
    after = [saturate(((coefficient * 32768 + 32768 * x -
                        coefficient * signed((x*x) >> 15, 16)) >> 17) - 8192) for x in dry]
    assert list(read_pcm(directory / 'rtl.pcm')) == expected + after
    print(f'Live shape={shape}: both signed16 sweeps exact; unaffected coefficient/handle preserved', flush=True)

# Flip the same handle repeatedly without resetting or reallocating resources.
directory = args.output / 'repeated'
directory.mkdir(parents=True, exist_ok=True)
edges = [0, 1, -1, -32768, 32767, -16384, 16384, 12345] * 32
write_pcm(directory / 'dry.pcm', edges * 4)
arguments = []
reference = []
for segment, shape in enumerate((0.125, -0.25, 0.0, 0.5)):
    coefficient = int(shape * 131072)
    reference.extend(saturate(((coefficient * 32768 + 32768 * x -
                               coefficient * signed((x*x) >> 15, 16)) >> 17) - 8192)
                     for x in edges)
    if segment:
        arguments.extend([args.output / f'live-{shape}' / 'update.bin', segment * len(edges)])
command([ROOT / 'kestrel_core/verilator/test/dsp_core' /
         os.environ.get('CORE_TEST_BUILD', 'obj_dir') / 'Vcore_test',
         '--render-polynomial-update', args.output / 'live--0.25/program.bin',
         directory / 'dry.pcm', directory / 'rtl.pcm', *arguments], cwd=ROOT / 'kestrel_core')
assert list(read_pcm(directory / 'rtl.pcm')) == reference
print('Repeated live updates: 1024 exact samples across three bank flips without reset', flush=True)

# Replay freshly compiled bodies through actual SPI/controller/filter masters.
# Fixed input 0.5; the enclosing audio pipeline/mixer is not in this fixture.
arguments = []
for shape in (-0.25, 0.0, 0.5):
    arguments.extend([args.output / f'live-{shape}' / 'update.bin',
                      int((0.75 * shape - 0.125) * 32768)])
command([ROOT / 'kestrel_core/verilator/test/spi_control/run.sh',
         args.output / 'live--0.25/program.bin', *arguments])
print('Compiled polynomial SPI: three commits across eight phases/two CS patterns exact', flush=True)
command([ROOT / 'kestrel_core/verilator/test/spi_control/run.sh', '--engine',
         args.output / 'live--0.25/program.bin', *arguments])
print('Compiled polynomial full engine: live commits, endpoints and four-frame continuous streams exact', flush=True)

# Silent carrier fixture: audio verification and default model-memory check.
# Physical UART HIL separately checks the actual scratchpad values after UI edits.
directory = args.output / 'carrier-probe'
record = verify_case(ROOT / 'kestrel_interface/tests/fixtures/KTPOLY.EFF', {}, directory,
                     [0, 1, -1, -32768, 32767] * 100)
model = DSP(read_program(directory / 'program.bin'))
assert model.sample(0) == 0 and model.memory[0] == -1024
(directory / 'results.json').write_text(json.dumps([record], indent=2) + '\n')
print('KTPOLY carrier fixture: 500 silent samples exact; default model scratchpad -1024', flush=True)
