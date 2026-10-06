#!/usr/bin/env python3
"""Check settled and continuous production register updates through the SPI/DSP engine."""
import argparse
import hashlib
import json
import math
import subprocess
import tempfile
from pathlib import Path

from dsp_model import DSP, Program, read_pcm, read_program, write_pcm
from effect_library import ROOT, command, probe

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, default=Path('/tmp/kestrel-engine-updates'))
parser.add_argument('--effect', choices=('LEVEL', 'SVFLP', 'SVFHP', 'SPIRAL'))
parser.add_argument('--samples', type=int, default=512, help='Input frames; live updates occur at quarter intervals')
spiral_controls = {
    'frequency': [-200, 0, 400], 'echo': [0, 600, 130],
    'feedback': [0.85, 0, 0.72], 'mirror': [1, 0.5, 0],
    'damping': [200, 12000, 8000], 'pressure': [4, 1, 1.5],
    'wet': [2, 0, 1], 'dry': [0, 0.5, 1],
}
parser.add_argument('--control', choices=spiral_controls, help='SPIRAL control to update (default frequency)')
parser.add_argument('--live', action='store_true', help='Compare continuous controls using issued register tuples and retained DSP state')
parser.add_argument('--read32', action='store_true', help='Verify mapped reply words during every audio frame')
args = parser.parse_args()
if args.samples < 8:
    parser.error('--samples must be at least eight')
if args.control and args.effect != 'SPIRAL':
    parser.error('--control requires --effect SPIRAL')
if args.effect == 'SPIRAL' and not args.live:
    parser.error('SPIRAL requires --live to retain its oscillator and delay state across updates')
args.output = args.output.resolve()
args.output.mkdir(parents=True, exist_ok=True)
command(['make', '-C', ROOT / 'kestrel_interface', 'compile-eff'], stdout=subprocess.DEVNULL)
compiler = ROOT / 'kestrel_interface/bin/lib/compile_eff'
executable = ROOT / 'kestrel_core/verilator/test/spi_control/obj_dir_engine/Vtest_spi_engine'
cases = {
    'LEVEL': [{'level': -24}, {'level': 0}, {'level': -12}],
    'SVFLP': [{'cutoff': 30, 'Q': 3}, {'cutoff': 1200, 'Q': 0.7}, {'cutoff': 5000, 'Q': 2}],
    'SVFHP': [{'cutoff': 5000, 'Q': 2}, {'cutoff': 1200, 'Q': 0.7}, {'cutoff': 30, 'Q': 2}],
}
if args.effect:
    control = args.control or 'frequency'
    cases = {args.effect: ([{control: value} for value in spiral_controls[control]]
                          if args.effect == 'SPIRAL' else cases[args.effect])}
records = []
for index, (name, changes) in enumerate(cases.items()):
    directory = args.output / (f'{name}-{control}' if name == 'SPIRAL' else name)
    directory.mkdir(parents=True, exist_ok=True)
    descriptor = ROOT / 'effects' / f'{name}.EFF'
    if name == 'SPIRAL':
        descriptor = ROOT / 'effects/experimental/SPIRAL.EFF'
    program, final, dry, wet = [directory / file for file in
                               ('program.bin', 'final.bin', 'dry.pcm', 'rtl.pcm')]
    updates, programs = [], []
    for i, values in enumerate(changes):
        update = directory / f'update-{i}.bin'
        command([compiler, descriptor, program, '--update', update,
                 *[f'{key}={value}' for key, value in values.items()]])
        updates.append(update)
        if args.live:
            stage = directory / f'stage-{i}.bin'
            command([compiler, descriptor, stage, *[f'{key}={value}' for key, value in values.items()]])
            programs.append(read_program(stage))
    command([compiler, descriptor, final,
             *[f'{key}={value}' for key, value in changes[-1].items()]])
    model = DSP(read_program(program if args.live else final))
    assert model.sample(0) == 0, 'fixture must preserve zero state through warmup/updates'
    samples = probe(args.samples)
    frames = [args.samples * i // 4 for i in (1, 2, 3)]
    if args.live:
        samples = [-32768, -16384, -1, 0, 1, 8192, 16384, 32767] + [
            int(8000 * math.sin(2 * math.pi * 100 * n / 44100) +
                4000 * math.sin(2 * math.pi * 8000 * n / 44100)) for n in range(args.samples - 8)]
    write_pcm(dry, samples)
    if args.live:
        assert all([p[0] for p in model.program] == [p[0] for p in stage] for stage in programs)
    prefix = [ROOT / 'kestrel_core/verilator/test/spi_control/run.sh', '--engine'] if index == 0 else [executable]
    update_args = [item for pair in zip(updates, frames) for item in pair] if args.live else updates
    mode = '--render-live' if args.live else '--render'
    if args.read32:
        mode = '--render-live-read32' if args.live else '--render-read32'
    command([*prefix, mode, program, dry, wet, *update_args], cwd=ROOT / 'kestrel_core')
    warmup = int(Path(str(wet) + '.warmup').read_text())
    model = DSP(read_program(program if args.live else final))
    for _ in range(warmup):
        assert model.sample(0) == 0
    expected = None if args.live else [model.sample(sample) for sample in samples]
    if args.live:
        initial = read_program(program)
        per_frame = [[] for _ in samples]
        # Long programs straddle frame boundaries. Group a complete execution
        # from block zero, using this fixture's observed input/dispatch alignment.
        dispatch_offset = 0 if name == 'SPIRAL' else -1
        frame = None
        for line in Path(str(wet) + '.registers.csv').read_text().splitlines():
            engine_frame, block, reg0, reg1 = map(int, line.split(','))
            if block == 0:
                frame = engine_frame + dispatch_offset
            if frame is not None and 0 <= frame < len(samples):
                per_frame[frame].append((block, reg0, reg1))
        expected, observed, activation_frames = [], [], []
        for frame, (sample, issued) in enumerate(zip(samples, per_frame)):
            assert [row[0] for row in issued] == list(range(len(initial))), (name, frame, issued)
            executed = [(word, row[1], row[2]) for (word, _, _), row in zip(initial, issued)]
            assert executed in [initial, *programs], (name, frame, executed)
            if not observed or executed != observed[-1]:
                observed.append(executed)
                activation_frames.append(frame)
            model.program = Program(executed, initial.delays, initial.polynomials)
            expected.append(model.sample(sample))
        assert observed == [initial, *programs], (name, activation_frames)
        assert all(actual >= requested - 1 for actual, requested in zip(activation_frames[1:], frames))
    actual = list(read_pcm(wet))
    assert actual == expected, (name, next((i for i, pair in enumerate(zip(actual, expected)) if pair[0] != pair[1]), 'length'))
    records.append({'effect': name, 'updates': changes, 'frames': frames if args.live else None,
                    'descriptor_sha256': hashlib.sha256(descriptor.read_bytes()).hexdigest(),
                    'program_sha256': hashlib.sha256(program.read_bytes()).hexdigest(),
                    'warmup_executions': warmup,
                    'dispatch_frame_offset': dispatch_offset if args.live else None,
                    'activation_frames': activation_frames if args.live else None,
                    'samples': len(samples), 'latency_frames': 4,
                    'read32_words': len(samples) if args.read32 else 0})
    print(f'{name}: three production updates, {len(samples)} engine outputs exact', flush=True)
with tempfile.TemporaryDirectory(prefix='kestrel-engine-update-invalid-') as temporary:
    for name, body in [('truncated', b'\x0d\x00'), ('missing-sync', b'\x0d\x00\x00\x00\x0f'),
                       ('early-sync', b'\x0f\x0d\x00\x00\x00\x00'), ('unsupported', b'\x13\x00\x0f')]:
        update = Path(temporary) / f'{name}.bin'
        update.write_bytes(body)
        result = subprocess.run([str(executable), '--render', str(program), str(dry),
                                 str(Path(temporary) / 'output.pcm'), str(update)], capture_output=True)
        assert result.returncode == 1, (name, result.returncode)
        print(f'{name}: rejected before simulation', flush=True)
(args.output / 'results.json').write_text(json.dumps(records, indent=2) + '\n')
