#!/usr/bin/env python3
"""Verify the configurable bass delay, including independent timing and recurrence."""
import argparse
import json
import math
import subprocess
from pathlib import Path

from dsp_model import read_pcm, read_program
from effect_library import RATE, ROOT, command, prepare, verify_case


def check_configurations(directory):
    directory.mkdir(parents=True, exist_ok=True)
    compiler = ROOT / 'kestrel_interface/bin/lib/compile_eff'
    effect = ROOT / 'effects/experimental/RHYTHM.EFF'
    output = directory / 'configuration.bin'
    for tempo in (30, 60, 120, 300):
        for division in (6, 12, 16, 18, 24, 48, 96):
            command([compiler, effect, output, f'setting.tempo={tempo}',
                     f'setting.division={division}'])
            taps = [math.ceil(RATE * beat / tempo * division / 24) for beat in (60, 45)]
            sizes = [tap + 4 + (4 - (tap + 4) % 4) for tap in taps]
            assert read_program(output).delays == list(zip(sizes, taps))
    for override in ('setting.tempo=29', 'setting.tempo=301', 'setting.tempo=120.5',
                     'setting.division=7', 'setting.missing=1', 'setting.tempo=nan'):
        result = subprocess.run([str(compiler), str(effect), str(output), override],
                                capture_output=True)
        assert result.returncode == 2, (override, result.stderr)
    result = subprocess.run([str(compiler), str(effect), str(output), '--update',
                             str(directory / 'update.bin'), 'setting.tempo=90'], capture_output=True)
    assert result.returncode == 2, result.stderr


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('/tmp/kestrel-rhythm'))
    parser.add_argument('--skip-build', action='store_true')
    args = parser.parse_args()
    if not args.skip_build:
        prepare()
    check_configurations(args.output / 'configurations')
    bass = [round(8000 * math.exp(-5 * (n % 22050) / RATE) * sum(
        math.sin(2 * math.pi * 41.2034 * h * n / RATE) / h
        for h in range(1, 7)) / 2) for n in range(4 * RATE)]
    impulse = [0] * 100000
    impulse[30000] = 8192
    feedback = [0] * 120000
    feedback[30000], feedback[40000] = 8192, -4096
    cases = [
        ('default', {}, bass),
        ('bypass', {'mix': 0}, [-32768, -1, 0, 1, 32767] * 1000),
        ('silence', {}, [0] * 50000),
        ('impulse', {'feedback': 0, 'mix': 0.5}, impulse),
        ('dark-impulse', {'feedback': 0, 'mix': 0.5, 'damping': 80}, impulse),
        ('bright-impulse', {'feedback': 0, 'mix': 0.5, 'damping': 12000}, impulse),
        ('feedback', {'feedback': 0.5, 'mix': 0.5}, feedback),
        ('maximum-feedback', {'feedback': 0.8, 'mix': 0.65}, bass),
    ]
    configurations = {'quarter-90': (90, 24), 'dotted-60': (60, 18),
                      'triplet-300': (300, 16)}
    for name, (tempo, division) in configurations.items():
        cases.append((name, {'feedback': 0, 'mix': 0.5,
                            'setting.tempo': tempo, 'setting.division': division}, impulse))
    records = []
    for name, params, dry in cases:
        directory = args.output / name
        record = verify_case(ROOT / 'effects/experimental/RHYTHM.EFF', params, directory, dry)
        wet = read_pcm(directory / 'rtl.pcm')
        tempo = params.get('setting.tempo', 120)
        division = params.get('setting.division', 24)
        taps = [math.ceil(RATE * 60 / tempo * division / 24),
                math.ceil(RATE * 45 / tempo * division / 24)]
        program = read_program(directory / 'program.bin')
        padded = lambda delay: delay + 4 + (4 - (delay + 4) % 4)
        assert program.delays == [(padded(tap), tap) for tap in taps]
        assert len(program) == 14
        # Independent one-pole coefficient bounds and state topology.
        damping = params.get('damping', 2500)
        a = 1 / (1 + 2 * math.pi * damping / RATE)
        qa, qb = program[5][1], program[6][1]
        assert abs(qa - int(a * 32768)) <= 1
        assert abs(qb - int((1 - a) * 32768)) <= 1
        assert program[4][0] & 31 == 19 and program[7][0] & 31 == 20
        if name == 'bypass':
            assert list(wet) == dry
        elif name == 'silence':
            assert not any(wet)
        elif name.endswith('impulse') or name in configurations:
            expected = [0] * len(dry)
            dark = 0
            rounded = lambda value, coef: (value * coef + 16384) // 32768
            for n, sample in enumerate(dry):
                average = sum((dry[n-tap] + 1)//2 if n >= tap else 0 for tap in taps)
                dark = rounded(dark, qa) + rounded(average, qb)
                expected[n] = (sample + 1)//2 + (dark + 1)//2
            assert list(wet) == expected
            first = 30000 + min(taps)
            assert 0 < wet[first] < 2048 and wet[first+1] > 0
        elif name == 'feedback':
            # Pulses start after both buffers' startup ramps. Both receive
            # the same write; derive every echo from past writes directly.
            history = []
            dark = 0
            half = lambda value: (value + 1) // 2
            rounded = lambda value, coef: (value * coef + 16384) // 32768
            for n, sample in enumerate(dry):
                quarter = history[n - 22050] if n >= 22050 else 0
                dotted = history[n - 16538] if n >= 16538 else 0
                average = half(quarter) + half(dotted)
                dark = rounded(dark, qa) + rounded(average, qb)
                history.append(half(sample) + half(dark))
            assert list(wet) == history
        else:
            energy = sum(x * x for x in dry)
            gain = math.sqrt(sum(y * y for y in wet) / energy)
            change = math.sqrt(sum((x - y) ** 2 for x, y in zip(dry, wet)) / energy)
            assert record['peak'] < 32767
            if name == 'default':
                assert gain >= 10 ** (-3 / 20) and change > 0.2, record
            record.update(relative_rms_gain=gain, relative_rms_change=change)
        record.update(case=name, delay_samples=taps)
        records.append(record)
        print(f'{name}: {record["samples"]} exact samples, {record["max_cycles"]} cycles/sample',
              flush=True)
    # Longest allocation fits the delay unit's per-buffer and total limits.
    boundary = args.output / 'whole-30.bin'
    command([ROOT / 'kestrel_interface/bin/lib/compile_eff',
             ROOT / 'effects/experimental/RHYTHM.EFF', boundary,
             'setting.tempo=30', 'setting.division=96'])
    assert read_program(boundary).delays == [(352808, 352800), (264608, 264600)]
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'results.json').write_text(json.dumps(records, indent=2) + '\n')


if __name__ == '__main__':
    main()
