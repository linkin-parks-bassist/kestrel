#!/usr/bin/env python3
"""Check experimental bass chorus against RTL, with independent level/identity checks."""
import argparse
import json
import math
from pathlib import Path

from dsp_model import read_pcm
from effect_library import RATE, ROOT, prepare, verify_case


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('/tmp/kestrel-chorus'))
    parser.add_argument('--skip-build', action='store_true')
    parser.add_argument('--case', choices=('default', 'bypass', 'silence', 'dc', 'maximum-sweep'))
    args = parser.parse_args()
    if not args.skip_build:
        prepare()
    bass = [round(9000 * math.exp(-3 * (n % 11025) / RATE) * sum(
        math.sin(2 * math.pi * 41.2034 * h * n / RATE) / h
        for h in range(1, 7)) / 2) for n in range(4 * RATE)]
    cases = [
        ('default', {}, bass),
        ('bypass', {'mix': 0}, [-32768, -1, 0, 1, 32767] * 1000),
        ('silence', {}, [0] * 4096),
        ('dc', {}, [8192] * RATE),
        ('maximum-sweep', {'rate': 3, 'depth': 10, 'mix': 0.5}, bass),
    ]
    records = []
    for name, params, dry in cases:
        if args.case and name != args.case:
            continue
        directory = args.output / name
        record = verify_case(ROOT / 'effects/experimental/CHORUS.EFF', params, directory, dry)
        wet = read_pcm(directory / 'rtl.pcm')
        assert max(abs(y) for y in wet) <= max(abs(x) for x in dry) + 2, name
        if name == 'bypass':
            assert list(wet) == dry
        elif name == 'silence':
            assert not any(wet)
        elif name == 'dc':
            assert all(abs(y - 8192) <= 2 for y in wet[-10000:])
        else:
            energy = sum(x * x for x in dry)
            gain = math.sqrt(sum(y * y for y in wet) / energy)
            change = math.sqrt(sum((y - x) ** 2 for x, y in zip(dry, wet)) / energy)
            assert change > 0.12 and gain > 0.45 and record['peak'] < 32767, record
            record.update(relative_rms_gain=gain, relative_rms_change=change)
        records.append(record)
        print(f'{name}: {record["samples"]} exact samples, {record["max_cycles"]} cycles/sample',
              flush=True)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'results.json').write_text(json.dumps(records, indent=2) + '\n')


if __name__ == '__main__':
    main()
