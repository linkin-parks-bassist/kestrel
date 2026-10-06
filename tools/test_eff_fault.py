#!/usr/bin/env python3
"""Render Fault Choir through the compiler/model/core; audition remains separate."""
import argparse
import json
import math
from pathlib import Path

from dsp_model import read_pcm, read_program
from effect_library import RATE, ROOT, prepare, verify_case


def check_topology(program, params):
    time, split = params.get('time', 17), params.get('split', 0.37)
    taps = [math.ceil(time * RATE / 1000),
            math.ceil(time * (0.5 + 0.45 * split) * RATE / 1000)]
    sizes = [tap + 4 + (4 - (tap + 4) % 4) for tap in taps]
    assert program.delays == list(zip(sizes, taps))
    assert len(program) == 31 and not program.polynomials
    assert [word & 31 for word, _, _ in program] == [
        17, 17, 1, 1, 19, 1, 1, 20, 1, 1, 1,
        1, 7, 5, 1, 7, 5, 1, 1, 1, 7, 5, 1, 7, 5, 1, 1, 18, 18, 1, 1]
    for index, handle in ((0, 0), (1, 1), (4, 0), (7, 0), (27, 0), (28, 1)):
        assert program[index][0] >> 20 == handle
    fold = params.get('fold', 0.22)
    for index in (11, 14, 19, 22):
        assert abs(program[index][1] - math.floor(fold * 32768)) <= 1
    for index in (12, 15, 20, 23):
        assert program[index][1] == -32767
    pole = 1 / (1 + 2 * math.pi * params.get('damping', 3500) / RATE)
    assert abs(program[5][1] - math.floor(pole * 32768)) <= 1
    assert abs(program[6][1] - math.floor((1-pole) * 32768)) <= 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('/tmp/kestrel-fault'))
    parser.add_argument('--skip-build', action='store_true')
    args = parser.parse_args()
    if not args.skip_build:
        prepare()
    bass = [round(10000 * math.exp(-8 * (n % 22050) / RATE) * sum(
        math.sin(2 * math.pi * 41.2034 * h * n / RATE) / h
        for h in range(1, 7)) / 2) for n in range(2 * RATE)]
    cases = [('default', {}, bass),
             ('bypass', {'mix': 0}, [-32768, -1, 0, 1, 32767] * 1000),
             ('silence', {}, [0] * 30000),
             ('no-memory', {'feedback': 0}, bass),
             ('low-pressure', {'drive': 1}, bass),
             ('extreme', {'time': 100, 'split': 1, 'feedback': 0.9,
                          'drive': 12, 'fold': 0.05, 'damping': 12000, 'mix': 2}, bass)]
    records, outputs = [], {}
    for name, params, dry in cases:
        directory = args.output / name
        record = verify_case(ROOT / 'effects/experimental/FAULT.EFF', params, directory, dry)
        check_topology(read_program(directory / 'program.bin'), params)
        wet = list(read_pcm(directory / 'rtl.pcm'))
        assert record['blocks'] == 31 and record['max_cycles'] < 2551
        if name == 'bypass':
            assert wet == dry
        elif name == 'silence':
            assert not any(wet)
        else:
            energy = sum(x*x for x in dry)
            record['relative_rms_gain'] = math.sqrt(sum(x*x for x in wet) / energy)
            record['relative_rms_change'] = math.sqrt(sum((x-y)**2 for x,y in zip(dry,wet)) / energy)
            if name == 'default':
                assert record['relative_rms_gain'] >= 0.95
                assert record['relative_rms_change'] > 0.1
                assert record['peak'] < 32767
        record['case'] = name
        records.append(record)
        outputs[name] = wet
        print(f'{name}: {record["samples"]} exact outputs, {record["max_cycles"]} cycles/sample', flush=True)
    records[0]['control_contrasts'] = {}
    for name in ('no-memory', 'low-pressure'):
        contrast = math.sqrt(sum((x-y)**2 for x,y in zip(outputs['default'], outputs[name])) /
                             sum(x*x for x in bass))
        assert contrast > 0.02, (name, contrast)
        records[0]['control_contrasts'][name] = contrast
    (args.output / 'results.json').write_text(json.dumps(records, indent=2) + '\n')


if __name__ == '__main__':
    main()
