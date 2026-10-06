#!/usr/bin/env python3
"""Verify the five-voice chorus, dry bass retention and envelope/spread controls."""
import argparse
import json
import math
from pathlib import Path

from dsp_model import read_pcm, read_program
from effect_library import RATE, ROOT, prepare, verify_case


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('/tmp/kestrel-crowd'))
    parser.add_argument('--skip-build', action='store_true')
    args = parser.parse_args()
    if not args.skip_build:
        prepare()
    bass = [round(9000 * math.exp(-6 * (n % 22050) / RATE) * sum(
        math.sin(2 * math.pi * 41.2034 * h * n / RATE) / h
        for h in range(1, 9)) / 2) for n in range(2 * RATE)]
    cases = [
        ('default', {}, bass),
        ('bypass', {'mix': 0}, [-32768, -1, 0, 1, 32767] * 1000),
        ('silence', {}, [0] * 8192),
        ('dc', {}, [8192] * RATE),
        ('no-envelope', {'feel': 0}, bass),
        ('coincident', {'spread': 0, 'width': 0}, bass),
        ('extreme', {'rate': 3, 'depth': 8, 'spread': 1, 'width': 8,
                     'feel': 1, 'mix': 1}, bass),
    ]
    records, outputs = [], {}
    for name, params, dry in cases:
        directory = args.output / name
        record = verify_case(ROOT / 'effects/experimental/CROWD.EFF', params, directory, dry)
        record['case'] = name
        program = read_program(directory / 'program.bin')
        opcodes = [word & 31 for word, _, _ in program]
        assert len(program) <= 256
        assert len(program.delays) == len(program.polynomials) == 1
        assert (opcodes.count(17), opcodes.count(18), opcodes.count(27)) == (5, 1, 5)
        wet = list(read_pcm(directory / 'rtl.pcm'))
        assert record['max_cycles'] < 2551
        if name == 'bypass':
            assert wet == dry
        elif name == 'silence':
            assert not any(wet)
        elif name == 'dc':
            assert max(abs(y - 8192) for y in wet[-10000:]) < 64
        else:
            energy = sum(x * x for x in dry)
            gain = math.sqrt(sum(y * y for y in wet) / energy)
            change = math.sqrt(sum((y-x)**2 for x, y in zip(dry, wet)) / energy)
            record.update(relative_rms_gain=gain, relative_rms_change=change)
            if name == 'default':
                assert gain >= 0.95 and change > 0.08 and record['peak'] < 32767, record
            outputs[name] = wet
        records.append(record)
        print(f'{name}: {record["samples"]} exact samples, {record["max_cycles"]} cycles/sample', flush=True)
    energy = sum(x*x for x in bass)
    for name in ('no-envelope', 'coincident'):
        contrast = math.sqrt(sum((a-b)**2 for a, b in zip(outputs['default'], outputs[name])) / energy)
        assert contrast > 0.02, (name, contrast)
        next(r for r in records if r['case'] == name)['relative_control_contrast'] = contrast
        print(f'{name}: control contrast {contrast:.4f}', flush=True)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'results.json').write_text(json.dumps(records, indent=2) + '\n')


if __name__ == '__main__':
    main()
