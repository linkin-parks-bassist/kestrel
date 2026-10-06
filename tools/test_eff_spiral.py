#!/usr/bin/env python3
"""Qualify Spectral Spiral execution and selected sideband fixtures, not audition."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from dsp_model import DSP, read_pcm, read_program
from effect_library import RATE, ROOT, prepare, verify_case


def amplitude(values, hz):
    weights = [.5 - .5 * math.cos(2 * math.pi * i / (len(values) - 1))
               for i in range(len(values))]
    real = sum(y * w * math.cos(2 * math.pi * hz * i / RATE)
               for i, (y, w) in enumerate(zip(values, weights)))
    imag = sum(y * w * math.sin(2 * math.pi * hz * i / RATE)
               for i, (y, w) in enumerate(zip(values, weights)))
    return 2 * math.hypot(real, imag) / sum(weights)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('/tmp/kestrel-spiral'))
    parser.add_argument('--skip-build', action='store_true')
    parser.add_argument('--case')
    parser.add_argument('--recheck', action='store_true',
                        help='check retained execution evidence and recompute signal properties')
    args = parser.parse_args()
    if not args.skip_build and not args.recheck:
        prepare()
    source = ROOT / 'effects/experimental/SPIRAL.EFF'
    isolated = {'feedback': 0, 'pressure': 1, 'dry': 0, 'wet': 1, 'echo': 0}
    cases = [(name, params, hz, [round(8000 * math.sin(2 * math.pi * hz * n / RATE))
                                for n in range(16384)])
             for name, params, hz in (
                 ('up', isolated, 110), ('bass-up', isolated, 41.2034),
                 ('mirror-down', {**isolated, 'mirror': 1}, 110),
                 ('negative', {**isolated, 'frequency': -17.5}, 110))]
    cases += [
        ('bypass', {'dry': 1, 'wet': 0}, None, [-32768, -1, 0, 1, 32767] * 1000),
        ('silence', {}, None, [0] * 8192),
        ('dc', {**isolated, 'frequency': 0}, None, [8192] * 16384),
        ('dc-negative', {**isolated, 'frequency': 0}, None, [-8192] * 16384),
        ('quiet-tail', {**isolated, 'frequency': 0}, None, [32] * 8192 + [0] * 16384),
        ('bass-tail', {}, None, [round(8000 * math.exp(-3 * (n % 11025) / RATE) * sum(
            math.sin(2 * math.pi * 41.2034 * h * n / RATE) / h for h in range(1, 7)) / 2)
            for n in range(2 * RATE)] + [0] * RATE),
        ('extreme-tail', {'frequency': 400, 'echo': 0, 'feedback': .85,
                          'mirror': 1, 'damping': 12000, 'pressure': 4,
                          'wet': 1, 'dry': 0}, None,
         [round(8000 * math.sin(2 * math.pi * 41.2034 * n / RATE))
          for n in range(RATE // 4)] + [0] * RATE),
    ]
    if args.case:
        cases = [c for c in cases if c[0] == args.case]
        if not cases:
            parser.error('unknown case')
    records = []
    for name, params, hz, dry in cases:
        directory = args.output / name
        if args.recheck:
            record = json.loads((directory / 'result.json').read_text())
            assert record['descriptor_sha256'] == hashlib.sha256(source.read_bytes()).hexdigest()
            assert record['program_sha256'] == hashlib.sha256((directory / 'program.bin').read_bytes()).hexdigest()
            assert record['parameters'] == params and record['exact_matches'] == len(dry)
            assert list(read_pcm(directory / 'dry.pcm')) == dry
        else:
            record = verify_case(source, params, directory, dry)
        program = read_program(directory / 'program.bin')
        assert len(program) == 149 and program.delays == [(32772, 1)]
        assert len(program.polynomials) == 1
        assert {word >> 20 for word, _, _ in program if (word & 31) in (19, 20)} == set(range(35))
        wet = read_pcm(directory / 'rtl.pcm')
        assert len(wet) == len(dry)
        if args.recheck:
            model = DSP(program)
            assert all(model.sample(x) == y for x, y in zip(dry, wet))
        if hz is not None:
            # Read the compiled counter's one-sample step; spectral projection is
            # independent of the DSP output oracle and also checks nominal error.
            counter = DSP(program)
            counter.sample(0)
            carrier = counter.memory[0] * RATE / 32768
            nominal = params.get('frequency', 17.5)
            assert abs(carrier - nominal) <= RATE / 32768
            wanted = hz + carrier * (1 - 2 * params.get('mirror', 0))
            other = 2 * hz - wanted
            desired = amplitude(wet[-8192:], wanted)
            rejected = amplitude(wet[-8192:], other)
            rejection = 20 * math.log10(desired / max(rejected, 1e-9))
            assert 7600 < desired < 8400 and rejection > 30, (name, desired, rejection)
            record.update(carrier_hz=carrier, desired_hz=wanted,
                          desired_amplitude=desired, opposite_amplitude=rejected,
                          sideband_rejection_db=rejection)
        elif name == 'bypass':
            assert list(wet) == dry
        elif name == 'silence':
            assert not any(wet)
        elif name in ('dc', 'dc-negative'):
            assert all(abs(y - dry[-1]) < 128 for y in wet[-4096:])
        elif name == 'quiet-tail':
            # Bound quantized low-level error and residual, independently of the model.
            assert max(abs(y - 32) for y in wet[4096:8192]) <= 8
            assert max(abs(y) for y in wet[-4096:]) <= 8
            record['residual_peak'] = max(abs(y) for y in wet[-4096:])
        elif name == 'extreme-tail':
            assert record['peak'] <= math.ceil(.95 * 32768)
            record['final_tail_rms'] = math.sqrt(sum(y * y for y in wet[-RATE // 4:]) / (RATE // 4))
            assert record['final_tail_rms'] < 8
        else:
            energy = sum(x * x for x in dry[:2 * RATE])
            gain = math.sqrt(sum(y * y for y in wet[:2 * RATE]) / energy)
            assert gain > 1 and record['peak'] < 32767, (gain, record['peak'])
            record['relative_rms_gain'] = gain
            early = wet[2 * RATE:2 * RATE + RATE // 4]
            record['early_tail_rms'] = math.sqrt(sum(y * y for y in early) / len(early))
            record['final_tail_rms'] = math.sqrt(sum(y * y for y in wet[-RATE // 4:]) / (RATE // 4))
            # At least 6 dB decay over the one-second tail; bit equality alone
            # would also pass a wrongly growing feedback loop.
            assert record['final_tail_rms'] < record['early_tail_rms'] / 2
        (directory / 'qualification.json').write_text(json.dumps(record, indent=2) + '\n')
        records.append(record)
        action = 'retained' if args.recheck else 'exact'
        print(f'{name}: {record["samples"]} {action} samples, {record["max_cycles"]} cycles/sample', flush=True)
        (args.output / 'results.json').write_text(json.dumps(records, indent=2) + '\n')


if __name__ == '__main__':
    main()
