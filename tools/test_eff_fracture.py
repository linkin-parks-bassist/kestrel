#!/usr/bin/env python3
"""Check Fracture Memory DSP agreement, dry identity and bounded bass contrast."""
import argparse
import json
import math
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dsp_model import read_pcm, read_program
from effect_library import RATE, ROOT, prepare, verify_case


def verify_allocations(output, descriptor):
    output.mkdir(parents=True, exist_ok=True)
    for tempo in (30, 120, 300):
        program = output / f'tempo-{tempo}.bin'
        subprocess.run([str(ROOT / 'kestrel_interface/bin/lib/compile_eff'),
                        str(descriptor), str(program),
                        f'setting.tempo={tempo}'], check=True)
        parsed = read_program(program)
        size = math.ceil(RATE * 240 / tempo + 16)
        size += 4 - size % 4
        assert parsed.delays == [(size, 1)]
        assert size < (1 << 20) and (size >> 4) < 32768
        assert len(parsed) <= 256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('/tmp/kestrel-fracture'))
    parser.add_argument('--skip-build', action='store_true')
    parser.add_argument('--descriptor', type=Path, default=ROOT / 'effects/experimental/FRACTURE.EFF',
                        help='check a Fracture candidate without replacing the shipped descriptor')
    parser.add_argument('--case', action='append', choices=('default', 'fixed', 'bypass', 'silence', 'chaos', 'bright'),
                        help='run selected checks; omit for the five baseline cases; bright adds sustained high-Dust stress')
    args = parser.parse_args()
    if not args.skip_build:
        prepare()
    verify_allocations(args.output / 'allocations', args.descriptor.resolve())
    bass = [round(9000 * math.exp(-6 * (n % 22050) / RATE) * sum(
        math.sin(2 * math.pi * 41.2034 * h * n / RATE) / h
        for h in range(1, 7)) / 2) for n in range(3 * RATE)]
    cases = [('default', {}, bass), ('fixed', {'fracture': 0}, bass),
             ('bypass', {'mix': 0, 'setting.tempo': 300}, [-32768, -1, 0, 1, 32767] * 10000),
             ('silence', {'setting.tempo': 300}, [0] * 50000),
             ('chaos', {'setting.tempo': 300, 'rate': 4, 'fracture': .7,
                        'spread': 1, 'feedback': .88, 'collision': 4,
                        'pressure': 8, 'damping': 100, 'grip': 1, 'mix': 2},
              bass[:2 * RATE] + [0] * RATE)]
    if args.case:
        if 'bright' in args.case:
            sustained = [round(7000 * math.sin(2 * math.pi * 41.2034 * n / RATE) +
                               1400 * math.sin(2 * math.pi * 82.4068 * n / RATE) +
                               700 * math.sin(2 * math.pi * 164.8136 * n / RATE))
                         for n in range(3 * RATE)]
            cases.append(('bright', {'setting.tempo': 300, 'rate': 4, 'fracture': .7,
                                     'spread': 1, 'feedback': .88, 'collision': 4,
                                     'pressure': 8, 'damping': 12000, 'grip': 1, 'mix': 2},
                          sustained + [0] * (2 * RATE)))
        cases = [case for case in cases if case[0] in args.case]
    records, outputs = [], {}
    def check(case):
        name, params, dry = case
        directory = args.output / name
        record = verify_case(args.descriptor, params, directory, dry)
        record['case'] = name
        wet = list(read_pcm(directory / 'rtl.pcm'))
        assert record['max_cycles'] < 2551
        if name == 'bypass':
            assert wet == dry
        elif name == 'silence':
            assert not any(wet)
        else:
            energy = sum(x*x for x in dry)
            record['relative_rms_gain'] = math.sqrt(sum(x*x for x in wet) / energy)
            record['relative_rms_change'] = math.sqrt(sum((x-y)**2 for x,y in zip(dry,wet)) / energy)
            if name == 'default':
                assert record['relative_rms_gain'] >= 0.9
                assert record['relative_rms_change'] > 0.1
                assert record['peak'] < 32767
            elif name in ('chaos', 'bright'):
                assert record['relative_rms_change'] > 0.1
                driven = (2 if name == 'chaos' else 3) * RATE
                record['rail_samples'] = sum(x in (-32768, 32767) for x in wet)
                tail = wet[driven:]
                record['tail_rms'] = math.sqrt(sum(x*x for x in tail) / len(tail))
                assert record['rail_samples'] == 0, 'extreme controls reach the output rails'
                assert record['tail_rms'] <= math.sqrt(energy / driven), 'tail exceeds excitation RMS'
        print(f'{name}: {record["samples"]} exact outputs, {record["max_cycles"]} cycles/sample', flush=True)
        return name, record, wet
    with ThreadPoolExecutor(max_workers=2) as workers:
        for name, record, wet in workers.map(check, cases):
            records.append(record)
            outputs[name] = wet
    if 'default' in outputs and 'fixed' in outputs:
        contrast = math.sqrt(sum((x-y)**2 for x,y in zip(outputs['default'],outputs['fixed'])) /
                             sum(x*x for x in bass))
        assert contrast > 0.05, contrast
        records[0]['fracture_contrast'] = contrast
    (args.output / 'results.json').write_text(json.dumps(records, indent=2) + '\n')


if __name__ == '__main__':
    main()
