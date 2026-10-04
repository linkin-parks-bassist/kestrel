#!/usr/bin/env python3
"""Compile delay fixtures and check actual delay RTL through a delayed RAM responder."""
import argparse
from pathlib import Path
import subprocess

from dsp_model import DSP, read_pcm, read_program, saturate, write_pcm
from effect_library import ROOT, prepare, verify_case

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, default=Path('/tmp/kestrel-delay-state'))
args = parser.parse_args()
prepare()
fixtures = ROOT / 'kestrel_interface/tests/fixtures'
dry = [i % 30001 - 15000 for i in range(4096)]
for i, params in enumerate(({}, {'mod_a': 1, 'mod_b': 1},
                           {'mod_a': 1, 'mod_b': .5},
                           {'mod_a': -.5, 'mod_b': -.5},
                           {'mod_a': -.25, 'mod_b': .25},
                           {'mod_a': -1, 'mod_b': 1})):
    directory = args.output / f'case-{i}'
    result = verify_case(fixtures / 'delay-state.eff', params, directory, dry)
    if not params or params.get('mod_a', 0) < 0:
        size, delay = read_program(directory / 'program.bin').delays[0]
        expected = [(dry[n-delay] * min(16384, max(0, n-size) * 64)) >> 14
                    if n >= delay else 0 for n in range(len(dry))]
        assert list(read_pcm(directory / 'rtl.pcm')) == expected
    print(f'delay {params}: {len(dry)} exact samples, {result["max_cycles"]} cycles/sample', flush=True)

for name in ('delay-feedback', 'delay-pair'):
    signal = [8192 if i == 1024 else -4096 if i == 1152 else 0 for i in range(4096)]
    directory = args.output / name
    result = verify_case(fixtures / f'{name}.eff', {}, directory, signal)
    wet = read_pcm(directory / 'rtl.pcm')
    if name == 'delay-feedback':
        assert [wet[1024 + 8*i] for i in range(1, 6)] == [8192, 4096, 2048, 1024, 512]
        size, delay = read_program(directory / 'program.bin').delays[0]
        history, expected = [], []
        for n, sample in enumerate(signal):
            gain = min(16384, max(0, n-size) * 64)
            output = (history[n-delay] * gain) >> 14 if n >= delay else 0
            expected.append(output)
            history.append(saturate(sample + ((output + 1) // 2)))
        assert list(wet) == expected
    else:
        configs = read_program(directory / 'program.bin').delays
        expected = [saturate(sum((signal[n-delay] * min(16384, max(0, n-size) * 64)) >> 14
                                for size, delay in configs if n >= delay))
                    for n in range(len(signal))]
        assert list(wet) == expected
    print(f'{name}: {len(signal)} exact samples, {result["max_cycles"]} cycles/sample', flush=True)

# Current negative-offset behavior is an identified RTL defect, not qualified audio.
directory = args.output / 'negative'
directory.mkdir(parents=True, exist_ok=True)
program = directory / 'program.bin'
subprocess.run([str(ROOT / 'kestrel_interface/bin/lib/compile_eff'),
                str(fixtures / 'delay-state.eff'), str(program), 'mod_a=1', 'mod_b=-1'], check=True)
try:
    DSP(read_program(program)).sample(8192)
except ValueError as error:
    assert 'outside its allocated buffer' in str(error)
else:
    raise AssertionError('expected the known negative-offset bounds defect')
write_pcm(directory / 'dry.pcm', [8192]*100)
result = subprocess.run([str(ROOT / 'kestrel_core/verilator/test/dsp_core/obj_dir/Vcore_test'),
                         '--render-program', str(program), str(directory / 'dry.pcm'),
                         str(directory / 'rtl.pcm')], cwd=ROOT / 'kestrel_core', capture_output=True, text=True)
assert result.returncode != 0 and 'delay access outside its buffer: 60' in result.stderr
print('Known negative-B offset defect reproduced: address 60 outside 36-word buffer', flush=True)
