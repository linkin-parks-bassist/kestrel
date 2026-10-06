#!/usr/bin/env python3
"""Check the experimental tremolo's envelope, dry identity and bass attenuation."""
import argparse
import json
import math
from pathlib import Path

from dsp_model import read_pcm
from effect_library import RATE, ROOT, prepare, verify_case


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('/tmp/kestrel-tremolo'))
    parser.add_argument('--skip-build', action='store_true', help='use existing compiler/core builds')
    parser.add_argument('--slow', action='store_true', help='also render complete 0.1-Hz full-depth sweeps')
    parser.add_argument('--case', help='run one named case')
    args = parser.parse_args()
    if not args.skip_build:
        prepare()
    source = ROOT / 'effects/experimental/TREMOLO.EFF'
    endpoints = [-32768, -1, 0, 1, 32767] * 1000
    bass = [round(9000 * math.exp(-3 * (n % 11025) / RATE) * sum(
        math.sin(2 * math.pi * 41.2034 * h * n / RATE) / h
        for h in range(1, 7)) / 2) for n in range(RATE)]
    cases = [
        ('default', {}, [8192] * RATE),
        ('bypass', {'depth': 0}, endpoints),
        ('silence', {}, [0] * 4096),
        ('full-depth', {'rate': 12, 'depth': 1}, [8192] * RATE),
        ('slow-bypass', {'rate': 0.1, 'depth': 0}, endpoints),
        ('bass', {}, bass),
        ('full-range', {'rate': 12, 'depth': 1}, list(range(-32768, 32768))),
    ]
    if args.slow:
        cases.append(('slow-full-depth', {'rate': 0.1, 'depth': 1},
                      [8192] * math.ceil(2.6 * RATE / 0.1)))
    if args.case:
        cases = [case for case in cases if case[0] == args.case]
        if not cases:
            parser.error('unknown case; slow-full-depth requires --slow')
    records = []
    for name, params, dry in cases:
        directory = args.output / name
        record = verify_case(source, params, directory, dry)
        wet = read_pcm(directory / 'rtl.pcm')
        assert all(abs(y) <= abs(x) + 1 for x, y in zip(dry, wet)), name
        if name.endswith('bypass'):
            assert list(wet) == dry
        elif name == 'silence':
            assert not any(wet)
        elif name == 'bass':
            change = math.sqrt(sum((y - x) ** 2 for x, y in zip(dry, wet)) /
                               sum(x * x for x in dry))
            assert change > 0.2, change
            record['relative_rms_change'] = change
        elif name == 'full-range':
            assert all(y == 0 or (x > 0) == (y > 0) for x, y in zip(dry, wet))
        else:
            full = params.get('depth') == 1
            assert (min(wet) <= 4 if full else 3270 <= min(wet) < 3300)
            assert 8180 <= max(wet) <= 8192
            midpoint = 4096 if full else 5734
            crossings = [i for i in range(1, len(wet))
                         if wet[i - 1] <= midpoint < wet[i]]
            assert len(crossings) >= 3, crossings
            measured = RATE * (len(crossings) - 1) / (crossings[-1] - crossings[0])
            assert abs(measured - params.get('rate', 4)) < 0.01, measured
            record.update(measured_rate_hz=measured,
                          envelope_min=min(wet), envelope_max=max(wet))
        records.append(record)
        print(f'{name}: {len(dry)} exact samples, {record["max_cycles"]} cycles/sample', flush=True)
    (args.output / 'results.json').write_text(json.dumps(records, indent=2) + '\n')


if __name__ == '__main__':
    main()
