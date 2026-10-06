#!/usr/bin/env python3
"""Qualify granular Pitch Undertow; tone fixtures do not imply universal tuning."""
import argparse
import json
import math
from pathlib import Path

from dsp_model import read_pcm, read_program
from effect_library import RATE, ROOT, prepare, verify_case


def frequency(signal):
    crossings = [i for i in range(1, len(signal)) if signal[i - 1] <= 0 < signal[i]]
    assert len(crossings) > 10, crossings
    return RATE * (len(crossings) - 1) / (crossings[-1] - crossings[0])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('/tmp/kestrel-undertow'))
    parser.add_argument('--skip-build', action='store_true')
    parser.add_argument('--case')
    args = parser.parse_args()
    if not args.skip_build:
        prepare()
    source = ROOT / 'effects/experimental/UNDERTOW.EFF'
    tone = [round(8000 * math.sin(2 * math.pi * 110 * n / RATE)) for n in range(3 * RATE // 2)]
    bass = [round(8000 * math.exp(-3 * (n % 11025) / RATE) * sum(
        math.sin(2 * math.pi * 41.2034 * h * n / RATE) / h
        for h in range(1, 7)) / 2) for n in range(2 * RATE)] + [0] * RATE
    isolated = {'grain': 200, 'feedback': 0, 'pressure': 1, 'wet': 1, 'dry': 0, 'damping': 12000}
    cases = [(name, {**isolated, 'shift': shift}, tone)
             for name, shift in (('tone-down', -12), ('tone-fifth', 7), ('tone-up', 12))]
    cases += [
        ('short-grain', {**isolated, 'shift': 12, 'grain': 50}, tone),
        ('bypass', {'dry': 1, 'wet': 0}, [-32768, -1, 0, 1, 32767] * 1000),
        ('silence', {}, [0] * 65536),
        ('dc', {**isolated, 'shift': 0}, [8192] * 65536),
        ('bass', {}, bass),
        ('extreme', {'shift': 24, 'grain': 20, 'echo': 0, 'feedback': 0.85,
                     'pressure': 6, 'damping': 12000, 'wet': 1, 'dry': 0}, bass),
    ]
    if args.case:
        cases = [c for c in cases if c[0] == args.case]
        if not cases:
            parser.error('unknown case')
    records = []
    for name, params, dry in cases:
        directory = args.output / name
        record = verify_case(source, params, directory, dry)
        program = read_program(directory / 'program.bin')
        assert len(program) == 79 and program.delays == [(16388, 1), (32772, 1)]
        assert not program.polynomials
        assert sum((word & 31) == 17 for word, _, _ in program) == 3
        assert sum((word & 31) == 18 for word, _, _ in program) == 2
        assert {word >> 20 for word, _, _ in program if (word & 31) in (19, 20)} == {0, 1, 2}
        wet = read_pcm(directory / 'rtl.pcm')
        if name == 'bypass':
            assert list(wet) == dry
        elif name == 'silence':
            assert not any(wet)
        elif name == 'dc':
            assert all(abs(y - 8192) <= 4 for y in wet[-10000:])
        elif name.startswith('tone-'):
            measured = frequency(wet[-RATE:])
            expected = 110 * 2 ** (params['shift'] / 12)
            assert abs(measured - expected) < 0.5, (name, measured, expected)
            assert 7800 <= max(wet[-RATE:]) <= 8010
            record.update(measured_hz=measured, expected_hz=expected)
        elif name == 'short-grain':
            measured = frequency(wet[-RATE:])
            assert 228 <= measured <= 232, measured
            record.update(measured_hz=measured, nominal_hz=220,
                          limitation='Short-grain sidebands; not transparent pitch transposition')
        else:
            energy = sum(x * x for x in dry[:2 * RATE])
            gain = math.sqrt(sum(y * y for y in wet[:2 * RATE]) / energy)
            change = math.sqrt(sum((y - x) ** 2 for x, y in zip(dry[:2 * RATE], wet[:2 * RATE])) / energy)
            tail = math.sqrt(sum(y * y for y in wet[-RATE // 4:]) / (RATE // 4))
            early_tail = math.sqrt(sum(y * y for y in wet[2 * RATE:2 * RATE + RATE // 4]) /
                                   (RATE // 4))
            assert tail < max(8, early_tail) and tail < math.sqrt(energy / (2 * RATE)), \
                (name, early_tail, tail)
            if name == 'bass':
                assert gain > 0.9 and change > 0.15 and record['peak'] < 32767
            record.update(relative_rms_gain=gain, relative_rms_change=change,
                          early_tail_rms=early_tail, final_tail_rms=tail)
        records.append(record)
        print(f'{name}: {record["samples"]} exact samples, {record["max_cycles"]} cycles/sample', flush=True)
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / 'results.json').write_text(json.dumps(records, indent=2) + '\n')


if __name__ == '__main__':
    main()
