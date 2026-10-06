#!/usr/bin/env python3
"""Qualify the Swamp Machine's compiled DSP and bounded control contrasts."""
import argparse
import json
import math
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dsp_model import read_pcm
from effect_library import RATE, ROOT, prepare, verify_case


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('/tmp/kestrel-swamp'))
    parser.add_argument('--skip-build', action='store_true')
    args = parser.parse_args()
    if not args.skip_build:
        prepare()
    bass = [round(10000 * math.exp(-8 * (n % 22050) / RATE) * sum(
        math.sin(2 * math.pi * 41.2034 * h * n / RATE) / h
        for h in range(1, 7)) / 2) for n in range(3 * RATE)]
    impulse = [0] * (5 * RATE)
    impulse[40000] = 20000
    cases = [
        ('default', {}, bass),
        ('bypass', {'mix': 0}, [-32768, -1, 0, 1, 32767] * 1000),
        ('silence', {}, [0] * 50000),
        ('no-metal', {'metal': 0}, bass),
        ('no-bloom', {'bloom': 0}, bass),
        ('extreme', {'time': 600, 'scatter': 1, 'feedback': 0.85,
                     'damping': 80, 'metal': 1, 'carrier': 400,
                     'bloom': 1, 'mix': 0.8}, bass),
        ('feedback-tail', {'time': 20, 'feedback': 0.85, 'metal': 0,
                           'bloom': 0, 'mix': 0.8}, impulse),
        ('overdrive', {'time': 20, 'feedback': 0, 'metal': 0, 'bloom': 0,
                       'damping': 6000, 'mix': 0.8, 'return': 24, 'dry': 0},
                      [32767] * 45000),
    ]
    records, outputs = [], {}
    def check(case):
        name, params, dry = case
        directory = args.output / name
        record = verify_case(ROOT / 'effects/experimental/SWAMP.EFF', params, directory, dry)
        wet = list(read_pcm(directory / 'rtl.pcm'))
        assert record['max_cycles'] < 2551
        if name == 'bypass':
            assert wet == dry
        elif name == 'silence':
            assert not any(wet)
        else:
            assert record['peak'] <= 32768
            if name == 'default':
                assert record['peak'] < 32767
            energy = sum(x * x for x in dry)
            record['relative_rms_gain'] = math.sqrt(sum(x*x for x in wet) / energy)
            record['relative_rms_change'] = math.sqrt(sum((x-y)**2 for x,y in zip(dry,wet)) / energy)
            if name == 'default':
                assert record['relative_rms_gain'] >= 0.95
                assert record['relative_rms_change'] > 0.1
            if name == 'feedback-tail':
                assert any(wet[41000:50000])
                assert max(abs(x) for x in wet[-RATE:]) < 32
            elif name == 'overdrive':
                assert not any(wet[:400])
                assert wet[-1000:] == [32767] * 1000
        print(f'{name}: {record["samples"]} exact outputs, {record["max_cycles"]} cycles/sample', flush=True)
        return name, record, wet
    with ThreadPoolExecutor(max_workers=3) as workers:
        for name, record, wet in workers.map(check, cases):
            records.append(record)
            outputs[name] = wet
    records[0]['control_contrasts'] = {}
    for name in ('no-metal', 'no-bloom'):
        delta = math.sqrt(sum((x-y)**2 for x,y in zip(outputs['default'],outputs[name])) /
                          sum(x*x for x in bass))
        assert delta > 0.005, (name, delta)
        records[0]['control_contrasts'][name] = delta
    (args.output / 'results.json').write_text(json.dumps(records, indent=2) + '\n')


if __name__ == '__main__':
    main()
