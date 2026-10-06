#!/usr/bin/env python3
"""Compare compiled effects and LUT/state fixtures through SPI and the DSP engine."""
import argparse
import hashlib
import json
import math
import subprocess
import tempfile
from pathlib import Path

from dsp_model import DSP, read_pcm, read_program, saturate, write_pcm
from effect_library import ROOT, command

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, default=Path('/tmp/kestrel-engine-effects'))
selection = parser.add_mutually_exclusive_group()
selection.add_argument('--resources-only', action='store_true', help='Run only built-in LUT and scratchpad fixtures')
selection.add_argument('--delays-only', action='store_true', help='Run settled delay fixtures with the engine RAM responder')
selection.add_argument('--effect', action='append', help='Run only the named library effect (repeatable)')
selection.add_argument('--descriptor', type=Path, help='Run only this descriptor, including a separate tuning candidate')
parser.add_argument('--param', action='append', default=[], metavar='NAME=VALUE',
                    help='Control override for a single --effect or --descriptor')
parser.add_argument('--setting', action='append', default=[], metavar='NAME=INTEGER',
                    help='Setting override for a single --effect or --descriptor')
parser.add_argument('--samples', type=int, default=512, help='Library endpoint/two-tone sample count (at least eight)')
parser.add_argument('--read32', action='store_true', help='Verify alternating magic/capability reads during every audio frame')
args = parser.parse_args()
if args.descriptor:
    args.descriptor = args.descriptor.resolve()
    if not args.descriptor.is_file():
        parser.error('--descriptor must name an existing file')
    args.effect = [args.descriptor.stem]
if args.samples < 8:
    parser.error('--samples must be at least eight')
if (args.param or args.setting) and (not args.effect or len(args.effect) != 1):
    parser.error('--param/--setting requires one --effect or --descriptor')
overrides = {}
for item in args.param:
    try:
        key, value = item.split('=', 1)
        overrides[key] = float(value)
    except ValueError:
        parser.error('--param must be NAME=VALUE')
args.output = args.output.resolve()
settings = {}
for item in args.setting:
    try:
        key, value = item.split('=', 1)
        settings[key] = int(value)
    except ValueError:
        parser.error('--setting must be NAME=INTEGER')
args.output.mkdir(parents=True, exist_ok=True)
command(['make', '-C', ROOT / 'kestrel_interface', 'compile-eff'], stdout=subprocess.DEVNULL)
dry = [-32768, -16384, -1, 0, 1, 8192, 16384, 32767] + [
    int(8000 * math.sin(2 * math.pi * 100 * n / 44100) +
        4000 * math.sin(2 * math.pi * 8000 * n / 44100)) for n in range(args.samples - 8)]
records = []
cases = [(name, {}) for name in ('LEVEL', 'CLIP', 'CUBEDRV', 'SVFLP', 'SVFHP', 'VOWEL')]
cases += [('LEVEL', {'level': -24}), ('CLIP', {'drive': 24, 'ceiling': 0.1}),
          ('CUBEDRV', {'drive': 18, 'level': 0}), ('SVFLP', {'cutoff': 30, 'Q': 3}),
          ('SVFHP', {'cutoff': 5000, 'Q': 2}), ('VOWEL', {'mouth': 0, 'Q': 3}),
          ('VOWEL', {'mouth': 1, 'Q': 3})]
if args.resources_only or args.delays_only:
    cases = []
if not args.delays_only:
    cases += [(name, {}) for name in ('lut-sin', 'lut-tanh', 'memory-state')]
if not args.resources_only:
    cases += [(name, {}) for name in ('delay-state', 'delay-feedback', 'delay-pair')]
    cases += [('delay-state', {'mod_a': a, 'mod_b': b}) for a, b in
              ((1, 1), (1, .5), (-.5, -.5), (-.25, .25), (-1, 1), (1, -.25), (1, -1))]
if args.effect:
    cases = [(name, overrides) for name in args.effect]
for index, (name, parameters) in enumerate(cases):
    directory = args.output / f'{index:02d}-{name}'
    directory.mkdir(parents=True, exist_ok=True)
    program, input_pcm, output_pcm = [directory / filename for filename in
                                      ('program.bin', 'dry.pcm', 'rtl.pcm')]
    fixture = name in ('lut-sin', 'lut-tanh', 'memory-state', 'delay-state', 'delay-feedback', 'delay-pair')
    descriptor = args.descriptor or (ROOT / 'kestrel_interface/tests/fixtures' / f'{name}.eff' if fixture
                  else ROOT / 'effects' / f'{name}.EFF')
    if not fixture and not descriptor.exists():
        descriptor = ROOT / 'effects/experimental' / f'{name}.EFF'
    command([ROOT / 'kestrel_interface/bin/lib/compile_eff', descriptor, program,
             *[f'{key}={value}' for key, value in parameters.items()],
             *[f'setting.{key}={value}' for key, value in settings.items()]])
    model = DSP(read_program(program))
    assert model.sample(0) == 0, 'fixture must preserve silence during engine warmup'
    samples = (list(range(-32768, 32768)) if name.startswith('lut-') else
               [8192] + [0] * 64 + [32767, -32768, 1, -1] * 1024 if name == 'memory-state' else
               [8192 if n == 0 else -4096 if n == 128 else 0 for n in range(1024)]
               if name.startswith('delay-') else dry)
    write_pcm(input_pcm, samples)
    if index == 0:
        executable = ROOT / 'kestrel_core/verilator/test/spi_control/run.sh'
        prefix = [executable, '--engine']
    else:
        executable = ROOT / 'kestrel_core/verilator/test/spi_control/obj_dir_engine/Vtest_spi_engine'
        prefix = [executable]
    command([*prefix, '--render-read32' if args.read32 else '--render', program, input_pcm, output_pcm], cwd=ROOT / 'kestrel_core')
    actual = list(read_pcm(output_pcm))
    warmup = int(Path(str(output_pcm) + '.warmup').read_text())
    model = DSP(read_program(program))
    for _ in range(warmup):
        assert model.sample(0) == 0
    expected = [model.sample(sample) for sample in samples]
    if name == 'memory-state':
        state = 0
        for sample, value in zip(samples, expected):
            state = saturate((state + 1) // 2 + sample)
            assert value == state, (sample, value, state)
    assert actual == expected, (name, next((i for i, pair in enumerate(zip(actual, expected))
                                         if pair[0] != pair[1]), 'length'))
    if name == 'RHYTHM' and not parameters:
        tempo, division = settings.get('tempo', 120), settings.get('division', 24)
        taps = [math.ceil(44100 * beats / tempo * division / 24) for beats in (60, 45)]
        assert [tap for _, tap in read_program(program).delays] == taps
        first_echo = min(taps)
        # Default dry return is rounded Q15 0.75; delay contents begin at zero.
        # The first return's buffer must have wrapped and completed its gain ramp.
        if len(samples) > first_echo and warmup + first_echo >= min(
                size for size, _ in read_program(program).delays) + 256:
            dry_return = [(sample * 24576 + 16384) // 32768 for sample in samples]
            assert actual[:first_echo] == dry_return[:first_echo], 'early rhythm echo'
            assert actual[first_echo] != dry_return[first_echo], 'missing first rhythm echo'
    if name in ('LEVEL', 'INVPHASE') and parameters.get('level', 0) == 0:
        independent = samples if name == 'LEVEL' else [saturate(-sample) for sample in samples]
        assert actual == independent, (name, 'independent unity/polarity check')
    if name.startswith('delay-'):
        delays = read_program(program).delays
        if name == 'delay-feedback':
            delay = delays[0][1]
            history, independent = [], []
            for n, sample in enumerate(samples):
                wet = history[n-delay] if n >= delay else 0
                independent.append(wet)
                history.append(saturate(sample + ((wet + 1) // 2)))
        else:
            if name == 'delay-state' and parameters:
                # Independent taps for this eight-sample fixture (allocation
                # includes compiler-added padding beyond the requested size):
                # positive modulation, negative-A clamp and final minimum-one clamp.
                tap = {(1, 1): delays[0][0] - 1, (1, .5): 23, (-.5, -.5): 8,
                       (-.25, .25): 8, (-1, 1): 8, (1, -.25): 1, (1, -1): 1}[
                           (parameters['mod_a'], parameters['mod_b'])]
                delays = [(delays[0][0], tap)]
            independent = [saturate(sum(samples[n-delay] if n >= delay else 0
                                        for _, delay in delays)) for n in range(len(samples))]
        assert actual == independent, (name, 'independent settled-delay recurrence')
    if name == 'lut-sin':
        assert actual[:32768] == actual[32768:]
        assert actual[32768 + 8192] == 32767 and actual[32768 - 8192] == -32767
    elif name == 'lut-tanh':
        assert all(a <= b for a, b in zip(actual, actual[1:]))
        assert actual[0] < -32000 and actual[-1] > 32000 and abs(actual[32768]) <= 1
    records.append({'effect': name, 'parameters': parameters, 'settings': settings, 'samples': len(samples),
                    'descriptor_sha256': hashlib.sha256(descriptor.read_bytes()).hexdigest(),
                    'program_sha256': hashlib.sha256(program.read_bytes()).hexdigest(),
                    'latency_frames': 4, 'warmup_executions': warmup,
                    'read32_words': len(samples) if args.read32 else 0})
    print(f'{name} {parameters}: {len(samples)} full-engine samples exact', flush=True)
with tempfile.TemporaryDirectory(prefix='kestrel-engine-invalid-') as temporary:
    for name, body in (('truncated', b'\x02\x00'), ('truncated-delay', b'\x05\x27'),
                       ('missing-tail', b'\x03\x00\x00\x00\x27'), ('early-tail', b'\x27\x27')):
        path = Path(temporary) / f'{name}.bin'
        path.write_bytes(body)
        result = subprocess.run([str(executable), '--render', str(path), str(input_pcm),
                                 str(Path(temporary) / 'output.pcm')], capture_output=True)
        assert result.returncode == 1, (name, result.returncode)
        print(f'{name}: rejected before simulation', flush=True)
(args.output / 'results.json').write_text(json.dumps(records, indent=2) + '\n')
